# Query Endstop Continuesly in Klipper
Klipper module that adds a G-code command so Klipper will pause until specified endstop is triggered.

Query an endstop and wait for it to be triggered or not triggered.
>Usage: QUERY_ENDSTOP_CONTINUESLY ENDSTOP= TRIGGERED= ATEMPTS=
ENDSTOP= The name of the endstop to query.
TRIGGERED= The state the endstop should be in. 0 or 1. Default is 1, Triggered.
ATEMPTS= The number of atempts to query the endstop. Default is continuesly.

>Example: QUERY_ENDSTOP_CONTINUESLY ENDSTOP=probe TRIGGERED=0 ATEMPTS=5
This will query the endstop 'probe' 5 times until it is not triggered, with a 0.1 second delay between each query. If the endstop is not triggered after 5 atempts, the command will return. If the endstop is triggered before 5 atempts, the command will return.
>Example: QUERY_ENDSTOP_CONTINUESLY ENDSTOP=probe TRIGGERED=0\
This will query the endstop 'probe' continuesly until it is not triggered, with a 1 second delay between each query. The command will not return until the endstop is not triggered.




This is migrated from Klipper Toolchanger code.
It can for example be used by a Jubilee style toolchanger to check if tool is locked.
If it is not locked in place it will pause until it is.