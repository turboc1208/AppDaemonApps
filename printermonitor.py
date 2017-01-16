import appdaemon.appapi as appapi
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


  def hourly_check_handler(self,kwargs):
    self.check_printers()

  def check_printers(self):
    self.log("in check_printers")
#    ptrdict=self.getInkjetInkLevels({"dsp1hp":{"ipaddr": "192.168.2.247",
#                                               "device": "inkjet",
#                                               "input_slider.blackink":  {"name":{"oid":"1.3.6.1.2.1.43.11.1.1.6.0.1","value":""},
#                                                          "capacity":{"oid":"1.3.6.1.2.1.43.11.1.1.8.0.1","value":""},
#                                                          "current":{"oid":"1.3.6.1.2.1.43.11.1.1.9.0.1","value":""}},
#                                               "input_slider.yellowink": {"name":{"oid":"1.3.6.1.2.1.43.11.1.1.6.0.2","value":""},
#                                                          "capacity":{"oid":"1.3.6.1.2.1.43.11.1.1.8.0.2","value":""},
#                                                          "current":{"oid":"1.3.6.1.2.1.43.11.1.1.9.0.2","value":""}},
#                                               "input_slider.cyanink":   {"name":{"oid":"1.3.6.1.2.1.43.11.1.1.6.0.3","value":""},
#                                                          "capacity":{"oid":"1.3.6.1.2.1.43.11.1.1.8.0.3","value":""},
#                                                          "current":{"oid":"1.3.6.1.2.1.43.11.1.1.9.0.3","value":""}},
#                                               "input_slider.magentaink":{"name":{"oid":"1.3.6.1.2.1.43.11.1.1.6.0.4","value":""},
#                                                          "capacity":{"oid":"1.3.6.1.2.1.43.11.1.1.8.0.4","value":""},
#                                                          "current":{"oid":"1.3.6.1.2.1.43.11.1.1.9.0.4","value":""}}
#                                              },
#                                     "ofhp1":{"ipaddr": "192.168.2.249",
#                                              "device": "laserjet",
#                                              "input_boolean.ofhp1tonerlow":  {"toner":{"oid":"1.3.6.1.4.1.11.2.3.9.1.1.2.10.0","value":""}}}})
#    self.log("before writing out ptrdict={}".format(ptrdict),"DEBUG")
    filename=self.config["AppDaemon"]["app_dir"] + "/" + "PrinterMibs.cfg"
#    with open(filename,'w') as json_data:
#      json.dump(ptrdict,json_data)
        
    with open(filename) as json_data:
      ptrdict=json.load(json_data) 

    ptrdict=self.getInkjetInkLevels(ptrdict)

#    self.blacklevel=0
#    self.yellowlevel=0
#    self.cyanlevel=0
#    self.magentalevel=0
 
    self.log("ptrdict={}".format(ptrdict),"DEBUG")

    for sys in ptrdict:
      self.log("sys={}".format(sys))
      level=0.0
      for component in ptrdict[sys]:
        self.log("  component={}".format(component))
        if component=="ipaddr" :
          self.log("  component={} value={}".format(component,ptrdict[sys][component]))
          continue
        elif component=="device":
          self.log("  component={} value={}".format(component,ptrdict[sys][component]))
          if ptrdict[sys][component]=="inkjet":
            self.device="inkjet"
          elif ptrdict[sys][component]=="laserjet":
            self.device="laserjet"
          else:
            self.log("Unknown device type = {}".format(ptrdict[sys][component]))
        else:
          self.log("  component={} value={}".format(component,ptrdict[sys][component]))
          devtyp,entity=self.split_entity(component)
          if devtyp=="input_slider":
            self.log("current={} capacity={}".format(type(ptrdict[sys][component]["current"]["value"]),type(ptrdict[sys][component]["capacity"]["value"])))
            level=(float(ptrdict[sys][component]["current"]["value"])/(float(ptrdict[sys][component]["capacity"]["value"])+0.01)+0.01)*100
            self.set_state(component,state=level)
          elif ptrdict[sys][component]=="laserjet":
            level=ptrdict[sys][component]["toner"]["value"]
            self.set_state(component,state=level)
          else:
            self.log("Unknown device type - {}".format(ptrdict[sys][component]))

