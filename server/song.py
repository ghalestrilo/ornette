import os
import gc # TODO: clear 
import sys
import mido
from os.path import normpath, join
from mido import MidiFile, MidiTrack, Message, MetaMessage, tempo2bpm
import mido
from math import floor
from datetime import datetime
from itertools import takewhile

from channel import Channel

# TODO: Make FastEnum
units = ['measures', 'bars', 'seconds', 'ticks', 'beats']

# - generation_start
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
      print(f'len(messages): {len(self.messages)}')
      return self.messages[index] if index < len(self.messages) else None

    def reset(self, initialize_output_tracks=True):
        if self.data is not None:
          for t in self.data.tracks: t.clear()
          self.data.tracks.clear()


        # TODO: Internal State
        host = self.host
        self.data = MidiFile(ticks_per_beat=host.get('ticks_per_beat'))
        host.set('playhead', 0)
        host.set('generation_start', 0) # Channels
        # host.set('output_tracks', [0])
        if self.get_tempo() is None: host.set('tempo', mido.bpm2tempo(120))

    def empty(self):
        """ Returns true if the song has no musical data """
        return len(self.data.tracks) < 1 or all(len(t) < 1 for t in self.data.tracks)

    def save(self, filename=f'session-{datetime.now()}'):
        """ Save the current MIDI data to a file """
        data = self.data

        for track in data.tracks:
          for msg in track:
            if hasattr(msg,'time'): msg.time = int(round(msg.time))

        if not any(filename.endswith(ext) for ext in ['.mid', '.midi']):
          filename += '.mid'
        filename = join('/output', filename)

        # TODO: throw an event instead of callling host
        host = self.host
        if (self.empty()):
            host.io.log(f'[error] No data to write in file: {filename}')
            return
        host.io.log(f'Saving data to: {filename}')
        host.io.log(f'Total length: {self.total_ticks()} ticks = {self.total_length("bars")} bars = {self.total_length("seconds")}s')

        data.save(normpath(filename))
        while not os.path.exists(filename): pass

        # TODO: throw an event instead of callling host
        host = self.host
        if host is not None: host.bridge.notify_task_complete()

    def update_messages(self):
      self.messages = list(msg for msg in self.data)

    def append(self, message, track_number):
        """ Adds a message to a track """
        tracks = self.data.tracks
        if self.empty(): self.init_conductor()
        while not len(tracks) > track_number:
          self.data.add_track(f'Track {len(tracks)}')

        for msg in tracks[track_number]:
          if msg.type == 'end_of_track': tracks[track_number].remove(msg)
        tracks[track_number].append(message)
        tracks[track_number].append(MetaMessage('end_of_track', time=0))

    def load(self, filename, max_len=None, max_len_units='ticks'):
        """ Load midi from a file onto the host's history
            optionally cropping it to a max_ticks length
        """
        mid = MidiFile(filename) # This checks if the file exists, before anything

        self.host.set('ticks_per_beat', mid.ticks_per_beat)
        self.reset()
        max_ticks = self.to_ticks(max_len or 0, max_len_units)

        tempo_set = False
        for i, file_track in enumerate(mid.tracks):
          ticks_so_far = 0  # Ticks from first note event onwards
          useless_ticks = 0 # Ticks from beginning, before first note event
          first_note_found = False
          
          # Create new track if necessary
          if i >= len(self.data.tracks):
            self.data.add_track(file_track.name)

          for msg in file_track:
            # Detect first note_on event
            if not first_note_found and msg.type == 'note_on':
              first_note_found = True
              msg.time = 0
            
            # Accumulate time
            if first_note_found:
              ticks_so_far += msg.time
            else:
              useless_ticks += msg.time

            # Stop reading
            if max_len is not None: 
              if i == 0 and (useless_ticks + ticks_so_far): continue
              if first_note_found and ticks_so_far >= max_ticks:
                continue

            # Copy everything from first note on
            if first_note_found or msg.time == 0:
              self.data.tracks[i].append(msg)

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
            

        # Correct conductor header
        if any(self.data.tracks) and any(self.data.tracks[0]):
          for msg in self.data.tracks[0]:
            if msg.type == 'end_of_track':
              msg.time = 0
        
        # self.crop(max_len_units, 0, max_len)
        if max_len:
          self.pad(max_len, max_len_units)
        else:
          self.check_end_of_tracks()
        total_ticks = self.total_ticks()
        self.host.set('primer_ticks', total_ticks)
        self.host.set('generation_start', self.from_ticks(total_ticks, 'seconds'))
        self.host.io.log(f'total ticks loaded: {self.total_ticks()}')



    def drop_primer(self):
      ''' Remove primer from generated output '''
      primer_ticks = self.host.get('primer_ticks')
      # unit = 'beats'
      self.host.io.log('dropping primer')
      unit = self.host.get('input_unit')
      self.crop('ticks', primer_ticks)
      self.host.set('primer_ticks', 0)
      self.host.set('generation_start', self.total_length(unit))
      
      self.pad(self.host.get('generation_start'), unit)

    def total_ticks(self):
      # return int(round(sum(self.to_ticks(msg.time, 'seconds') for msg in self.data if not msg.is_meta)))
      return int(round(sum(self.to_ticks(msg.time, 'seconds') for msg in self.data if hasattr(msg, 'time'))))

    def total_length(self, unit='bars'):
      return self.from_ticks(self.total_ticks(), unit)

    def init_conductor(self):
        host = self.host
        if len(self.data.tracks): return
        track = MidiTrack()
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

        buffer_end = self.total_ticks()
        buffer_start = max(0,buffer_end - ticks)
        self.host.io.log(f'buffer: {buffer_start} to {buffer_end} ({buffer_end - buffer_start} of {ticks})')
        ret = [self.crop_track(track,'ticks',buffer_start,buffer_end) for track in self.data.tracks]
        return ret


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








    def crop_track(self, track, unit, start, end):
      new_track = track.copy()
      # Copy track headers
      is_header_msg = lambda msg: msg.is_meta and msg.time == 0
      header = list(takewhile(is_header_msg, track)).copy()
      time = 0
      start_index = 0
      end_index = 0

      # Find start and end of crop
      for msg_index, msg in enumerate(new_track):
        end_index = msg_index + 1
        time += msg.time
        if start >= time: start_index = msg_index + 1
        if time > end: break

      cropped_track = track[start_index:end_index].copy()

      new_track.clear()
      for msg in header: new_track.append(msg.copy())
      for msg in cropped_track: new_track.append(msg.copy())

      # print('self.get_track_length(new_track)')
      # print(self.get_track_length(new_track), self.to_ticks(end, unit))
      desired_length_ticks = self.to_ticks(end, unit) - self.to_ticks(start, unit)
      excess = 1
      while excess:
        if any(new_track):
          excess = self.get_track_length(new_track) - desired_length_ticks
          excess = max(0, excess)
          
          if new_track[-1].time >= excess:
            old_time = new_track[-1].time
            new_track[-1].time = int(round(new_track[-1].time - excess))
            if old_time == new_track[-1].time: break
            # if old_time == new_track[-1].time: excess = 0
          else: new_track.remove(new_track[-1])
        else: 
          break

      return new_track



    def crop(self, unit, _start=None, _end=None):
      """ Crops the current song between a specified _start and _end times
          unit: The cropping unit (one of 'ticks', 'bars', 'measures', 'beats', 'seconds')
      """
      
      start_time = self.to_ticks(_start or 0, unit)
      end_time = self.to_ticks(_end, unit) if _end else self.total_ticks()

      log = self.host.io.log

      if start_time > end_time:
        log(f'Cropping start_time ({start_time}) is bigger than end_time ({end_time}), aborting.')
        return

      # Set crop bounds
      start_time = max(start_time, 0)
      end_time = min(end_time, self.total_ticks())

      log(f'Cropping between {start_time} and {end_time} ticks ({end_time - start_time})')

      for i, track in enumerate(self.data.tracks):
        if i == 0 and self.host.get('preserve_conductor') == True: continue
        self.data.tracks[i] = self.crop_track(track, unit, start_time, end_time)


    def get_track_length(self, track):
      # return sum(msg.time for msg in track if not msg.is_meta)
      return sum([msg.time for msg in track if hasattr(msg, 'time')])

    # TODO: Units
    def get_measure_length(self, unit):
        length = 1
        if (unit == 'measures'): return length
        return self.get_beat_length(length, unit)







    def show(self):
      data = self.data
      self.host.io.log(data)
      # self.host.io.log(f'total ticks: {self.host.song.total_ticks()}')
      for track in data.tracks:
        self.host.io.log(track)
        for msg in track:
          self.host.io.log(f'  {msg}')

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

    def get_buffer_length(self, unit='bars', truncate=False):

      # Total Song Time
      total_song_time = self.from_ticks(self.total_ticks(), unit)

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






    # TODO: WIP

    def pad(self, length, unit):
      """ places `end_of_track` messages that ensure tracks match expected length """
      total_expected_ticks = self.to_ticks(length, unit)
      
      for i, track in enumerate(self.data.tracks):
        end_of_tracks = [msg for msg in track if msg.type == 'end_of_track']
        for eot in end_of_tracks: track.remove(eot)
        total_track_ticks = self.get_track_length(track)

        # New implementation
        padlen = max(0, total_expected_ticks - total_track_ticks) if i else 0
        self.data.tracks[i].append(MetaMessage('end_of_track', time=int(round(padlen))))


    def check_end_of_tracks(self):
      self.pad(self.host.get('generation_start'), 'beats')