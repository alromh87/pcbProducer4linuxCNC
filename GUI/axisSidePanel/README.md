# axisSidePanel

Axis Side panel helper for PCB production functions.

	Probing closed indicator (To ensure probing is working before trying)
	Display prepared and actual tool
	Display actual tool offset
	Stablish tool measuring table location (G30.1)
	Controls for launching a probing call
	Feed rate and spindle speed display

Installation

To include as a side panel copy this directory files into gladevcp subfolder in your machine config dir then edit your machine *.ini file to include the next line in [DISPLAY] section:

	GLADEVCP = -H pcbProducer/pcb_producer.hal -u pcbProducer/pcb_producer.py pcbProducer/pcb_producer.ui

