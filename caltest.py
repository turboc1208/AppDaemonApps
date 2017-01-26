#!/usr/bin/python
#
# Copyright 2012 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# requires tzlocal install

import httplib2
import sys
from datetime import datetime
from tzlocal import get_localzone

from apiclient.discovery import build
from oauth2client import tools
from oauth2client.file import Storage
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import OAuth2WebServerFlow

client_id = "22946252841-dsmt2h71j4as4s91npps5lbg1mge74lt.apps.googleusercontent.com"
client_secret = "ONhlpv5K6tYJt1kBq0qxyagW"

tzoffset="-06:00"

# The scope URL for read/write access to a user's calendar data
scope = 'https://www.googleapis.com/auth/calendar'

# Create a flow object. This object holds the client_id, client_secret, and
# scope. It assists with OAuth 2.0 steps to get user authorization and
# credentials.
flow = OAuth2WebServerFlow(client_id, client_secret, scope)

def main():

  # Create a Storage object. This object holds the credentials that your
  # application needs to authorize access to the user's data. The name of the
  # credentials file is provided. If the file does not exist, it is
  # created. This object can only hold credentials for a single user, so
  # as-written, this script can only handle a single user.
  storage = Storage('credentials.dat')

  # The get() function returns the credentials for the Storage object. If no
  # credentials were found, None is returned.
  credentials = storage.get()

  # If no credentials are found or the credentials are invalid due to
  # expiration, new credentials need to be obtained from the authorization
  # server. The oauth2client.tools.run_flow() function attempts to open an
  # authorization server page in your default web browser. The server
  # asks the user to grant your application access to the user's data.
  # If the user grants access, the run_flow() function returns new credentials.
  # The new credentials are also stored in the supplied Storage object,
  # which updates the credentials.dat file.
  if credentials is None or credentials.invalid:
    credentials = tools.run_flow(flow, storage, tools.argparser.parse_args())

  # Create an httplib2.Http object to handle our HTTP requests, and authorize it
  # using the credentials.authorize() function.
  http = httplib2.Http()
  http = credentials.authorize(http)

  # The apiclient.discovery.build() function returns an instance of an API service
  # object can be used to make API calls. The object is constructed with
  # methods specific to the calendar API. The arguments provided are:
  #   name of the API ('calendar')
  #   version of the API you are using ('v3')
  #   authorized httplib2.Http() object that can be used for API calls
  service = build('calendar', 'v3', http=http)
  page_token=None

  try:
    while True:
      cal_list = service.calendarList().list(pageToken=page_token).execute()
      for cal in cal_list["items"]:
        if not cal["id"].find("@group")>=0:
          print("{}".format(cal["id"]))
          now = datetime.now()
          strtime = now.isoformat('T')+tzoffset
          request = service.events().list(calendarId=cal["id"],timeMin=strtime)
          # Loop until all pages have been processed.
          while request != None:
            # Get the next page.
            response = request.execute()
            # Accessing the response like a dict object with an 'items' key
            # returns a list of item objects (events).
            for event in response.get('items', []):
              if not event["status"]=="cancelled":
                if "dateTime" in event["start"]:
                  # The event object is a dict object with a 'summary' key.
                  print("{} - {}".format(event['start']['dateTime'], event['summary']))
            # Get the next request object by passing the previous request object to
            # the list_next method.
            request = service.events().list_next(request, response)
      page_token = cal_list.get("nextPageToken")
      if not page_token:
        break

  except AccessTokenRefreshError:
    # The AccessTokenRefreshError exception is raised if the credentials
    # have been revoked by the user or they have expired.
    print ("The credentials have been revoked or expired, please re-run"
           "the application to re-authorize")

if __name__ == '__main__':
  main()
