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

    def generate(self):
      seq = self.host.model.tick()[-128:]
      self.state['playhead'] = self.state['playhead'] - self.state['buffer_length'] + (len(seq) - len(self.state['history'][0]))
      self.state['playhead'] = max(self.state['playhead'], 0)
      self.state['history'][0] = seq
      self.wait_for_more = False

    def generate_in_background(self):
      Thread(target=self.generate).start()

    def has_history(self):
      hist = self.state['history']
      # return np.any(hist) and np.any(hist[0])
      return any(hist) and any(hist[0])

    def get_next_token(self):
      hist = self.state['history']

      if (self.has_history() == False):
        return None

      if (self.state['playhead'] >= len(hist[0])):
        self.wait_for_more = True
        return None

      # return self.host.model.decode(self.state['history'][0][self.state['playhead']])
      return self.state['history'][0][self.state['playhead']]

    def process_next_token(self):
      e = self.get_next_token()

      if (e == None):
        print("No event / history is empty")
        return

      action = self.host.model.get_action(e)
      if (action is None):
          print(f'No action returned for event {e}')
          return

      # Host#perform(action)
      for (name, value) in action:
        if (name == 'play'): self.host.play(int(value))
        if (name == 'wait'): self.state['until_next_event'] = value

      self.state['playhead'] = self.state['playhead'] + 1


    def run(self):
      model = self.host.model

      self.generate_in_background()
      while not self.stopped.wait(self.state['until_next_event']):
        if (self.state['is_running'] == True and self.wait_for_more == False):
          self.process_next_token()

          if(len(self.state['history'][0]) == 0):
            self.generate_in_background()
            return

          if (self.state['playhead'] / len(self.state['history'][0]) > self.state['trigger_generate']):
            if (self.state['debug_output'] == True):
              print("Generating more tokens ({} /{} > {})".format(self.state['playhead'], len(self.state['history'][0]), self.state['trigger_generate']))            
            self.generate_in_background()

            if (self.state['debug_output'] == True):
              print('history: {}'.format([model.decode(h) for h in self.state['history'][0]]))