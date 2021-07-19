
# WIP: This is the "Commands" module
# It specifies commands that the user can issue to the server
# These can be passed via command-line or interactively via OSC

def set(host, *args):
    print(args)
    # args = args[1:]
    key = args[0]
    value = list(args[1:])
    if len(value) == 1: value = value[0]
    host.set(key, value)

commands = (
    { 'reset':     lambda host: host.reset()
    , 'set':       lambda host, *args: set(host, *args)
    , "debug":     lambda host, key: host.io.print() if key == 'all' else host.io.print(key)

    # Engine
    , "generate":  lambda host, length, unit='beats': host.engine.generate(int(length), unit, True)
    , "start":     lambda host: host.engine.start()
    , "stop":      lambda host: host.engine.stop()

    # Song
    , "load":       lambda host, filename, length=None, unit='bars': host.song.load(filename, int(length), unit)
    , "save":       lambda host, name: host.song.save(name)
    , "buffer":     lambda host, num: host.io.log(host.song.buffer(num))
    , "event":      lambda host, ev: host.push_event(ev)
    , "instrument": lambda host, addr, index, *inst: host.song.get_voice(index).set_instrument(inst)
    , "play":       lambda host, pitch: host.bridge.play(pitch)

    # General Control
    , "quit":       lambda host: host.close()
    , "exit":       lambda host: host.close()
    , "kill":       lambda host: host.close()
    , "end":        lambda host: host.close()
    }
)

def run(cmd, host, args):
    """ Runs a user command """
    host.io.log(f'cmd request: {cmd} {args}')
    try:
      fn = commands[cmd]
      fn(host, *args)
    except KeyError:
      print(f'unknown command: {cmd}')


def run_batch(host, command_list):
    """ Parses and runs multiple commands at once"""
    if not isinstance(command_list, str): return

    for line in command_list.split(';'):
      line = line.split(' ')
      cmd, args = line[0], line[1:]
      run(cmd, host, args)
