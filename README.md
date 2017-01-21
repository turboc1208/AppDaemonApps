# AppDaemonApps
Files<P>
<table>
<tr><td>alarmclock.py <td>Alarm Clock uses groups to hold alarm time and devices to turn on in response to alarm time being reached.  Relies heavily on a specific naming convention, but by doing so, allows you to support multiple rooms with seperate alarms.</tr>
<tr><td>nightlight.py <td>during nighttime hours, turns on dimable lights at really low power to not blind me when I go for a midnight snack.</tr>
<tr><td>printermonitor.py <td>use SNMP to monitor printers toner and ink levels.</tr>
<tr><td>speak.py<td>an innitial attempt as a speach engine for HA</tr>
<tr><td>sunrise_sunset<td>This turns on my carriage lamps on the garage at sundown and turns them off at sunup.  It also checks for lights being turned on during nighttime hours and turns them off automatically after 5 minutes (configurable).  My kids are bad about leaving lights on when they come down for a midnight snack.</tr>
<tr><td>talk.py<td>test program using speak.py</tr>
<tr><td>template.py<td>Template I use for starting new apps</tr>
<tr><td>vacant_lights.py<td>doesn't work</tr>
<tr><td>weatherAlert.py<td>trigger persistent notifications on weather underground weather alert data</tr>
<tr><td>samplealert.json<td>Sample data to use to debug weatherAlert (use LOGLEVEL="DEBUG" to use</tr>
<tr><td>xmaslights.py<td>handles processing of my Christmas lights.  Includes logic to turn off outdoor lights if it's raining according to weather underground.</tr>
</table>
