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
howOften = 1
pollerTimeout = 10
# WeMo light switch to listen for/set
switchToListenFor = 'LivingRoomPhysicalLightSwitch'
# End of user modifyable bits

# Appname for Hue
appname = 'WeMoHueControl'

# Logging setup
logging.basicConfig(
    format='[%(levelname)s] %(asctime)s (%(threadName)-10s) %(message)s')
logger = logging.getLogger('wemo_hue_control')
logger.setLevel(logging.INFO)

logger.info('Starting')

# Initiate WeMo environment
wemoEnv = Environment()
logger.debug('Starting WeMo environment')
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

# Threading event used to trigger exit from the Hue thread
run_event = threading.Event()
run_event.set()

# Hue watcher thread polls the Hue hub for changes
# If it finds a change, it will set the WeMo switch appropriately
class hueWatcherThread(threading.Thread):
    def run(self):
        logger.debug('Starting Hue polling')
        while run_event.is_set():
            onBeforePoll = myHue.getLight(whichLights[0])['json']['state']['on']
            logger.debug('Current Hue on/off state is: %s', onBeforePoll)
            logger.debug('Watching for it to change')
            # The poll times out and loops after 10 seconds so that the main thread
            # can quit this for KeyboardInterrupt etc without waiting forever
            try:
                polling.poll(
                    lambda: myHue.getLight(whichLights[0])['json']['state']['on'] != onBeforePoll,
                    step = howOften,
                    timeout = pollerTimeout
                )
            except polling.TimeoutException, te:
                logger.debug('Hue poller timed out')
            onAfterPoll = myHue.getLight(whichLights[0])['json']['state']['on']
            if onAfterPoll != onBeforePoll:
                logger.debug('Lamps are now %s', ('Off', 'On')[onAfterPoll])
                logger.info('Hue event detected - Updating WeMo')
                # Now send the on/off to the WeMo switch
                switch.on() if onAfterPoll else switch.off()
                logger.debug('Turning on switch') if onAfterPoll else logger.debug('Turning off switch')

# Handle the WeMo stuff in the main thread because it needs to receive signals
# Create a statechange receiver
@receiver(statechange)
def switch_toggle(sender, **kwargs):
    logger.info('WeMo event detected - Updating Hue')
    logger.debug('Sender: %s, Args: %s', sender, kwargs['state'])
    if sender == switch:
        # Now actually set all the lights
        for light in whichLights:
	    if kwargs['state'] == 0:
	        myHue.turnOff(light)
            else:
                myHue.turnOn(light)

# Kick off the Hue thread
logger.info('Starting the Hue watcher thread')
hueWatcherThread().start()

# Start the WeMo event loop
logger.info('Entering WeMo event loop')
wemoEnv.wait()
logger.debug('Interrupted, bailing...')
logger.debug('You might need to wait up to %d seconds for Hue thread to die')
run_event.clear()
logger.info('Quitting')
exit(0)
