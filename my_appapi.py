import appdaemon.appapi as appapi
import inspect
import os
import json

class my_appapi(appapi.AppDaemon):

  #######  Override AppDaemon log function
  def log(self,msg,level="INFO"):
    try:
      obj,fname, line, func, context, index=inspect.getouterframes(inspect.currentframe())[1]
      super().log("{} - ({}) {}".format(func,str(line),msg),level)
    except IndexError:
      super().log("Unknown - (xxx) {}".format(msg),level)
  
  ###### Set house state
  def set_house_state(self,entity,state):
    if self.entity_exists(entity):
      self.select_option(entity,state)
      retval=self.get_state(entity)
    else:
      retval=None
    return(retval)

  ######  Get house state
  def get_house_state(self,entity):
    if self.entity_exists(entity):
      state=self.get_state(entity)
      self.log("house state={}".format(state),"DEBUG")
    else:
      state=None
    return(state)

  ######################
  #
  # build_entity_list (self, ingroup, inlist - optional: defaults to all entity types))
  #
  # build a list of all of the entities in a group or nested hierarchy of groups
  #
  # ingroup = Starting group to cascade through
  # inlist = a list of the entity types the list may contain.  Use this if you only want a list of lights and switches for example.
  #            this would then exclude any input_booleans, input_sliders, media_players, sensors, etc. - defaults to all entity types.
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
    for karg in kwargs:
      self.log("kwargs[{}]={}".format(karg,kwargs[karg]))
    super().turn_on(entity_id,**kwargs)

  def turn_on_in(self,entity_id,delay):
    self.run_in(self.turn_on_handler,delay,entity_id=entity_id)

  def turn_on_handler(self,kwargs):
    self.turn_on(kwargs["entity_id"])

  #####  Override Appdaemon turn_off function
  def turn_off(self,entity_id):
    self.log("in my_turn_off {}".format(entity_id))
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

  def get_state(self,target,attribute="state",**kwargs):
    #self.log("in get_state target={}, attribute={}, kwargs={}".format(target,attribute,kwargs))
    if not self.entity_exists(target):
      _new_state=super().get_state(target,attribute)
    else:
      _new_state=super().get_state(target,attribute)
      self.log("in get_state")
      if "type" in kwargs:
        _type=kwargs["type"]
        if _type=="temperature":
          #_new_state=super().get_state(target)
          self.log("under temperature, new state for {} is {}".format(target,_new_state))
          if not "max" in kwargs:
            _max=-1.0
          else:
            _max=float(kwargs["max"])
          if not "min" in kwargs:
            _min=999.0
          else:
            _min=float(kwargs["min"])
          if float(_new_state)>_max:
            _new_state="on"
          elif float(_new_state)<=_min:
            _new_state="off"
          elif (float(_new_state)>_min) and (float(_new_state) < _max):
            _new_state="unk"
        elif _type=="motion":
          if _new_state=="8":
            _new_state="on"
          else:
            _new_state="off"
        elif _type=="door":
          if _new_state=="23":
            _new_state="on"
          else:
            _new_state="off"
        elif _type=="location":
         if _new_state.upper in ["HOME","HOUSE"]:
           _new_state="home"
       
    return _new_state

