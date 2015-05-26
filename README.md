# pcbProducer4linuxCNC

Tools to build pcb from pcb2gcode using linuxCNC, including:
	Z Probing and compensation originaly taken from https://github.com/mattvenn/cad/blob/master/tools/etchZAdjust/Etch_Z_adjust.2.2.py
	Engraving, drilling and cutting integration with compensation
	Center drilling
	Tool ofset compensation

Probing is based on conductivity between the cuter and the board.

Usage
	Set tool probing station location
	Load PCB_enhancer.py in linuxCNC and select engrave, drill and cut files. This will integrate all files in one with compensated moves and tool offsets.
	The program will start by meassuring the tool and then probing the board to compensate moves, after that it will start compensated moves, when done with engraving it will make center drilling and then ask for tool change. After each tool change they are meassured in the measuring table in order to compensate moves.

