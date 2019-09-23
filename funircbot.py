#!/usr/bin/env python3

import time
import importlib
import threading
import queue
import os
import argparse
import logging


parser = argparse.ArgumentParser()
parser.add_argument('-c', '--configfile', action='store', type=str, required=False, dest='configfile', help='Give a path (absolute or relative) to a config file')
parser.add_argument('-l', '--logfile', action='store', type=str, required=False, dest='logfile', help='Give a path (absolute or relative) to a config file')
args = parser.parse_args()

# if there isn't any configuration file in the arguments list, give a default path
if not args.configfile:
    configfile = os.path.join('.', 'config.dat')

if os.path.isdir(configfile):
    configfile = os.path.join(configfile, 'config.dat')

if 

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

def main():
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

if __name__ == '__main__':
    main()
