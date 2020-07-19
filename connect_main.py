import sys
import time
import clr
from openhab import OpenHAB
from msvcrt import kbhit # Detect key press to exit
from subprocess import check_output # Check processes running

clr.AddReference('EngineIO')
from EngineIO import *


# There is no way to check if OpenHAB and Home I/O are running and Home I/O API is available
# Here's a best-effort process check by name.
ps = check_output('tasklist', shell=True)
#print(ps)
if "java.exe" not in str(ps):
    print("OpenHAB seems not running. Closing...")
    sys.exit()
if "Home IO.exe" not in str(ps):
    print("Home I/O seems not running. Closing...")
    sys.exit()

# Base OpenHAB config & ensure OpenHAB connection
base_url = 'http://localhost:8080/rest'
try:
    openhab = OpenHAB(base_url)
except Exception as e:
    print("Unable to open OpenHAB data:", e)
    sys.exit()

print("Initializing variables...")

# Correlate all variables of interest in this dict of dicts
# OHitem: name of the item as given in OpenHAB. If none, it won't be registered in OpenHAB
# HIOitem: item instance as per the memory map from Home I/O. If none, it's just an OpenHAB entity
OH2HIO = {
    # Ground Floor
    "GF_LivingRoom_Light": {
        "OHitem": openhab.get_item("GF_LivingRoom_Light"),
        "HIOitem": MemoryMap.Instance.GetBit(0, MemoryType.Output),
        },
    "GF_LivingRoom_Shutter": {
        "OHitem": openhab.get_item("GF_LivingRoom_Shutter"),
        "HIOitem": MemoryMap.Instance.GetBit(1, MemoryType.Output),
        "HIOitem2": MemoryMap.Instance.GetBit(2, MemoryType.Output),
        },
    "GF_LivingRoom_Temperature": {
        "OHitem": openhab.get_item("GF_LivingRoom_Temperature"),
        "HIOitem": MemoryMap.Instance.GetFloat(150, MemoryType.Memory),
        },

    # Garage
    "GG_Garage_Light": {
        "OHitem": openhab.get_item("GG_Garage_Light"),
        "HIOitem": MemoryMap.Instance.GetBit(69, MemoryType.Output),
        },

    # Garden
    "GD_FrontYard_AutoLight": {
        "OHitem": openhab.get_item("GD_FrontYard_AutoLight"),
        "HIOitem": None,
        },
    "GD_FrontYard_LightDimmer": {
        "OHitem": openhab.get_item("GD_FrontYard_LightDimmer"),
        "HIOitem": MemoryMap.Instance.GetFloat(161, MemoryType.Output),
        },

    # Garage Door
    "GD_FrontYard_Shutter": {
        "OHitem": openhab.get_item("GD_FrontYard_Shutter"),
        "HIOitem": MemoryMap.Instance.GetBit(72, MemoryType.Output),
        "HIOitem2": MemoryMap.Instance.GetBit(73, MemoryType.Output),
        },

    # Sensors
    "GD_FrontYard_Garage_Closed": {
        "OHitem": openhab.get_item("GD_FrontYard_Garage_Status"),
        "HIOitem": MemoryMap.Instance.GetBit(101, MemoryType.Input),
        "HIOctype": "NO",
        },
    "GD_FrontYard_Garage_Open": {
        "OHitem": None,
        "HIOitem": MemoryMap.Instance.GetBit(100, MemoryType.Input),
        "HIOctype": "NO",
        },
    "GF_LivingRoom_Shutter_Openness": {
        "OHitem": None,
        "HIOitem": MemoryMap.Instance.GetFloat(3, MemoryType.Input),
        },
    "GD_FrontYard_LightSensorBool": {
        "OHitem": None,
        "HIOitem": MemoryMap.Instance.GetBit(259, MemoryType.Input),
        "HIOctype": "NC",
        },
    "GD_FrontYard_LightSensorFloat": {
        "OHitem": None,
        "HIOitem": MemoryMap.Instance.GetFloat(139, MemoryType.Input),
        },
    # "": {
        # "OHitem": openhab.get_item(""), # or None if not in OpenHAB
        # "HIOitem": MemoryMap.Instance.Get***(*, MemoryType.****), # or None if not in Home I/O
        # "HIOitem2": MemoryMap.Instance.Get***(*, MemoryType.****), # Specify on Rollershutter OH items only
        # "HIOctype": "NO", # "NO" or "NC". Specify only on Bit Input.
        # },
    }

# If Home I/O memory is not updated now, all values will read wrong.
MemoryMap.Instance.Update()

