#!/usr/bin/python


##  Introduction
#     This code when run will ask you: 
#     (1) what units your file uses (inch or mm)
#     (2) how many steps you want your probe gride to have on the X axis
#     (3) how many steps you want your probe gride to have on the Y axis
#     (4) which PCB G code file you want to etch

#     It then gets your mill to probe a grid on a blank PCB based on your spacing
#     It stores the probe Z values to memory, then uses those Z values to adjust Z heights for etch moves along the now well probed PCB.
#     You can reuse the generated file again and again as it will always start out by re-probing the surface before etching. 

#     It is based on a neat idea by Poul-Henning Kamp. See: http://phk.freebsd.dk/CncPcb/index.html
#     It also links to a version of Opti, a file optimisation utility that optimises etch paths, that was first posted by
#     Daniel Purvis and later added to by Jay Couture. See: http://pcbgcode.org/read.php?6,5
#     Many thanks to Jay Couture for customising Opti to allow it to be called from within a python script!

##  Where the output is saved
#     The output is saved to a new file where 
#     file_out_name = file_in_name + file_name_suffix, 
#     and the default file out suffix (which you could change by modifying the code) is "_Zadj_[grid size].ngc"
#     Finally, and this is very handy if you are running the Python code in EMC2, it outputs the file to the screen, and you are ready to roll.
#     You can always comment out the print line if you don't need it.

##  What it doesn't do
#     It doesn't reject spurious probe values - you need to make sure the PCB blank you use is clean and free of debris
#     It doesn't optimise X Y paths (you could use opti_qt.exe to do this first - see http://pcbgcode.org/read.php?6,5,5)) 
#     It doesn't optimise X Y moves between drills (Opti_qt can do this for 'simple drill moves', Gopt is apparently better for multiple drill sizes)
#     It doesn't adjust Z heights during arc etching (G02 and G03 moves) - this should not be a problem if arcs have a diameter of less than 10mm.
#     Feel free to address any of these issues!

##  How it works
#     This Python code parses your selected G code file and looks at every etch move: G01 Xaa Ybb Zcc Fdd, where Z is greater than -0.5 
#     It ignores milling and drilling moves ie where Z is deeper than -0.5mm.  
#     It finds the max and min values of X and Y from amongst the file's etch moves.
  
#     It then generates a custom G code routine that will probe a grid that encompasses those max and min X and Y values. 
#     The probe points are spaced by the selected grid spacing, and the Z values at each probe point are stored in memory. 

#     It generates a G code subroutine that will draw on the stored probe data and does the etching on the PCB at the adjusted heights. 
#     For long etch moves it puts in a way point at a distance of half the X grid spacing and calculates a new etch depth for each way point 
#     as it goes along.

#     All the etch moves in the original file(ie G01 Xaa Ybb Zcc Fdd (where Z is greater than -0.5) are then replaced by a subroutine call
#        in the format O200 sub [x_start] [y_start] [aa] [bb]  (where O200 is the etch subroutine referred to above)

##  Using Opti
#     If you wish to use the Opti optimisation file option, 
#      (1) make sure Opt_cli's location is correctly specified in 'opti_path' below
#      (2) remember Opti is a very fast, but specific purpose optimiser
#     Opti will work only on a file that contains only etch moves with no tool changes
#     Tool changes and drill moves in a file will cause Opti to hang.

##  Defaults
#     You can change the defaults below here.  There are four sections. Three sections are immediately below here:
#     unitless defaults, inch defaults and mm defaults. The fourth, Tkinter defaults is well below (but well labelled).
#     Note that inch and mm defaults are not interchangeable, if you change an inch default it does not update the mm default.
#     For ease of use you may want to change the default start up directory 'initial directory' below.
#     If you are going to use Opti, make sure Opti_cli's location is correctly specified in 'opti_path' below.
#     The ~/ notation doesn't work - you must give the full path.
 

# UNITLESS DEFAULTS: These values are not unit sensitive (you can change these here)
initial_directory = '/home/alejandro/Descargas/pcb2gcode_gui/PCBMillingProbing'
opti_path         = ''
X_grid_lines      = 10
Y_grid_lines      =  5
units             = "inch"
grid_def          = "step size"
file_in_name      = ''
file_name_mill    = '/home/alejandro/Descargas/pcb2gcode_gui/PCBMillingProbing/back.ngc'
file_name_drill   = '/home/alejandro/Descargas/pcb2gcode_gui/PCBMillingProbing/drill.ngc'
file_name_outline = '/home/alejandro/Descargas/pcb2gcode_gui/PCBMillingProbing/outline.ngc'

G_modal           = 0
G_dest            = 0
M_dest            = 0
mill_loaded       = False
mill_finished     = False
drill_loaded      = False
drill_finished    = False
first_drill       = True
outline_loaded    = False
outline_finished  = False

G_modal_codes     = [0,1,81]
G_codes_probing   = [1,81]
  
def Unit_set():
    global units,units_G_code,X_dest,Y_dest,Z_dest,etch_definition,etch_speed,probe_speed,probe_speed_fast,z_safety,z_probe
    global etch_depth,etch_max,z_trivial,z_probe_detach,z_tool_change,grid_clearance,step_size,tool_probe
    global X_grid_lines,Y_grid_lines,grid_def

    to_inch = 1/25.4

    # MM DEFAULTS: if units are mm, set the defaults in mm (you can change these here too)
