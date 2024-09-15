'''
Suspend-Klipper-Until-Endstop-State
Copyright (C) 2024 Andrei Ignat <andrei@ignat.se>

This file may be distributed under the terms of the GNU GPLv3 license.
'''
import typing

# Only import these modules for type checking in development.
# Need to add path to Klipper to the Type Checker in VSCode settings.
# Link the klippy folder to the klippy folder in the Klipper source code like so:
# ln -s ~/klipper/klippy/ ~/Query-Endstop-Continuesly-in-Klipper/klippy
if typing.TYPE_CHECKING:
    from ..klipper.klippy import configfile as klippy_cf, mcu as klippy_mcu
    from ..klipper.klippy import gcode as klippy_gcode
    from ..klipper.klippy import klippy, toolhead as klippy_th
    from ..klipper.klippy.extras import query_endstops as klippy_qe


class QueryEndstopContinuesly:
    '''Main class for the module. This is the class that is loaded by Klipper.'''
    def __init__(self, config: 'klippy_cf.ConfigWrapper'):
        #Reference the instance attributes
        self._printer = typing.cast('klippy.Printer', config.get_printer())
        self._reactor = typing.cast('klippy.reactor.Reactor',
                                   self._printer.get_reactor())
        self._gcode = typing.cast('klippy_gcode.GCodeDispatch',
                                 self._printer.lookup_object('gcode'))
        self.last_endstop_query = {}

        # Register the GCode command
        self._gcode.register_command(
            'QUERY_ENDSTOP_CONTINUESLY', self.cmd_QUERY_ENDSTOP_CONTINUESLY, 
            False, self.QUERY_ENDSTOP_CONTINUESLY_help)

    QUERY_ENDSTOP_CONTINUESLY_help = (
        "Query an endstop and wait for it to be triggered or not triggered.\n"
        "Usage: QUERY_ENDSTOP_CONTINUESLY ENDSTOP= TRIGGERED= ATEMPTS=\n"
        "ENDSTOP= The name of the endstop to query.\n"
        "TRIGGERED= The state the endstop should be in. 0 or 1. Default is 1, Triggered.\n"
        "ATEMPTS= The number of atempts to query the endstop. Default is continuously."
        "Example: QUERY_ENDSTOP_CONTINUESLY ENDSTOP=probe TRIGGERED=0 ATEMPTS=5\n"
        "This will query the endstop 'probe' 5 times until it is not triggered"
        ", with a 0.1 second delay between each query."
        "If the endstop is not triggered after 5 atempts, the command will return."
        "If the endstop is triggered before 5 atempts, the command will return."
        "Example: QUERY_ENDSTOP_CONTINUESLY ENDSTOP=probe TRIGGERED=0\n"
        "This will query the endstop 'probe' continuously until it is not triggered"
        ", with a 1 second delay between each query."
        "The command will not return until the endstop is not triggered."

    )
    def cmd_QUERY_ENDSTOP_CONTINUESLY(self, gcmd: 'klippy_gcode.GCodeCommand'):  # pylint: disable=invalid-name
        '''GCode command callback for KTC_ENDSTOP_QUERY. 
        This is the function that is called when the GCode command is executed.
        '''
        endstop_name = gcmd.get("ENDSTOP")
        # If the TRIGGERED parameter is not set, then it is assumed to be 1.
        # This means that the endstop should be triggered.
        # If the TRIGGERED parameter is set to 0, then the endstop should not be triggered.
        should_be_triggered = bool(gcmd.get_int("TRIGGERED", 1, minval=0, maxval=1))
        # The ATEMPTS parameter is the number of times the endstop should be queried.
        # Valid values are 1 or higher.
        # The endstop is queried every 0.1 second if a number of atempts is set.
        # If the ATEMPTS parameter is not set, then it is assumed to be continuously.
        # When it is queried continuously, the endstop is queried every 1 second.
        atempts = gcmd.get_int("ATEMPTS", -1, minval=1)

        self.query_endstop(endstop_name, should_be_triggered, atempts)

    def query_endstop(self, endstop_name, should_be_triggered=True, atempts=-1):
        '''Query the endstop and wait for it to be triggered or not triggered.'''
        # Initialize the local variables
        endstop = None
        toolhead = typing.cast('klippy_th.ToolHead', self._printer.lookup_object("toolhead"))
        eventtime = self._reactor.monotonic()
        query_endstops = typing.cast('klippy_qe.QueryEndstops',
                                     self._printer.lookup_object("query_endstops"))

        # Get the endstop object specified by the GCode command
        for es, name in query_endstops.endstops:
            if name == endstop_name:
                endstop = typing.cast('klippy_mcu.MCU_endstop', es)
                break
        if endstop is None:
            raise self._printer.command_error(f"Unknown endstop '{endstop_name}'")

        # If atempts is -1 then we are running continuously.
        dwell = 0.1
        if atempts == -1:
            dwell = 1.0

        a = 0   # Counter for the number of atempts
        # while not self._printer.is_shutdown()
        while self._printer.get_state_message()[1] == "ready":
            a += 1
            last_move_time = toolhead.get_last_move_time()
            is_triggered = bool(endstop.query_endstop(last_move_time))

            # Break if the endstop is in the state we are waiting for.
            if is_triggered == should_be_triggered:
                break

            # Break if we have reached the number of atempts
            if atempts > 0 and atempts <= a:
                break

            eventtime = self._reactor.pause(eventtime + dwell)

        self.last_endstop_query[endstop_name] = is_triggered

    def get_status(self, eventtime=None):   # pylint: disable=unused-argument
        '''Return the status of the module to Klipper as JSON. 
        This is the function that is called when Klipper requests the status of the module.'''
        status = {
            "last_endstop_query": self.last_endstop_query,
        }
        return status

def load_config(config):
    '''Load the module into Klipper. This is the function that is called by Klipper.'''
    return QueryEndstopContinuesly(config)
