# OpenHAB-python-HomeIO
This is an integration between OpenHAB (Open Home Automation Bus, an open source home automation software) and Home I/O (closed-source home simulation software), done in Python, built on top of the python-openhab integration by sim0nx (https://github.com/sim0nx/python-openhab), which makes use of the REST API offered by OpenHAB. Integration is limited to any items declared and available in OpenHAB and the devices installed on the virtual home in Home I/O. This code is just a proof of concept and can be easily expanded upon.

This code was born as a college project and has since been made clearer for the reader.

The API DLL file `EngineIO.dll` has been included with permission from Home I/O development team. 

### Currently included
- Examples of light controls (as switches) in Living Room and Garage (rooms A and F in Home I/O, respectively)
- Example of light control (as a dimmable light) in the Garden, with 2 ways of operation:
  - Manual, in which you manually set the light values
  - Automatic, in which, when the brightness detector is on (low external luminosity), sets light value proportionally to the brightness measurement outside.
- Example of Rollershutter item with an openness detector in the Living Room (room A in Home I/O), which allows some sort of closed-loop control. 
- Example of Rollershutter item without openness detector but with limit switch sensors (Contact item), such as the Garage door (room F in Home I/O).
- Example of temperature readings (Number item) in the Living Room (room A in Home I/O).
- Simple, easily expandable program in Python.
- Corresponding items and sitemap in OpenHAB's conf folder for all these examples, with the proper names (essential!) as used in the Python code, for control via OpenHAB Classic UI or other interfaces that allow control over the home such as the Android or iOS app.

These examples cover all the basic devices installed in Home I/O, as all other devices not added in this example can also be controlled as a Switch, Dimmer, Rollershutter, Contact or Number items. Datetime items from Home I/O are not supported yet, but would be an easy addition.

### Current limitations
- Usage of the REST API from the python-openhab integration (asynchronous communication by definition) nullifies the bus nature (syncronous by definition) of OpenHAB. As such, it cannot capture events on the bus and limits usage to commands obtainable via the API
- Everything passes through Python, so control is not directly done via OpenHAB (the illusion of control is, indeed). Python gets, receives and parses OpenHAB commands, then transmits actions to Home I/O. At startup, Python updates all applicable OpenHAB items with the corresponding Home I/O values.
- Datetime items from Home I/O are not supported yet.

### Not included
Python source does not include: 
- Python (version used: 3.7)
- The OpenHAB version (used: 2.5.2 but any 2.x version should work just fine) or any of its prerequisites, like Java. Full documentation about OpenHAB is accessible at its own homepage: https://www.openhab.org/
- The python-openhab integration by sim0nx (https://github.com/sim0nx/python-openhab): `pip install python-openhab`. Works with commit https://github.com/sim0nx/python-openhab/commit/f71fdf1f9a3b039215392231b92e627fd738de36.

This has not been tested with any later versions of Python, OpenHAB or the python-openhab bridge as the proof of concept has been made for college. However, I will update this to make it work with latest versions in case there is enough interest.
