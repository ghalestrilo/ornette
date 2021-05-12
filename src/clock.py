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
      self.should_wait = False
      # self.start_metronome()
      # TODO: Set delays
      # host.set('delays', [0 for voice in host.get('voices')])

    def bind(self,server_state):
      self.state = server_state
      self.state['playhead'] = 0

    def stop(self):
      self.stopped.set()

    def generate_in_background(self):
      Thread(target=self.host.generate).start()
      # self.should_wait = False

    def run(self):
      host = self.host

      # self.generate_in_background()
      while not self.stopped.wait(self.state['until_next_event']):
        if (host.is_running() == True and self.should_wait == False):
          i = 0
          self.host.process_next_token(i)

          if (host.must_generate()):
            self.generate_in_background()

    def start_metronome(self):
      pass
      # Thread(target=self.run_metronome).start()
    
    def run_metronome(self):
      # TODO: step to time is host logic
      while not self.stopped.wait(60/self.state['bpm']/4):
        if (self.state['is_running'] == True):
          self.host.play(0,'hh')

    def notify_wait(self,should=True):
      self.should_wait = should
