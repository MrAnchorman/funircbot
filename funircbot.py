#!/usr/bin/env python3

import time
import importlib
import threading
from queue import Queue

def main():
    plugins = dict()
    plugins['irc'] = importlib.import_module('IRC')
    irc = plugins['irc'].IRC()
    queueToIRC = Queue()
    queueFromIRC = Queue()
    queueToIRC.put('Testing the shit outta queues!')
    t = threading.Thread(target=irc.startup, args=[queueToIRC, queueFromIRC]).start()
    i = 0
    irc.sendChannelMessage(queueFromIRC.get())
    queueFromIRC.task_done()
    

if __name__ == '__main__':
    main()
