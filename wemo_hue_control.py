#!/usr/bin/env python

# Imports
import logging, threading

from gevent               import socket
from ouimeaux.environment import Environment
from ouimeaux.signals     import statechange, receiver, devicefound

import pyphue, polling

# Config that should be modified by the user
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
howOften = 3
# WeMo light switch to listen for/set
switchToListenFor = 'KitchenOverheads'
# End of user modifyable bits

# Appname for Hue
appname = 'WeMoHueControl'

# Logging setup
logging.basicConfig(
    format='[%(levelname)s] %(asctime)s (%(threadName)-10s) %(message)s')
logger = logging.getLogger('wemo_hue_control')
logger.setLevel(logging.DEBUG)

# Initiate WeMo environment
wemoEnv = Environment()
logger.debug('Starting environment')
wemoEnv.start()

# Debug handler for finding devices
@receiver(devicefound)
def handler(sender, **kwargs):
    logger.debug('Found device: %s', sender)

logger.debug('Discovering switches')
wemoEnv.discover(2)
try:
    switch = wemoEnv.get_switch(switchToListenFor)
except:
    logger.error('The WeMo switch you specified can\'t be found')
    exit(1)

# Initiate Hue environment
myHue = pyphue.PyPHue(user = hueUser, AppName = appname, wizard = False)

# Report back some debug info for Hue
logger.debug('Hue Bridge IP: %s', myHue.ip)
logger.debug('Hue Lights:    %s', myHue.lightIDs)

# Hue watcher thread polls the Hue hub for changes
# If it finds a change, it will set the WeMo switch appropriately
class hueWatcherThread(threading.Thread):
    def run(self):
        global myHue, switch

        logger.debug('Starting Hue polling')
        while True:
            currentOnOff = myHue.getLight(whichLights[0])['json']['state']['on']
            logger.debug('Current Hue on/off state is: %s', currentOnOff)
            logger.debug('Watching for it to change')

            polling.poll(
                lambda: myHue.getLight(whichLights[0])['json']['state']['on'] != currentOnOff,
                step = howOften,
                poll_forever=True
            )
            logger.debug('State changed - Will update WeMo')
            currentOnOff = myHue.getLight(whichLights[0])['json']['state']['on']
            logger.debug('Lamps are now %s', ('Off', 'On')[currentOnOff])

            # Now send the on/off to the WeMo switch
            switch.on() if currentOnOff else switch.off()
            logger.debug('Turning on switch') if currentOnOff else logger.debug('Turning off switch')

# Handle the WeMo stuff in the main thread because it needs to receive signals
# Create a statechange receiver
@receiver(statechange)
def switch_toggle(sender, **kwargs):
    logger.debug('Event detected - Will update Hue')
    logger.debug('Sender: %s, Args: %s', sender, kwargs['state'])
    # Now actually set all the lights
    for light in whichLights:
	if kwargs['state'] == 0:
	    myHue.turnOff(light)
	else:
	    myHue.turnOn(light)

# Kick off the Hue thread
hueWatcherThread().start()

# Start the WeMo event loop
logger.debug('Entering WeMo event loop')
wemoEnv.wait()
