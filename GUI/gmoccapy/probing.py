#!/usr/bin/env python

class MyCallbacks :
    def on_button_probing_set_clicked(self,obj,data=None):
        print "this_signal happened2, obj=",obj, self.builder.get_object('dialog_probing')
        self.dialog_probing.show()

    def on_probe_z_action_mdi_command_start(self,obj,data=None):
        self.probe_running = True
    def on_probe_z_action_mdi_command_stop(self,obj,data=None):
        self.dialog_probing.hide()
        self.probe_running = False

    def on_button_cancel_clicked(self,obj,data=None):
#        if self.probe_running == True:
            #lanzar cancelacion de instruccion
        self.dialog_probing.hide()

    def on_dialog_probing_close(self,obj,data=None):
#TODO: handle close correctly
        return true
        print "this_signal happened2, obj=",obj, self.builder.get_object('dialog_probing')
        print "on_destroy() - saving state"
        self.ini.save_state(self)
        self.dialog_probnig.hide

    def __init__(self, halcomp,builder,useropts):
        self.halcomp = halcomp
        self.builder = builder
        self.dialog_probing = self.builder.get_object('dialog_probing')
        self.probe_running = False

def get_handlers(halcomp,builder,useropts):
    print "hal: ",halcomp,"\nbuilder: ",builder,"\nuseropts: ",useropts
    return [MyCallbacks (halcomp,builder,useropts)]

