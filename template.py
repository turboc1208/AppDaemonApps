import appdaemon.appapi as appapi
             
class test(appapi.AppDaemon):

  def initialize(self):
    self.log("Test App")
    self.setup_mode()

  def setup_mode(self):
    self.maintMode=False
    self.vacationMode=False
    self.partyMode=False
    self.maintMode=self.getOverrideMode("input_boolean.maint")
    self.vacationMode=self.getOverrideMode("input_boolean.vacation")
    self.partyMode=self.getOverrideMode("input_boolean.party")
    self.log("Maint={} Vacation={} Party={}".format(self.maintMode,self.vacationMode,self.partyMode),"DEBUG")

  def getOverrideMode(self,ibool):
    self.listen_state(self.set_self, entity=ibool)
    return(True if self.get_state(ibool)=='on' else False)

  def set_self(self,entity,attribute,old,new,kwargs):
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

