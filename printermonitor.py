import appdaemon.appapi as appapi
import binascii
from pysnmp.proto.rfc1902 import *
from pysnmp.entity.rfc3413.oneliner import cmdgen
            
class printermonitor(appapi.AppDaemon):

  def initialize(self):
    self.log("Test App")
    self.setup_mode()
    self.check_printers()
    self.run_hourly(self.hourly_check_handler,start=None)

  def hourly_check_handler(self,kwargs):
    self.check_printers()

  def check_printers(self):
    ptrdict=self.getInkjetInkLevels({"ipaddr": "192.168.2.247",
                                     "black":  {"name":{"oid":"1.3.6.1.2.1.43.11.1.1.6.0.1","value":""},
                                                "capacity":{"oid":"1.3.6.1.2.1.43.11.1.1.8.0.1","value":""},
                                                "current":{"oid":"1.3.6.1.2.1.43.11.1.1.9.0.1","value":""}},
                                     "yellow": {"name":{"oid":"1.3.6.1.2.1.43.11.1.1.6.0.2","value":""},
                                                "capacity":{"oid":"1.3.6.1.2.1.43.11.1.1.8.0.2","value":""},
                                                "current":{"oid":"1.3.6.1.2.1.43.11.1.1.9.0.2","value":""}},
                                     "cyan":   {"name":{"oid":"1.3.6.1.2.1.43.11.1.1.6.0.3","value":""},
                                                "capacity":{"oid":"1.3.6.1.2.1.43.11.1.1.8.0.3","value":""},
                                                "current":{"oid":"1.3.6.1.2.1.43.11.1.1.9.0.3","value":""}}   #,
                                    # "magenta":{"name":{"oid":"1.3.6.1.2.1.43.11.1.1.6.0.4","value":""},
                                    #            "capacity":{"oid":"1.3.6.1.2.1.43.11.1.1.8.0.4","value":""},
                                    #            "current":{"oid":"1.3.6.1.2.1.43.11.1.1.9.0.4","value":""}}
                                     })
    self.log("ptrdict={}".format(ptrdict),"DEBUG")
    self.blacklevel=(ptrdict["black"]["current"]["value"]/ptrdict["black"]["capacity"]["value"])*100
    self.log("blacklevel {} {} {}".format(ptrdict["black"]["current"]["value"],ptrdict["black"]["capacity"]["value"],self.blacklevel),"DEBUG")   
    self.set_state("input_slider.blackink",state=self.blacklevel)
    self.yellowlevel=(ptrdict["yellow"]["current"]["value"]/ptrdict["yellow"]["capacity"]["value"])*100
    self.log("yellowlevel {} {} {}".format(ptrdict["yellow"]["current"]["value"],ptrdict["yellow"]["capacity"]["value"],self.yellowlevel),"DEBUG")
    self.set_state("input_slider.yellowink",state=self.yellowlevel)
    self.cyanlevel=(ptrdict["cyan"]["current"]["value"]/ptrdict["cyan"]["capacity"]["value"])*100
    self.log("cyanlevel {} {} {}".format(ptrdict["cyan"]["current"]["value"],ptrdict["cyan"]["capacity"]["value"],self.cyanlevel),"DEBUG")
    self.set_state("input_slider.cyanink",state=self.cyanlevel)
    if (self.blacklevel < 20) or (self.yellowlevel < 20) or (self.cyanlevel < 20):
      self.printer_ink_state="Low"
    else:
      self.printer_ink_state="Ok"
    self.log("black={} cyan={} yellow={} magenta={} printer_state={}".format(self.blacklevel,self.yellowlevel,self.cyanlevel,"unknown",self.printer_ink_state),"INFO")
    self.set_state("group.dsp1hp",state=self.printer_ink_state)

    ptrdict=self.getInkjetInkLevels({"ipaddr": "192.168.2.249",
                                     "black":  {"toner":{"oid":"1.3.6.1.4.1.11.2.3.9.1.1.2.10.0","value":""}}})
    self.tonerlow=ptrdict["black"]["toner"]["value"]
    self.log("toner={}".format(self.tonerlow),"INFO")

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
    for color in oids:
      self.log("color={}".format(oids[color]),"DEBUG")
      if color!="ipaddr":
        for attribute in oids[color]:
          self.log("color={} attribute={}".format(oids[color],oids[color][attribute]),"DEBUG")
          errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
                 cmdgen.CommunityData('public', mpModel=0),
                 cmdgen.UdpTransportTarget((oids["ipaddr"], 161)),
                 oids[color][attribute]["oid"]
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
                oids[color][attribute]["value"]=int(varBind)
              elif isinstance(varBind,OctetString):
                self.log("name={} varBind={} is type {}".format(name,"".join(map(chr,varBind)),type("".join(map(chr,varBind)))),"DEBUG")
                oids[color][attribute]["value"]="".join(map(chr,varBind))
              else:
                self.log("unknown type {}".format(type(varBind)),"WARNING")
    return(oids)

