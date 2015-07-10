# GUI components

Helpers for PCB production functions
To use them copy this directory files into pcbProducer subfolder in your machine config dir then edit your machine *.ini file to include needed line in [DISPLAY] section

## Gmocappy extra controls

* Probing closed indicator (To ensure probing is working before trying)
* Stablish tool measuring table location (G30.1)
* Controls for launching a probing call

### Installation

To include as an extra panel next to speed controls, use:

	EMBED_TAB_NAME = Probing
	EMBED_TAB_LOCATION = box_custom_1
	EMBED_TAB_COMMAND = gladevcp -x {XID} -c probing -H pcbProducer/gmoccapy/probing.hal pcbProducer/gmoccapy/probing.glade

## Axis lateral Panel

* Probing closed indicator (To ensure probing is working before trying)
* Display prepared and actual tool
* Display actual tool offset
* Stablish tool measuring table location (G30.1)
* Controls for launching a probing call
* Feed rate and spindle speed display

### Installation

To include as a side panel, use:

	GLADEVCP = -H pcbProducer/axisSidePanel/pcb_producer.hal -u pcbProducer/axisSidePanel/pcb_producer.py pcbProducer/axisSidePanel/pcb_producer.ui

## Probing emulation (just for testing enhancer algorithm)

* GUI Control to send probe touch emulation

### Installation

To included stand alone, use:

	EMBED_TAB_NAME = Probing_emulation
	EMBED_TAB_LOCATION = ntb_user_tabs
	EMBED_TAB_COMMAND = gladevcp -c probing_emul -H pcbProducer/emul/probing_emul.hal pcbProducer/emul/probing_emul.glade

