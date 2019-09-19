#!/usr/bin/env python3

import time
import importlib
import threading

def main():
    plugins = dict()
    plugins['irc'] = importlib.import_module('IRC')
    irc = plugins['irc'].IRC()
    t = threading.Thread(target=irc.startup).start()
    i = 0
    while True:
        print(i)
        i += 1
        if i == 30:
            break
        time.sleep(1)
    print('ende')
    print(t)

if __name__ == '__main__':
    main()