#    if units == "mm": 
    units_G_code      =              21
    X_dest            =          -80.00
    Y_dest            =           40.00
    Z_dest            =           40.00
    etch_definition   =           -0.50
    etch_speed        =          120.00
    etch_depth        =            0.10
    etch_max          =            0.50
    probe_speed       =           20.00
    probe_speed_fast  =  probe_speed*10
    z_safety          =            1.50  
    z_probe           =           -1.50
    tool_probe        =          -45.00
    z_trivial         =            0.02
    z_probe_detach    =           15.00
    z_tool_change     =           45.00
    grid_clearance    =            0.01
    step_size         =           10.00

    # INCH DEFAULTS: if units are inches, adjust them
    if units == "inch": 
        units_G_code      =                          20
        X_dest            =              X_dest*to_inch
        Y_dest            =              Y_dest*to_inch 
        Z_dest            =              Z_dest*to_inch
        etch_definition   =     etch_definition*to_inch
        etch_speed        =          etch_speed*to_inch
        etch_depth        = round(etch_depth*to_inch,4)
        etch_max          =            etch_max*to_inch 
        probe_speed       =         probe_speed*to_inch
        probe_speed_fast  =    probe_speed_fast*to_inch
        z_safety          =            z_safety*to_inch
        z_probe           =             z_probe*to_inch
        tool_probe        =          tool_probe*to_inch
        z_trivial         =           z_trivial*to_inch
        z_probe_detach    =      z_probe_detach*to_inch
        z_tool_change     =      z_tool_change*to_inch
        grid_clearance    =      grid_clearance*to_inch
        step_size         =  round(step_size*to_inch,4)


def Unit_sel():
    global units,G_dest,X_dest,Y_dest,Z_dest,etch_definition,etch_speed,probe_speed,z_safety,z_probe
    global etch_depth,etch_max,z_trivial,z_probe_detach,z_tool_change,grid_clearance,step_size,tool_probe
    global X_grid_lines,Y_grid_lines,grid_def, file_name_mill, file_name_drill
    
    units = get_units.get()
    Unit_set()
    
    # Refresh the defaults in the display
    RB_step.config(text = "grid step size (" + units + ")")
    L_etch_depth.config(text = "Etch depth (" + units + "):")
    Ent_etch_depth.delete(0, END)
    Ent_etch_depth.insert(0, etch_depth)
    Ent_step.config(state=NORMAL)
    Ent_step.delete(0, END)
    Ent_step.insert(0, step_size)
    if get_grid_def.get() == "grid lines":
        Ent_step.config(state=DISABLED)
  
def Def_sel():
    grid_def = get_grid_def.get()
    if grid_def == "step size":
        Ent_X.config(state=DISABLED)
        Ent_Y.config(state=DISABLED)
        Ent_step.config(state=NORMAL)
    
    elif grid_def == "grid lines":
        Ent_X.config(state=NORMAL)
        Ent_Y.config(state=NORMAL)
        Ent_step.config(state=DISABLED)
        Ent_X.delete(0, END)
        Ent_X.insert(0, X_grid_lines)
        Ent_Y.delete(0, END)
        Ent_Y.insert(0, Y_grid_lines)        

def BrowseMill():
    global file_name_mill, initial_directory
    import tkFileDialog
    file_name_mill = tkFileDialog.askopenfilename(parent=top,initialdir=initial_directory,
                                        filetypes= [('nc files', '*.ngc'),('nc files', '*.nc')],
                                        title='Choose Mill file to import:')
    L_file_name_mill.config(text = file_name_mill)
    if file_name_mill != '':
        n = file_name_mill.rfind("/")
        initial_directory = file_name_mill[0:n]

def BrowseDrill():
    global file_name_drill, initial_directory
    import tkFileDialog
    file_name_drill = tkFileDialog.askopenfilename(parent=top,initialdir=initial_directory,
                                        filetypes= [('nc files', '*.ngc'),('nc files', '*.nc')],
                                        title='Choose Drill file to import:')
    L_file_name_drill.config(text = file_name_drill)
    if file_name_drill != '':
        n = file_name_drill.rfind("/")
        initial_directory = file_name_drill[0:n]

def BrowseOutline():
    global file_name_outline, initial_directory
    import tkFileDialog
    file_name_outline = tkFileDialog.askopenfilename(parent=top,initialdir=initial_directory,
                                        filetypes= [('nc files', '*.ngc'),('nc files', '*.nc')],
                                        title='Choose Outline file to import:')
    L_file_name_outline.config(text = file_name_outline)
    if file_name_outline != '':
        n = file_name_outline.rfind("/")
        initial_directory = file_name_outline[0:n]

def OK() :
    global OK, file_name_mill
    if file_name_mill == '' and file_name_drill == '' and file_name_outline == '': OK = False
    else: OK = True
    top.destroy()

def Cancel() :
    global OK
    OK = False
    top.destroy()   

