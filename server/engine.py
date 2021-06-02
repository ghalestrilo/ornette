from threading import Thread, Event, Lock

# import numpy as np
import math


import mido # FIXME: Remove this once #decode() / #getaction() have been updated


# FIXME: This should come from the module
from filters import midotrack2noteseq, noteseq2midotrack

class Engine():
    def __init__(self, host):
      self.host = host
      self.state = host.state
      self.stopped = Event()
      self.should_wait = False
      self.curtick = 0
      self.lock = Lock()

      self.input_filters = [midotrack2noteseq]
      self.output_filters = [noteseq2midotrack]

    # Controls
    def start(self):
        Thread(target=self.playback).start()

    def pause(self):
      self.stopped.set()

    def reset(self):
      # self.stopped = Event()
      self.notify_wait(False)
      self.curtick = 0

    def stop(self):
      self.pause()
      self.reset()

    # Core
    def playback(self):
      if self.host.get('is_running') == True: return
      
      self.host.set('is_running', True)

      if (self.must_generate()): self.generate()
      else: self.host.io.log('it\'s cool')

      # TODO: Update this buffer while it runs (make an while ! self.stopped loop?)
      for msg in self.host.song.play():
        with self.lock:
            
            # TODO: Event: play note
            self.host.song.perform(msg)

        self.curtick += msg.time
        if (self.must_generate()):
            self.generate_in_background()

      self.host.set('is_running', False)

    def generate(self, length=None, unit='beats', respond=False):
      host = self.host
      host.set('is_generating', True)

      if length is None: length = self.host.get('output_length')

      # Assert Song State
      host.song.init_conductor()
      print(host.song.data.tracks)

      # Prepare Input Buffer
      buflen = host.get('input_length')
      buflen = host.song.to_ticks(length, 'beats')
      buffer = host.song.buffer(buflen)
      for _filter in self.input_filters: buffer = _filter(buffer, host)

      # Generate sequence
      tracks = host.get('voices')
      final_length = host.song.convert(length, unit, host.get('input_unit'))
      if final_length is None:
        host.io.log(f'error: trying to generate length {final_length} ({length} {unit} to {host.get("input_unit")})')
        return

      # Generate Output
      output = host.model.generate(buffer, final_length, tracks)
      for _filter in self.output_filters: output = _filter(output, host)

      # Warn (TODO: validation methods)
      if len(output) != len(tracks):
          host.io.log(f'Expected model to generate {len(tracks)} tracks, but got {len(output)}')

      # Save Output to track
      for track_messages, track_index in zip(output, tracks):
          for msg in track_messages:
            host.song.append(msg, track_index)

      host.set('is_generating', False)


    def must_generate(self):
      host = self.host
      with self.lock:
        if self.is_generating(): return False
        elif host.song.empty(): return True

        # TODO: wtf is this
        # if (host.get('batch_mode') and host.task_ended()): return False

        print(' ')
        host.io.log(f'empty: {host.song.empty()}')
        song_length = host.song.to_ticks(host.song.data.length, 'seconds')
        host.io.log(f'song_length: {song_length} ticks')

        curtick = self.curtick
        curtick = host.song.to_ticks(curtick, 'seconds')
        host.io.log(f'self.curtick: {curtick}')

        remaining_ticks = song_length - curtick
        host.io.log(f'remaining_ticks: {remaining_ticks}')

        buffer_length = host.song.to_ticks(host.get('input_length'), host.get('input_unit'))
        buffer_length = buffer_length
        host.io.log(f'buffer_length: {buffer_length}')

        ratio = remaining_ticks / buffer_length
        host.io.log(f'ratio: {ratio}')

        must = ratio < host.get('trigger_generate')
        host.io.log(f'must: {must}')

      # TODO: Test
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
      # self.should_wait = False

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
