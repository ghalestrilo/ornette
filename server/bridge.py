from pythonosc import osc_server, udp_client
from pythonosc.dispatcher import Dispatcher
from threading import Thread

from commands import commands, run

NOTE_OFFSET=60

class Bridge:
    def __init__(self, host, args):
        self.host = host
        self.dummy = args.no_server == True
        if self.dummy == True:return
        dispatcher = Dispatcher()
        self.bind_dispatcher(dispatcher)
        self.server = osc_server.ThreadingOSCUDPServer((args.ip, args.port), dispatcher)
        self.client = udp_client.SimpleUDPClient(args.sc_ip, args.sc_port)

    def start(self):
        if self.dummy: return
        self.server.serve_forever()

    def run_command(self, addr, args, command):
        if self.dummy: return
        run(addr[1:], self.host, args)

    def bind_command(self, title, command):
        if self.dummy: return
        self.dispatcher.map(f'/{title}', lambda addr, *args: self.run_command(addr, args, command))

    def bind_dispatcher(self, dispatcher):
        if self.dummy: return
        self.dispatcher = dispatcher
        for title, command in commands.items():
            self.bind_command(title, command)

    def play(self, msg):
        if self.dummy: return
        self.client.send_message('/play2', msg)

    def stop(self):
        if self.dummy: return
        Thread(target=self.server.shutdown).start()

    def notify_task_complete(self):
        print('[server] task complete')
        if self.dummy: return
        self.client.send_message('/ok',[])