# Entry validation functions
def IntCheck(new_string) :
    if new_string == "": new_string = "0"
    try:
        v = int(new_string)
        if v > 99 or v < 0: return False
        return True
            # True tells Tkinter to accept the new string
    except ValueError:
        return False
            # False means don't accept it

def EtchCheck(new_string) :
    global etch_max
    if new_string == "": new_string = "0"
    try:
        v = float(new_string)
        if v > etch_max or v < 0: return False
        if len(new_string) > 6 : return False
        return True
            # True tells Tkinter to accept the new string
    except ValueError:
        return False
            # False means don't accept it

def StepCheck(new_string) :
    if new_string == "": new_string = "0"
    try:
        v = float(new_string)
        if v < 0: return False
        if len(new_string) > 6 : return False
        return True
            # True tells Tkinter to accept the new string
    except ValueError:
        return False
            # False means don't accept it

# parsing functions
def get_num(line,char_ptr,num_chars):
    char_ptr=char_ptr+1
    numstr = ''
    good   = '-.0123456789'  
    while char_ptr < num_chars:
        digit = line[char_ptr]
        if good.find(digit) != -1:
           numstr = numstr + digit
           char_ptr = char_ptr + 1
        else: break    
    return numstr

def test_X(X_min, X_max):
    if X_dest < X_min : X_min = X_dest
    elif X_dest > X_max : X_max = X_dest
    return X_min, X_max

def test_Y(Y_min, Y_max):
    if Y_dest < Y_min : Y_min = Y_dest
    elif Y_dest > Y_max : Y_max = Y_dest
    return Y_min, Y_max
            

## Don't change these ...
file_in        = []
file_out       = []
intro          = []
numstr         = ''
char           = ''
drill_guides   = []
drill_moves    = []
outline_moves  = []

# Set units up to start
Unit_set()

# Fire up the Tkinter GUI
from Tkinter import *
top = Tk()
top.title("Etch_Z_adjust setup")

# Define the Tkinter variables
get_units       = StringVar()
get_grid_def    = StringVar()
get_X           = IntVar()
get_Y           = IntVar()
get_step        = DoubleVar()
get_etch        = DoubleVar()
get_file_in     = StringVar()
get_opti        = BooleanVar()

# define the label, checkbutton, radiobutton, button and entry widgets:
# Label widgets:
L_blank1             = Label(top, text="")
L_blank2             = Label(top, text="")
L_blank3             = Label(top, text="")                       
L_blank4             = Label(top, text="")
L_blank5             = Label(top, text="")    
L_units              = Label(top, text="Units to use:")
L_grid_def           = Label(top, text="Define grid by:")
L_X_eq               = Label(top, text="X  = ")
L_Y_eq               = Label(top, text="Y  = ")
L_etch_depth         = Label(top, text="Etch depth:")
L_file_mill_quest    = Label(top, text="Mill file:")
L_file_name_mill     = Label(top, text= file_name_mill)
L_file_drill_quest   = Label(top, text="Drill file:")
L_file_name_drill    = Label(top, text= file_name_drill)
L_file_outline_quest = Label(top, text="Outline file:")
L_file_name_outline  = Label(top, text= file_name_outline)

# Checkbutton
C_opti = Checkbutton(top, text="Use Opti to optimise etch path", variable=get_opti)

# Radiobutton widgets:
RB_inch         = Radiobutton(top, padx=45, text="inch",                 variable=get_units,    value="inch",       command=Unit_sel)
RB_mm           = Radiobutton(top, padx=45, text="millimetre",           variable=get_units,    value="mm",         command=Unit_sel)
RB_lines        = Radiobutton(top, padx=45, text="number of grid lines", variable=get_grid_def, value="grid lines", command=Def_sel)
RB_step         = Radiobutton(top, padx=45, text="grid step size",       variable=get_grid_def, value="step size",  command=Def_sel)

# Button widgets:
B_browse_mill     = Button(top, text ="Browse...", command = BrowseMill)
B_browse_drill    = Button(top, text ="Browse...", command = BrowseDrill)
B_browse_outline  = Button(top, text ="Browse...", command = BrowseOutline)
B_cancel          = Button(top, text ="CANCEL",    command = Cancel)
B_OK              = Button(top, text ="OK",        command = OK)

# Entry widgets validation process
# The validation process in Tkinter is not straight forward...

# top.register(validate_function) gives a number that, when called by validatecommand in the Entry widget,
# allows validatecommand to pass a Tk % parameter to the validate_function so it can determine if the edit is to be allowed. 
# ' %P' (the space is important) is the Tk % parameter for the string that would result if the edit was to be allowed.
# For a list of other Tk % parameters, see: http://www.tcl.tk/man/tcl8.4/TkCmd/entry.htm#M16 .
# For more detail on this tortuous validation method, see:
# http://www.velocityreviews.com/forums/t329365-re-using-bound-variables-in-tkinter-events.html

# Define validation function numbers for validatecommand to call 
val_int  = top.register(IntCheck)
val_etch = top.register(EtchCheck)
val_step = top.register(StepCheck)

# Entry widget definitions:
Ent_X           = Entry(master=top, width = 2,  textvariable = get_X,
                        validate = "key", validatecommand = val_int + ' %P')
