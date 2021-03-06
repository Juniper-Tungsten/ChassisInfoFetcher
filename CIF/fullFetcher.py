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

from __future__ import print_function
import sys
import re
import json
import logging
import logging.config
import os

from StringIO import StringIO
from lxml import etree
from directFetcher import DirectFetcher

from jnpr.space import rest
from jnpr.space.rest import RestException

TIMEOUT_REST_API = 3

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import warnings

class FullFetcher(DirectFetcher):

    # Override the load and validate to work from Junos Space instead of intput file
    # return (False,ErrorMessage) if inputs are invalid or (True,SuccessMessage) if they are valid
    def LoadInputFile(self):
        warnings.filterwarnings("ignore")
        devices = []
        general_settings = []

        #### Read the general settings information
        try:
            with open('conf/fullFetcher.conf') as data_file:
                general_settings = json.load(data_file)
        except IOError:
            msg = "Loading and Verifying Device List failed : Unable to read input or parse file 'assistedFetcher.conf' responsible for storing general settings."
            logging.error(msg)
            return (False, msg)

        self.THREADCOUNT = int(general_settings["parallelProcesses"])

        # Create a Space REST end point
        space = rest.Space(url="https://"+general_settings["url"], user=general_settings["username_js"], passwd=general_settings["password_js"])
        logging.info("Connecting to Junos Space to retrieve the devices list.")
        try:
            domains = space.domain_management.domains.get()
            children = etree.SubElement(domains[0].children, "domain")

            domain_name = general_settings["domain"]
            if domain_name=="":
                domain_name = "Global"
            domain_id = 0
            ip_address = general_settings["ip"]

            for child_domain in domains[0].children.domain:
                domain = etree.SubElement(child_domain, "name")
                if domain_name == str(child_domain.name):
                    domain_id = child_domain.id
            if domain_id != 0:
                if ip_address != "":
                    devices = space.device_management.devices.\
                        get(filter_={'deviceFamily': 'junos', 'connectionStatus': 'up', 'domain-id':str(domain_id), 'ipAddr': ip_address})
                else:
                    devices = space.device_management.devices.\
                        get(filter_={'deviceFamily': 'junos', 'connectionStatus': 'up', 'domain-id':str(domain_id)})
            else:
                if ip_address != "":
                    devices = space.device_management.devices.\
                      get(filter_={'deviceFamily': 'junos', 'connectionStatus': 'up', 'ipAddr':ip_address})
                else:
                    devices = space.device_management.devices.\
                      get(filter_={'deviceFamily': 'junos', 'connectionStatus': 'up'})

        except RestException as ex:
            msg = "An errror occured during the communication with the Junos Space API.\n\tHTTP error code : %s;\n\tJunos Space Message : %s " % (ex.response, ex.response.text)
            logging.error(msg)
            return ("False", msg)

        #### Build the in-memory structure
        for device in devices:
            entry = {}
            entry["username"] = general_settings["username_js"]
            entry["password"] = general_settings["password_js"]
            entry["url"] = general_settings["url"]
            entry["serialNumber"] = str(device.serialNumber)
            entry["ipAddr"] = str(device.ipAddr)
            entry["name"] = str(device.name)

            self.jobList.append(entry)

        msg = "Loading and Verifying Device List was successful, loaded (%s) hosts!" % str(len(self.jobList))
        logging.info(msg)
        return (True, msg)

    def unwrap(self, text):

        tagToUnwrap = ["replyMsgData", "configuration-information", "configuration-output"]
        for i in xrange(len(tagToUnwrap)):
            text = re.sub('<'+tagToUnwrap[i]+'.*>', '', text)
            text = re.sub('</'+tagToUnwrap[i]+'>', '', text)
        return text

    def cleanNamespace(self, text):
        it = etree.iterparse(StringIO(text))
        for _, el in it:
            if '}' in el.tag:
                el.tag = el.tag.split('}', 1)[1]  # strip all namespaces
        root = it.root

        string = ""


        self.parse_tree(root)
        for value in self.parsedValues:
            string = string + value + "\n"
        self.parsedValues = []
        return string

    def parse_tree(self, root, commandLine=[""]):
        blacklist = {"name", "contents", "daemon-process"}
        ignore = {"configuration", "undocumented", "rpc-reply", "cli"}
        if root.tag not in ignore:  #!!!ignores comments, and the <configuration> and <rpc-reply> tags and root.tag.find("{")==-1)
            if root.tag not in blacklist:
                commandLine.append(root.tag)
            if len(root) == 0:
                if root.text != None:
                    if len(root.text.strip().replace(" ", "")) == len(root.text.strip()):
                        line = " ".join(commandLine) + " " + root.text.strip() + "\n"
                    else:
                        line = " ".join(commandLine) + ' "' + root.text.strip() + '"'
                else:
                    line = " ".join(commandLine)
                self.parsedValues.append(line.strip())
            else:

                if root[0].tag == "name" and len(root) > 1:
                    commandLine.append(root[0].text.strip())
                    for i in xrange(1, len(root)):
                        self.parse_tree(root[i], commandLine)
                    commandLine.pop()
                else:
                    for child in root:
                        self.parse_tree(child, commandLine)

            if root.tag not in blacklist:
                commandLine.pop()
        elif root.tag == "cli":
            pass
        else:
            for child in root:
                self.parse_tree(child, commandLine)

    # Process job OVERIDED from the directFecther since it uses SpaceEz and not direct connections
    def job(self, args):
        output = {}
        output["router_%s"%args["ipAddr"]] = ""
        commandOutput = ""
        commandCheck = ""
        flag = 0

        logging.info("Connecting to: "+args["ipAddr"])

        try:
            space = rest.Space("https://" + args["url"], args["username"], args["password"])

            autoDetect = space.device_management.devices.\
                          get(filter_={'serialNumber': args["serialNumber"]})[0].\
                          exec_rpc.post(rpcCommand="<command>show chassis hardware</command>")

        except RestException as ex:
            logging.error("An errror occured during the communication with the Junos Space API.\n\tHTTP error code : %s;\n\tJunos Space Message : %s "%(ex.response, ex.response.text))
            return ""

        if self.path == "IB":
            output_xml_ib = autoDetect.xpath('netConfReplies/netConfReply/replyMsgData')
            if len(output_xml_ib) != 1:
                logging.error("The reply from the server does not contain a valid 'show chassis hardware' reply. Full reply was logged in DEBUG level.")
                logging.debug(etree.tostring(output_xml_ib, pretty_print=True))
                return ""

            output_text_ib = etree.tostring(output_xml_ib[0], pretty_print=True)
            finalTextIB = self.unwrap(output_text_ib)
            commandOutputIB = "root@%s> %s\n" % (args["ipAddr"], "show chassis hardware") + finalTextIB + "\n\n\n"
            output["router_%s"%args["ipAddr"]] = commandOutputIB
            output['show chassis hardware detail | display xml'] = commandOutputIB
            return output
        
        autoDetect = etree.tostring(autoDetect, pretty_print=True)

        if autoDetect.find("<description>MX") > -1 or autoDetect.find("<description>VMX") > -1 or autoDetect.find("<description>M") > -1 or autoDetect.find("<description>T") > -1 or autoDetect.find("<description>PTX") > -1 or autoDetect.find("<description>ACX") > -1:
            try:
                with open("commands/MX_4.txt", "r") as data_file:
                    commandSettings = json.load(data_file)
                    logging.info("Loaded list of commands " + "["+args["ipAddr"] + "]")

            except IOError:
                msg = "Loading and Verifying Device List : Unable to read input file 'commands/MX_4.txt.'."
                logging.error(msg)
                return (False, msg)

        elif autoDetect.find("<description>SRX") > -1 or autoDetect.find("<description>VSRX") > -1:
            try:
                with open("commands/SRX_4.txt", "r") as data_file:
                    commandSettings = json.load(data_file)
                    logging.info("Loaded list of commands " + "["+args["ipAddr"] + "]")

            except IOError:
                msg = "Loading and Verifying Device List : Unable to read input file 'commands/SRX_4.txt'."
                logging.error(msg)
                return (False, msg)

        elif autoDetect.find("<description>QFX") > -1 or autoDetect.find("<description>EX") > -1:
            try:
                with open("commands/QFX_4.txt", "r") as data_file:
                    commandSettings = json.load(data_file)
                    logging.info("Loaded list of commands " + "["+args["ipAddr"] + "]")

            except IOError:
                msg = "Loading and Verifying Device List : Unable to read input file 'commands/QFX_4.txt'."
                logging.error(msg)
                return (False, msg)
        else:
            msg = "The device was not recognized!"
            logging.error(msg)
            return {'result': False}

        for i in xrange(len(commandSettings["commandList"])):
            commandCheck = commandSettings["commandList"][i].strip()  #commandCheck contains the current command being evaluated

            if (commandCheck.split(" ", 1)[0] == "show" or commandCheck == "request support information") and commandCheck.split("|")[-1].strip() != "display xml":

                result = space.device_management.devices.\
                      get(filter_={'serialNumber': args["serialNumber"]})[0].\
                      exec_rpc.post(rpcCommand="<command>" + commandCheck + "</command>")

                output_xml = result.xpath('netConfReplies/netConfReply/replyMsgData')

                if len(output_xml) != 1:
                    logging.error("The reply from the server does not contain a valid \"" + commandCheck + "\" reply. Full reply was logged in DEBUG level.")
                    logging.debug(etree.tostring(output_xml, pretty_print=True))
                    return ""

                output_text = etree.tostring(output_xml[0], pretty_print=True)
                finalText = self.unwrap(output_text)

                commandOutput = "root@%s> %s\n" % (args["ipAddr"], commandCheck) + finalText + "\n\n\n"
                output["router_%s" % args["ipAddr"]] += commandOutput         #Preparation for the two types of output: file_host1 contains the output of all the commands ran on host1;
                output[commandCheck] = commandOutput                    #file_show_chassis_hardware contains the output of the "show chassis harware" command from all hosts
            else:
                logging.error("The following command is not allowed : %s " % (commandCheck))
                return output

        logging.info("Done [" + args["ipAddr"] + "].")
        return output

if __name__ == '__main__':
    logging.config.fileConfig('conf/logging.conf')
    FULL = FullFetcher(sys.argv[1])
    FULL.LoadInputFile()

    FULL.Run()