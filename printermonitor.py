#  Printermonitor -
#                   Monitor printers for low ink or toner level
#  Written by Chip Cox
#  Date 16Jan2017
#
import appdaemon.appapi as appapi
import appdaemon.conf as conf
import binascii
from pysnmp.proto.rfc1902 import *
from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.proto.rfc1905 import NoSuchObject
import io
import json
            
class printermonitor(appapi.AppDaemon):

  def initialize(self):
    #self.LOGLEVEL="DEBUG"
    self.check_printers()
    self.run_hourly(self.hourly_check_handler,start=None)


  # overrides appdaemon log file to handle application specific log files
  # to use this you must set self.LOGLEVEL="DEBUG" or whatever in the initialize function
  # although technically you could probably set it anywhere in the app if you wanted to 
  # just debug a function, although you probably want to set it back when you get done
  # in the function or the rest of the program will start spewing messages
  def log(self,message,level="INFO"):
    levels = {                                          # these levels were taken from AppDaemon's files which were taken from python's log handler
              "CRITICAL": 50,
              "ERROR": 40,
              "WARNING": 30,
              "INFO": 20,
              "DEBUG": 10,
              "NOTSET": 0
            }

    if hasattr(self, "LOGLEVEL"):                        # if the LOGLEVEL attribute has been set then deal with whether to print or not.
      if levels[level]>=levels[self.LOGLEVEL]:           # if the passed in level is >= to the desired LOGLevel the print it.
        super().log("{} - {}".format(level,message))
    else:                                                # the LOGLEVEL attribute was not set so just do the log file normally
      super().log("{}".format(message),level)


  # check hourly to see if the print status has changed.
  def hourly_check_handler(self,kwargs):
    self.check_printers()


  # function that hopefully will eventually be incorporated into AppDaemon
  # Check and see if the entity_id exists as an object in HA
#  def device_exists(self,entity_id):
#    if entity_id in conf.ha_state:
#      self.log("found {} in HA".format(entity_id), level="DEBUG")
#      return(True)
#    else:
#      self.log("{} not found in HA".format(entity_id), level="DEBUG")
#      return(False)


  #
  # main process to check the printers and update their status in HA
  def check_printers(self):
    self.log("in check_printers",level="DEBUG")

    # read in json file with printer and MIB descriptions
    filename=self.config["AppDaemon"]["app_dir"] + "/" + "PrinterMibs.cfg"
        
    with open(filename) as json_data:
      ptrdict=json.load(json_data) 

    ptrdict=self.getInkjetInkLevels(ptrdict)                      # go query the printer via SNMP

    self.log("ptrdict={}".format(ptrdict),level="DEBUG")

    for sys in ptrdict:                                           # loop through printers in ptrdict
      self.log("sys={}".format(sys),level="DEBUG")
      if sys=="sample":
        continue
      else:
        level=0.0
        group_state="Ok"
        ipa=ptrdict[sys]["ipaddr"]
        self.device=ptrdict[sys]["device"]
        for component in ptrdict[sys]["marker"]:
          self.log("sys={} component={}".format(sys,component),level="DEBUG")
          devtyp,entity=self.split_entity(component)
          if devtyp =="input_slider":                              # if this is an input slider, it's supposed to show % used so calc percentage
            self.log("current={} capacity={}".format(type(ptrdict[sys]["marker"][component]["current"]["value"]),type(ptrdict[sys]["marker"][component]["capacity"]["value"])),level="DEBUG")
            level=(float(ptrdict[sys]["marker"][component]["current"]["value"])/(float(ptrdict[sys]["marker"][component]["capacity"]["value"])+0.01)+0.01)*100
            group_state=group_state if level>10 else "Low" 
            self.set_state(component,state=level)                 # set the state of the HA component
          elif devtyp =="input_boolean":
            level=ptrdict[sys]["marker"][component]["tonerlow"]["value"]
            self.log("component {} - input_boolean level={}".format(component,level),"DEBUG")
            self.set_state(component,state="on" if level==1 else "off")                 # set ha value for input boolean
          else:
            self.log("Unknown device type - {}".format(component),level="WARNING")

      if self.entity_exists("group."+sys):                        # if we have a group named the same as the printer update group status
        self.set_state("group."+sys,state=group_state)


  #
  # query printer via SNMP
  def getInkjetInkLevels(self,oids):
    self.log("oids={}".format(oids),level="DEBUG")

    # SNMP query stuff starts here
    cmdGen=cmdgen.CommandGenerator()
    colors={}
    self.log("starting snmptest","DEBUG")
    for sys in oids:                                                          # Outter level is the printer name
      if sys=="sample":
        continue
      else:
        for control in oids[sys]["marker"]:
          self.log("control={} attribute={}".format(control,oids[sys]["marker"][control]),"DEBUG")
          for attribute in oids[sys]["marker"][control]:
            self.log("attribute={} oid={}".format(attribute,oids[sys]["marker"][control][attribute]["oid"]),"DEBUG")

            errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(      # Launch SNMP Query
                   cmdgen.CommunityData('public', mpModel=0),
                   cmdgen.UdpTransportTarget((oids[sys]["ipaddr"], 161)),
                   oids[sys]["marker"][control][attribute]["oid"]
            )

            self.log("back from getCmd call {} {} {} {}".format(errorIndication, errorStatus, errorIndex, varBinds),"DEBUG")
            if errorIndication:                                               # Handle errors from SNMP query
              self.log("errorIndication={}".format(errorIndication)),"ERROR"
            elif errorStatus:
              self.log(" {} at {}".format(errorStatus,errorIndex),"ERROR")
            else:                                                             # Everything is good.
              self.log("varBinds={}".format(varBinds),"DEBUG")
              for name, varBind in varBinds:
                self.log("name={} varbind={} is type {}".format(name,varBind,type(varBind)),"DEBUG")
                if isinstance(varBind,Integer32):                             # handle response based on the object type (int, string, etc)
                  oids[sys]["marker"][control][attribute]["value"]=int(varBind)
                elif isinstance(varBind,OctetString):
                  self.log("name={} varBind={} is type {}".format(name,"".join(map(chr,varBind)),type("".join(map(chr,varBind)))),"DEBUG")
                  oids[sys]["marker"][control][attribute]["value"]="".join(map(chr,varBind))
                elif isinstance(varBind,NoSuchObject):                        # in this case SNMP could not find the object so it's not an error, but it's not ok either
                  oids[sys]["marker"][control][attribute]["value"]="0"
                  self.log("No Such Object returned from SNMP lookup: {}".format(oids[sys]["marker"][control][attribute]["oid"]))
                else:
                  self.log("unknown type {}".format(type(varBind)),"WARNING")
    return(oids)

