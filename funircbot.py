#!/usr/bin/env python3

### funircbot.py

# imports
import importlib
import threading
import queue
import os
import sys
import argparse
import logging
import socket
from Configuration.configuration import Config

# Ready up the Logging
if not args.logfile:
    logfile = './logs/funircbot.log'
if (not os.path.exists(logfile)) or (not os.access(logfile, os.W_OK)):
    if not os.path.isdir('./logs'):
        os.makedirs('./logs')
        open(logfile, 'a+').close()

logging.basicConfig(
filename=logfile,
level = logging.DEBUG,
style = '{',
format = '{asctime} [{levelname:7}] {message}',
datefmt = '%d.%m.%Y %H:%M:%S')

class funircbot():

    def __init__():
        self.plugins = dict()
        self.plugins['irc'] = importlib.import_module('IRC')
        config = Config('.')
        c = config.createConfig()
        self.irc = plugins['irc'].IRC()
        self.irc.setup(c)
        self.queueToIRC = queue.Queue()
        self.mainQueue = queue.Queue()

    # start the real program
    def start():
        t = threading.Thread(target=self.irc.startup, args=[self.queueToIRC, self.mainQueue])
        t.start()
        while True:
            q = self.mainQueue.get()
            if q == 'quit':
                print('Got quit in my main queue.')
                self.irc.disconnect()
                t.join()
                break
        return 0

    def processCommand(self, message):
        message['content'] = message['content'][1:]
        command = message['content'].split()[0]
        try:
            self.plugins[command] = self.loadIRCPlugin(command)
            if self.plugins[command] == False:
                self.plugins.pop(command)
            else:
                output = self.plugins[command].run(message, self.ircsock)
            if isinstance(output, str):
                self.sendChannelMessage(output, message['channel'])
        except Exception as e:
            print(e.__class__.__name__)
            print(e.args)
        return 0

    def loadIRCPlugin(self, command):
        # if a command is given (messageText has : as first char)
        # let's see if there's a plugin in the plugins folder
        # if there's such a file, load (or reload) the plugin
        # and call it
        commandFile = command + '.py'
        if command in self.plugins.keys():
            if commandFile in os.listdir(os.path.join('.', 'plugins')):
                logging.debug('Plugin ' + command + ' reloaded.')
                return importlib.reload(self.plugins[command])
            else:
                return False
        elif commandFile in os.listdir(os.path.join('.', 'plugins')):
            logging.debug('Plugin ' + command + ' loaded.')
            return importlib.import_module('.' + command, 'plugins')
        else:
             logging.warning('A plugin called ' + command + ' could not be found.')
             raise Exception('Cannot load module ' + command + '.')
