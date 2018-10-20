  #####  Imports should be in adlib_imports.pyi file and must be included up near module imports
  #import inspect
  #import os
  #import json

  #######  Override AppDaemon log function
  def log(self,msg,level="INFO"):
    try:
      obj,fname, line, func, context, index=inspect.getouterframes(inspect.currentframe())[1]
      super().log("{} - ({}) {}".format(func,str(line),msg),level)
    except IndexError:
      super().log("Unknown - (xxx) {}".format(msg),level)
  
  ######################
  #
  # build_entity_list (self, ingroup, inlist - optional: defaults to all entity types))
  #
  # build a list of all of the entities in a group or nested hierarchy of groups
  #
  # ingroup = Starting group to cascade through
  # inlist = a list of the entity types the list may contain.  Use this if you only want a list of lights and switches for example.
  #            this would then exclude any input_booleans, input_numbers, media_players, sensors, etc. - defaults to all entity types.
  #
  # returns a python list containing all the entities found that match the device types in inlist.
  ######################
  def build_entity_list(self,ingroup,inlist=['all']):
    retlist=[]
    types=[]
    typelist=[]

    # validate values passed in
    if not self.entity_exists(ingroup):
      self.log("entity {} does not exist in home assistant".format(ingroup))
      return None
    if isinstance(inlist,list):
      typelist=inlist
    else:
      self.log("inlist must be a list ['light','switch','media_player'] for example")
      return None

    # determine what types of HA entities to return
    if "all" in typelist:
      types=["all"]
    else:
      types= types + typelist
      types.append("group")            # include group so that it doesn't ignore child groups

    # check the device type to see if it is something we care about
    devtyp, devname = self.split_entity(ingroup)
    if (devtyp in types) or ("all" in types):                # do we have a valid HA entity type
      if devtyp=="group":                                    # entity is a group so iterate through it recursing back into this function.
        for entity in self.get_state(ingroup,attribute="all")["attributes"]["entity_id"]:
          newitem=self.build_entity_list(entity,typelist)    # recurse through each member of the child group we are in.
          if not newitem==None:                              # None means there was a problem with the value passed in, so don't include it in our output list
            retlist.extend(newitem)                          # all is good so concatenate our lists together
      else:
        retlist.append(ingroup)                                      # actual entity so return it as part of a list so it can be concatenated
    return retlist

  ###########################
  #
  # Restart application by touching the app
  ###########################
  def restart_app(self):
    import os
    import fnmatch
    import subprocess

    matches=[]
    module=self.args["module"]                           #  Who am i
    module=module+".py"
    path=self.config["AppDaemon"]["app_dir"]             # find py file
    for root,dirnames,filenames in os.walk(path):
      #self.log("root={} dirnames={} filenames={}".format(root,dirnames,filenames))
      for filename in fnmatch.filter(filenames, module):
        matches.append(os.path.join(root,filename))
    self.log("restarting {}".format(matches))            # found matching files
    subprocess.call(["touch",matches[0]])                # touch the files

  ######  Override Appdaemon turn_on function
  def turn_on(self,entity_id,**kwargs):
    self.log("in my_turn_on {}".format(entity_id))
    etyp,enam = self.split_entity(entity_id)
    eid=etyp+"/"+enam
    for karg in kwargs:
      self.log("kwargs[{}]={}".format(karg,kwargs[karg]))

    if etyp in ["cover"]:
      self.log("Opening cover {}".format(entity_id))
      self.call_service("cover/open_cover",entity_id=entity_id)
    else:
      super().turn_on(entity_id,**kwargs)

  def turn_on_in(self,entity_id,delay):
    self.run_in(self.turn_on_handler,delay,entity_id=entity_id)

  def turn_on_handler(self,kwargs):
    self.turn_on(kwargs["entity_id"])

  #####  Override Appdaemon turn_off function
  def turn_off(self,entity_id,**kwargs):
    self.log("in my_turn_off {}".format(entity_id))
    etyp,enam=self.split_entity(entity_id)
    eid=etyp+"/"+enam
    if etyp in ["cover"]:
      self.log("closing cover {}".format(entity_id))
      self.call_service("cover/close_cover",entity_id=entity_id)
    else:
      super().turn_off(entity_id)

  def turn_off_in(self,entity_id,delay):
    self.run_in(self.turn_off_handler,delay,entity_id=entity_id)

  def turn_off_handler(self,kwargs):
    self.turn_off(kwargs["entity_id"])

  #####  Read jseon file named  filename  return dictionary
  def readjson(self,_filename):
    result={}
    if os.path.exists(_filename):
      fin=open(_filename,"rt")
      result=json.load(fin)
      fin.close()
    else:
      self.log("file {} does not exist".format(_filename))
    return result

  ##### Write dictionary out as a json file to filename
  def savejson(self,_filename,_out_dict):
    fout=open(_filename,"wt")
    json.dump(_out_dict,fout)
    fout.close()

  ##### Set unix file permissions
  def setfilemode(self,_in_file,_mode):
    if len(_mode)<9:
      self.log("mode must bein the format of 'rwxrwxrwx'")
    else:
      result=0
      for val in _mode: 
        if val in ("r","w","x"):
          result=(result << 1) | 1
        else:
          result=result << 1
      self.log("Setting file to mode {} binary {}".format(_mode,bin(result)))
      os.chmod(_in_file,result)

  ##### Send an email
  def emailme(self,_service,_target,_subject,_msg):
    self.call_service("notify/"+_service,title=_subject,message=_msg,target=_target)

  def listen_state(self,cb,e,**kwargs):
    self.log("in my listen_state")
    if self.entity_exists(e):
      super().listen_state(cb,e,**kwargs,ent=e)
    else:
      self.log("Entity {} does not exist in AD".format(e))
      self.log("kwargs={}".format(kwargs))
      if "retry" in kwargs:
        self.log("running _listen_state_retry in 10 seconds")
        if "_cb" in kwargs:
          # we have already tried once so _cb and _e are already in kwargs, adding them again will get an error.
          self.run_in(self._listen_state_retry,10,**kwargs)
        else:
          self.run_in(self._listen_state_retry,10,**kwargs,_cb=cb,_e=e)

  def _listen_state_retry(self,kwargs):
    self.log("_cb={},_e={},kwargs={}".format(kwargs["_cb"],kwargs["_e"],kwargs))
    self.listen_state(kwargs["_cb"],kwargs["_e"],**kwargs)
