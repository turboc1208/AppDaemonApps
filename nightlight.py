import appdaemon.appapi as appapi
             
class nightlight(appapi.AppDaemon):
   
  def initialize(self):
    self.log("Initializing NightLight")
# Get Current Status
# Listen for state change
    self.listen_state(self.lightStateChanged,entity=None,new="on")

#  def getCurrentStatus(self):
# check light state
#    self.log("Checking current light state")
# for each light in group nightlight
#   if light on
#     turnOnLight(entity)

  def lightStateChanged(self,entity,attribute,old,new,kwargs):
    self.nightlight_list=self.get_state("group.nightlight",attribute="all")["attributes"]["entity_id"]
    if entity in self.nightlight_list :
      for e in self.nightlight_list:
        self.turnOnLight(e)
    else:
      self.log("entity {} not a nightlight".format(entity))

  def turnOnLight(self,entity):
     nighttime=self.get_state("sensor.begin_night_time") + ":00"
     morning=self.get_state("sensor.begin_morning") + ":00"
     #if after nighttime then turn on at 10% brightness
     if self.now_is_between(str(nighttime),str(morning)) :
       self.log("It is nighttime between {} and {} state({})={}".format(nighttime,morning,entity,self.get_state(entity)))
       if self.get_state(entity)=="off":
         self.log("Turning on {}".format(entity))
         self.turn_on(entity,brightness="1")
       else:
         self.log("{} already on".format(entity))
     else:
       self.log("not nighttime")
