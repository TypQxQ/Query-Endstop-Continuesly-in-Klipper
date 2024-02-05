
# Query Endstop Continuesly in Klipper

Klipper module that adds a G-code command so Klipper will pause until 
specified endstop is in selected state, triggered or not triggered.
Alternativley it can querry a specified amount of times.

## Usage

Query an endstop and wait for it to be triggered or not triggered.

```
QUERY_ENDSTOP_CONTINUESLY ENDSTOP= TRIGGERED= ATEMPTS=
 - ENDSTOP= The name of the endstop to query.
 - TRIGGERED= The state the endstop should be in. 0 or 1.
   Default is 1, Triggered.
 - ATEMPTS= The number of atempts to query the endstop. Default is continuesly.
```

## Examples

```
QUERY_ENDSTOP_CONTINUESLY ENDSTOP=probe TRIGGERED=0 ATEMPTS=5
```
This will query the endstop 'probe' 5 times until it is not triggered, with a 
0.1 second delay between each query. If the endstop is not triggered after 5 
atempts, the command will return. If the endstop is triggered before 5 
atempts, the command will return.
```
QUERY_ENDSTOP_CONTINUESLY ENDSTOP=probe TRIGGERED=0\
```
This will query the endstop 'probe' continuesly until it is not triggered, 
with a 1 second delay between each query. The command will not return until the
 endstop is not triggered.

## Query results

The result can be accessed in GCode macros and other modules under the 
`printer` object.
```
printer.query_endstop_continuesly.last_endstop_query['probe'] : False
```

## Installation

Install by running this command in the shell of your printer running Klipper
```
git.....
```


## This is migrated from Klipper Toolchanger code.

It can for example be used by a Jubilee style toolchanger to check if tool is 
locked and pause a print until it is.
This is also usefull for other toolchangers that check if a tool is mounted or 
parked with endstops.