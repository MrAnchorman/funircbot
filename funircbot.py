#!/usr/bin/env python3

# imports
import time
import importlib
import threading
import queue
import os
import sys
import argparse
import logging
import socket
from Configuration.configuration import Config

# start the real program
def main():
    confpath = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])))
    conf = Config(confpath)
    conf.createConfig()
    plugins = dict()
    plugins['irc'] = importlib.import_module('IRC')
    irc = plugins['irc'].IRC()
    queueToIRC = queue.Queue()
    queueFromIRC = queue.Queue()
    queueToIRC.put('Testing the shit outta queues!')
    #t = threading.Thread(target=irc.startup, args=[queueToIRC, queueFromIRC]).start()
    queueFromIRC.put('echo:test')
    que = queueFromIRC.get()
    #do, tuple(parameters) = que.split(':')

    queueFromIRC.task_done()

### The Arguments are scripted, but will not be used atm. 
logging.debug('This is scripted, but will not be used atm. First I need to understand where I should store a given configfile path.')
parser = argparse.ArgumentParser()
parser.add_argument('-c', '--configfile', action='store', type=str, required=False, dest='configfile', help='Give a path (absolute or relative) to a config file')
parser.add_argument('-l', '--logfile', action='store', type=str, required=False, dest='logfile', help='Give a path (absolute or relative) to a config file')
args = parser.parse_args()


### Setup the program, at the end: if script was executed, call main function from top of script


# Ready up the Logging
if not args.logfile:
    logfile = './logs/gitbot.log'
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

if __name__ == '__main__':
    main()
