import os
import sys
import logging
import socket
from configparser import ConfigParser

class UserAbort(Exception):
    def __init__(self, msg = None):
        super().__init__()
        if msg != None:
            print(msg)


class Config:
    def __init__(self, path):
        self.path = None
        if os.path.isdir(path):
            self.path = os.path.join(path, 'config.ini')
        else:
            self.path = path

    def createConfig(self):

        config = ConfigParser(allow_no_value=True)

        while True:
            if os.path.exists(self.path):
                config.read_file(open(self.path))
                break
            else:
                print('Cannot open config file. Please configure another path to configuration file')
                self.path = input('Path to config file: ')
                if self.path == 'c':
                    raise UserAbort('User aborted the configuration')

        if not config.has_section('IRCSERVER'): config.add_section('IRCSERVER')

        if not config.has_option('IRCSERVER', 'server') or \
                                     config.get('IRCSERVER', 'server').strip ==  \
                                     '':
            try:
                host = self.getServerAddress()
                config.set('IRCSERVER', 'server', host)
            except UserAbort as e: print(e)
            sys.exit(127)

        if not config.has_option('IRCSERVER', 'port'):
            try:
                port = self.getServerPort()
            except UserAbort as e:
                print(e)
                sys.exit(127)
            config.set('IRCSERVER', 'port', str(port))

        if not config.has_section('IRCUSER'):
            config.add_section('IRCUSER')

        if not config.has_option('IRCUSER', 'nick'):
            nick = self.getBotNickname()
            config.set('IRCUSER', 'nick', nick)

        if not config.has_option('IRCUSER', 'password'):
            botpassword = self.getBotPassword()
            config.set('IRCUSER', 'password', botpassword)

        if not config.has_section('IRCADMIN'):
            config.add_section('IRCADMIN')

        adminlist = self.getBotAdministrators()
        config.set('IRCADMIN', 'administrators', adminlist)

        try:
            with open(self.path, 'w') as f:
                config.write(f)
        except Exception as e:
            print(e.args)
            print(e.__class__.__name__)
        else:
            f.close()

    def getServerAddress(self):
        while True:
                host = input('Hostname for IRC Server: ')
                if host == '':
                    return 'chat.freenode.net'
                if host == 'c':
                    raise UserAbort('User aborted')
                try:
                    socket.gethostbyname(host)
                    return host
                except socket.gaierror:
                    print('Host cannot be reached. I will ask for a Server until it can be reached.')

    def getServerPort(self):
        while True:
            port = input('Port (SSL is usually 6697: ')
            if port == '':
                return 6697
            if port == 'c':
               raise UserAbort('User aborted')
            port = int(port)
            if port < 1024 or port > 65535:
                print('This is not an acceptable port. Get the portnumber from the homepage of the network you want to connect to (usually this is 6697)')
                logging.error('Invalid user input: port was smaller or bigger than the allowed ports: {}'.format(port))
            else:
                return port

    def getBotNickname(self):
        nick = input('Bot\'s nickname: ')
        return nick

    def getBotPassword(self):
        pw = input('Bot\'s password: ')
        return pw


    def getBotAdministrators(self):
        adminlist = list()
        while True:
                adminnick = input('Nickname of administrator, c to finish list: ')
                if adminnick == 'c':
                    if len(adminlist) < 1:
                        print('You have to insert at least one administrator')
                        continue
                    else:
                        break
                if adminnick != '':
                    if adminnick in adminlist:
                        print('You don\'t need to insert {} twice'.format(adminnick))
                    else:
                        adminlist.append(adminnick)

        return ';'.join(adminlist)
