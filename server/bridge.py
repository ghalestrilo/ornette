from pythonosc import osc_server, udp_client
from pythonosc.dispatcher import Dispatcher

from commands import commands

NOTE_OFFSET=60

class Bridge:
    def __init__(self, host, args):
        self.host = host
        dispatcher = Dispatcher()
        self.bind_dispatcher(dispatcher)
        self.server = osc_server.ThreadingOSCUDPServer((args.ip, args.port), dispatcher)
        self.client = udp_client.SimpleUDPClient(args.sc_ip, args.sc_port)

    def start(self):
        self.server.serve_forever()

    def set(self, *args):
        args = args[1:]
        key = args[0]
        value = list(args[1:])
        if len(value) == 1: value = value[0]
        self.host.set(key, value)

    def run_command(self, addr, args, command):
        # print(addr)
        # print(args)
        # print(command)
        command(self.host, *args)

    def bind_command(self, title, command):
      self.dispatcher.map(f'/{title}', lambda addr, *args: self.run_command(addr, args, command))

    def bind_dispatcher(self, dispatcher):
      self.dispatcher = dispatcher
      for title, command in commands.items():
        self.bind_command(title, command)

    def play(self, msg):
        self.client.send_message('/play2', msg)

    def stop(self):
        self.server.shutdown()

    def notify_task_complete(self):
        print('[server] task complete')
        self.client.send_message('/ok',[])