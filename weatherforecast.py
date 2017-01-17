import appdaemon.appapi as appapi
import requests
from requests.auth import HTTPDigestAuth
import json
             
class weatherforecast(appapi.AppDaemon):

  def initialize(self):
    self.LOGLEVEL="DEBUG"
    self.log("Weather Forecast App")
    self.key="c54290c5f59273ed"
    self.state="TN"
    self.city="Cordova"
    self.getForecast()

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

  def getForecast(self):
    # Replace with the correct URL
    url = "http://api.wunderground.com/api/{}/forecast/q/{}/{}.json".format(self.key,self.state,self.city)

    # It is a good practice not to hardcode the credentials. So ask the user to enter credentials at runtime
    myResponse = requests.get(url)
    self.log("myResponse.status_code={}".format(myResponse.status_code))

    # For successful API call, response code will be 200 (OK)
    if( not myResponse.ok):
       myResponse.raise_for_status()
    else:
      # Loading the response data into a dict variable
      # json.loads takes in only binary or string variables so using content to fetch binary content
      # Loads (Load String) takes a Json file and converts into python data structure (dict or list, depending on JSON)
      jData = json.loads(myResponse.content.decode('utf-8'))

      self.log("The response contains {0} properties".format(len(jData)))
      for key in jData:    # response & features:
        self.log("key={}".format(key))
        for x in jData[key]:
          self.log("x=    {}".format(x))
          if type(jData[key][x]) is dict:
            for y in jData[key][x]:
              self.log("y=        {}".format(y))
              if type(jData[key][x][y]) is list:
                for z in range(0,len(jData[key][x][y])):
                  self.log("z=            {}".format(z))
                  for z1 in jData[key][x][y][z]:
                    self.log("z1=                {}".format(z1))
                    if z1=="fcttext":
                      msg=jData[key][x][y][z][z1]
                      priority="1"
                      lang="en"
                      self.fire_event("SPEAK_EVENT",text=msg,priority=priority,language=lang)
                    else:
                      self.log("z2                    {}".format(jData[key][x][y][z][z1]))
              else:
                self.log("y=            {}".format(jData[key][x][y]))
          else:
            self.log("x=        {}".format(jData[key][x]))

