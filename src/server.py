import pprint
from pythonosc import osc_server, udp_client
from pythonosc.dispatcher import Dispatcher

NOTE_OFFSET=60

# TODO: Move to server.py
state = {
    'is_running': False,
    'is_generating': False,
    'history': [[]],
    'temperature': 1.2,
    'until_next_event': 0.25,
    'buffer_length': 16,
    'trigger_generate': 0.5,
    'playback': True,
    'playhead': 0,
    'model_name': None,
    'model': None,
    'scclient': None,
    'debug_output': False,
    'sync_mode': False,
    'return': 0,
    'tempo': 120,
    'time_shift_denominator': 100,
}

class Server(osc_server.ThreadingOSCUDPServer):
    def __init__(self, model, args, clock):
        init_state(args)
        self.model = model
        state['model'] = model
        dispatcher = Dispatcher()
        self.bind_dispatcher(dispatcher)
        self.clock = clock
        super().__init__((args.ip, args.port), dispatcher)
        # print("Serving {} on {}".format(state['model_name'], state['server'].server_address))

    def bind_dispatcher(self, dispatcher):
        dispatcher.map("/start", engine_set, 'is_running', True)
        dispatcher.map("/pause", engine_set, 'is_running', False)
        dispatcher.map("/reset", server_reset)
        dispatcher.map("/end", self.close)
        dispatcher.map("/quit", self.close)
        dispatcher.map("/exit", self.close)
        dispatcher.map("/debug", engine_print)
        # dispatcher.map("/tfdebug", debug_tensorflow)
        dispatcher.map("/event", push_event)  # event2word

        dispatcher.map("/set", lambda addr, k, v: engine_set(addr, [k, v]))

        if (self.model):
            dispatcher.map("/sample", sample_model, self.model)
        
        if (state['playback'] == True):
          dispatcher.map("/play", lambda _,note: play(note))

    def is_running(self):
      return state['is_running']

    def clock_running(self):
      return state['clock_running']

    def stop_timer(self):
        # this will stop the timer
        self.clock.stop()

    def close(self,unused_addr):
        self.stop_timer()
        self.shutdown()

def engine_set(unused_addr, args):
    try:
        field, value = args
        state[field] = value
        print("[{0}] ~ {1}".format(field, value))
    except KeyError:
        print("no such key ~ {0}".format(field))
        pass


def push_event(unused_addr, event):
    print("[event] ~ {0}".format(event))
    state['history'][0].append(event)


def engine_print(unused_addr, args=None):
    field = args
    if (args == None):
      pprint.pprint(state)
      return
    try:
        # data = [state['model'].word2event[word] for word in state[field][0]] if field == 'history' else state[field]
        data = state[field]
        if (field == 'history'):
          pprint.pprint([state['model'].decode(e) for e in data[0]])
          return
        print("[{0}] ~ {1}".format(field, data))
    except KeyError:
        print("no such key ~ {0}".format(field))
        pass


def sample_model(unused_addr, args):
    model = args[0]
    event = model.predict()
    print(event)

def play(note):
    state['scclient'].send_message('/play2', ['s', 'superpiano', 'note', note - NOTE_OFFSET])

def server_reset(unused_addr):
    [voice.clear() for voice in state['history']]
    state['playhead'] = 0

# def debug_tensorflow(unused_addr):
#   tf.config.list_physical_devices("GPU")
#   print('tf.test.is_gpu_available() = {}'.format(tf.test.is_gpu_available()))

def init_state(args):
    state['model_name'] = args.model_name
    state['playback'] = args.playback
    state['scclient'] = udp_client.SimpleUDPClient(args.sc_ip, args.sc_port)
    state['max_seq'] = args.max_seq
    # state['history'] = [[int(x) for x in str(args.state).split(',')]]

# /TODO: Move to server.py