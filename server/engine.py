from threading import Thread, Event

# import numpy as np
import math






class Engine(Thread):
    def __init__(self, host):
      Thread.__init__(self)
      self.host = host
      # self.song = host.song
      self.state = host.state
      self.stopped = Event()
      self.should_wait = False

    def stop(self):
      self.stopped.set()

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

      if (host.is_debugging()):
          host.log(f'generating tokens ({playhead}/{len(hist_)} > {threshold})')
          host.log(f'requested length: {length} {unit} ({song.to_ticks(length, unit)} ticks)')

      # Generate sequence
      ticks = song.to_ticks(length, unit)
      final_length = song.from_ticks(ticks, host.get('input_unit'))
      host.log(f'request: host.model.generate(history, {final_length})')

      if final_length is None:
        host.log(f'error: trying to generate length {final_length}')
        return

      output = host.model.generate(history, final_length, voices)
      # host.log(f'{len(seq)} tokens were generated')

      host.log(output)
      host.log(f'len(output): {len(output)}')
      host.log(f'len(hist): {len(history)}')

      for i, v in enumerate(voices):
        output_ = output[i]
        hist_ = history[v]
        
        generated_length = len(output_) - len(hist_)
        host.state['history'][v] = output_[-max_len:]
        for event in output_[-generated_length:]:
          for message in host.decode(event, v):
              # song.add_message(host.state, message, v)
              host.song.add_message(host.state, message, v)
              # state['output_data'].tracks[v].append(message)

      # Update Playhead
      self.rewind(max(0, generated_length))

      host.set('is_generating',False)
      self.notify_wait(False)

      if (respond):
        # host.dump_history()
        host.notify_task_complete()

    def rewind(self, number):
      host = self.host
      playhead = host.state['playhead']
      target_playhead = playhead - number
      new_playhead = max(target_playhead, 0)
      if (host.is_debugging()):
          host.log(f'Rewinding Playhead ({playhead} -> {new_playhead})')

      host.state['playhead'] = new_playhead

    def generate_in_background(self):
      Thread(target=self.host.generate).start()
      # self.should_wait = False

    def run(self):
      host = self.host

      # self.generate_in_background()
      while not self.stopped.wait(self.state['until_next_event']):
        if (host.is_running() == True and self.should_wait == False):
          
          for voice in host.get('voices'):
            self.host.process_next_token(voice)

          voice = host.get('voices')[0]
          if (host.must_generate(voice)):
            self.generate_in_background()


    # def start_metronome(self):
      # pass
      # Thread(target=self.run_metronome).start()
    
    # def run_metronome(self):
    #   # TODO: step to time is track logic
    #   while not self.stopped.wait(60/self.state['bpm']/4):
    #     if (self.state['is_running'] == True):
    #       self.host.play(0,'hh')

    def notify_wait(self,should=True):
      self.should_wait = should






# TODO: Extract stateful code to host
# class Clock(Thread):
#     def __init__(self, host):
#       Thread.__init__(self)
#       self.state = host.state
#       self.host = host
#       self.stopped = Event()
#       self.should_wait = False
#       # self.start_metronome()
#       # TODO: Set delays
#       # host.set('delays', [0 for voice in host.get('voices')])

#     # def bind(self,server_state):
#     #   self.state = server_state
#     #   self.state['playhead'] = 0

#     def stop(self):
#       self.stopped.set()

#     def generate_in_background(self):
#       Thread(target=self.host.generate).start()
#       # self.should_wait = False

#     def run(self):
#       host = self.host

#       # self.generate_in_background()
#       while not self.stopped.wait(self.state['until_next_event']):
#         if (host.is_running() == True and self.should_wait == False):
          
#           for voice in host.get('voices'):
#             self.host.process_next_token(voice)

#           voice = host.get('voices')[0]
#           if (host.must_generate(voice)):
#             self.generate_in_background()


#     def start_metronome(self):
#       pass
#       # Thread(target=self.run_metronome).start()
    
#     def run_metronome(self):
#       # TODO: step to time is host logic
#       while not self.stopped.wait(60/self.state['bpm']/4):
#         if (self.state['is_running'] == True):
#           self.host.play(0,'hh')

#     def notify_wait(self,should=True):
#       self.should_wait = should
