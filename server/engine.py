from threading import Thread, Event, Lock

# import numpy as np
import math


import mido # FIXME: Remove this once #decode() / #getaction() have been updated





class Engine():
    def __init__(self, host):
      self.host = host
      self.state = host.state
      self.stopped = Event()
      self.should_wait = False
      self.curtick = 0
      
      self.lock = Lock()


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
      for msg in self.host.song.play():
        with self.lock:
            if self.stopped: break          
            self.host.io.log(msg)
            
            # TODO: Event: play note
            # self.host.bridge.play(msg)
            # chan = self.host.song.get_channel(msg.channel)
            # if chan:  chan.play(msg.note)
            

        if (self.must_generate()):
            self.generate_in_background() # self.treshold_met

      self.host.set('is_running', False)


      # while not self.stopped.wait(self.state['until_next_event']):
      #   if (self.is_running() == True and self.should_wait == False):
          
      #     for voice in host.get('voices'):
      #       self.process_next_token(voice)

      #     voice = host.get('voices')[0]
      #     if (self.must_generate(voice)):
      #       self.generate_in_background()


    def must_generate(self):
      host = self.host
      if self.is_generating(): return False
      elif host.song.empty(): return True

      # TODO: wtf is this
      if (host.get('batch_mode') and host.task_ended()): return False

      remaining_ticks = host.song.to_ticks(host.song.data.length, 'seconds') - self.curtick

      # TODO: Test
      return remaining_ticks / host.get('buffer_length') < host.get('trigger_generate')





    # TODO:
    # 1. Fix start/run (why is it not printing?)
    # 2. Make OSC great again! (send it to sclang)
    # 3. Test must_generate
    # 4. Refactor Generate:
    #   - call get_buffer
    #   - erase 'history'
    #   - refactor encoding/decoding
    #   - stretch: make filters?











    def generate(self, length=None, unit='beats', respond=False):
      host = self.host
      song = host.song
      # song = self.song
      if length is None:
        length = host.get('missing_beats')

      host.set('is_generating',True)
      history = host.get('history')
      hist_ = history[0]
      threshold = host.get('trigger_generate')
      playhead = host.get('playhead')
      voices = host.get('voices')

      max_len = host.get('buffer_length') 

      # if not any(state['output_data'].tracks):
          # data.init_output_data(state)

      if (self.is_debugging()):
          host.io.log(f'generating tokens ({playhead}/{len(hist_)} > {threshold})')
          host.io.log(f'requested length: {length} {unit} ({song.to_ticks(length, unit)} ticks)')

      # Generate sequence
      ticks = song.to_ticks(length, unit)
      final_length = song.from_ticks(ticks, host.get('input_unit'))
      host.io.log(f'request: host.model.generate(history, {final_length})')

      if final_length is None:
        host.io.log(f'error: trying to generate length {final_length}')
        return

      output = host.model.generate(history, final_length, voices)
      # host.io.log(f'{len(seq)} tokens were generated')

      host.io.log(output)
      host.io.log(f'len(output): {len(output)}')
      host.io.log(f'len(hist): {len(history)}')

      for i, v in enumerate(voices):
        output_ = output[i]
        hist_ = history[v]
        
        generated_length = len(output_) - len(hist_)
        host.state['history'][v] = output_[-max_len:]
        for event in output_[-generated_length:]:
          for message in self.decode(event, v):
              # song.add_message(host.state, message, v)
              host.song.append(message, v)
              # state['output_data'].tracks[v].append(message)

      # Update Playhead
      self.rewind(max(0, generated_length))

      host.set('is_generating',False)
      self.notify_wait(False)

      if (respond):
        # host.dump_history()
        host.bridge.notify_task_complete()



















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








    # TODO: Prop
    def is_generating(self):
      return self.host.get('is_generating') == True

    def is_debugging(self):
      return self.state['debug_output'] == True





    # Engine (update to mido) | Put side by side with run (core functions)
    def perform(self,action):
      ''' Performs a musical action described by a tuple (name, value)
          Name can be:
          
          'wait': waits value miliseconds until next action is performed
          'play': sends an osc message to play the desired note (value)
      '''
      name, value = action
      host = self.host
      if (self.is_debugging()):
        host.io.log(f'({host.get("playhead")}/{len(host.get("history")[0])}): {name} {value}')

      if (host.set('batch_mode')):
        self.state['until_next_event'] = 0
        return

      # Deprecate this
      if (name == 'play'): host.play(int(value))
      
      # FIXME: Calculate seconds from incoming value unit (melody_rnn: beats)
      if (name == 'wait'):
          # ticks = self.to_ticks(value, state['output_unit'])
          # secs = self.from_ticks(ticks, 'seconds')
          self.state['until_next_event'] = value



    # Engine
    def is_running(self):
      return self.host.get('is_running') == True

    # Song
    def push_event(self, event, voice=1):
        self.host.io.log("[event] ~ {0}".format(event))
        self.state['history'][voice].append(event)
















### Deprecate (Destroy, Erase, Improve)


    # Engine (depr)

    # TODO: Deprecate
    def get_next_token(self,voice):
      return self.peek(voice,0)

    # Engine (depr)
    def peek(self,voice=1,offset=1):
      """ Check next event in history """
      host = self.host
      hist = host.get('history')
      playhead = host.get('playhead')

      if (host.song.has_history() == False): return None

      no_more_tokens = playhead >= len(hist[voice])
      position = playhead + offset

      if (no_more_tokens):
          self.notify_wait()
          return None

      if (position < 0):
        host.io.log(f'Warning: trying to read a negative position in history ({playhead} + {offset} = {position})')
        return None

      return hist[voice][position]




    # Engine (depr)
    def decode(self, event, voice):
      return [mido.Message(name,
        note=note,
        channel=voice,
        velocity=velocity,
        time=int(round(mido.second2tick(time, self.host.get('ticks_per_beat'), self.host.get('midi_tempo')))))
        for (name, note, velocity, time)
        in self.host.model.decode(event)]

    # Engine (depr)
    def get_action(self,message,voice=0):
        ''' Get Action
            Decode a midi message into a sequence of actions
        '''
        name, note, velocity, time = message
        msg = mido.Message(name,
          note=note,
          channel=voice,
          velocity=velocity,
          time=self.host.song.to_ticks(time * self.host.get('steps_per_quarter'),'beat'))
          
        self.host.song.append(msg, voice)
        return [('wait', time), ('play', note)] if name != 'note_off' else [('wait', time)]


    # Engine (depr)
    def process_next_token(self, voice=1):
      ''' Reads the next token from the history
          Decodes the token onto a mido messagee
          Saves the message to the output
          Decodes each message into actions
          Performs the required actions
          Increments playhead
      '''
      e = self.get_next_token(voice)

      if (e == None):
        if (self.is_debugging()): self.host.io.log(f'No event / voice {voice} is empty')
        if (self.host.get('batch_mode') and self.host.task_ended()):
            self.host.set('is_running', False)
            self.host.save_output(self.host.get('output_filename'))
        return

      for message in self.host.model.decode(e):
        for action in self.get_action(message,voice):
          self.perform(action)

      self.state['playhead'] = self.state['playhead'] + 1
    # TODO: Deprecate