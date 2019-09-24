#!/usr/bin/env python3

import time
import importlib
import threading
import queue
import os
import argparse
import logging
import configparser
import socket


parser = argparse.ArgumentParser()
parser.add_argument('-c', '--configfile', action='store', type=str, required=False, dest='configfile', help='Give a path (absolute or relative) to a config file')
parser.add_argument('-l', '--logfile', action='store', type=str, required=False, dest='logfile', help='Give a path (absolute or relative) to a config file')
args = parser.parse_args()

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

class Config:
    def __init__(self, path):
        self.path = path

    def checkPath(self):
        if os.path.isdir(self.path):
            logging.debug('Config file is a path, not a file. Will create file named config.dat in given path')
            self.path = os.path.join(self.path, 'config.dat')

        if not os.access(self.path, os.R_OK):
            logging.error('Given config file: {} cannot be read.'.format(self.path))
            self.path = os.path.join('.', 'config.dat')

        if not os.access(self.path, os.W_OK):
            logging.error('Config file can not be written.')
            self.path = os.path.join('.', 'config.dat')

    def createConfig(self):
        config = configparser.ConfigParser()
        self.path = 'test.dat'
        if not os.path.exists(self.path):
            open(self.path, 'a').close()
            

        if os.path.getsize(self.path) < 10000:
            logging.warning('Config file is too small. We will set it up')
            
            with open(self.path, 'w') as f:
                config.add_section('IRCSERVER')
                host = self.getServerAddress()
                if host == False:
                    raise Exception('Aborted by user')
                else:
                    config.set('IRCSERVER', 'server', host)

                port = input('Port (SSL is usually 6697: ')
                config.set('IRCSERVER', 'port', port)
                
                config.add_section('IRCUSER')
                config.set('IRCUSER', 'nick', input('Bot\'s nickname: '))
                config.set('IRCUSER', 'password', input('Bot\'s password (Warning: stored in clear text in config file!): '))
                
                config.add_section('IRCADMIN')
                adminlist = list()
                while True:
                    adminnick = input('Nickname of administrator, c to cancel: ')
                    if adminnick == 'c':
                        if len(adminlist) < 1:
                            print('You have to insert at least one administrator')
                            continue
                        else:
                            break
                    if adminnick != '':
                        if adminnick in adminlist:
                            print('You don\'t need to insert that admin twice')
                        else:
                            adminlist.append(adminnick)
                config.set('IRCADMIN', 'administrators', ';'.join(adminlist))
                
                config.write(f)

    def getServerAddress(self):
        while True:
            try:
                host = input('Hostname for IRC Server: ')
                if host == 'c':
                    return False
                socket.gethostbyname(host)
                return host
            except:
                continue
                

# if there isn't any configuration file in the arguments list, give a default path
if not args.configfile:
    logging.debug('No logfile given per argument. Will use path {}.'.format(os.path.join(os.getcwd(), 'config.dat')))
    configfile = os.path.join(os.getcwd(), 'config.dat')




    

def main():
    c = Config(configfile)
    c.createConfig()
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
