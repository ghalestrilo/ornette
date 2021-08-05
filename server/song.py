import os
import gc # TODO: clear 
import sys
import mido
from os.path import normpath, join
from mido import MidiFile, MidiTrack, Message, MetaMessage, tempo2bpm
import mido
from math import floor
from datetime import datetime

from channel import Channel

# TODO: Make FastEnum
units = ['measures', 'bars', 'seconds', 'ticks', 'beats']

# - last_end_time
# - history
# - ticks_per_beat
# - track_name
# - tempo
# - bpm
# - time_signature_numerator
# - time_signature_denominator
# - output_tracks

# Gets
# - output_data
# - batch_mode
# - history
# - time_signature_numerator
# - time_signature_denominator
# - tempo
# - bpm
# - ticks_per_beat
# - missing_beats
# - input_unit
# - output_tracks

class Song():
    def __init__(self, host, data=None):
        self.host = host
        self.state = host.state
        self.data = data
        self.channels = []
        self.messages = []
        self.reset()

    # TODO: Deprecate
    def play(self):
      return self.data.play()

    def getmsg(self,index):
      return self.messages[index] if index < len(self.messages) else None

    def reset(self, initialize_output_tracks=True):
        if self.data is not None:
          for t in self.data.tracks: t.clear()
          self.data.tracks.clear()


        # TODO: Internal State
        host = self.host
        self.data = MidiFile(ticks_per_beat=host.get('ticks_per_beat'))
        host.set('playhead', 0)
        host.set('last_end_time', 0) # Channels
        if self.get_tempo() is None: host.set('tempo', mido.bpm2tempo(120))

    def empty(self):
        """ Returns true if the song has no musical data """
        return len(self.data.tracks) < 1 or all(len(t) < 1 for t in self.data.tracks)

    def save(self, filename=f'session-{datetime.now()}'):
        """ Save the current MIDI data to a file """
        data = self.data

        # TODO: Create wrapper for output dir
        filename = join('/output', f'{filename}.mid')

        # TODO: throw an event instead of callling host
        host = self.host
        if (self.empty()):
            host.io.log(f'[error] No data to write in file: {filename}')
            return
        host.io.log(f'Saving data to: {filename}')

        data.save(normpath(filename))
        while not os.path.exists(filename): pass

        # TODO: throw an event instead of callling host
        host = self.host
        if host is not None: host.bridge.notify_task_complete()

    def append(self, message, track):
        """ Adds a message to a track """
        if self.empty(): self.init_conductor()
        while not len(self.data.tracks) > track:
          self.data.add_track(f'Track {len(self.data.tracks)}')

        self.data.tracks[track].append(message)

        # TODO: Switch mode (append/extend)
        self.messages = [msg for msg in self.data]

    def load(self, filename, max_len=None, max_len_units=None):
        """ Load midi from a file onto the host's history
            optionally cropping it to a max_ticks length
        """
        mid = MidiFile(filename) # This checks if the file exists, before anything

        self.host.set('ticks_per_beat', mid.ticks_per_beat)
        self.reset()

        for i, file_track in enumerate(mid.tracks):
          ticks_so_far = 0
          offset = 0
          
          track = mido.MidiTrack()

          for msg in file_track:
            if max_len is not None: 
              max_ticks = self.to_ticks(max_len, max_len_units) + offset
              if ticks_so_far >= max_ticks:
                continue

            track.append(msg)

            tempo_set = False

            if msg.is_meta:
                if msg.type == 'track_name':
                    self.host.set('track_name', msg.name)
                if msg.type == 'set_tempo' and not tempo_set:
                    tempo_set = True
                    self.host.set('tempo', msg.tempo)
                if msg.type == 'time_signature':
                    self.host.set('time_signature_numerator', msg.numerator)
                    self.host.set('time_signature_denominator', msg.denominator)
                    self.host.set('clocks_per_click', msg.clocks_per_click)
                    self.host.set('steps_per_quarter', msg.notated_32nd_notes_per_beat)
                continue
            
            if (ticks_so_far == 0 and msg.time > 0): offset = msg.time
            ticks_so_far = ticks_so_far + msg.time
          self.data.tracks.append(track)


    def init_conductor(self):
        host = self.host
        if len(self.data.tracks): return
        track = MidiTrack('Conductor')
        track.append(MetaMessage('track_name', name=host.get('track_name')))
        track.append(MetaMessage('set_tempo', tempo=self.get_tempo()))
        track.append(MetaMessage('time_signature',
              numerator=host.get('time_signature_numerator'),
            denominator=host.get('time_signature_denominator')))
        self.data.tracks.append(track)

    def buffer(self, ticks):
        """ Returns the last messages of each track
            within a limit of <ticks>
        """

        # TODO: take conductor into acccount
        out = []

        for track in self.data.tracks:
          curticks = 0
          out.append([])

          for msg in reversed(list(track)):
            # print(f'msg: {msg}')
            if curticks > ticks: break
            if isinstance(msg,str): continue

            # Only return note_on and note_off messages
            # TODO: accumulate time from other messages
            if msg.is_meta:
              self.host.io.log(f'ignoring {msg}')
              continue
            if msg.type not in ['note_on', 'note_off']: continue
            curticks += msg.time
            out[-1].append(msg)

        # return out
        out = [list(reversed(x)) for x in out]
        out = [list(self.data.tracks[0])] + out[1:]
        return out


    def get_channel(self, idx):
      default_instrument = [ 's', 'superpiano', 'velocity', '0.4' ]
      while idx >= len(self.channels):
        self.host.io.log(f'Adding new channel: {len(self.channels)}')
        self.channels.append(Channel(len(self.channels), default_instrument, self.host))
      return self.channels[idx]


    def perform(self, message, idx=0):
      if message.type in ['note_on', 'note_off']:
        chan = self.host.song.get_channel(message.channel)
        if chan: chan.play(message)


    def crop(self, unit, _start, _end):
      """ Crops the current song between a specified _start and _end times
          unit: The cropping unit (one of 'ticks', 'bars', 'measures', 'beats', 'seconds')
      """
      start_time = self.to_ticks(_start, unit)
      end_time = self.to_ticks(_end, unit)

      

      log = self.host.io.log


      log(f'Cropping between {start_time} and {end_time} ticks ({end_time - start_time})')

      for i, track in enumerate(self.data.tracks[1:]):
        log(f'"{track.name}" initial length = {self.get_track_length(track)}')
        time = 0
        start_index = 0
        end_index = 0
        for msg_index, msg in enumerate(track):
          time += msg.time
          end_index = msg_index

          if time <= start_time: start_index = msg_index
          if time > end_time: break

        track = track[start_index:end_index] # here, +2 with (1, 2) works
        self.data.tracks[i + 1] = track

        log(f'"{track.name}" final length = {self.get_track_length(track)}')

    def get_track_length(self, track):
      return sum(msg.time for msg in track if not msg.is_meta) 


    # TODO: Units
    def get_measure_length(self, unit):
        length = 1
        if (unit == 'measures'): return length
        return self.get_beat_length(length, unit)









    # Time Conversion
    def get_beat_length(self, length, unit):
        host = self.host
        length = length * 4 * host.get('time_signature_numerator') / host.get('time_signature_denominator')
        if (unit == 'beats'): return length

        length = length * host.get('ticks_per_beat')
        if (unit == 'ticks'): return length
        
        if (unit == 'seconds'):
          return mido.tick2second(length,
            host.get('ticks_per_beat'),
            self.get_tempo())
        return None

    def convert(self, length, _from, _to):
      ticks = self.to_ticks(length, _from)
      final_length = self.from_ticks(ticks, _to)
      return final_length

    def get_time_signature(self):
      return 4 * self.host.get('time_signature_numerator') / self.host.get('time_signature_denominator')
      # return 4

    def from_ticks(self, length, unit):
        host = self.host
        if unit not in units:
          host.io.log(f'unknown unit: \'{unit}\'')
        if (length is None): return None
        if (unit == 'ticks'): return length

        if (unit == 'seconds'):
          return mido.tick2second(length,
            host.get('ticks_per_beat'),
            self.get_tempo())

        length = length / host.get('ticks_per_beat')
        if (unit == 'beats'):
          return length

        length = length / self.get_time_signature()
        if (unit in ['measures', 'bars']): 
          return length

        return None

    def get_bpm(self):
      tempo = self.get_tempo()
      return int(round(tempo2bpm(tempo)))

    def get_tempo(self):
      return self.host.get('tempo')

    def to_ticks(self, length, unit):
        host = self.host
        if unit not in units:
          host.io.log(f'unknown unit: \'{unit}\'')
        if (length is None): return None
        if (unit == 'seconds'): return mido.second2tick(length,
            host.get('ticks_per_beat'),
            self.get_tempo())

        if (unit == 'ticks'): return int(round(length))

        length = length * host.get('ticks_per_beat')
        if (unit == 'beats'): return int(round(length))

        length = length * self.get_time_signature()
        if (unit in ['measures', 'bars']): return int(round(length))
        return None


    # Move to... bridge? IO? maybe
    def time_debug(self, measures=1):
      host = self.host
      ticks = self.to_ticks(measures, "measures")
      beats = self.from_ticks(ticks, "beats")
      ticks = self.from_ticks(ticks, "ticks")
      seconds = self.from_ticks(ticks, "seconds")
      gtf = self.to_ticks
      host.io.log('Time info:')
      host.io.log(f'   {measures} measure = {beats} beats = {ticks} ticks = {seconds} seconds')
      host.io.log(f'   {gtf(1, "measures")} == {gtf(beats, "beats")} == {gtf(ticks, "ticks")} == {gtf(seconds, "seconds")}')
      host.io.log(f'   tempo: {self.get_tempo()} | bpm: {self.get_bpm()} | tpb: {host.get("ticks_per_beat")}')
      host.io.log(f'   model input:  {host.get("input_length")} {host.get("input_unit")} ')
      host.io.log(f'   model output: {host.get("output_length")} {host.get("output_unit")} ')

    # TODO: Get Buffer Length:
    def get_buffer_length(self, unit='bars', truncate=False):

      # Total Song Time
      total_song_time = self.convert(self.data.length, 'seconds', unit)

      # Requested Input
      input_length = self.convert(self.host.get('input_length'), self.host.get('input_unit'), unit)

      # Whichever is lowest
      length = min(total_song_time, input_length)
      if truncate: length = floor(length)
      return length






    # TODO: When are these used? Are they necessary?

    # Move "Channels" to bridge/backend (rename: get_channel)
    def get_voice(self, voice_index=None):
      if voice_index is None:
        voice_index = self.host.get('output_tracks')[0]
      return self.host.get('output_tracks')[voice_index]