# Debug: print all data
##for key in OH2HIO:
##    print(key)
##    print("OHdata: ", end="")
##    print(OH2HIO[key]["OHitem"])
##    if OH2HIO[key]["OHitem"] is not None:
##        print(OH2HIO[key]["OHitem"].type_,OH2HIO[key]["OHitem"].state,OH2HIO[key]["OHitem"].is_state_null(),OH2HIO[key]["OHitem"].group)
##    print("HIOval: ", end ="")
##    if OH2HIO[key]["HIOitem"] is not None:
##        print(OH2HIO[key]["HIOitem"].Value, end=" ")
##    else:
##        print(None, end ="")
##    if "HIOitem2" in OH2HIO[key]:
##        print(OH2HIO[key]["HIOitem2"].Value, end=" ")
##    if "HIOctype" in OH2HIO[key]:
##        print(OH2HIO[key]["HIOctype"], end = "")
##    print("") # End of line


# Force init all variables in OpenHAB according to current Home I/O data
# Assert status for OpenHAB-only items as 0 or off
for item in OH2HIO.values():
    # print(item)
    if item["OHitem"] is not None: # Update only values meaningful to OpenHAB
    
        # Switches are Bool values in Home I/O. For contact types: -> Contact
        if item["OHitem"].type_ == "Switch":
            if item["HIOitem"] is None: # Assert off
                val = False
            elif item["HIOitem"].Value == False:
                val = False
            elif item["HIOitem"].Value == True:
                val = True
            else:
                raise Exception("Unknown init status for: " + key)

            # Set to the actual value
            if val == True:
                item["OHitem"].on()
            else:
                item["OHitem"].off()

        # Dimmers are Float type in 0-10 range in Home I/O. Cap & map to 0-100.
        elif item["OHitem"].type_ == "Dimmer": 
            if item["HIOitem"] is None: # Assert zero
                val = 0
            else:
                val = item["HIOitem"].Value

            # Cap & map to 0-100
            val = round(10*val)
            if val > 100:
                val = 100
            elif val < 0:
                val = 0
            item["OHitem"].update(val)
            
        # Just make Rollershutters stop, since they are stopped most of the time.
        # Its state is not meaningful anyways until we start control.
        elif item["OHitem"].type_ == "Rollershutter":
            item["OHitem"].stop()

        # Contact items are Bit with a contact.
        elif item["OHitem"].type_ == "Contact":
            if "HIOctype" not in item: #If contact type unavailable assert NO
                item["HIOctype"] = "NO"
                print("Item", item, "is a Contact and has no contact type. Assuming NO...")

            if item["HIOitem"] is None: # Assert open in any case
                val = False
            elif ((item["HIOitem"].Value == True and item["HIOctype"] == "NO") or
                  (item["HIOitem"].Value == False and item["HIOctype"] == "NC")):
                val = True
            else:
                val = False

            if val == True:
                item["OHitem"].closed()
            else:
                item["OHitem"].open()

        # Number items are any type of numeric value. Round to 1 decimal.
        # This generic process does not convert K to C (since we don't know yet what is a temperature and what is not)
        elif item["OHitem"].type_ == "Number":
            if item["HIOitem"] is None: # Assert zero
                val = 0
            else:
                val = item["HIOitem"].Value

            val = round(val,1)
            item["OHitem"].update(val)
            
        elif item["OHitem"].type_ == "DateTime":
            raise Exception("Current support for DateTime items is not available. OH2HIO key: " + key)
        else:
            # Home I/O does not use Color items. 
            # Image, Location, Player and String item have no support by python-openhab library yet.
            raise Exception("Unknown or unsupported item type (" + item.type_ + ") for OH2HIO key: " + key)

# Start all interesting things here
print("Process working. Hit any key or Ctrl-C to exit.")

