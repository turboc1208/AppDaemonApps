import appdaemon.appapi as appapi
import random
       
class testspeak(appapi.AppDaemon):

  def initialize(self):
    self.log("about to fire SPEAK event")
    self.run_in(self.say_something,2)

  def say_something(self, kwargs):
    priority="1"
    speaktext = "i am alive"
    sound = self.get_app("speak")
    sound.say(speaktext,"en",priority)
    self.run_in(self.say_something,random.randint(60,600))
