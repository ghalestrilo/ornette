from pythonosc import osc_server, udp_client
from pythonosc.dispatcher import Dispatcher

NOTE_OFFSET=60

class Bridge:
    def __init__(self, host, args):
        self.host = host

        self.server = osc_server.ThreadingOSCUDPServer
        self.client = udp_client.SimpleUDPClient(args.sc_ip, args.sc_port)

        dispatcher = Dispatcher()
        self.bind_dispatcher(dispatcher)
        self.clock = clock
        super().__init__((args.ip, args.port), dispatcher)
        # print("Serving {} on {}".format(state['module'], state['server'].server_address))

    def bind_dispatcher(self, dispatcher):
        host = self.host
        dispatcher.map("/start", lambda _: host.engine_set('is_running', True))
        dispatcher.map("/pause", lambda _: host.engine_set('is_running', False))
        dispatcher.map("/reset", lambda _: host.server_reset())
        dispatcher.map("/end", self.close)
        dispatcher.map("/quit", self.close)
        dispatcher.map("/exit", self.close)
        # dispatcher.map("/tfdebug", debug_tensorflow)
        dispatcher.map("/event", lambda _, ev: host.push_event(ev))  # event2word

        dispatcher.map("/set", lambda addr, k, v: host.engine_set(k, v))
        dispatcher.map("/debug", lambda addr, key: host.engine_print(key))

        # if (self.host.model):
        #     dispatcher.map("/sample", sample_model, self.model)
        
        if (self.host.state['playback'] == True):
          dispatcher.map("/play", lambda _,pitch: self.play(pitch))

    def stop_timer(self):
        # this will stop the timer
        self.clock.stop()

    def close(self,unused_addr):
        self.stop_timer()
        self.server.shutdown()

    def play(self,pitch):
        self.client.send_message('/play2', ['s', 'superpiano', 'note', pitch - NOTE_OFFSET])

# /TODO: Move to server.py