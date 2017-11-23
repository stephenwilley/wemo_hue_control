#!/usr/bin/env python

# Imports
import logging
from gevent               import socket
from ouimeaux.environment import Environment
from ouimeaux.signals     import statechange, receiver, devicefound

switchToListenFor = 'KitchenOverheads'

# Logging setup
logging.basicConfig(format='%(asctime)s %(message)s')
logger = logging.getLogger('wemo_watcher')
logger.setLevel(logging.DEBUG)

# Initiate WeMo environment
env = Environment()
logger.debug('Starting environment')
env.start()

# Debug handler for finding devices
@receiver(devicefound)
def handler(sender, **kwargs):
    logger.debug('Found device: %s', sender)

logger.debug('Discovering switches')
env.discover(2)
switch = env.get_switch(switchToListenFor)

# Create a statechange receiver
@receiver(statechange)
def switch_toggle(sender, **kwargs):
    logger.debug('Event detected')
    logger.debug('Sender: %s', sender)
    logger.debug('Args:   %s', kwargs['state'])

# Start the event loop
try:
    logger.debug('Entering event loop')
    env.wait()
except (KeyboardInterrupt, SystemExit):
    logger.debug('Exiting WeMo switch daemon')
    exit(0)
