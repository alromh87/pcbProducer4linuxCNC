#
# Makefile para liberar PCBMillingProbbing
# Herramienta para ajustar archivos de codigo G para producción de PCBs
# empleando ajuste de herramienta por probing e integrando en un solo
# archivo: desbaste, barrenos y corte
#

GIT_VERSION	= $$(git rev-parse HEAD)

all: release

release:
		cp PCB_enhancer.py PCB_enhancer_release.py && \
		sed -i "s/\(initial_directory.*=.*'\).*\('\)/\1~\/\2/" PCB_enhancer_release.py && \
#		sed -i "s/\(file_name_mill.*=.*'\).*\('\)/\1\2'/" PCB_enhancer_release.py && \
#		sed -i "s/\(file_name_mill.*= \).*/\1''/" PCB_enhancer_release.py && \
		sed -i "0,/file_name_mill/{s/\(file_name_mill.*= \).*/\1''/}" PCB_enhancer_release.py && \
		sed -i "0,/file_name_drill/{s/\(file_name_drill.*= \).*/\1''/}" PCB_enhancer_release.py && \
		sed -i "0,/file_name_outline/{s/\(file_name_outline.*= \).*/\1''/}" PCB_enhancer_release.py && \
		sed -i "s/\(.*line = \";PCB_enhancer(\).*\().*\)/\1$(GIT_VERSION)\2/" PCB_enhancer_release.py 
