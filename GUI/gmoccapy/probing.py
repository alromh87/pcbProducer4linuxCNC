#!/usr/bin/env python
import linuxcnc

class MyCallbacks :

    def on_vcp_stat_all_homed(self,obj):
        self.builder.get_object('button_probing_set').set_sensitive(True)
        self.builder.get_object('button_tool_changer_position').set_sensitive(True)

    def on_vcp_stat_not_all_homed(self,obj,unhommed):
        self.builder.get_object('button_probing_set').set_sensitive(False)
        self.builder.get_object('button_tool_changer_position').set_sensitive(False)

    def on_button_probing_set_clicked(self,obj,data=None):
        self.dialog_probing.show()

    def on_probe_z_action_mdi_command_start(self,obj,data=None):
        self.probe_running = True

    def on_probe_z_action_mdi_command_stop(self,obj,data=None):
        self.dialog_probing.hide()
        self.probe_running = False

    def on_vcp_stat_state_estop(self,obj,data):
        print self, obj,data

    def on_button_cancel_clicked(self,obj):
        self.cancel_probe()

    def on_dialog_probing_delete_event(self,obj,data):
        self.cancel_probe()
        return True

    def cancel_probe(self):
        if self.probe_running == True:
            c = linuxcnc.command()
            c.abort()
        self.dialog_probing.hide()

    def __init__(self, halcomp,builder,useropts):
        self.halcomp = halcomp
        self.builder = builder
        self.dialog_probing = self.builder.get_object('dialog_probing')
        self.probe_running = False

def get_handlers(halcomp,builder,useropts):
    print "hal: ",halcomp,"\nbuilder: ",builder,"\nuseropts: ",useropts
    return [MyCallbacks (halcomp,builder,useropts)]

