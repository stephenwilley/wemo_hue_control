#!/usr/bin/env python

# Imports
import logging
import pyphue
import polling

# Bits to modify by end user
# Enter hub user ID here after doing the join described in the README
hueUser = 'zF-NXt7ZRDYBYWUh1KizQjHv9xDYXNJ5nLEkL7l8'
# List of lights to associate with the WeMo switch
whichLights = ['1', '2', '4', '5']
# How bright to make them when you turn it on
brightness = 254
# How often to check in seconds.  I don't really care about the switch being
# updated super quickly if I've turned the Hue lights on/off some other way
# and figured pinging the hub less often is good, but I dunno if this really
# matters.  If you had both normal and Hue lights on the same switch you'd
# probably want to set this lower
howOften = 5
# End of user modifyable bits

# Appname for Hue
appname = 'WeMoHueControl'

# Logging setup
logging.basicConfig(format='%(asctime)s %(message)s')
logger = logging.getLogger('hue_watcher')
logger.setLevel(logging.DEBUG)

# Initiate Hue environment
myHue = pyphue.PyPHue(user = hueUser, AppName = appname, wizard = False)

# Report back some debug info
logger.debug('Hue Bridge IP: %s', myHue.ip)
logger.debug('Hue Lights:    %s', myHue.lightIDs)

# Start an infinite loop that will poll the hub for state change of the
# first lamp in the list above
try:
    while True:
        currentOnOff = myHue.getLight(whichLights[0])['json']['state']['on']
        logger.debug('Current Hue on state is: %s', currentOnOff)
        logger.debug('Watching for it to change')
        polling.poll(
            lambda: myHue.getLight(whichLights[0])['json']['state']['on'] != currentOnOff,
            step = howOften,
            poll_forever=True
        )
        logger.debug('State changed')
except KeyboardInterrupt, SystemExit:
    logger.debug('Exiting Hue daemon')
    exit(0)
