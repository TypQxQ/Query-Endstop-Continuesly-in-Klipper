'''
Suspend-Klipper-Until-Endstop-State
Copyright (C) 2024 Andrei Ignat <andrei@ignat.se>

This file may be distributed under the terms of the GNU GPLv3 license.
'''
import typing

# Only import these modules for type checking in development.
# Need to add path to Klipper to the Type Checker in VSCode settings.
# Link the klippy folder to the klippy folder in the Klipper source code like so:
# ln -s ~/klipper/klippy/ ~/Suspend-Klipper-Until-Endstop-Triggers/klippy
if typing.TYPE_CHECKING:
    from .klippy import configfile, gcode
    from .klippy import klippy
    from .klippy.extras import gcode_macro

class SuspendKlipperUntilEndstopState:
    '''Main class for the module. This is the class that is loaded by Klipper.'''
    def __init__(self, config: typing.Optional['configfile.ConfigWrapper'] = None):
        #Reference the instance attributes
        self._config = config
        self.printer = typing.cast('klippy.Printer', config.get_printer())
        self.reactor = typing.cast('klippy.reactor.Reactor', self.printer.get_reactor())
        self.gcode = typing.cast('gcode.GCodeDispatch', self.printer.lookup_object('gcode_macro'))
        self.last_endstop_query = {}

        # Register the GCode command
        self.gcode.register_command(
            'KTC_ENDSTOP_QUERY', self.SUSPEND_KLIPPER_UNTIL_ENDSTOP_STATE, 
            False, self.SUSPEND_KLIPPER_UNTIL_ENDSTOP_STATE_help)

    SUSPEND_KLIPPER_UNTIL_ENDSTOP_STATE_help = (
        "Wait for a ENDSTOP= untill it is TRIGGERED=0/[1] or ATEMPTS=#"
    )
    def SUSPEND_KLIPPER_UNTIL_ENDSTOP_STATE(self, gcmd: 'gcode.GCodeCommand'):
        '''GCode command callback for KTC_ENDSTOP_QUERY. 
        This is the function that is called when the GCode command is executed.'''
        endstop_name = gcmd.get("ENDSTOP")
        should_be_triggered = bool(gcmd.get_int("TRIGGERED", 1, minval=0, maxval=1))
        atempts = gcmd.get_int("ATEMPTS", -1, minval=1)

        self.query_endstop(endstop_name, should_be_triggered, atempts)

    def query_endstop(self, endstop_name, should_be_triggered=True, atempts=-1):
        '''Query the endstop and wait for it to be triggered or not triggered.'''
        # Get endstops
        endstop = None
        query_endstops = self.printer.lookup_object("query_endstops")
        for es, name in query_endstops.endstops:
            if name == endstop_name:
                endstop = es
                break
        if endstop is None:
            raise Exception("Unknown endstop '%s'" % (endstop_name))

        toolhead = self.printer.lookup_object("toolhead")
        eventtime = self.reactor.monotonic()

        dwell = 0.1
        if atempts == -1:
            dwell = 1.0

        i = 0
        while not self.printer.is_shutdown():
            i += 1
            last_move_time = toolhead.get_last_move_time()
            is_triggered = bool(endstop.query_endstop(last_move_time))
            self.log.trace(
                "Check #%d of %s endstop: %s"
                % (i, endstop_name, ("Triggered" if is_triggered else "Not Triggered"))
            )
            if is_triggered == should_be_triggered:
                break
            # If not running continuesly then check for atempts.
            if atempts > 0 and atempts <= i:
                break
            eventtime = self.reactor.pause(eventtime + dwell)
        # if i > 1 or atempts == 1:
        # self.log.debug("Endstop %s is %s Triggered after #%d checks." % (endstop_name, ("" if is_triggered else "Not"), i))

        self.last_endstop_query[endstop_name] = is_triggered

    def get_status(self, eventtime=None):   # pylint: disable=unused-argument
        status = {
            "last_endstop_query": self.last_endstop_query,
        }
        return status

def load_config(config):
    '''Load the module into Klipper. This is the function that is called by Klipper.'''
    return SuspendKlipperUntilEndstopState(config)
