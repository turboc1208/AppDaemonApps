import appdaemon.appapi as appapi
            
class talk(appapi.AppDaemon):

  def initialize(self):
    self.log("about to fire SPEAK event")
    self.run_in(self.say_something,2)

  def say_something(self, kwargs):
    priority="1"
    lang = "en"
    speaktext= "ahlexa, Turn off stairway light switch"
    self.fire_event("SPEAK_EVENT",text=speaktext, priority=priority,language=lang)
