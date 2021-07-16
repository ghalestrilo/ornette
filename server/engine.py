from threading import Thread, Event, Lock

# import numpy as np
import math

class Engine():
    def __init__(self, host):
      self.host = host
      self.state = host.state
      self.stopped = Event()
      self.fresh_buffer = Event()

      self.should_wait = False
      self.curmsg = 0
      
      # TODO: Move to host
      # self.host.lock = Lock()

    # Controls
    def start(self):
        Thread(target=self.playback).start()

    def pause(self):
      self.stopped.set()

    def reset(self):
      self.notify_wait(False)
      self.curmsg = 0

    def stop(self):
      self.pause()
      self.reset()

    # Core
    def playback(self):
      if self.host.get('is_running') == True: return
      
      self.host.set('is_running', True)

      if (self.must_generate()): self.generate()

      time = 0
      # output_unit = self.host.get('output_unit')
      while not self.stopped.wait(self.host.song.from_ticks(time, 'seconds')):
      # while not self.stopped.wait(self.host.song.convert(time, output_unit, 'seconds')): #* self.host.get('time_coeff')):
        time = 0
        _last_curmsg = self.curmsg

        while not self.fresh_buffer.wait(0.1):
          pass
        
        if self.must_generate(): self.generate_in_background()

        with self.host.lock:
          msg = self.host.song.getmsg(self.curmsg)

        if msg is not None:
          
          # TODO: Remove
          self.host.io.log(f'({self.curmsg}/{len(self.host.song.messages)}) {msg}')

          self.curmsg = self.curmsg + 1
          self.host.song.perform(msg)
          time = msg.time # Here, msg.time MUST be in ticks
        
        # Notify 
        if _last_curmsg == self.curmsg:
          self.fresh_buffer = Event()

      self.host.set('is_running', False)

    def generate(self, length=None, unit='beats', respond=False):
      host = self.host

      with self.host.lock: host.set('is_generating', True)

      if length is None: length = self.host.get('output_length')

      # Assert Song State
      host.song.init_conductor()
      # print(host.song.data.tracks)

      # Prepare Input Buffer
      buflen = host.get('input_length')
      buflen = host.song.to_ticks(length, 'beats')
      with self.host.lock:
        buffer = host.song.buffer(buflen)

      # Apply Input Filters
      for _filter in host.filters.input: buffer = _filter(buffer, host)

      # Generate sequence
      tracks = host.get('voices')
      final_length = host.song.convert(length, unit, host.get('input_unit'))
      if final_length is None:
        host.io.log(f'error: trying to generate length {final_length} ({length} {unit} to {host.get("input_unit")})')
        return

      # Generate Output
      output = host.model.generate(buffer, final_length, tracks)

      # Apply Output Filters
      for _filter in host.filters.output: output = _filter(output, host)

      # Warn (TODO: validation methods)
      if len(output) != len(tracks):
          host.io.log(f'Expected model to generate {len(tracks)} tracks, but got {len(output)}')

      # Save Output to track
      with self.host.lock:
        for track_messages, track_index in zip(output, tracks):
            for msg in track_messages:
                host.song.append(msg, track_index)

      self.fresh_buffer.set()
      with self.host.lock: host.set('is_generating', False)


    def must_generate(self):
      host = self.host
      with self.host.lock:
        if self.is_generating(): return False
        elif host.song.empty(): return True
        msgcount = len(self.host.song.messages)

      buflen = 32
      ratio = msgcount - self.curmsg
      ratio = 1 - (ratio / buflen)
      # self.host.io.log(f'must = {ratio} < {host.get("trigger_generate")}')
      must = ratio > host.get('trigger_generate')
      return must
































    # HOLD: Needs Mido timing features
    def rewind(self, number):
      host = self.host
      playhead = host.state['playhead']
      target_playhead = playhead - number
      new_playhead = max(target_playhead, 0)
      if (self.is_debugging()):
          host.io.log(f'Rewinding Playhead ({playhead} -> {new_playhead})')

      host.state['playhead'] = new_playhead

    def generate_in_background(self):
      Thread(target=self.generate).start()

    def notify_wait(self,should=True):
      self.should_wait = should



    # def start_metronome(self):
      # pass
      # Thread(target=self.run_metronome).start()
    
    # def run_metronome(self):
    #   # TODO: step to time is track logic
    #   while not self.stopped.wait(60/self.state['bpm']/4):
    #     if (self.state['is_running'] == True):
    #       self.host.play(0,'hh')







    def is_generating(self):
      return self.host.get('is_generating') == True

    def is_debugging(self):
      return self.host.get('debug_output') == True

    # Engine
    def is_running(self):
      return self.host.get('is_running') == True










    # Song
    def push_event(self, event, voice=1):
        self.host.io.log("[event] ~ {0}".format(event))
        self.state['history'][voice].append(event)
