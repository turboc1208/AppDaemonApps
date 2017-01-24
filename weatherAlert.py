###################################################################
# Weather Alert - Poll for alerts from weatherunderground and alert to HA
# Written By : Chip Cox  20JAN2017
#              
#    V0.01.1 21JAN2017 - updated to handle european data
#    V0.01.2 21JAN2017 - added configuration options 
#
###################################################################
#
# Use:
#   Add the following lines to your appDaemon config file
#     [weatherAlert]
#     module=weatherAlert
#     class=weatheralert
#     alerts = {"HEA","TOR"}
#     key = "your weather underground key"
#   * location={"city":"your city","state":"your state"}  or {"zmw":"your zmw"}`
#   * frequency=minutes between checks   ( Defaults to 15 min )
#   * title=title of persistent notification window
#
#   * entries are  optional
#
#     location can be expressed as a dictionary containing the following:
#                                    {"city":"your city", "state":"your state"}
#                                    {"zip":"your zip code"}
#                                    {"Country":"Your country name","city":"Your city"}
#                                    if location is not in the config file, it defaults to your HomeAssistant Latitude/Longitude
#     
#   Possible values for alerts are : type	Translated
#                                    HUR	Hurricane Local Statement
#                                    TOR	Tornado Warning
#                                    TOW	Tornado Watch
#                                    WRN	Severe Thunderstorm Warning
#                                    SEW	Severe Thunderstorm Watch
#                                    WIN	Winter Weather Advisory
#                                    FLO	Flood Warning
#                                    WAT	Flood Watch / Statement
#                                    WND	High Wind Advisory
#                                    SVR	Severe Weather Statement
#                                    HEA	Heat Advisory
#                                    FOG	Dense Fog Advisory
#                                    SPE	Special Weather Statement
#                                    FIR	Fire Weather Advisory
#                                    VOL	Volcanic Activity Statement
#                                    HWW	Hurricane Wind Warning
#                                    REC	Record Set
#                                    REP	Public Reports
#                                    PUB	Public Information Statement
#
#  If you are using the following speach apps in appdaemon
#  sound - by Rene Tode - https://community.home-assistant.io/t/let-appdaemon-speak-without-tts-and-mediaplayer-in-hass/8058
#  speak - by Chip Cox - https://github.com/turboc1208/AppDaemonApps/blob/master/speak.py
#
#  weatherAlert will recognize them and send alerts to your speakers as well
#  as the persistent_notifications.
#
##################################################################################
#
# Visit the weatherunderground at the following link for more information about this API
# https://www.wunderground.com/weather/api/d/docs?d=data/alerts
##################################################################################
import appdaemon.appapi as appapi
import requests
from requests.auth import HTTPDigestAuth
import json
import time
import datetime
#from homeassistant.util import location    
         
