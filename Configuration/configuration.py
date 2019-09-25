import os
import sys
import logging
import configparser


class Config:
    def __init__(self, path):
        self.path = path


    def configRun(self):

        config = configparser.ConfigParser(allow_no_value=True)

        try:
            with open(self.path, 'a+') as f:
        except Exception as e:
            print('Cannot open config file. Please configure another path to configuration file')

            if not config.has_section('IRCSERVER'):
                config.add_section('IRCSERVER')
                
            if not config.has_option('IRCSERVER', 'server'):
                host = self.getServerAddress()
                if host == False:
                    raise Exception('Aborted by user')
                else:
                    config.set('IRCSERVER', 'server', host)
                    
            if not config.has_option('IRCSERVER', 'port'):
                port = self.getPort()
                if port == False:
                    raise Exception('Aborted by user')
                config.set('IRCSERVER', 'port', port)

            if not config.has_section('IRCUSER'):
                config.add_section('IRCUSER')

            if not config.has_option('IRCUSER', 'nick'):
                config.set('IRCUSER', 'nick', input('Bot\'s nickname: '))

            if not config.has_option('IRCUSER', 'password'):
                config.set('IRCUSER', 'password', input('Bot\'s password (Warning: stored in clear text in config file!): '))

            if not config.has_section('IRCADMIN'):
                config.add_section('IRCADMIN')

            adminlist = getBotAdministrators()
            config.set('IRCADMIN', 'administrators', adminlist)
            
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
                print('Host cannot be reached. I will ask for a Server until it can be reached.')
                continue

    def getServerPort(self):
        while True:
            port = input('Port (SSL is usually 6697: ')
            if port == 'c':
                return False
            if port < 1024 or port > 65535:
                print('This is not an acceptable port. Get the portnumber from the homepage of the network you want to connect to (usually this is 6697)')
                debug.error('Invalid user input: port was smaller or bigger than the allowed ports: {}'.format(port))
            else:
                return port

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


def main():
    c = Config('test.txt')
    c.checkPath()
    c.createConfig()

if __name__ == '__main__':
    main()
