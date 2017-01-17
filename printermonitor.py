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
    self.LOGLEVEL="DEBUG"
    self.log("Test App")
    self.setup_mode()
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
  def device_exists(self,entity_id):
    if entity_id in conf.ha_state:
      self.log("found {} in HA".format(entity_id), level="DEBUG")
      return(True)
    else:
      self.log("{} not found in HA".format(entity_id), level="DEBUG")
      return(False)


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
      level=0.0
      group_state="Ok"
      for component in ptrdict[sys]:                              # loop through each component of the printer (ip address, type, colors, etc)
        self.log("  component={}".format(component),level="DEBUG")
        if component=="ipaddr" :                                  # handle IP address
          self.log("  component={} value={}".format(component,ptrdict[sys][component]))
        elif component=="device":                                 # handle printer device type inkjet, laserjet, etc
          self.log("  component={} value={}".format(component,ptrdict[sys][component]),level="DEBUG")
          if ptrdict[sys][component]=="inkjet":                   # this is an inkjet
            self.device="inkjet"
          elif ptrdict[sys][component]=="laserjet":               # this is a laserjet
            self.device="laserjet"
          else:
            self.log("Unknown device type = {}".format(ptrdict[sys][component]),level="DEBUG")
            self.device=""
        else:                                                     # this should be a color
          self.log("  component={} value={}".format(component,ptrdict[sys][component]),level="DEBUG")
          devtyp,entity=self.split_entity(component)
          if devtyp=="input_slider":                              # if this is an input slider, it's supposed to show % used so calc percentage
            self.log("current={} capacity={}".format(type(ptrdict[sys][component]["current"]["value"]),type(ptrdict[sys][component]["capacity"]["value"])),level="DEBUG")
            level=(float(ptrdict[sys][component]["current"]["value"])/(float(ptrdict[sys][component]["capacity"]["value"])+0.01)+0.01)*100
            group_state=group_state if level>10 else "Low" 
            self.set_state(component,state=level)                 # set the state of the HA component
          elif ptrdict[sys][component]=="laserjet":
            level=ptrdict[sys][component]["toner"]["value"]
            self.set_state(component,state=level)                 # set ha value for input boolean
          else:
            self.log("Unknown device type - {}".format(ptrdict[sys][component]),level="WARNING")

      if self.device_exists("group."+sys):                        # if we have a group named the same as the printer update group status
        self.set_state("group."+sys,state=group_state)


  #
  # setup_mode - sets override values.  If one of the override modes are set we can use those checks to 
  #              prevent certain activities to start
  # 
  def setup_mode(self):
    self.log("in setup mode")
    self.maintMode=False
    self.vacationMode=False
    self.partyMode=False
    self.log("varaibles defined calling getOverrideMode",level="DEBUG")
    self.maintMode=self.getOverrideMode("input_boolean.maint")
    self.log("maint done, calling vacation",level="DEBUG")
    self.vacationMode=self.getOverrideMode("input_boolean.vacation")
    self.log("vacation done, calling party",level="DEBUG")
    self.partyMode=self.getOverrideMode("input_boolean.party")
    self.log("party done",level="DEBUG")
    self.log("Maint={} Vacation={} Party={}".format(self.maintMode,self.vacationMode,self.partyMode),"DEBUG")


  # setup listeners for different flags
  #
  def getOverrideMode(self,ibool):
    self.listen_state(self.set_mode, entity=ibool)
    return(True if self.get_state(ibool)=='on' else False)


  # check the entity that flagged us.  If it's one of our override flags set the appropriate flags
  #
  def set_mode(self,entity,attribute,old,new,kwargs):
    if old!=new:
      if entity=='input_boolean.maint':
        self.maintMode=True if self.get_state(entity)=='on' else False
      elif entity=='input_boolean.vacation':
        self.vacationMode=True if self.get_state(entity)=='on' else False
      elif entity=='input_boolean.party':
        self.partyMode=True if self.get_state(entity)=='on' else False
      else:
        self.log("unknown entity {}".format(entity))
    self.log("Maint={} Vacation={} Party={}".format(self.maintMode,self.vacationMode,self.partyMode),"DEBUG")


  #
  # query printer via SNMP
  def getInkjetInkLevels(self,oids):
    self.log("oids={}".format(oids),level="DEBUG")

    # SNMP query stuff starts here
    cmdGen=cmdgen.CommandGenerator()
    colors={}
    self.log("starting snmptest","DEBUG")
    for sys in oids:                                                          # Outter level is the printer name
      for color in oids[sys]:                                                 # Second level contains information about printer
        self.log("color={}".format(oids[sys][color]),"DEBUG")
        if color=="device":
          continue
        elif color!="ipaddr":
          for attribute in oids[sys][color]:
            self.log("color={} attribute={}".format(oids[sys][color],oids[sys][color][attribute]),"DEBUG")
            errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(      # Launch SNMP Query
                   cmdgen.CommunityData('public', mpModel=0),
                   cmdgen.UdpTransportTarget((oids[sys]["ipaddr"], 161)),
                   oids[sys][color][attribute]["oid"]
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
                  oids[sys][color][attribute]["value"]=int(varBind)
                elif isinstance(varBind,OctetString):
                  self.log("name={} varBind={} is type {}".format(name,"".join(map(chr,varBind)),type("".join(map(chr,varBind)))),"DEBUG")
                  oids[sys][color][attribute]["value"]="".join(map(chr,varBind))
                elif isinstance(varBind,NoSuchObject):                        # in this case SNMP could not find the object so it's not an error, but it's not ok either
                  oids[sys][color][attribute]["value"]="0"
                  self.log("No Such Object")
                else:
                  self.log("unknown type {}".format(type(varBind)),"WARNING")
    return(oids)

