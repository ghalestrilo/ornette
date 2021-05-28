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

    def set(self, *args):
      args = args[1:]
      key = args[0]
      value = list(args[1:])
      if len(value) == 1: value = value[0]
      self.host.set(key, value)


    def bind_dispatcher(self, dispatcher):
        host = self.host

        # Host
        dispatcher.map("/reset", lambda _: host.reset())

        # dispatcher.map("/tfdebug", debug_tensorflow)

        dispatcher.map("/set",       self.set)
        dispatcher.map("/debug",     lambda addr, key: host.print() if key == 'all' else host.print(key))

        # Engine
        dispatcher.map("/generate",  lambda addr, length, unit: host.engine.generate(length, unit, True))
        dispatcher.map("/start",     lambda _: host.engine.start())
        dispatcher.map("/stop",      lambda _: host.engine.stop())

        # Song
        dispatcher.map("/load",      lambda *args: host.song.load(args[1],
            args[2] if len(args) > 2 else None,
            args[3] if len(args) > 3 else 'bars',
          ))
        dispatcher.map("/save",    lambda addr, name: host.song.save(name))
        dispatcher.map("/buffer",  lambda addr, num: host.io.log(host.song.buffer(num)))
        dispatcher.map("/event",   lambda _, ev: host.push_event(ev))  # event2word

        # if (self.host.model):
        #     dispatcher.map("/sample", sample_model, self.model)
        
        if (self.host.state['playback'] == True):
          dispatcher.map("/play", lambda _,pitch: self.play(pitch))

        dispatcher.map("/quit",  lambda _: host.close())
        dispatcher.map("/exit",  lambda _: host.close())
        dispatcher.map("/kill",  lambda _: host.close())
        dispatcher.map("/end",   lambda _: host.close())

    # TODO: Set sound
    def play(self,pitch):
        self.client.send_message('/play2',
          [ 'note', pitch - NOTE_OFFSET
          , 'cut', pitch - NOTE_OFFSET
          , 'gain', 1
          ]
          +
          self.host.get_instrument())
    
    def kill_note(self,pitch):
        self.client.send_message('/play2',
          [ 'note', pitch - NOTE_OFFSET
          , 'cut', pitch - NOTE_OFFSET
          , 'gain', 0
          ]
          +
          self.host.get_instrument())

    def stop(self):
        self.server.shutdown()

    def notify_task_complete(self):
        print('[server] task complete')
        self.client.send_message('/ok',[])