#    self.blacklevel=(ptrdict["black"]["current"]["value"]/(ptrdict["black"]["capacity"]["value"]+0.01)+0.01)*100
#    self.log("blacklevel {} {} {}".format(ptrdict["black"]["current"]["value"],ptrdict["black"]["capacity"]["value"],self.blacklevel),"DEBUG")   
#    self.yellowlevel=(ptrdict["yellow"]["current"]["value"]/(ptrdict["yellow"]["capacity"]["value"]+0.01)+0.01)*100
#    self.log("yellowlevel {} {} {}".format(ptrdict["yellow"]["current"]["value"],ptrdict["yellow"]["capacity"]["value"],self.yellowlevel),"DEBUG")
#    self.cyanlevel=(ptrdict["cyan"]["current"]["value"]/(ptrdict["cyan"]["capacity"]["value"]+0.01)+0.01)*100
#    self.log("cyanlevel {} {} {}".format(ptrdict["cyan"]["current"]["value"],ptrdict["cyan"]["capacity"]["value"],self.cyanlevel),"DEBUG")

#    self.set_state("input_slider.blackink",state=self.blacklevel)
#    self.set_state("input_slider.yellowink",state=self.yellowlevel)
#    self.set_state("input_slider.cyanink",state=self.cyanlevel)

#    if (self.blacklevel < 20) or (self.yellowlevel < 20) or (self.cyanlevel < 20):
#      self.printer_ink_state="Low"
#    else:
#      self.printer_ink_state="Ok"
#    self.log("black={} cyan={} yellow={} magenta={} printer_state={}".format(self.blacklevel,self.yellowlevel,self.cyanlevel,"unknown",self.printer_ink_state),"INFO")
#    self.set_state("group.dsp1hp",state=self.printer_ink_state)

#    ptrdict=self.getInkjetInkLevels({"ipaddr": "192.168.2.249",
#                                     "black":  {"toner":{"oid":"1.3.6.1.4.1.11.2.3.9.1.1.2.10.0","value":""}}})
#    self.tonerlow=ptrdict["black"]["toner"]["value"]
#    self.log("toner={}".format(self.tonerlow),"INFO")
#    with open(filename,'w') as outfile:
#      json.dump(ptrdict,outfile)

  def setup_mode(self):
    self.log("in setup mode")
    self.maintMode=False
    self.vacationMode=False
    self.partyMode=False
    self.log("varaibles defined calling getOverrideMode")
    self.maintMode=self.getOverrideMode("input_boolean.maint")
    self.log("maint done, calling vacation")
    self.vacationMode=self.getOverrideMode("input_boolean.vacation")
    self.log("vacation done, calling party")
    self.partyMode=self.getOverrideMode("input_boolean.party")
    self.log("party done")
    self.log("Maint={} Vacation={} Party={}".format(self.maintMode,self.vacationMode,self.partyMode),"DEBUG")

  def getOverrideMode(self,ibool):
    self.listen_state(self.set_mode, entity=ibool)
    return(True if self.get_state(ibool)=='on' else False)

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

  def getInkjetInkLevels(self,oids):
    self.log("oids={}".format(oids),"DEBUG")
    cmdGen=cmdgen.CommandGenerator()
    colors={}
    self.log("starting snmptest","DEBUG")
    for sys in oids:
      for color in oids[sys]:
        self.log("color={}".format(oids[sys][color]),"DEBUG")
        if color=="device":
          continue
        elif color!="ipaddr":
          for attribute in oids[sys][color]:
            self.log("color={} attribute={}".format(oids[sys][color],oids[sys][color][attribute]),"DEBUG")
            errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
                   cmdgen.CommunityData('public', mpModel=0),
                   cmdgen.UdpTransportTarget((oids[sys]["ipaddr"], 161)),
                   oids[sys][color][attribute]["oid"]
            )
            self.log("back from getCmd call {} {} {} {}".format(errorIndication, errorStatus, errorIndex, varBinds),"DEBUG")
            if errorIndication:
              self.log("errorIndication={}".format(errorIndication)),"ERROR"
            elif errorStatus:
              self.log(" {} at {}".format(errorStatus,errorIndex),"ERROR")
            else:
              self.log("varBinds={}".format(varBinds),"DEBUG")
              for name, varBind in varBinds:
                self.log("name={} varbind={} is type {}".format(name,varBind,type(varBind)),"DEBUG")
                if isinstance(varBind,Integer32):
                  oids[sys][color][attribute]["value"]=int(varBind)
                elif isinstance(varBind,OctetString):
                  self.log("name={} varBind={} is type {}".format(name,"".join(map(chr,varBind)),type("".join(map(chr,varBind)))),"DEBUG")
                  oids[sys][color][attribute]["value"]="".join(map(chr,varBind))
                elif isinstance(varBind,NoSuchObject):
                  oids[sys][color][attribute]["value"]="0"
                  self.log("No Such Object")
                else:
                  self.log("unknown type {}".format(type(varBind)),"WARNING")
    return(oids)

