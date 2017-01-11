import appdaemon.appapi as appapi
import datetime
import tempfile
import subprocess
import os
from gtts import gTTS

class speaknow(appapi.AppDaemon):

  def initialize(self):
    self.filelist = {"1":["empty"],"2":["empty"],"3":["empty"],"4":["empty"],"5":["empty"]}
    self.run_in(self.check_soundlist,2)
    self.listen_event(self.handle_speak_event,"SPEAK_EVENT")

  def handle_speak_event(self, event_name, data, kwargs):
    self.log("handling speak event {} text={} priority={}".format(event_name,data["text"],data["priority"]))
    self.say(data["text"],"en",data["priority"])

  def check_soundlist(self, kwargs):
#    self.log("runsound is running")
    for priorityfilelist in self.filelist.values():
      for file in priorityfilelist:
        if file != "empty":
          self.log("file gevonden: " + file)
          self.play(file)
          priorityfilelist.remove(file)
          os.remove(file)
          self.run_in(self.check_soundlist,2)        
          return
#        self.log("priorityfilelist was empty")
#    self.log("list was empty, restart check")
    self.run_in(self.check_soundlist,2)
    
  def say(self,text,lang,priority):
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
        fname = f.name
    tts = gTTS(text=text, lang=lang)
    tts.save(fname)
    self.filelist[priority].append(fname)
  
  def playsound(self,file,priority):
    self.filelist[priority].append(file)

  def play(self,filename):
    cmd = ['omxplayer','-o','local',filename]
    with tempfile.TemporaryFile() as f:
        subprocess.call(cmd, stdout=f, stderr=f)
        f.seek(0)
        output = f.read()
