from pythonosc import osc_server, udp_client
from pythonosc.dispatcher import Dispatcher

NOTE_OFFSET=60

class Bridge:
    def __init__(self, host, args):
        self.host = host
        dispatcher = Dispatcher()
        self.bind_dispatcher(dispatcher)
        self.server = osc_server.ThreadingOSCUDPServer((args.ip, args.port), dispatcher)
        self.client = udp_client.SimpleUDPClient(args.sc_ip, args.sc_port)

    def start(self):
        # print("Serving {} on {}".format(state['module'], state['server'].server_address))
        self.server.serve_forever()

    def bind_dispatcher(self, dispatcher):
        host = self.host
        dispatcher.map("/start", lambda _: host.set('is_running', True))
        dispatcher.map("/pause", lambda _: host.set('is_running', False))
        dispatcher.map("/reset", lambda _: host.reset())
        dispatcher.map("/event", lambda _, ev: host.push_event(ev))  # event2word
        # dispatcher.map("/tfdebug", debug_tensorflow)

        dispatcher.map("/set", lambda addr, k, v: host.set(k, v))
        dispatcher.map("/debug", lambda addr, key: host.print() if key == 'all' else host.print(key))

        # if (self.host.model):
        #     dispatcher.map("/sample", sample_model, self.model)
        
        if (self.host.state['playback'] == True):
          dispatcher.map("/play", lambda _,pitch: self.play(pitch))

        dispatcher.map("/quit",  lambda _: host.close())
        dispatcher.map("/exit",  lambda _: host.close())
        dispatcher.map("/kill",  lambda _: host.close())
        dispatcher.map("/end",   lambda _: host.close())

    def play(self,pitch,sound='superpiano'):
        self.client.send_message('/play2', ['s', sound, 'note', pitch - NOTE_OFFSET])

    def stop(self):
        self.server.shutdown()

# /TODO: Move to server.py