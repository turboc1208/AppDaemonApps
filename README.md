# AppDaemonApps
Files
alarmclock.py - Alarm Clock uses groups to hold alarm time and devices to turn on in response to alarm time being reached.  Relies heavily on a specific naming convention, but by doing so, allows you to support multiple rooms with seperate alarms.
nightlight.py - during nighttime hours, turns on dimable lights at really low power to not blind me when I go for a midnight snack.
sunrise_sunset - This turns on my carriage lamps on the garage at sundown and turns them off at sunup.  It also checks for lights being turned on during nighttime hours and turns them off automatically after 5 minutes (configurable).  My kids are bad about leaving lights on when they come down for a midnight snack.
xmaslights.py - handles processing of my Christmas lights.  Includes logic to turn off outdoor lights if it's raining according to weather underground.