Ent_Y           = Entry(master=top, width = 2,  textvariable = get_Y,
                        validate = "key", validatecommand = val_int + ' %P')
Ent_step        = Entry(master=top, width = 6,  textvariable = get_step,
                        validate = "key", validatecommand = val_step + ' %P')
Ent_etch_depth  = Entry(master=top, width = 6,  textvariable = get_etch,
                        validate = "key", validatecommand = val_etch + ' %P ')
Ent_file_in     = Entry(master=top, width = 70, textvariable =  get_file_in,
                        justify = RIGHT, state = DISABLED)  

# lay out the widgets:
L_blank1.grid       (row=0, column=0)
L_units.grid        (row=1, column=0, sticky=W, padx = 25)
RB_mm.grid          (row=2, column=0, sticky=W)
RB_inch.grid        (row=3, column=0, sticky=W)
L_blank2.grid       (row=4, column=0)
L_blank3.grid       (row=6, column=1)

L_grid_def.grid     (row=1, column=1, sticky=W, padx = 25)
RB_step.grid        (row=2, column=1, sticky=W)
Ent_step.grid       (row=2, column=2, sticky=W)

RB_lines.grid       (row=3, column=1, sticky=W)
L_X_eq.grid         (row=3, column=2, sticky=E)
Ent_X.grid          (row=3, column=3, sticky=W)
L_Y_eq.grid         (row=4, column=2, sticky=E)
Ent_Y.grid          (row=4, column=3, sticky=W)
L_etch_depth.grid   (row=6, column=1, sticky=W, padx = 25)
Ent_etch_depth.grid (row=6, column=2, sticky=W)

C_opti.grid         (row=6, column=0, padx = 43)

L_blank4.grid             (row=9, column=1)
L_file_mill_quest.grid    (row=10, column=0, sticky=W, padx = 25)
L_file_name_mill.grid     (row=10, column=1, columnspan = 2)
B_browse_mill.grid        (row=10, column=3, sticky=W, padx = 25)
L_file_drill_quest.grid   (row=11, column=0, sticky=W, padx = 25)
L_file_name_drill.grid    (row=11, column=1, columnspan = 2)
B_browse_drill.grid       (row=11, column=3, sticky=W, padx = 25)
L_file_outline_quest.grid (row=12, column=0, sticky=W, padx = 25)
L_file_name_outline.grid  (row=12, column=1, columnspan = 2)
B_browse_outline.grid     (row=12, column=3, sticky=W, padx = 25)
B_OK.grid                 (row=13, column=1, sticky=W, padx = 43)
B_cancel.grid             (row=13, column=2)
L_blank5.grid             (row=14, column=1)


## Tkinter defaults
#   set the default units  
if units == "inch":
    RB_inch.select()
else:
    RB_mm.select()

Unit_sel()

#   set the default grid definition
RB_step.select()
# RB_lines.select()

Def_sel()

#   use Opti by default
# C_opti.select()

## End Tkinter defaults


# Now let's get the Tkinter loop twirling
top.mainloop()

# After exiting the Tkinter loop, process the data
if OK == True:
    units        = get_units.get()
    grid_def     = get_grid_def.get()
    step_size    = get_step.get()
    etch_depth   = - get_etch.get()
    X_grid_lines = get_X.get()
    Y_grid_lines = get_Y.get()
    opti         = get_opti.get()

    # Do optimisation first?
    if opti == True:
        if file_name_mill != '':
            n = file_name_mill.rfind(".")
            file_out_name = file_name_mill[0:n] + "_OPT.nc"
            import subprocess
            p = subprocess.call([opti_path, file_name_mill, file_out_name])
            file_name_mill = file_out_name

