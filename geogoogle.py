import os
import datetime
import urllib
from urllib.parse import urlencode
from urllib.request import urlopen
import json

serviceurl='http://maps.googleapis.com/maps/api/geocode/json?'

while True:
  address = "Cordova, TN"
      
  url = serviceurl + urllib.parse.urlencode({'sensor':'false','address': address})
  print ("retrieving URL={}".format(url))
  
  uh = urllib.request.urlopen(url)

  data=uh.read()
  print("data={}".format(data))

  break
