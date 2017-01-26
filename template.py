import appdaemon.appapi as appapi
import inspect
             
class test(appapi.AppDaemon):

  def initialize(self):
    # self.LOGLEVEL="DEBUG"
    self.log("Test App")
    self.setup_mode()

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
        super().log("{}({}) - {} - message={}".format(inspect.stack()[1][3],inspect.stack()[1][2],level,message))
    else:                                                # the LOGLEVEL attribute was not set so just do the log file normally
      super().log("{}".format(message),level)


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

  ######################
  # 
  #  Load location configuration data from HA
  #
  ######################
  def loadHAconfig(self):
    haConfig={}
    locinfo=location.detect_location_info()
    haConfig["IP"]=locinfo.ip
    haConfig["country_code"]=locinfo.country_code
    haConfig["country_name"]=locinfo.country_name
    haConfig["region_code"]=locinfo.region_code
    haConfig["region_name"]=locinfo.region_name
    haConfig["city"]=locinfo.city
    haConfig["zip_code"]=locinfo.zip_code
    haConfig["time_zone"]=locinfo.time_zone
    haConfig["latitude"]=locinfo.latitude
    haConfig["longitude"]=locinfo.longitude
    haConfig["metric"]=locinfo.use_metric
    return haConfig