class weatheralert(appapi.AppDaemon):

  def initialize(self):
    self.LOGLEVEL="INFO"
    self.alertlog={}
    self.log("Weather Alert App")
    self.haConfig=self.loadHAconfig()
    self.key=self.args["key"]
    if "location" in self.args:
      self.loc=eval(self.args["location"])
    else:
      self.loc={}

    if "title" in self.args:
      self.title=self.args["title"]
    else:
      self.title="Weather Alert"

    if "zmw" in self.loc:
      self.location=self.loc["zmw"]
    elif "zip" in self.loc:
      self.location=self.loc("zip")
    elif ("country" in self.loc) and ("city" in self.loc):
      self.location=self.loc["country"]+"/"+self.loc["city"]
    elif ("city" in self.loc) and ("state" in self.loc):
      self.location=self.loc["state"]+"/"+self.loc["city"]
    else:
      self.location=str(self.haConfig["latitude"])+","+str(self.haConfig["longitude"])
    self.log("haConfig={}".format(self.haConfig))
    if "frequency" in self.args:
      self.freq=int(float(self.args["frequency"]))
    else:
      self.freq=15
    self.desired_alerts=self.args["alerts"]

    self.log("Location={}".format(self.location))
    self.log("Key=ImNotTelling")
    self.log("Alert Levels={}".format(self.desired_alerts))
    self.log("Setting WeatherAlert to run ever {} minutes or {} seconds".format(self.freq,self.freq*60),"INFO")
    # you might want to use run_minutely for testing and run every (self.freq)  minutes for production.
    #self.run_minutely(self.getAlerts,start=None)
    self.run_every(self.getAlerts,self.datetime(),self.freq*60)

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

  ###########################
  def getAlerts(self,kwargs):
    # Get Alert Data
    url = "http://api.wunderground.com/api/{}/alerts/q/{}.json".format(self.key,self.location)
    self.log("url={}".format(url),"DEBUG")

    myResponse = requests.get(url)
    self.log("myResponse.status_code={}".format(myResponse.status_code),"DEBUG")

    # For successful API call, response code will be 200 (OK)
    if( not myResponse.ok):
       myResponse.raise_for_status()
    else:
      # Loading the response data into a dict variable
      # json.loads takes in only binary or string variables so using content to fetch binary content
      # Loads (Load String) takes a Json file and converts into python data structure (dict or list, depending on JSON)
      jData = json.loads(myResponse.content.decode('utf-8'))
      if self.LOGLEVEL=="DEBUG":
        filename=self.config["AppDaemon"]["app_dir"] + "/" + "samplealert.json"
        with open(filename) as json_data:
          jData=json.load(json_data)         

      self.log("alerts={}".format(jData),"DEBUG")
      if not "alerts" in jData:                                                      # can't do anything without an alerts section
        self.log("For some reason there is no alerts key in the data coming from WeatherUnderground")
        return

      self.log("The response contains {0} properties".format(len(jData)),"DEBUG")
      if len(jData)==0:                                                              # if there aren't any alerts clean out the alertlog and skip the rest.
        self.alertlog={}
        self.log("No Alerts at this time","INFO")
      else:
        for alert in jData["alerts"]:                                                  # Loop through all the alerts
          alert["key"]=alert["type"]+alert["expires"]                                  # setup a unique reproducable key for each alert 
          self.log("alert[type]={}".format(alert["type"]),"DEBUG")
          if alert["type"] in self.desired_alerts:                                     # is this an alert type we are interested in
            if not alert["key"] in self.alertlog:                                      # if the key is in the alertlog we have already alerted on it
              if self.timefromstring(alert["expires"])<datetime.datetime.now():        # has this alert expired?
                self.log("Alert has expired {}".format(alert),"INFO")
              else:                                                                    # nope it has not expired
                self.alertlog[alert["key"]]=alert["expires"]                           # put the key and expire date into the alertlog so we don't show it again
                self.log("this is an alert we are interested in {}".format(alert["type"]),"INFO")
                if "message" in alert:                                                 # Alert using a persistent notification ( you could add other methods of alerting here too)
                  self.sendAlert(alert["message"])
                else:
                  self.sendAlert(alert["level_meteoalarm_description"])
                  #self.call_service("persistent_notification/create",title="Weather Alert",message=alert["level_meteoalarm_description"])
            else:                                                                      # we have already notified on this so don't do it again
              self.log("Alert already in list","DEBUG")
          else:                                                                        # there is an alert but we aren't interested in this type
            self.log("we are not interested in alert type {}".format(alert["type"]),"INFO")

  #######################
  #
  # send the proximity alert and send it to speak if it's installed
  #
  #######################
  def sendAlert(self,msg):
    self.call_service("persistent_notification/create",title=self.title,message=msg)   # send persistent_notification 
    if not  self.get_app("speak")==None:                                                    # check if speak is running in AppDaemon
      self.log("Speak is installed")
      priority=1
      self.fire_event("SPEAK_EVENT",text=msg,priority=priority,language="en")               # Speak is installed so call it
    elif not self.get_app("soundfunctions")==None:
      self.log("Soundfunctions is installed")
      sound = self.get_app("soundfunctions")                                                 
      sound.say("Any text you like","your_language","your_priority")    
    else:
      self.log("No supported speack apps are installed")                                                    # Speak is not installed

  #######################
  # Had some problems getting weather undergrounds date format to behave so I had to parse it out myself
  #######################
  def timefromstring(self,instr):
    # This is weather undergrounds timestamp format.  Notice the "on" in the middle.  This caused a problem.
    # h:mm AM TZZ on month dd, yyyy

    strtime=instr[0:instr.find("on")-1]
    strdate=instr[instr.find("on")+3:]
    self.log("strtime {} strdate {}".format(strtime,strdate),"DEBUG")
    tdate=datetime.datetime.strptime(strdate + " " + strtime,"%B %d, %Y %I:%M %p %Z")
    self.log("tDate {}".format(tdate),"DEBUG")
    return tdate

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