# kbhit works only in console mode, but closing it with Ctrl+C does no harm
while not kbhit(): 
    # Now we need to know which specific items we are applying control to.

    # Living Room light control
    if OH2HIO["GF_LivingRoom_Light"]["OHitem"].state == None:
        pass
    elif OH2HIO["GF_LivingRoom_Light"]["OHitem"].state == "ON":
        OH2HIO["GF_LivingRoom_Light"]["HIOitem"].Value = True
    else:
        OH2HIO["GF_LivingRoom_Light"]["HIOitem"].Value = False

    # Garage light control
    if OH2HIO["GG_Garage_Light"]["OHitem"].state == None:
        pass
    elif OH2HIO["GG_Garage_Light"]["OHitem"].state == "ON":
        OH2HIO["GG_Garage_Light"]["HIOitem"].Value = True
    else:
        OH2HIO["GG_Garage_Light"]["HIOitem"].Value = False

    # Manual/Auto garden dimmer
    # Remember in OpenHAB they're in range 0-100. Home I/O expects 0-10
    if OH2HIO["GD_FrontYard_AutoLight"]["OHitem"].state == "OFF": # Manual mode
        if OH2HIO["GD_FrontYard_LightDimmer"]["OHitem"].state == "ON":
            val = 100
        elif OH2HIO["GD_FrontYard_LightDimmer"]["OHitem"].state == "OFF":
            val = 0
        else:
            val = OH2HIO["GD_FrontYard_LightDimmer"]["OHitem"].state

    elif OH2HIO["GD_FrontYard_AutoLight"]["OHitem"].state == "ON": # Auto mode
        # ON at 100-(33.33*Brightness sensor reading) if brightness sensor is on
        if OH2HIO["GD_FrontYard_LightSensorBool"]["HIOitem"].Value == True:
            val = 100 - (33.33*OH2HIO["GD_FrontYard_LightSensorFloat"]["HIOitem"].Value)
        else:
            val = 0

        # Cap & post value back to OpenHAB so it notices too
        if val > 100:
            val = 100
        elif val < 0:
            val = 0
        OH2HIO["GD_FrontYard_LightDimmer"]["OHitem"].update(round(val))

    OH2HIO["GD_FrontYard_LightDimmer"]["HIOitem"].Value = val/10

    # Rollershutter controls
    # Careful, in OpenHAB 100 means down and 0 means up; in Home I/O 0 is down and 10 is up!
    # Sadly, up, down and stop are not statuses so control can't be any finer than this.
    # These control methods execute slowly but steadily

    # Living Room Rollershutter
    # Has an openness sensor from Home I/O so it can be controlled better
    # Do nothing if shutter is in unknown state
    if OH2HIO["GF_LivingRoom_Shutter"]["OHitem"].state != None:
        # Convert to the same unit of measurement
        OHval = OH2HIO["GF_LivingRoom_Shutter"]["OHitem"].state
        HIOval = OH2HIO["GF_LivingRoom_Shutter_Openness"]["HIOitem"].Value

        HIOval = 10*(10-HIOval) # Now HIOval represents closedness %
        # print(HIOval, end=" ")

        # Reduce sensitivity and allow up to 5% error (1 in 20)
        OHval = round(OHval/5)
        HIOval = round(HIOval/5)
        # print(OHval,HIOval)

        if OHval > HIOval: # Go down
            OH2HIO["GF_LivingRoom_Shutter"]["HIOitem2"].Value = True
            OH2HIO["GF_LivingRoom_Shutter"]["HIOitem"].Value = False
        elif OHval < HIOval: # Go up
            OH2HIO["GF_LivingRoom_Shutter"]["HIOitem2"].Value = False
            OH2HIO["GF_LivingRoom_Shutter"]["HIOitem"].Value = True
        elif OHval == HIOval: # Stop
            OH2HIO["GF_LivingRoom_Shutter"]["HIOitem2"].Value = False
            OH2HIO["GF_LivingRoom_Shutter"]["HIOitem"].Value = False

    # Garage Door Rollershutter
    # No openness sensor, so only control possible is via the limit switch sensors 
    if OH2HIO["GD_FrontYard_Shutter"]["OHitem"].state != None:
        downSensor = OH2HIO["GD_FrontYard_Garage_Closed"]["HIOitem"].Value
        upSensor = OH2HIO["GD_FrontYard_Garage_Open"]["HIOitem"].Value

        #print(OH2HIO["GD_FrontYard_Shutter"]["OHitem"].state,downSensor,upSensor)

        # Both sensors are NO so it is not necessary to switch their readings
        if OH2HIO["GD_FrontYard_Shutter"]["OHitem"].state == 100 and downSensor == False:
            # Go down
            OH2HIO["GD_FrontYard_Shutter"]["HIOitem2"].Value = True
            OH2HIO["GD_FrontYard_Shutter"]["HIOitem"].Value = False
        elif OH2HIO["GD_FrontYard_Shutter"]["OHitem"].state == 0 and upSensor == False:
            # Go up
            OH2HIO["GD_FrontYard_Shutter"]["HIOitem2"].Value = False
            OH2HIO["GD_FrontYard_Shutter"]["HIOitem"].Value = True
        elif ((OH2HIO["GD_FrontYard_Shutter"]["OHitem"].state == 100 and downSensor == True) or
              (OH2HIO["GD_FrontYard_Shutter"]["OHitem"].state == 0 and upSensor == True)):
            # Stop
            OH2HIO["GD_FrontYard_Shutter"]["HIOitem2"].Value = False
            OH2HIO["GD_FrontYard_Shutter"]["HIOitem"].Value = False

    # Post Garage Door status to OpenHAB
    if OH2HIO["GD_FrontYard_Garage_Closed"]["HIOitem"].Value == True:
        OH2HIO["GD_FrontYard_Garage_Closed"]["OHitem"].closed()
    else:
        OH2HIO["GD_FrontYard_Garage_Closed"]["OHitem"].open()

    # Temperature Sensors
    # Round to 1 decimal place
    OH2HIO["GF_LivingRoom_Temperature"]["OHitem"].update(round(OH2HIO["GF_LivingRoom_Temperature"]["HIOitem"].Value-273.15,1))

    # Calling the Update method will update all data to the memory map.
    MemoryMap.Instance.Update()
    
    # Home I/O's FPS rate is 60 fps, here we refresh at just 10 FPS
    # This is good if fast-forwarding will not be used
    time.sleep(0.1)

# When we no longer need the MemoryMap we should call the Dispose method to release all the allocated resources.
MemoryMap.Instance.Dispose()

print("Closing...")
