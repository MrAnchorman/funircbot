# funircbot
Just an IRC Bot for testing and joking and learning better python

At the moment, just add a config.py with the following content:
nick = ''\n
password = ''\n
channel = ''\n

Add the Strings as needed.

The Bot at the current state will:
 - Connect to freenode per SSL (if I did that correctly)
 - Join the Channel you configured
 - it will load and reload plugins if the first char in a channel or query string is ":" (without quotes)
  - if command :xyz is sent in irc, the bot searches for a file xyz.py in plugins folder.
      if its not found, nothing will happen (except for logging as debug) else the file will be (re-)loaded and the run method will be called.
      the parameter message is the irc message as sent from the server
