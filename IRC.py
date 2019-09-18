import os
import sys
import socket
import ssl
import logging
import importlib
from datetime import datetime
import config

# Ready up the Logging
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

class IRC:
    def __init__(self):
        # Set some variables which are needed to connect
        self.ircserver = 'chat.freenode.net'
        self.ircport = 6697
        self.nick = config.nick
        self.password = config.password
        self.channel = config.channel
        self.encoding = 'utf-8'
        self.plugins = dict()

    def connect(self):
        # create a socket and connect to the server
        logging.debug("Creating socket")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        logging.debug("Connecting to {server} on port {port}".format(server =
                                                                    self.ircserver,
                                                                    port =
                                                                    self.ircport))

        logging.debug("Wrapping socket to SSL")
        context = ssl.SSLContext()
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = True
        context.load_default_certs()
        self.ircsock = context.wrap_socket(s, server_hostname='chat.freenode.net')

        self.ircsock.connect((self.ircserver, self.ircport))

    def identifyServer(self):
        '''
        This nickname is registered. Please choose a different nickname, or identify via /msg NickServ identify <password>
        '''
        self.sendServerMessage("USER " + self.nick + " " + self.nick + " " + \
                               self.nick + " :Just testing my skills to write a bot")
        self.sendServerMessage("NICK " + self.nick)

    def identifyUser(self):
        print('Identifying myself as ' + self.nick)
        self.sendServerMessage("PRIVMSG" + " :NICKSERV identify " + self.password + "\n")

    def joinChannel(self, channelname = None):
        if channelname is None:
            channelname = self.channel
        if channelname[:1] != '#':
            channelname = '#' + channelname
        self.sendServerMessage("JOIN " + channelname)
        ircmsg = ""
        while ircmsg.find('End of /NAMES list.') == -1:
            ircmsg = self.receiveMessage()
            print(ircmsg)
            if ircmsg.find('This nickname is registered. Please choose a different nickname, or identify via /msg NickServ identify <password>') != -1:
                self.identifyUser()

    def sendServerMessage(self, message):
        if isinstance(message, str):
            totalsent = 0
            while totalsent < len(message):
                sent = self.ircsock.send(bytes(message[totalsent:] + "\n", self.encoding))
                if sent == 0:
                    return False
                totalsent = totalsent + sent
            return True
        return False

    def sendChannelMessage(self, message, target = None):
        if target == None:
            target = self.channel
        try:
            self.sendServerMessage("PRIVMSG " + target + " :" + message)
        except Exception as e:
            return False
        return True

    def receiveMessage(self):
        message = self.ircsock.recv(4096).decode(self.encoding)
        message = message.strip('\n\r')
        return message

    def ping(self, message):
        ret = message.split()[1]
        ret = "PONG " + ret
        self.sendServerMessage(ret)
        print("Pong!")

    def disconnect(self):
        self.sendServerMessage("QUIT :My Master told me to leave.")
        m = self.receiveMessage()
        logging.debug('Got the Disconnectmessage. ' + m.split(':')[1])
        '''
        I was told to go. I go
        :MrAnchorman!~MrAnchorm@pgno.dvag.com QUIT :Client Quit

        ERROR :Closing Link: pgno.dvag.com (Client Quit)
        '''
        logging.debug('Closed connection')
        return True

    def run(self):
        logging.debug('Running...')
        while True:
            ircmsg = self.receiveMessage()
            print(ircmsg)
            if ircmsg.startswith('PING :'):
                print('Ping? ', end='')
                self.ping(ircmsg)
            elif ircmsg.find('peer') != -1:
                print('PEER FOUND!!!: ' + ircmsg)
                logging.warning(ircmsg)
            else:
                messageProperties = self.getMessageProperties(ircmsg)
                if messageProperties['messageText'] == 'byebot' and messageProperties['sender'] == 'break3r':
                    print('I was told to go. I go')
                    self.disconnect()
                    break
                if ircmsg.find('peer') != -1:
                    print('PEER FOUND!!!: ' + ircmsg)
                    logging.warning(ircmsg)
                self.processMessage(messageProperties)
        logging.debug('Left run()-Method.')
        return True

    def getMessageProperties(self, message):
        '''
        :break3r!~Nameless@unaffiliated/break3r PRIVMSG ##gitbottest :Testnachricht
        Ping? Pong!
        :break3r!~Nameless@unaffiliated/break3r PRIVMSG MrAnchorman :Query MSG
        Ping? Pong!
        :break3r!~Nameless@unaffiliated/break3r NOTICE MrAnchorman :Notice
        Ping? Pong!
        :break3r!~Nameless@unaffiliated/break3r PRIVMSG MrAnchorman :TEST
        Ping? Pong!
        :break3r!~Nameless@unaffiliated/break3r PRIVMSG MrAnchorman :DCC CHAT chat 171786923 52684
        Ping? Pong!
        '''
        messageProperties = dict()
        msgDict = message.split()
        messageProperties['sender'] = msgDict[0].split('!', 1)[0][1:]
        messageProperties['type'] = msgDict[1]
        messageProperties['channel'] = msgDict[2] if msgDict[2] != self.nick else messageProperties['sender']
        messageProperties['messageText'] = ''
        s = messageProperties['channel'] if messageProperties['channel'][:1] == '#' else self.nick
        if message.find(s + ' :') != -1:    
            messageProperties['messageText'] = message.split(s + ' :')[1]
        return messageProperties

    def processMessage(self, message):
        if message['messageText'][:1] == ':' and message['messageText'][1:2] != ' ' and message['messageText'][1:2] != ':':
            command = message['messageText'].split()[0][1:]
            try:
                self.plugins[command] = self.loadIRCPlugin(command)
                if self.plugins[command] == False:
                    self.plugins.pop(command)
                else:
                    output = self.plugins[command].run(message)
                if isinstance(output, str):
                    self.sendChannelMessage(output, message['channel'])
            except Exception as e:
                print(e.args)
            

    def loadIRCPlugin(self, command):
        print('I should load a plugin. Command is: ' + command)
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

def main():
	i = IRC()
	i.connect()
	i.identifyServer()
	i.joinChannel()
	i.run()
	
if __name__ == '__main__':
	main()
