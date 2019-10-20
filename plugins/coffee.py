def run(message, socket):
    m = message['content'].split()
    if len(m) > 1:
        target = m[1]
        addon = 'Mit freundlichen Grüßen von {}'.format(message['usernick'])
    else:
        target = message['usernick']
        addon = ''

    socket.send(bytes('PRIVMSG {} :abc die Katze liegt im Schnee\n'.format(message['channel']), 'UTF-8'))

    return '\x01ACTION bringt {} einen Kaffee. {}\x01'.format(target, addon)
