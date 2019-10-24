## IRC.py

import os # check pathes for existence
import sys # used for exit
import socket # socket to irc
import ssl # ssl context
import logging # logging
import importlib # used to import plugins
import queue # used for queue to and from irc to main thread
import time # used for time.sleep if channel is on invite
import threading

class Disconnected(Exception):
    def __init__(self):
        super().__init__()


class IRC:
    def __init__(self):
        self.plugins = dict()
        self.IRCQueue = None
        self.mainQueue = None
        self.encoding = 'UTF-8'
        self.activeServer = None

    def setup(self, config):
        logging.debug('Setting up Class IRC')
        logging.debug('Setup IRC Server URL')
        self.ircserver = config.get('IRCSERVER', 'server')
        logging.debug('Setting up IRC Server Port')
        self.ircport = config.getint('IRCSERVER', 'port')
        logging.debug('Setting up Channellist')
        self.channel = config.get('IRCSERVER', 'channellist').split(';')[0]
        logging.debug('Setting up IRC Nickname')
        self.nick = config.get('IRCUSER', 'nick')
        logging.debug('Setting up Nickserv password')
        self.password = config.get('IRCUSER', 'password')
        logging.debug('Setting up Administrators')
        self.administrators = config.get('IRCADMIN', 'administrators').split(';')
        self.commandLabel = config.get('GLOBAL', 'command label')
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
        logging.debug('Connecting to {} via port {}'.format(self.ircserver, self.ircport))
        try:
            self.ircsock.connect((self.ircserver, self.ircport))
        except Exception as e:
            print('Cannot connect to server. Exiting program.')
            logging.critical('Cannot connect to server: {}'.format(e.args))
            sys.exit(127)

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
        print('Nickserv asked to identify. Doing so!')
        logging.debug('Identifying myself as ' + self.nick)
        self.sendServerMessage("PRIVMSG" + " NICKSERV :identify " + self.password + "\n")

    def joinChannel(self, channelname = None):
        # Join channel. If channelname is not given, the bot will join the channel which is given per object variable
        if channelname is None:
            logging.debug('Channelname is None, i\'ll make it the default channel')
            channelname = self.channel
        if channelname[:1] != '#':
            channelname = '#' + channelname
        logging.debug('Joining channel {}'.format(channelname))
        self.sendServerMessage("JOIN " + channelname)
        logging.debug('Joining channel ' + channelname)

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
            self.sendServerMessage("PRIVMSG {} :{}".format(target, message))
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
        return 0

    def disconnect(self):
        # send the quit command with a quit message
        # receiving the quit answer from the server
        self.sendServerMessage("QUIT :My Master told me to leave.")
        '''
        I was told to go. I go
        :MrAnchorman!~MrAnchorm@pgno.dvag.com QUIT :Client Quit

        ERROR :Closing Link: pgno.dvag.com (Client Quit)
        '''
        logging.debug('Closed connection')
        print('Disconnect')
        return 0

    def run(self):
        # run forever, receive messages and do whatever you want
        logging.debug('Running...')
        print('Run thread started')
        self.identifyUser()
        while True:
            ircmsg = self.receiveMessage()
            print(ircmsg)
            if ircmsg.startswith('PING :'):
                print('Ping?', end=' ')
                self.ping(ircmsg)
            elif ircmsg.find('peer') != -1:
                print('PEER FOUND!!!: ' + ircmsg)
                logging.warning(ircmsg)
            else:
                message = dict()
                try:
                    message['type'] = self.getMessageType(ircmsg)
                except Disconnected:
                    break
                if message['type'] == ':Closing':
                    message['content'] = ircmsg.rsplit('(')[1][:-1]
                    break
                message.update(self.getGlobalIrcmsgProperties(ircmsg))
                if message['usernick'] != self.nick:
                    message.update(self.getSelectiveIrcmsgProperties(ircmsg, message['type']))
                    if message['type'] == 'CHANMSG':
                        message.update(self.onChanMsg(message))
                    if message['type'] == 'CHANACTION':
                        message.update(self.onChanAction(message))
                    if message['type'] == 'PRIVMSG':
                        message.update(self.onPrivMsg(message))
                    if message['type'] == 'PRIVACTION':
                        message.update(self.onPrivAction(message))
                    if message['type'] == 'PRIVNOTICE':
                        message.update(self.onPrivNotice(message))
                    if message['type'] == 'CHANNOTICE':
                        message.update(self.onChanNotice(message))
                    if message['type'] == 'JOIN':
                        message.update(self.onJoin(message))
                    if message['type'] == 'PART':
                        message.update(self.onPart(message))
                    if message['type'] == 'QUIT':
                        message.update(self.onQuit(message))
                    if message['type'] == 'NICK':
                        message.update(self.onNick(message))
                    if message['type'] == 'KICK':
                        message.update(self.onKick(message))
                    if message['type'] == 'MODE':
                        message.update(self.onMode(message))
                    print(message)
        print('Left run()-Method.')
        logging.debug('Left run()-Method.')
        return 0

    def getMessageType(self, message):
            # split the message in the parts we need
            '''
            :break3r!~Nameless@unaffiliated/break3r PRIVMSG MrAnchorman :TEST
            :break3r!~Nameless@unaffiliated/break3r PRIVMSG MrAnchorman :DCC CHAT chat 171786923 52684
            :break3r!~Nameless@unaffiliated/break3r PRIVMSG ##funircbot :ACTION test

            '''
            msgDict = message.split()
            if len(msgDict) < 1:
                raise Disconnected
            if msgDict[1] == 'PRIVMSG':
                if msgDict[3].startswith(':\x01ACTION'):
                    msgtype = 'ACTION'
                else:
                    msgtype = 'MSG'
                if msgDict[2].startswith('#'):
                    target = 'CHAN'
                else:
                    target = 'PRIV'
            elif msgDict[1] == 'NOTICE':
                msgtype = 'NOTICE'
                if msgDict[2].startswith('#'):
                    target = 'CHAN'
                else:
                    target = 'PRIV'
            else:
                return msgDict[1]

            return target + msgtype

    def getGlobalIrcmsgProperties(self, ircmsg):
            if ircmsg.startswith('ERROR :'):
                return dict()
            m = ircmsg.split()
            msg = dict()
            msg['user'] = m[0][1:]
            msg['usernick'] = m[0].split('!')[0][1:]
            msg['username'] = m[0].split('!')[1].split('@')[0]
            if msg['username'].startswith('~'):
                msg['username'] = msg['username'][1:]
            msg['userdomain'] = m[0].split('@')[1]
            msg['useraccount'] = ''
            if msg['userdomain'].find('/') != -1:
                msg['userhost'] = msg['userdomain'].split('/')[0]
                msg['useraccount'] = msg['user'].split('/')[1]
            return msg

    def getSelectiveIrcmsgProperties(self, ircmsg, type):
        msg = dict()
        if type == 'NICK':
            msg['newnick'] = ircmsg.rsplit(':')[1]
            return msg
        if type == 'QUIT':
            msg['quitmsg'] = ' '.join(ircmsg[2:])
            return msg
        ircmsg = ircmsg.split()
        msg['channel'] = ircmsg[2]
        if not msg['channel'].startswith('#'):
            msg['channel'] = ircmsg[0].split('!')[0][1:]
        msg['content'] = ' '.join(ircmsg[3:])[1:]
        if msg['content'].startswith('\x01ACTION'):
            msg['content'] = msg['content'][8:][:-1]
        if type == 'MODE':
            msg['activate'] = True if ircmsg[3][:1] == '+' else False
        return msg

    def onChanMsg(self, message):
        # :break3r!~Nameless@unaffiliated/break3r PRIVMSG ##gitbottest :Testnachricht
        if message['content'].startswith('byebot') and message['usernick'] in self.administrators:
            self.mainQueue.put('quit')
        if message['content'].startswith(self.commandLabel):
            threading.Thread(target=self.processCommand, args=(message,)).start()
        return dict()

    def onChanAction(self, message):
        # :break3r_test!~bre@185.64.159.168 PRIVMSG ##funircbot :ACTION test
        return dict()

    def onPrivMsg(self, message):
        # :break3r!~Nameless@unaffiliated/break3r PRIVMSG MrAnchorman :Query MSG
        if message['content'].startswith(self.commandLabel):
            threading.Thread(target=self.processCommand, args=(message,)).start()
        return dict()

    def onPrivAction(self, message):
        # :break3r_test!~bre@185.64.159.168 PRIVMSG Anchorman :ACTION test
        return dict()

    def onPrivNotice(self, message):
        # :break3r!~Nameless@unaffiliated/break3r NOTICE MrAnchorman :Notice
        # :NickServ!NickServ@services. NOTICE Anchorman :You are now identified for Anchorman.
        #This nickname is registered. Please choose a different nickname, or identify via /msg NickServ identify <password>
        return dict()

    def onChanNotice(self, message):
        # :break3r!~Nameless@unaffiliated/break3r NOTICE ##funircbot :test
        return dict()

    def onJoin(self, message):
        # :b_test!~Nameles@185.64.159.168 JOIN ##funircbot
        return dict()

    def onPart(self, message):
        # :b_test!~Nameles@185.64.159.168 PART ##funircbot :"Leaving"
        return dict()

    def onQuit(self, message):
        # :break3r_test!~bre@185.64.159.168 QUIT :Quit: Testing quit message
        return dict()

    def onNick(self, message):
        # :b_t!~b_usernam@p4FF0ABD8.dip0.t-ipconnect.de NICK :bre_test
        return dict()

    def onKick(self, message):
        # :break3r!~Nameless@unaffiliated/break3r KICK ##funircbot b_test :b_test
        # :break3r!~Nameless@unaffiliated/break3r KICK ##funircbot b_test :kicking
        return dict()

    def onMode(self, message):
        '''
        :break3r!~Nameless@unaffiliated/break3r MODE ##funircbot +v b_test
        :break3r!~Nameless@unaffiliated/break3r MODE ##funircbot -v b_test
        :break3r!~Nameless@unaffiliated/break3r MODE ##funircbot +b *!*Nameles@185.64.159.*
        :break3r!~Nameless@unaffiliated/break3r MODE ##funircbot -b *!*Nameles@185.64.159.*
        :break3r!~Nameless@unaffiliated/break3r KICK ##funircbot b_test :b_test
        :break3r!~Nameless@unaffiliated/break3r MODE ##funircbot +o b_test
        :break3r!~Nameless@unaffiliated/break3r MODE ##funircbot +g
        '''
        return dict()

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

    def startup(self, IRCQueue, mainQueue):
        # since i tried to make this bot a threaded bot, i need to call this function
        # setting up the needed queues and running up from hereon
        self.IRCQueue = IRCQueue
        self.mainQueue = mainQueue
        self.connect()
        self.identifyServer()
        self.joinChannel()
        while True:
            ircmsg = self.receiveMessage()
            if ircmsg.find('473 Anchorman ##funircbot :Cannot join channel (+i) - you must be invited') != -1:
                print('THE CHANNEL IS ON INVITE!')
                time.sleep(5)
                self.joinChannel()
            if ircmsg.find('366 Anchorman ##funircbot :End of /NAMES list.') != -1:
                print('Joined channel')
                break
        self.run()
        return 0

