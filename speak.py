####################
#   speak.py
#   Written by Chip Cox & Rene Tode
#
#   Allow your HA and AD installs to talk to you and your family.
#
#   This was heavily influenced by the work done by Rene Tode on his sound application
#
####################
#
#   you will need to install gtts and omxplayer if not already installed
#
###################
#
#   set your appdaemon.cfg file as follows
#
#   [speak]
#   module=speak
#   class=speak
#
###################
#
#   Save this in your appdaemon appdir with your apps.
#
#   to use this simply fire the "SPEAK_EVENT" with text, priority, and language parameters as follows
#   self.fire_event("SPEAK_EVENT",text=speaktext, priority=pri, language=lang)
#
###################

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
    self.listen_event(self.handle_speak_event,"SPEAK_EVENT")              # listen for a SPEAK_EVENT

  def handle_speak_event(self, event_name, data, kwargs):
    self.log("handling speak event {} text={} language={}  priority={}".format(event_name,data["text"],data["language"],data["priority"]),"INFO")
    self.say(data["text"],data["language"],data["priority"])              # Say it

  ##################################
  # schedule callback to see if anything is in our list to say
  ##################################
  def check_soundlist(self, kwargs):
    for priorityfilelist in self.filelist.values():                       # loop through the priorities each priority has a list of files
      for file in priorityfilelist:                                       # loop through any files in the priority we are on
        if file != "empty":                                               # if we have a file then play it
          self.log("filename : " + file,"DEBUG")
          self.play(file)
          priorityfilelist.remove(file)
          os.remove(file)
    self.run_in(self.check_soundlist,2)                                   # Reschedule another check
    
  #################################
  # Generate mp3 file and add it to the priority list
  #################################
  def say(self,text,lang,priority):
    if str(priority) in self.filelist:                                      # Do we have a valid priority
      with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:   # generate a temp filename
        fname = f.name
      tts = gTTS(text=text, lang=lang)                                      # generate mp3 file
      tts.save(fname)
      self.filelist[str(priority)].append(fname)                            # add file to priority list
    else:
      self.log("invalid priority {}".format(priority))

  ########################
  #  Send file to omxplayer over local speaker
  ########################
  def play(self,filename):
    cmd = ['omxplayer','-o','local',filename]                               # use omxplayer to play sound
    with tempfile.TemporaryFile() as f:
        subprocess.call(cmd, stdout=f, stderr=f)
        f.seek(0)
        output = f.read()
