# developed by Chip Cox
#              January 2017
#

import appdaemon.appapi as appapi
import os
import json
import datetime
                       
class sunrise_sunset(appapi.AppDaemon):

  def initialize(self):
    self.log("SunUp Sundown setup",level="INFO")
    self.setup_mode()
    # initialize variables
    self.times={}
    self.times['morning']='05:00:00'
    self.times['nighttime']='22:00:00'
    self.times['timeout']='600'

    # build list of entities subject to timeout
    self.timeout_list={}
    self.timeout_list=self.build_timeout_list("group.timeout_lights")
    self.log("timeout_list final={}".format(self.timeout_list),level = "DEBUG")

    # read actual times from config file and update HA with the saved values.
    self.filename=self.config["AppDaemon"]["app_dir"] + "/" + "sunrisesunset.cfg"
    self.load_times()
    self.process_current_state()

    # Setup callbacks
    self.listen_state(self.light_timeout_check, new="on", old="off")
    self.listen_state(self.process_input_slider, entity="input_slider")
    self.run_at_sunset(self.begin_nighttime)
    self.run_at_sunrise(self.begin_morning)

  def setup_mode(self):
    self.maintMode=False
    self.vacationMode=False
    self.partyMode=False
    self.maintMode=self.getOverrideMode("input_boolean.maint")
    self.vacationMode=self.getOverrideMode("input_boolean.vacation")
    self.partyMode=self.getOverrideMode("input_boolean.party")
    self.log("Maint={} Vacation={} Party={}".format(self.maintMode,self.vacationMode,self.partyMode))

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
    self.log("Maint={} Vacation={} Party={}".format(self.maintMode,self.vacationMode,self.partyMode))

  # this is called only on startup to check the current state of lights and adjust them according to the current time.
  def process_current_state(self):
    self.log("time to process current state of lights","INFO")
    if self.sun_down():
      # after sundown to turn on carriage lights if they are off.
      self.log("after sundown state={}".format(self.get_state("switch.carriage_lights")),level="DEBUG")
      #handle carriage lights.  They aren't a timeout thing, but they do change at sunrise and sunset.
      if self.get_state("switch.carriage_lights")=='off':
        self.turn_on("switch.carriage_lights")
    else:
      # if the sun isn't down, it must be up so if the carriage lights are on, turn them off.
      if self.get_state("switch.carriage_lights")=='on':
        self.turn_on("switch.carriage_lights")
      elif self.get_state("light.outdoor_patio_light")=='on':
        self.turn_off("light.outdoor_patio_light")
    
    # check on the lights in the timeout list and schedule turnoff events if they are already on.
    for e in self.timeout_list:
      self.schedule_event(e)   

  # callback for sunset
  def begin_nighttime(self, kwargs):
    self.log("Sunset",level="INFO")
    self.turn_on("switch.carriage_lights")

  # callback for morning
  def begin_morning(self, kwargs):
    self.log("Sunrise",level="INFO")
    self.turn_off("switch.carriage_lights")

  # given an entity if it is between start of nighttime and start of morning, and the current state is on schedule a timeout event
  def schedule_event(self,entity):
    if self.now_is_between(self.times['nighttime'],self.times['morning']) and self.get_state(entity)=="on":
      # set current time, time when the event was scheduled.
      self.timeout_list[entity]=self.time()
 
      # Schedule the event to run in "timeout" seconds (timeout was read from config file")
      self.run_in(self.turn_light_off,self.times['timeout'],entity_id=entity)
      self.log("scheduled to run in {} seconds for {} timeout_list={}".format(self.times['timeout'],entity,self.timeout_list),level="INFO")

  # someone turned something on
  def light_timeout_check(self, entity, attribute, old, new, kwargs):
    # if the entity that turned on is in the timeout_list, try to schedule an event for it
    if entity in self.timeout_list:
      self.schedule_event(entity)

  # Deal with someone changing the time nighttime, morning, or the timeout value which are all input sliders.
  def process_input_slider(self, entity, attribute, old, new, kwargs):
    # is the input slider that was changed one of our starting times?
    if entity in ['input_slider.nighttime_hour','input_slider.nighttime_minutes','input_slider.morning_hour','input_slider.morning_minutes']:
      # the sliders are named carefully <tod>_<hour or minutes> this way we can compress our code a little
      # the TimeOfDay is everything from the period between the device type and the name, to the underscore in the name 
      #     we skip ahead 6 to get past the underscore in "input_slider"
      tod=entity[entity.find('.')+1:entity.find('_',6)]

      # time uom is either going to be hour or minutes
      timeuom=entity[entity.find('_',6)+1:]

      # convert new from floating point to the string representation of an integer
      timevalue=str(int(float(new)))

      # convert the current saved time value to a time structure
      newtime=self.parse_time(self.times[tod])

      if timeuom=='hour':
        # if we are dealing with hours then use the new value first and add the current minutes and 00 for seconds to it.
        self.times[tod]=timevalue+":"+str(newtime.minute)+":00"
      elif timeuom=='minutes':
        # for minutes we use the current hour and add the new minutes and 00 for seconds to it.
        self.times[tod]=str(newtime.hour)+":"+timevalue+":00"

      # write the times out to our config file
      self.save_times()

      # since we have new starting and ending times now check our current state again
      self.process_current_state()
  
    elif entity=="input_slider.timeout_value":
      # it wasn't a start or end time related slider, it was the timeout value that was adjusted
      # no fancy parsing here, just convert the new value to the string representation of an integer
      # save it and check the current state again
      self.times['timeout']=str(int(float(new)))
      self.save_times()
      self.process_current_state()
    else:
      # it was in input slider, but it wasn't one we are interested in.
      self.log("Unknown entity {}".format(entity),level="WARNING")    

  # write the times out to our configuration file
  def save_times(self):
    fout=open(self.filename,"wt")
    json.dump(self.times,fout)
    fout.close()
    os.chmod(self.filename,stat.S_IRUSR & stat.S_IWUSR & stat.S_IRGRP & stat.S_IWGRP & stat.S_IROTH & stat.S_IWOTH)

  # load times fromour configuration file
  def load_times(self):
    self.log("checking on file {}".format(self.filename),level="DEBUG")
    if os.path.exists(self.filename):
      # file exists so open and read it
      fout=open(self.filename,"rt")
      self.times=json.load(fout)
      fout.close()
      # update HA with the values we just read
      self.updateHA()
    else:
      # file did not exist so setup an empty dictonary 
      self.times={}

  # HA was restarted so when it comes up, we need to adjust the default values in HA to our values.
  def restartHA(self,event_name,data,kwargs):
    self.log("HA event {}".format(event_name),level="WARNING")
    self.updateHA()

  # adjust each of our sliders based on the values we have.
  def updateHA(self):
    self.select_value("input_slider.morning_hour",str(self.parse_time(self.times['morning']).hour))
    self.select_value("input_slider.morning_minutes",str(self.parse_time(self.times['morning']).minute))
    self.select_value("input_slider.nighttime_hour",str(self.parse_time(self.times['nighttime']).hour))
    self.select_value("input_slider.nighttime_minutes",str(self.parse_time(self.times['nighttime']).minute))
    self.select_value("input_slider.timeout_value",self.times['timeout'])

  # after all that we finally are going to turn off the lights
  def turn_light_off(self,kwargs):
    entity=kwargs["entity_id"]
    self.log("{} timed out turning off".format(entity),level="INFO")
    self.turn_off(entity)
    priority="1"
    speaktext = "Please remember to turn out the {}".format(entity)
    lang = "en"
    self.fire_event("SPEAK_EVENT",text=speaktext, priority=priority,language=lang)


  # loop through the group that was passed in as entity and return a dictionary of entities
  def build_timeout_list(self,entity):
    elist={}
    for object in self.get_state(entity,attribute='all')["attributes"]["entity_id"]:
      device, entity = self.split_entity(object)
      if device=="group":
        # if the device is a group recurse back into this function to process the group.
        elist.update(self.build_timeout_list(object))
      else:
        elist[object]=self.time()
      self.log("elist={}".format(elist),level="DEBUG")
    return(elist)
