from threading import Thread, Event

import numpy as np
import math

# TODO: Extract stateful code to host
class Clock(Thread):
    def __init__(self, host):
      Thread.__init__(self)
      self.state = host.state
      self.host = host
      self.stopped = Event()
      self.wait_for_more = False

    def bind(self,server_state):
      self.state = server_state
      self.state['playhead'] = 0

    def stop(self):
      self.stopped.set()

    #  TODO: Move to Host
    def generate(self):
      seq = self.host.model.tick()[-128:]
      self.state['playhead'] = self.state['playhead'] - self.state['buffer_length'] + (len(seq) - len(self.state['history'][0]))
      self.state['playhead'] = max(self.state['playhead'], 0)
      self.state['history'][0] = seq
      self.wait_for_more = False
      self.start_metronome()
    # /TODO

    def generate_in_background(self):
      Thread(target=self.generate).start()

    def run(self):
      model = self.host.model

      self.generate_in_background()
      while not self.stopped.wait(self.state['until_next_event']):
        if (self.state['is_running'] == True and self.wait_for_more == False):
          self.host.process_next_token()

          if(len(self.state['history'][0]) == 0):
            self.generate_in_background()
            return

          if (self.state['playhead'] / len(self.state['history'][0]) > self.state['trigger_generate']):
            if (self.state['debug_output'] == True):
              print("Generating more tokens ({} /{} > {})".format(self.state['playhead'], len(self.state['history'][0]), self.state['trigger_generate']))            
            self.generate_in_background()

            if (self.state['debug_output'] == True):
              print('history: {}'.format([model.decode(h) for h in self.state['history'][0]]))

    def start_metronome(self):
      pass
      # Thread(target=self.run_metronome).start()
    
    def run_metronome(self):
      while not self.stopped.wait(60/self.state['tempo']/4):
        if (self.state['is_running'] == True):
          self.host.play(0,'hh')