#######################################################
# Database functions

  ###############
  #
  #  db_open - returns connection handle
  #     dbname = full path filename
  #
  def db_open(self,dbname):
    try:
      conn=sqlite3.connect(dbname)
    except:
      self.log("Error opening connection to {}".format(dbname))
      conn=None
    finally:
      return conn

  ###############
  #
  # db_no_data_found - datadictionary
  #             return true if data dictionary is empty row
  def db_no_data_found(self,datadict):
    ndf=True
    if len(datadict)<=1:
       for col in datadict[0]:
         if datadict[0][col]!="":
           ndf=False
           break
    else:
      ndf=False
    return ndf

  #######
  #
  #  db_create_table - connection object, table name, columns dictionary
  #  {"columnname":["attribute list"],
  #   "nextcol":["attribute list"]}
  #  table_constraints are primarily for multi column unique constraints.  They
  #                    could have been added to the dictionary, that that would
  #                    make it more complex.
  #
  def db_create_table(self,conn,table,cols,table_constraints=""):
    self.log("creating table={}, table_constraints={}".format(table,table_constraints))
    curr=conn.cursor() 
    sqlstr="create table if not exists " + table +" ("
    numcol=len(cols)
    i=0
    for col in cols:
      i=i+1
      sqlstr=sqlstr + col + " "
      for opt in cols[col]:
        sqlstr=sqlstr + " " + opt
      if i<numcol:
        sqlstr=sqlstr + ", "
    if table_constraints!="":
      table_constraints=", " + table_constraints
    sqlstr=sqlstr + " " + table_constraints + ")"
    try:
      curr.executescript(sqlstr)
    except:
      raise
    finally:
      curr.close()
  
  ###############
  #
  # db_commit - connection parameter
  #             included for completeness
  def db_commit(self,conn):
    conn.commit()

  ###############
  #
  # db_close - connection parameter
  #             included for completeness
  def db_close(self,conn):
    conn.close()

  ###############
  #
  # db_rollback - connection parameter
  #             included for completeness
  def db_rollback(self,conn):
    conn.rollback()
 
  ###########
  #
  # db_select - returns a list of dictionaries of the columns selected
  #
  #
  def db_select(self,conn,query):
    self.log("query={}".format(query))
    curr=conn.cursor()
    try:
      curr.execute(query)
      result=curr.fetchall()
      desc=curr.description
    except:
      raise
    finally:
      curr.close()
    ret=[]
    r={}
    if len(result)==0:
      for col in range(len(desc)):
        r[desc[col][0]]=""
      ret.append(r)
    else:
      for row in range(len(result)):
        r={}
        for col in range(len(desc)):
          r[desc[col][0]]=result[row][col]
        ret.append(r)
    return ret

  ###############
  #
  #  db_insert_row -  Insert one or more rows into table.
  #     table - name of table
  #     data_dict - list of {column:data, col2,data} dictionaries
  # 
  def db_insert_row(self,conn,table,data_dict):
    for row in data_dict:
      curr=conn.cursor()
      sqlstr="insert into " + table 
      i=0
      colnames=" ("
      datavals=" ("
      for cname in row:
        if i!=0:
          colnames=colnames + ","
          datavals=datavals + ","
        colnames=colnames + " " + cname
        datavals=datavals + " '" + str(row[cname]) + "'"
        i=i+1
      colnames=colnames + ") "
      datavals=datavals + ") "
      sqlstr=sqlstr + colnames + " values " + datavals
      try:
        curr.execute(sqlstr)
      except:
        raise
      finally:
        curr.close()

  ###############
  #
  #  db_delete_row -  Delete one or more rows in a table.
  #     table - name of table
  #     data_dict - {column:data, col2,data} dictionaries
  #  All tests are for equality and all conditions are logical and
  #
  def db_delete_row(self,conn,table,wheredata):
    sqlstr="delete from " + table + " where "
    i=0
    for col in wheredata:
      if i!=0:
        sqlstr=sqlstr + " and "
      sqlstr=sqlstr + col + "='" + wheredata[col] + "'"
      i=i+1
    self.log("sqlstr={}".format(sqlstr))
    curr=conn.cursor()
    try:
      curr.execute(sqlstr)
    except:
      self.log("error deleting row from {} - {}".format(table,wheredata))
    finally:
      self.db_close(curr)

  ###############
  #
  #  db_update_row -  Delete one or more rows in a table.
  #     table - name of table
  #     update_dict - {column:data, col2,data} dictionary
  #     where_dict - {column:data, col2,data} dictinary
  #  All where_dict tests are for equality and all conditions are logical and
  #
  def db_update_row(self,conn,table,datadict,wheredata):
    sqlstr="update " + table + " set "
    i=0
    for f in datadict:
      if i!=0:
        sqlstr=sqlstr + ", "
      sqlstr=sqlstr + f + "= '" + datadict[f] + "' "
      i=i+1
    sqlstr=sqlstr + " where "
    i=0
    for w in wheredata:
      if i!=0:
        sqlstr=sqlstr + " and "
      sqlstr=sqlstr + w + " = '" + wheredata[w] + "' "
    self.log("update sqlstr={}".format(sqlstr)) 
    curr=conn.cursor()
    try:
      curr.execute(sqlstr)
    except:
      self.log("error updating row in {} to {} where {}".format(table,datadict,wheredata))
    finally:
      self.db_close(curr)

