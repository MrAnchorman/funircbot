import os
import sys
import socket
import ssl
import logging
import importlib
from datetime import datetime
from getpass import getpass
import queue

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
        # getting variables from config.py in same directory
        # if config.py does not exist, ask the user
        if os.path.isfile(os.path.join('.', 'config.py')):
            config = importlib.import_module('config')
            self.nick = config.nick
            self.password = config.password
            self.channel = config.channel
        else:
            self.nick = input('Nickname of the Bot: ')
            self.channel = input('Channels to join: ')
            self.password = getpass('Bot password for nickserv: ')
        self.encoding = 'utf-8'
        # self.plugins is gonna save loaded plugins (see self.loadIRCPlugins)
        self.plugins = dict()
        self.queueToIRC = None
        self.queueFromIRC = None

    def connect(self):
        # create a socket and connect to the server
        logging.debug("Creating socket")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        logging.debug("Connecting to {server} on port {port}".format(server =
                                                                    self.ircserver,
                                                                    port =
                                                                    self.ircport))

        logging.debug("Wrapping socket to SSL")
        # setting up a context to verify the hostname 
        context = ssl.SSLContext()
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = True
        context.load_default_certs()
        self.ircsock = context.wrap_socket(s, server_hostname=self.ircserver)

        # connect
        self.ircsock.connect((self.ircserver, self.ircport))

    def identifyServer(self):
        # after connecting to the server we need to send the following string
        # if we don't do this, the server won't let us connect and instead send a message like
        # 'not authorized'
        logging.debug('Sending User and Nick Information to the Server.')
        self.sendServerMessage("USER " + self.nick + " " + self.nick + " " + \
                               self.nick + " :Just testing my skills to write a bot")
        self.sendServerMessage("NICK " + self.nick)

    def identifyUser(self):
        # if nickserv is asking for identification, send the string like /msg nickserv identify <password>
        '''
        This nickname is registered. Please choose a different nickname, or identify via /msg NickServ identify <password>
        '''
        logging.debug('Identifying myself as ' + self.nick)
        self.sendServerMessage("PRIVMSG" + " :NICKSERV identify " + self.password + "\n")

    def joinChannel(self, channelname = None):
        if channelname is None:
            logging.debug('Channelname is None, i\'ll make it the default channel')
            channelname = self.channel
        if channelname[:1] != '#':
            channelname = '#' + channelname
        self.sendServerMessage("JOIN " + channelname)
        logging.debug('Joining channel ' + channelname)
        ircmsg = ""
        while ircmsg.find('End of /NAMES list.') != -1:
            ircmsg = self.receiveMessage()
            print(ircmsg)
            if ircmsg.find('This nickname is registered. Please choose a different nickname, or identify via /msg NickServ identify <password>') != -1:
                self.identifyUser()
        logging.debug('Joined channel ' + channelname)

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
                self.sendChannelMessage('I have a message in myqueue: ' + self.queueToIRC.get(False, 5))
                self.queueToIRC.task_done()
            except queue.Empty as q:
                pass
            self.queueFromIRC.put(message['sender'] + ' schrieb: ' + message['messageText'])
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

    def startup(self, queueToIRC, queueFromIRC):
        self.queueToIRC = queueToIRC
        self.queueFromIRC = queueFromIRC
        self.connect()
        self.identifyServer()
        self.joinChannel()
        self.run()
        return True
