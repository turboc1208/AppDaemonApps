# developed by Chip Cox
#              January 2017
#
import appdaemon.appapi as appapi
import os
import json
import datetime
                    
class sunrise_sunset(appapi.AppDaemon):

  def initialize(self):
    self.log("SunUp Sundown setup")
    self.times={}
    self.times['morning']='05:00:00'
    self.times['nighttime']='22:00:00'
    self.times['timeout']='600'
    self.filename=self.config["AppDaemon"]["app_dir"] + "/" + "sunrisesunset.cfg"
    # read sun config file to get start and end time
    # set start and end time
    # update HA with start and end times just in case they don't match
    self.timeout_list={}
    self.build_timeout_list("group.timeout_lights")
    self.load_times()
    self.process_current_state()
    # listen for change in morning value
    #self.listen_state(self.morning_change)
    self.listen_state(self.light_timeout_check, new="on")
    self.listen_state(self.light_timeout_check, entity="input_slider")
    self.run_at_sunset(self.begin_nighttime)
    self.run_at_sunrise(self.begin_morning)
  
  def process_current_state(self):
    self.log("time to process current state of lights")
    if self.sun_down():
      self.log("after sundown state={}".format(self.get_state("switch.carriage_lights")))
      if self.get_state("switch.carriage_lights")=='off':
        self.turn_on("switch.carriage_lights")
    else:
      if self.get_state("switch.carriage_lights")=='on':
        self.turn_on("switch.carriage_lights")

    for e in self.timeout_list:
      self.schedule_event(e)   

  def begin_nighttime(self, kwargs):
    self.log("Sunset")
    self.turn_on("switch.carriage_lights")

  def begin_morning(self, kwargs):
    self.log("Sunrise")
    self.turn_off("switch.carriage_lights")

  def schedule_event(self,entity):
    if self.now_is_between(self.times['nighttime'],self.times['morning']):
      self.timeout_list[entity]=self.time()
      self.run_in(self.turn_light_off,self.times['timeout'],entity_id=entity)
      self.log("scheduled to run in {} seconds for {} timeout_list={}".format(self.times['timeout'],entity,self.timeout_list))

  def light_timeout_check(self, entity, attribute, old, new, kwargs):
    if entity in self.timeout_list:
      self.schedule_event(entity)
    elif entity in ['input_slider.nighttime_hour','input_slider.nighttime_minutes','input_slider.morning_hour','input_slider.morning_minutes']:
      # someone changed the timeout times using the sliders.
      tod=entity[entity.find('.')+1:entity.find('_',6)]
      timevalue=str(int(float(new)))
      timeuom=entity[entity.find('_',6)+1:]
      newtime=self.parse_time(self.times[tod])
      if timeuom=='hour':
        self.times[tod]=timevalue+":"+str(newtime.minute)+":00"
      elif timeuom=='minutes':
        self.times[tod]=str(newtime.hour)+":"+timevalue+":00"
      self.save_times()
      self.process_current_state()
    elif entity=="input_slider.timeout_value":
      self.times['timeout']=str(int(float(new)))
      self.save_times()
      self.process_current_state()
    else:
      self.log("Unknown entity {}".format(entity))    

  def save_times(self):
    fout=open(self.filename,"wt")
    json.dump(self.times,fout)
    fout.close()

  def load_times(self):
    self.log("checking on file {}".format(self.filename))
    if os.path.exists(self.filename):
      fout=open(self.filename,"rt")
      self.times=json.load(fout)
      fout.close()
    else:
      self.alarms={}
    self.updateHA()

  def restartHA(self,event_name,data,kwargs):
    self.log("HA event {}".format(event_name))
    self.updateHA()

  def updateHA(self):
    self.select_value("input_slider.morning_hour",str(self.parse_time(self.times['morning']).hour))
    self.select_value("input_slider.morning_minutes",str(self.parse_time(self.times['morning']).minute))
    self.select_value("input_slider.nighttime_hour",str(self.parse_time(self.times['nighttime']).hour))
    self.select_value("input_slider.nighttime_minutes",str(self.parse_time(self.times['nighttime']).minute))
    self.select_value("input_slider.timeout_value",self.times['timeout'])

  def turn_light_off(self,kwargs):
    entity=kwargs["entity_id"]
    self.log("{} timed out turning off".format(entity))
    self.turn_off(entity)

  def build_timeout_list(self,entity):
    group_list=self.get_state(entity,attribute='all')["attributes"]["entity_id"]
    for object in group_list:
      device, entity = self.split_entity(object)
      if device=="group":
        self.build_timeout_list(object)
      else:
        self.timeout_list[object]=self.time()
    self.log("timeout_list={}".format(self.timeout_list))
