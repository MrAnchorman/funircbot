import os
import sys
import socket
import ssl
import logging
import importlib
from datetime import datetime
from getpass import getpass
import queue


class IRC:
    def __init__(self):
        self.plugins = dict()
        self.queueToIRC = None
        self.queueFromIRC = None

    def setup(self, config):
        self.ircserver = config.get('IRCSERVER', 'server')
        self.ircport = config.getint('IRCSERVER', 'port')
        self.nick = config.get('IRCUSER', 'nick')
        self.password = config.get('IRCUSER', 'password')
        self.administrators = config.get('IRCADMIN', 'administrators').split(';')
        return 0

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
        # Join channel. If channelname is not given, the bot will join the channel which is given per object variable
        if channelname is None:
            logging.debug('Channelname is None, i\'ll make it the default channel')
            channelname = self.channel
        if channelname[:1] != '#':
            channelname = '#' + channelname
        self.sendServerMessage("JOIN " + channelname)
        logging.debug('Joining channel ' + channelname)
        ircmsg = ""
        while ircmsg.find('End of /NAMES list.') != -1:
            ircmsg = self.receiveMessage
        self.identifyUser()
        logging.debug('Joined channel ' + channelname)

    def sendServerMessage(self, message):
        # this function sends a given string to the server
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
        # taking a string and sending it to the chat
        if target == None:
            target = self.channel
        try:
            self.sendServerMessage("PRIVMSG " + target + " :" + message)
        except Exception as e:
            return False
        return True

    def receiveMessage(self):
        # receive everything the server sends
        message = self.ircsock.recv(4096).decode(self.encoding)
        message = message.strip('\n\r')
        return message

    def ping(self, message):
        # answer to ping from the server
        ret = message.split()[1]
        ret = "PONG " + ret
        self.sendServerMessage(ret)
        print("Pong!")

    def disconnect(self):
        # send the quit command with a quit message
        # receiving the quit answer from the server
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
        # run forever, receive messages and do whatever you want
        logging.debug('Running...')
        while True:
            ircmsg = self.receiveMessage()
            if ircmsg.startswith('PING :'):
                print('Ping?', end=' ')
                self.ping(ircmsg)
            else:
                messageProperties = self.getMessageProperties(ircmsg)
                if messageProperties['messageText'] == 'byebot' and messageProperties['sender'] == 'break3r':
                    print('Received command quit. Putting quit into FROM IRC Queue.')
                    self.queueFromIRC.put('quit')
                    break
                if ircmsg.find('peer') != -1:
                    print('PEER FOUND!!!: ' + ircmsg)
                    logging.warning(ircmsg)
                if ircmsg.find('reloadtest') != -1 and messagePropeties['sender'] == 'break3r':
                    self.queueFromIRC.put('reload')
                    self.sendChannelMessage('Test')
                self.processMessage(messageProperties)
        logging.debug('Left run()-Method.')
        return True

    def getMessageProperties(self, message):
        # split the message in the parts we need
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
        messageProperties['userhost'] = msgDict[0][1:]
        messageProperties['sender'] = msgDict[0].split('!', 1)[0][1:]
        messageProperties['type'] = msgDict[1]
        messageProperties['channel'] = msgDict[2] if msgDict[2] != self.nick else messageProperties['sender']
        messageProperties['messageText'] = ''
        s = messageProperties['channel'] if messageProperties['channel'][:1] == '#' else self.nick
        if message.find(s + ' :') != -1:
            messageProperties['messageText'] = message.split(s + ' :')[1]
        return messageProperties

    def processMessage(self, message):
        # the argument takes the dict with the splitted server message
        if message['messageText'][:1] == ':' and message['messageText'][1:2] != ' ' and message['messageText'][1:2] != ':':
            command = message['messageText'].split()[0][1:]
            try:
                self.sendChannelMessage('I have a message in my queue: ' + self.queueToIRC.get(False, 5))
                self.queueToIRC.task_done()
            except queue.Empty as q:
                pass
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

        if message['messageText'][1:] == 'arrr':
            self.sendChannelMessage('You\'re a pirate?')

    def loadIRCPlugin(self, command):
        # if a command is given (messageText has : as first char)
        # let's see if there's a plugin in the plugins folder
        # if there's such a file, load (or reload) the plugin
        # and call it
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
        # since i tried to make this bot a threaded bot, i need to call this function
        # setting up the needed queues and running up from hereon
        self.queueToIRC = queueToIRC
        self.queueFromIRC = queueFromIRC
        self.connect()
        self.identifyServer()
        self.joinChannel()
        self.run()
        return True
