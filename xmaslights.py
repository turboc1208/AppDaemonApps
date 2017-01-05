import appdaemon.appapi as appapi
import datetime
import random
#import homeassistant.appapi as appapi
#
# XmasTree App
#
# Args:
#
        
class XmasLights(appapi.AppDaemon):

  def initialize(self):
     self.log("Turning on Xmas Tree.")
     self.colors=["Red","Green","Blue","Yellow"]
     self.xmashandle={}
     self.listen_event(self.ha_restart, "ha_started")
     self.log("Registering porch light listeners")
     self.listen_state(self.porchlightsavailable, entity = "light.front_porch_3", new="on")
     self.listen_state(self.porchlightsavailable, entity = "light.front_porch_4", new="on")
     self.log("Registering scheduled callbacks")
     self.run_at_sunset(self.turn_on_lights)
     self.run_daily(self.turn_off_lights,datetime.time(22,0,0))
     self.log("Registering rain listener")
     self.listen_state(self.raining, entity = "sensor.pws_precip_1hr_in")
     # Check current state
     if self.now_is_between("sunset","22:00:00"):
       self.turn_on_lights(kwargs=None)
     else:
       self.turn_off_lights(kwargs=None)

  def ha_restart(self, event_name, data,kwargs):
     self.log("apparently HA restarted {}".format(event_name))
     if self.sun_down() :
        if self.time() < self.parse_time("22:00:00") :
          self.turn_on_lights(kwargs)

  def raining(self, entity, attribute, old, new, kwargs):
     self.log("rain={}".format(new))
     if type(new)=="unknown":
       new="0.00"
     if float(new)>0.05:
       self.log("Turning off outdoor xmas lights due to rain")
       self.turn_off("switch.outdoor_xmas_lights")

  def turn_on_lights(self, kwargs):
     self.turn_on("group.xmas")

  def turn_off_lights(self, kwargs):
     if self.get_state("switch.switch")=="on":
       now=self.datetime()
       delta=datetime.timedelta(minutes=10)
       self.log("part override active {}, {}, {}".format(now, delta,now+delta))
       self.run_at(self.turn_off_lights,now+delta)
     else:
       self.turn_off("group.xmas")

  def porchlightsavailable(self, entity, attribute, old, new, kwargs):
    self.log("porch lights are available {}".format(entity, new))
    if (entity not in self.xmashandle) and (self.time() < self.parse_time("22:00:00")):
      self.xmashandle[entity]=self.run_minutely(self.change_porchlight_colors,datetime.time(0,0,50),entity_id=entity)
      self.log("registered run_minutely using entity {}".format(entity))
    else :
      if self.time() > self.parse_time("22:00:00") :
        self.cancel_timer(self.xmashandle[entity])
        del self.xmashandle[entity]
     
  def change_porchlight_colors(self, kwargs):
    entity=kwargs["entity_id"]
    self.log("changing lights on entity = {}".format(entity))
    self.turn_on(entity,color_name=self.colors[random.randint(0,len(self.colors)-1)])
