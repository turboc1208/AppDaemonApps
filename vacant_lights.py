import appdaemon.appapi as appapi
           
class vacant_lights(appapi.AppDaemon):

  def initialize(self):
    self.log("Initializing vacant_lights")
    self.room={}
    self.listen_event(self.event_happened)

  def event_happened(self, event_name, data, kwargs):
    #self.log("data={}".format(data))
    if "entity_id" in data:
      if data["entity_id"][:data["entity_id"].find(".")]=="device_tracker" :
        self.log("friendly_name={}".format(data["new_state"]["attributes"]["friendly_name"].lower()))
        checkroom=data["new_state"]["attributes"]["friendly_name"].lower()
        self.log("{} is {}".format(checkroom,data["new_state"]["state"]))
        if data["new_state"]["state"]=="not_home" :
          self.log("{} just left".format(checkroom))
          if checkroom=="chip" or checkroom=="susan" :
            checkroom="master"
            if self.check_room_presence(["chip","susan"]) == "not_home" :
              self.log("Chip and Susan are both gone")
              self.turn_out_lights(checkroom)
            else:
              self.log("Either Chip or Susan are still home")
          else:
            self.turn_out_lights(checkroom)
        else:
          self.log("{} just got home".format(checkroom))

  def check_room_presence(self, device_friendly_names) :
    for device in device_friendly_names :
      if self.check_device(device)=="home":
        self.log("device={} status={}".format(device,self.check_device(device)))
        return "home"
    return "not_home"

  def check_device(self, device_friendly_name) :
    for tracker in self.get_trackers():
      self.log("tracker={} - {}".format(self.get_state(tracker),self.get_state(tracker, attribute="attributes")["friendly_name"].lower()))
      if device_friendly_name  == self.get_state(tracker, attribute="attributes")["friendly_name"].lower():
        return self.get_state(tracker)
        
  def turn_out_lights(self,checkroom):
    check="group."+checkroom+"lights"
    self.log("check={}".format(check))
    room_attributes=self.get_state(check, attribute="all")
    self.log("{} lights= {}".format(checkroom,room_attributes["attributes"]["entity_id"]))
    for device in room_attributes["attributes"]["entity_id"]:
      self.log("checking light {} {}".format(device,self.get_state(device)))
      if self.get_state(device) == "on":
        self.turn_off(device)
