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

    def __init__(self):
        self.plugins = dict()
        self.plugins['irc'] = importlib.import_module('IRC')
        c = Config('.')
        self.config = c.createConfig()
        self.irc = self.plugins['irc'].IRC()
        self.IRCQueue = queue.Queue()
        self.mainQueue = queue.Queue()

    # start the real program
    def start(self):
        self.irc.setup(self.config)
        t = threading.Thread(target=self.irc.startup, args=[self.IRCQueue, self.mainQueue])
        t.start()
        while True:
            q = self.mainQueue.get()
            if q == 'quit':
                print('Got quit in my main queue.')
                self.irc.disconnect()
                t.join()
                break
        return 0

def main():
    bot = funircbot()
    bot.start()

if __name__ == '__main__':
    main()
