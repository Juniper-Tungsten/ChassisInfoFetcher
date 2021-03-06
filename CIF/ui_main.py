# coding: utf-8
#!/usr/bin/env python
# <*******************
# 
#   Copyright (c) 2017 Juniper Networks . All rights reserved.
#   Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
#
#   1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
#
#   2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the 
#   documentation and/or other materials provided with the distribution.
#
#   3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this 
#   software without specific prior written permission.
#
#   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, 
#   THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR 
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, 
#   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF 
#   LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, 
#   EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# 
# *******************>


import urwid
import json
from urlparse import urlparse
from ui_dialog import ui_dialog
from ui_directFetcher import ui_directFetcher
from ui_assistedFetcher import ui_assistedFetcher
from ui_fullFetcher import ui_fullFetcher
from ui_SNSIFetcher import ui_SNSIFetcher
from ui_help import ui_help
from ui_about import ui_about  
from ui_xmlTransformation import ui_xmlTransformation

class ui_main(ui_dialog):
    
    def __init__(self,top):
        self.top=top
        self.ui_directFetcher_dialog=ui_directFetcher(top)
        self.ui_assistedFetcher_dialog=ui_assistedFetcher(top)
        self.ui_fullFetcher_dialog=ui_fullFetcher(top)
        self.ui_SNSIFetcher_dialog=ui_SNSIFetcher(top)
        self.ui_help_dialog=ui_help(top)
        self.ui_about_dialog=ui_about(top)
        self.ui_xmlTransformation_dialog=ui_xmlTransformation(top)

    def Pass(self):
        pass
    def ShowDisclaimer(self):
        caption = urwid.Text([("standoutLabel",u"IMPORTANT INFORMATION")])

        disclaimer = urwid.Text([u"""
Copyright (c) 2016  Juniper Networks. All Rights Reserved.
 
YOU MUST ACCEPT THE TERMS OF THIS DISCLAIMER TO USE THIS SOFTWARE
 
JUNIPER IS WILLING TO MAKE THE INCLUDED SCRIPTING SOFTWARE AVAILABLE TO YOU ONLY UPON THE CONDITION THAT YOU ACCEPT ALL OF THE TERMS CONTAINED IN THIS DISCLAIMER. 

PLEASE READ THE TERMS AND CONDITIONS OF THIS DISCLAIMER  CAREFULLY.

THE SOFTWARE CONTAINED IN THIS FILE IS PROVIDED "AS IS." JUNIPER MAKES NO WARRANTIES OF ANY KIND WHATSOEVER WITH RESPECT TO SOFTWARE. ALL EXPRESS OR IMPLIED CONDITIONS, REPRESENTATIONS AND WARRANTIES, INCLUDING ANY WARRANTY OF NON-INFRINGEMENT OR WARRANTY OF MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE, ARE HEREBY DISCLAIMED AND EXCLUDED TO THE EXTENT ALLOWED BY APPLICABLE LAW.
  
IN NO EVENT WILL JUNIPER BE LIABLE FOR ANY LOST REVENUE, PROFIT OR DATA, OR FOR DIRECT, SPECIAL, INDIRECT, CONSEQUENTIAL, INCIDENTAL OR PUNITIVE DAMAGES HOWEVER CAUSED AND REGARDLESS OF THE THEORY OF LIABILITY ARISING OUT OF THE USE OF OR INABILITY TO USE THE SOFTWARE, EVEN IF JUNIPER HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.
  
Do you accept and acknowledge the above disclaimer."""])

        byes=self.menu_button(u'Yes', self.exit_window)
        bno=self.menu_button(u'No', self.exit_program)

        self.top.open_listbox(urwid.ListBox([caption,urwid.Divider(),disclaimer,urwid.Divider(),bno,byes]))

    def ShowDialog(self):
        help = urwid.Text([u'The ChassisInfoFetcher tool connects in parallel to all customer specified devices (mode dependant - check Help section), automatically detects the type of device and fetches the necessary information for that device type. The customer needs to select one of the modes, enter the required credentials (* Mode > Settings) and run the tool.'])
        menu_top = self.menu(u'Chassis Information Fetcher 2.0', [

        help,
        urwid.Divider(),
        self.menu_button(u'Direct Mode', self.ui_directFetcher_dialog.ShowDialog),
        self.menu_button(u'Junos Space | Assisted Mode', self.ui_assistedFetcher_dialog.ShowDialog),
        self.menu_button(u'Junos Space | Service Now Service Insight Mode', self.ui_SNSIFetcher_dialog.ShowDialog),
        self.menu_button(u'Junos Space | Full Mode', self.ui_fullFetcher_dialog.ShowDialog),
        urwid.Divider(),
        #self.menu_button(u'Additional features', self.ui_xmlTransformation_dialog.ShowDialog),
        self.menu_button(u'Help', self.ui_help_dialog.ShowDialog),
        self.menu_button(u'About', self.ui_about_dialog.ShowDialog),
        urwid.Divider(),
        self.menu_button(u'Exit', self.exit_program),
       ])

        return menu_top