#TODO: optimize drill too, ver si funciona
        if file_name_drill != '':
            n = file_name_drill.rfind(".")
            file_out_name = file_name_drill[0:n] + "_OPT.nc"
            import subprocess
            p = subprocess.call([opti_path, file_name_drill, file_out_name])
            file_name_drill = file_out_name

    # read in Mill G code file
    if file_name_mill != '':
        file_in_name = file_name_mill
        f = open(file_name_mill, 'r')
        mill_loaded = True
        for line in f:
            file_in.append(line)
        f.close()

    # read in Drill G code file
    if file_name_drill != '':
        if file_in_name == '':
            file_in_name = file_name_drill
        f = open(file_name_drill, 'r')
        drill_loaded = True
        for line in f:
            file_in.append(line)
        f.close()

    # read in Outline G code file
    if file_name_outline != '':
        if file_in_name == '':
            file_in_name = file_name_outline
        f = open(file_name_outline, 'r')
        outline_loaded = True
        for line in f:
            file_in.append(line)
        f.close()

    # Use these for checking max and min values later in the imported file
    is_first_X = True
    is_first_Y = True
    is_first_Z = True

    tool_change_commanded = False

    # parse each line
    line_ptr=0
    num_lines=len(file_in)
    while line_ptr < num_lines:
        line = file_in[line_ptr]
        X_start = X_dest
        Y_start = Y_dest
        Z_start = Z_dest
        
    # parse each character
        char_ptr = 0
        num_chars= len(line)
        coord_count = 0
        G_found     = False
        while char_ptr < num_chars:
            char = line[char_ptr]      
            if '(;'.find(char) != -1:
                break              
            elif char == 'G' :
                G_dest = int(get_num(line,char_ptr,num_chars))
                coord_count = coord_count+1
                G_found = True
            elif char == 'X' :
                X_dest = float(get_num(line,char_ptr,num_chars))
                coord_count = coord_count+1
            elif char == 'Y' :
                Y_dest = float(get_num(line,char_ptr,num_chars))
                coord_count = coord_count + 1
            elif char == 'Z' :
                Z_dest = float(get_num(line,char_ptr,num_chars))
                coord_count = coord_count + 1
            elif char == 'R' :
                R_dest = float(get_num(line,char_ptr,num_chars))
            elif char == 'F' :
                F_dest = float(get_num(line,char_ptr,num_chars))
            elif char == 'M' :
                M_dest = int(get_num(line,char_ptr,num_chars))
            char_ptr = char_ptr + 1

        if M_dest == 2:        # We ignore program end, since we are still adding files
            line = "M5 (Detener usillo)\n"
            M_dest = -1
            line_ptr=line_ptr+1
            if mill_loaded and not mill_finished:
                mill_finished = True
                if outline_loaded and not drill_loaded:
                    line = line + ("G00 Z%.4f(Salir para iniciar cambio de herramienta)\n(MSG, Coloque cortador recto para exterior)\nT1\nM6\nM0\nO<_probe_tool> call\n" % (z_tool_change))
                file_out.append(line)
            elif drill_loaded and not drill_finished:
                drill_finished = True
                if mill_finished:
                    drill_guides.append(line)
                if outline_loaded:
                    line = line + ("G00 Z%.4f(Salir para iniciar cambio de herramienta)\n(MSG, Coloque cortador recto para exterior)\nT1\nM6\nM0\nO<_probe_tool> call\n" % (z_tool_change))
                    drill_moves.append(line)
            elif outline_loaded and not outline_finished:
                    outline_finished = True
            continue

        if M_dest == 6:        # linuxCNC realiza el cambio de herramienta en M6
            line = ("G00 Z%.4f(Salir para iniciar cambio de herramienta)\n" % (z_tool_change)) + line + "O<_probe_tool> call \n"
            M_dest = -1
#            tool_change_commanded = True

#        if tool_change_commanded and M_dest == 0:
#            line = ("G00 Z%.4f(Salir para iniciar cambio de herramienta)\n" % (z_tool_change)) + line + "O<_probe_tool> call \n"
#            tool_change_commanded = False
        
        # Thake in account modal instructions
        if G_found:
            if G_dest in G_modal_codes:
                G_modal = G_dest
        else:
            if coord_count > 0:
                G_dest = G_modal

        # if we should consider coordinates for probbing
        if G_dest in G_codes_probing:
            # then check for max and min X and Y values
            if is_first_X == True :
                X_min = X_dest
                X_max = X_dest
                is_first_X = False
            else : (X_min, X_max) = test_X(X_min, X_max)

            if is_first_Y == True :
                Y_min = Y_dest
                Y_max = Y_dest
                is_first_Y = False
            else : (Y_min, Y_max) = test_Y(Y_min, Y_max)

        # if the line is an etch move, then replace the line with an etch call        
        if G_dest == 1 and Z_dest < 0:
            G_dest = -1
#        if G_dest == 1 and Z_dest > etch_definition:
            line = 'O200 call [%.4f] [%.4f] [%.4f] [%.4f] [%.4f]\n' % (X_start, Y_start, X_dest, Y_dest, Z_dest)

        # if the line is a drill move, then replace the line with an adjusted drill call        
        if G_dest == 81:
            G_dest = -1
            if mill_finished: #If we have loaded mill, add drill guides              
                if first_drill:
                    line = '\n(MSG, Iniciando guias de barrenos)\n\nM3      ( Spindle on clockwise.        )\n'
                    drill_guides.append(line)
                    first_drill = False
