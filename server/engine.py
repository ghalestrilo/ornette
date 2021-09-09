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

      # Trigger background generation
      if (self.must_generate()): self.generate()

      time = 0
      should_stop = False
      while not should_stop:
        time = 0
        _last_curmsg = self.curmsg

        # Wait until more notes have been generated
        while not self.fresh_buffer.wait(0.1):
          if self.stopped.is_set(): return
        
        # Trigger background generation
        if self.must_generate(): self.generate_in_background()

        # Get current note
        with self.host.lock:
          msg = self.host.song.getmsg(self.curmsg)

        # Play it
        if msg is not None:
          
          # TODO: Remove
          self.host.io.log(f'({self.curmsg}/{len(self.host.song.messages)}) {msg}')

          self.curmsg = self.curmsg + 1
          time = msg.time # Here, msg.time returns in BEATS (because of mido)
          time = self.host.song.convert(time, 'beats', 'seconds') # Convert that to seconds
          time = time * self.host.get('steps_per_quarter') #/ 2 # Without this, playback happens too fast (IDK why)
          # print(f'msg.time: {msg.time} | wait: {time}s')
          should_stop = self.stopped.wait(time)
          self.host.song.perform(msg)
        
        # Notify buffer has ended
        if _last_curmsg == self.curmsg:
          self.fresh_buffer = Event()

      self.host.set('is_running', False)


    def get_quantized_steps(self):
      self.host.song.get_buffer_length()
      total_quantized_steps = self.host.song.get_buffer_length(unit='beats')
      total_quantized_steps = int(round(total_quantized_steps))
      return total_quantized_steps

    def must_generate(self):
      host = self.host
      with self.host.lock:
        if self.is_generating(): return False
        elif host.song.empty(): return True
        msgcount = len(self.host.song.messages)

      buflen = 32
      # FIXME: Calculate Buffer Length from ticks?
      # buflen = host.get('input_length')
      ratio = msgcount - self.curmsg
      ratio = 1 - (ratio / buflen)
      # self.host.io.log(f'must = {ratio} < {host.get("trigger_generate")}')
      must = ratio > host.get('trigger_generate')
      return must



    def generate_until(self, length, unit):
      return


    def generate(self, length=None, unit=None, respond=False):
      host = self.host

      with self.host.lock: host.set('is_generating', True)

      # Default values for output length
      if length is None: length = self.host.get('output_length')
      if unit is None: unit = self.host.get('output_unit')

      # Assert Song State
      with self.host.lock: host.song.init_conductor()

      # Prepare Input Buffer (<input_length> <input_unit>s)
      buflen = host.get('input_length')
      buflen = host.song.to_ticks(buflen, host.get('input_unit'))
      with self.host.lock:
        buffer = host.song.buffer(buflen)

      # Calculate Generation Length
      generation_start = self.host.get('generation_start')
      requested_beats = self.host.song.convert(length, unit, self.host.get('output_unit'))
      host.set('generation_requested_beats', requested_beats)

      # Apply Input Filters
      for _filter in host.filters.input: buffer = _filter(buffer, host)

      # Generate sequence
      tracks = host.get('output_tracks')
      final_length = host.song.convert(length, unit, host.get('output_unit'))


      # Guarantee at least 2 notes are generated per segment
      i = 0
      output = [[]]
      count_notes = lambda seq: len([msg for msg in seq if msg.type.startswith('note_on')])
      while all(map(lambda seq: count_notes(seq) < 2, output)):
        i = i + 1
        self.host.io.log(f'retrying generation ({i})')
        output = host.model.generate(buffer, final_length, tracks)

        # Apply Output Filters
        for _filter in host.filters.output: output = _filter(output, host)
        if not self.host.get('guarantee_two_notes'): break

      # Before updating generation_start: pad all sequences (so new messages line up)
      self.host.song.pad(generation_start, unit)

      # Update generation_start
      self.host.set('generation_start', generation_start + requested_beats)

      # Warn (TODO: validation methods)
      if len(output) != len(tracks):
          host.io.log(f'Expected model to generate {len(tracks)} tracks, but got {len(output)}')

      # Save Output to track
      requested_ticks = self.host.song.to_ticks(length, unit)
      with self.host.lock:
        for track_messages, track_index in zip(output, tracks):
            ticks = 0
            for msg in track_messages:
                if hasattr(msg, 'time'): ticks += msg.time
                if ticks > requested_ticks: msg.time -= (ticks - requested_ticks)
                host.song.append(msg, track_index)
                if ticks > requested_ticks: break

      self.host.song.pad(requested_beats, unit)

      self.fresh_buffer.set()
      host.song.check_end_of_tracks()
      with self.host.lock: host.set('is_generating', False)












    max_retries = 50
    def generate_to(self, length, unit='bars'):
      i = 0
      while self.host.song.total_length(unit) < length:
        self.generate()
        i += 1
        if i > self.max_retries: break

      # trim excess
      return












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
