import appdaemon.appapi as appapi
             
class test(appapi.AppDaemon):

  def initialize(self):
    self.log("Test App")
