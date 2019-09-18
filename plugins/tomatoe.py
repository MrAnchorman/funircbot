import random

'''
this is just a plugin for the twitch bot. So it only needs a function called run, which will be called by the twitch bot
The message parameter gets the whole input of the command, so it can do whatever it wants with the information
'''

def run(message):
        x = message['messageText'].split()
        r = random.randint(1,2)
        if r == 1:
                addon = message['sender'] + ' misses! HAHA!'
        else:
                addon = 'HIT!!!'

        if len(x) > 1 and x[1].lower() == 'anchorman':
                target = 'me'
                addon = 'I can catch it and throw it back. HIT!'
        elif len(x) > 1:
                target = x[1]
        else:
                target = 'me'
                addon = 'I can catch it and I throw it back. HIT!'

        return message['sender'] + ' throws a tomatoe @ ' + target + '! ' + addon