#                line = 'O300 call [%.4f] [%.4f] [%.4f] [%.4f] [%.4f]\n' % (X_dest, Y_dest, etch_depth, z_safety, F_dest) #Para menor tiempo
                line = 'O300 call [%.4f] [%.4f] [%.4f] [%.4f] [%.4f]\n' % (X_dest, Y_dest, etch_depth, R_dest, F_dest)
                drill_guides.append(line)

            line = 'O300 call [%.4f] [%.4f] [%.4f] [%.4f] [%.4f]\n' % (X_dest, Y_dest, Z_dest, R_dest, F_dest)

        if mill_finished:
            drill_moves.append(line)
        elif drill_finished:
            outline_moves.append(line)
        else:    
            file_out.append(line)
        line_ptr=line_ptr+1

    # Now we have processed the data, check for etch moves
    if is_first_X == False:

        # then there were etch moves so get to work!

        # first stretch the X and Y max and min values a _tiny_ amount so the grid is just outside all the etch points
        X_min = X_min - grid_clearance
        X_max = X_max + grid_clearance
        Y_min = Y_min - grid_clearance
        Y_max = Y_max + grid_clearance
        t_line = ';Datos de circuito X_min =  %.4f , X_max = %.4f , Y_min =  %.4f , Y_max = %.4f\n' % (X_min, X_max, Y_min, Y_max)
        intro.append(t_line)


        # Use max and min values for the etch moves to work out the probe grid dimensions
        X_span = X_max - X_min
        X_grid_origin = X_min 
        Y_span = Y_max - Y_min
        Y_grid_origin = Y_min

        # Work out how many X and Y grid lines, using the approximate step size
        if grid_def == "step size" :  
            X_grid_lines = 2 + int(X_span/step_size)
            Y_grid_lines = 2 + int(Y_span/step_size)
            
        # Make sure grid lines are at least 2 
        if X_grid_lines < 2 : X_grid_lines = 2
        if Y_grid_lines < 2 : Y_grid_lines = 2

        # Now work out exact step sizes for X and Y
        Y_step_size = Y_span / (Y_grid_lines - 1)
        X_step_size = X_span / (X_grid_lines - 1)

        # Now we can name the output file
        file_name_suffix = "_Zadj_%dx%d.ngc" % (X_grid_lines, Y_grid_lines)
        n = file_in_name.rfind(".")
        if n != -1:
            file_out_name = file_in_name[0:n] + file_name_suffix
        else: file_out_name = file_in_name + file_name_suffix

        # OK now output the G code intro
        # (define the variables, set up the probe subroutine, the etch subroutine and the code to probe the grid)
        from time import localtime, strftime
        line = ";PCB_enhancer(): \n"
        intro.append(line)
        line = "(Imported from:  " + file_name_mill + " at " + strftime("%I:%M %p on %d %b %Y", localtime())+ ")\n"
        intro.append(line)
