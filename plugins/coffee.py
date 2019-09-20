def run(message):
    m = message['messageText'].split()
    if len(m) > 1:
        target = m[1]
        addon = 'Mit freundlichen Grüßen von {}'.format(message['sender'])
    else:
        target = message['sender']
        addon = ''

    
    return '\x01ACTION bringt {} einen Kaffee. {}\x01'.format(target, addon)