#TODO si se utilizo archivo de barrenos mencionarlo
        line = "(Drill file:     " + file_name_drill + " at " + strftime("%I:%M %p on %d %b %Y", localtime())+ ")\n"
        intro.append(line)
        line = "(Outline file:   " + file_name_outline + " at " + strftime("%I:%M %p on %d %b %Y", localtime())+ ")\n"
        intro.append(line)
        line = "(Output saved as " + file_out_name + ")\n\n"
        intro.append(line)
        line = "(G code configuration section)\n(you can change these values in the python code or in the G code output:)\n"
        intro.append(line)
        line = ("G%2d (" + units + ")\n") % (units_G_code)
        intro.append(line)
        line = "#<_etch_depth>         =   %.4f \n" % (etch_depth)
        intro.append(line)
        line = "#<_etch_speed>         =  %.4f \n" % (etch_speed)
        intro.append(line)
        line = "#<_probe_speed>        =   %.4f \n" % (probe_speed)
        intro.append(line)
        line = "#<_probe_speed_fast>   =   %.4f \n" % (probe_speed_fast)
        intro.append(line)
        line = "#<_z_safety>           =    %.4f \n" % (z_safety)
        intro.append(line)
        line = "#<_z_probe>            =   %.4f \n" % (z_probe)
        intro.append(line)
        line = "#<_tool_probe>         =   %.4f \n" % (tool_probe)
        intro.append(line)
        line = "#<_z_trivial>          =    %.4f \n\n" % (z_trivial)
        intro.append(line)

        line = "(Don't change these values here, they were calculated earlier)\n"
        intro.append(line)
        line =  '#<_x_grid_origin>     =  %.4f \n' % (X_grid_origin) 
        intro.append(line )
        line =  '#<_x_grid_lines>      =    %.4f \n' % (X_grid_lines )
        intro.append(line)
        line =  '#<_y_grid_origin>     =    %.4f \n' % (Y_grid_origin)
        intro.append(line)
        line =  '#<_y_grid_lines>      =    %.4f \n' % (Y_grid_lines )
        intro.append(line)
        line =  '#<_x_step_size>       =    %.4f \n' % (X_step_size)  
        intro.append(line)
        line =  '#<_y_step_size>       =    %.4f \n' % (Y_step_size)  
        intro.append(line)

        line =  """#<_last_z_etch>     =    #<_etch_depth>

(define subroutines:)
    O100 sub (probe subroutine)
         G00 X [#<_x_grid_origin> + #<_x_step_size>*#<_grid_x>]   
         G38.2 Z#<_z_probe> F#<_probe_speed>   
         #[1000 + #<_grid_x> + #<_grid_y> * #<_x_grid_lines>] = #5063   
         G00 Z#<_z_safety>
    O100 endsub

    O200 sub (etch subroutine)
         ( This subroutine calculates way points on the way to x_dest, y_dest, )
         ( and calculates the Z adjustment at each way point.                  )
         ( It moves to each way point using the etch level and etch speed set  )
         ( in the configuration section above.                                 )

         #<x_start>         = #1
         #<y_start>         = #2
         #<x_dest>          = #3
         #<y_dest>          = #4
         #<z_dest>          = #5
         #<distance>        = sqrt[ [#<x_dest> - #<x_start>]**2 + [#<y_dest> - #<y_start>]**2 ]
         #<waypoint_number> = fix[#<distance> / [#<_x_step_size>/2]]
         #<x_step>          = [[#<x_dest> - #<x_start>] / [#<waypoint_number> + 1]]
         #<y_step>          = [[#<y_dest> - #<y_start>] / [#<waypoint_number> + 1]]
         
         O201 while [#<waypoint_number> ge 0]
              #<_x_way>     =  [#<x_dest> - #<waypoint_number> * #<x_step>]
              #<_y_way>     =  [#<y_dest> - #<waypoint_number> * #<y_step>]   
              #<_grid_x_w>  =  [[#<_x_way> - #<_x_grid_origin>]/#<_x_step_size>]
              #<_grid_y_w>  =  [[#<_y_way> - #<_y_grid_origin>]/#<_y_step_size>]
              #<_grid_x_0>  =  fix[#<_grid_x_w>]
              #<_grid_y_0>  =  fix[#<_grid_y_w>]
              #<_grid_x_1>  =  fup[#<_grid_x_w>]
              #<_grid_y_1>  =  fup[#<_grid_y_w>]
              #<_cell_x_w>  =  [#<_grid_x_w> - #<_grid_x_0>]
              #<_cell_y_w>  =  [#<_grid_y_w> - #<_grid_y_0>]

              (Bilinear interpolation equations from http://en.wikipedia.org/wiki/Bilinear_interpolation)
              #<F00>        =  #[1000 + #<_grid_x_0> + #<_grid_y_0> * #<_x_grid_lines>]
              #<F01>        =  #[1000 + #<_grid_x_0> + #<_grid_y_1> * #<_x_grid_lines>]
              #<F10>        =  #[1000 + #<_grid_x_1> + #<_grid_y_0> * #<_x_grid_lines>]
              #<F11>        =  #[1000 + #<_grid_x_1> + #<_grid_y_1> * #<_x_grid_lines>] 
              #<b1>         =  #<F00>
              #<b2>         =  [#<F10> - #<F00>]
              #<b3>         =  [#<F01> - #<F00>]
              #<b4>         =  [#<F00> - #<F10> - #<F01> + #<F11>]          
              #<z_adj>      =  [#<b1> + #<b2>*#<_cell_x_w> + #<b3>*#<_cell_y_w> + #<b4>*#<_cell_x_w>*#<_cell_y_w>]
              #<z_etch>     =  [#<z_dest> + #<z_adj>]
                       
              (ignore trivial z axis moves)\n"""
              
        intro.append(line)
        line = "              O202 if [abs[#<z_etch> - #<_last_z_etch> ] lt #<_z_trivial>]" 
        intro.append(line)
        line = """
                   #<z_etch> = #<_last_z_etch> 
              O202 else
                   #<_last_z_etch> = #<z_etch>
              O202 endif
              
              (now do the move)
              G01 X#<_x_way>  Y#<_y_way>  Z[#<z_etch>] F[#<_etch_speed>]
              
              (and then go to the next way point)
              #<waypoint_number> = [#<waypoint_number> - 1]
         O201 endwhile
    O200 endsub


(***************************)
    O300 sub (compensated drill subroutine)
        ( This subroutine create z_compensated holes)

        #<x_dest>          = #1
        #<y_dest>          = #2
        #<z_dest>          = #3
        #<r_dest>          = #4
        #<f_dest>          = #5

        #<_grid_x_w>  =  [[#<x_dest> - #<_x_grid_origin>]/#<_x_step_size>]
        #<_grid_y_w>  =  [[#<y_dest> - #<_y_grid_origin>]/#<_y_step_size>]
        #<_grid_x_0>  =  fix[#<_grid_x_w>]
        #<_grid_y_0>  =  fix[#<_grid_y_w>]
        #<_grid_x_1>  =  fup[#<_grid_x_w>]
        #<_grid_y_1>  =  fup[#<_grid_y_w>]
        #<_cell_x_w>  =  [#<_grid_x_w> - #<_grid_x_0>]
        #<_cell_y_w>  =  [#<_grid_y_w> - #<_grid_y_0>]

        (Bilinear interpolation equations from http://en.wikipedia.org/wiki/Bilinear_interpolation)
        #<F00>        =  #[1000 + #<_grid_x_0> + #<_grid_y_0> * #<_x_grid_lines>]
        #<F01>        =  #[1000 + #<_grid_x_0> + #<_grid_y_1> * #<_x_grid_lines>]
        #<F10>        =  #[1000 + #<_grid_x_1> + #<_grid_y_0> * #<_x_grid_lines>]
        #<F11>        =  #[1000 + #<_grid_x_1> + #<_grid_y_1> * #<_x_grid_lines>] 
        #<b1>         =  #<F00>
        #<b2>         =  [#<F10> - #<F00>]
        #<b3>         =  [#<F01> - #<F00>]
        #<b4>         =  [#<F00> - #<F10> - #<F01> + #<F11>]          
        #<z_adj>      =  [#<b1> + #<b2>*#<_cell_x_w> + #<b3>*#<_cell_y_w> + #<b4>*#<_cell_x_w>*#<_cell_y_w>]
        #<z_etch>     =  [#<z_dest> + #<z_adj>]
              
        (now do the move)
        (G81. R0.19685   Z-0.01969   F39.37008 X2.29030 Y1.09330)
        G81.  R#<r_dest> Z#<z_etch>  X#<x_dest>  Y#<y_dest> F#<f_dest>
              
    O300 endsub

(************************)

    O<_probe_init> sub (Medir longitud de herremienta primaria)
        G49				( clear tool length compensation)
        G30				( to probe switch)
        (Usuar switch o Ajustar mecanica para acercarse rapido y luego medir con precision, resortes)
        ;G91				( relative mode for probing)
        ;G38.2 Z#<_tool_probe> F#<_probe_speed_fast>	( trip switch on the way down)
        ;G0 Z#<_z_safety>               	        ( back off the switch)
        ;G38.2 Z#<_z_probe> F#<_probe_speed>	        ( trip switch slowly)
        G38.2 Z#<_tool_probe> F#<_probe_speed>	        ( trip switch slowly)

        (DEBUG, Referencia de herramienta primaria: #5063)
        #<_ToolRefZ> = #5063  ( save trip point)
 
        ;G90                 ( absolute mode)
        G30                 ( return to safe level)
    O<_probe_init> endsub

    O<_probe_tool> sub (Medir longitud de herramienta y compensar)
        G49					( clear tool length compensation)
        G30					( to probe switch)
        ;G91					( relative mode for probing)
        ;G38.2 Z#<_tool_probe> F#<_probe_speed_fast>		( trip switch on the way down)
        ;G0 Z#<_z_safety>          	     		( back off the switch)
        ;G38.2 Z#<_z_probe> F#<_probe_speed>				( trip switch slowly)
        G38.2 Z#<_tool_probe> F#<_probe_speed>				( trip switch slowly)
 
        (DEBUG, Referencia de herramienta secundaria: #5063)
        #<_ToolZ> = #5063			( save new tool length)
 
        G43.1 Z[#<_ToolZ> - #<_ToolRefZ>]	( set new length)
 
        ;G90					( absolute mode)
        G30					( return to safe level)
    O<_probe_tool> endsub

(Medir altura de herramienta principal)
(MSG, Verificar ubicacion de cambiador de herramienta)
M0

O<_probe_init> call
G0 X0 Y0

( Probe grid section                                                                )
( This section probes the grid and writes the probe results for each probed point   )
( to variables #1000, #1001, #1002 etc etc such that the result at grid_x, grid_y   )
( on the grid is stored in memory location #[1000 + grid_x + grid_y*[x_grid_lines]] )
( EMC2 will run out of memory if you probe more than 4,000 points.                  ) 

#<_grid_x> = 0
#<_grid_y> = 0
G00 Z#<_z_safety>
G00 X#<_x_grid_origin> Y#<_y_grid_origin>
O001 while [#<_grid_y> lt #<_y_grid_lines>]
     G00 Y[#<_y_grid_origin> + #<_y_step_size> * #<_grid_y>]    
     O002 if [[#<_grid_y> / 2] - fix[#<_grid_y> / 2] eq 0]
          #<_grid_x> = 0
          O003 while [#<_grid_x> lt #<_x_grid_lines>]
               O100 call (probe subroutine)
               #<_grid_x> = [#<_grid_x> + 1]
          O003 endwhile       
     O002 else 
          #<_grid_x> = #<_x_grid_lines>
          O004 while [#<_grid_x> gt 0]
               #<_grid_x> = [#<_grid_x> - 1]  
               O100 call (probe subroutine)  
          O004 endwhile
     O002 endif
     #<_grid_y> = [#<_grid_y> + 1]
O001 endwhile
"""
        intro.append(line)
        line = "G00 Z%.4f \n" % (z_probe_detach)
        intro.append(line)
        line = """
( Main G code section                                                               )
( Python has replaced all G01 etch moves from original file eg G01 Xaa Ybb Zcc Fdd  )
( with an adjusted etch move in the format: O200 sub [x_start] [y_start] [aa] [bb]  )
( O200 is the etch subroutine                                                       )

(MSG, Iniciando maquinado...)
;M0

"""
        intro.append(line)

        # Finally, create and then save the output file
        file_out = intro + file_out + drill_guides + drill_moves + outline_moves

        line = '(MSG, Terminamos...)\nM02 (End Program)\n'
        file_out.append(line)

        f = open(file_out_name, 'w')
        for line in file_out:
            f.write(line)
        f.close()


        # and output the altered ngc file to the EMC2 screen
        for line in file_out:
            print line,
        
   #If no etch moves, give a warning and then exit
    else:
        from Tkinter import *
        def OK() : top.destroy()

        top = Tk()
        top.title("   Check file")
        var = IntVar()

        L1 = Label(top, text="")
        L2 = Label(top, text="Sorry, no etch moves found in that file.", font = "12")
        L3 = Label(top, text="")
        L4 = Label(top, text="Check file name, units, etch move definition etc.", font = "12")
        L5 = Label(top, text="")
        L6 = Label(top, text="")
        B1 = Button(top, text ="OK", command = OK, font = "18")

        L1.pack()
        L2.pack(anchor = W, padx=45)
        L3.pack()
        L4.pack(anchor = W, padx=45)
        L5.pack()    
        B1.pack()
        L6.pack()
        top.mainloop()

# or if you pressed cancel, just exit.
print "M02"
  
    
