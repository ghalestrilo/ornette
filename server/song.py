import os
# import gc # TODO: clear 
import sys
import mido
from os.path import normpath, join
from mido import MidiFile, MidiTrack, Message, MetaMessage, tempo2bpm
from datetime import datetime

# TODO: Make FastEnum
units = ['measures', 'bars', 'seconds', 'ticks', 'beats']

# - last_end_time
# - history
# - ticks_per_beat
# - track_name
# - midi_tempo
# - bpm
# - time_signature_numerator
# - time_signature_denominator
# - voices

# Gets
# - output_data
# - batch_mode
# - history
# - time_signature_numerator
# - time_signature_denominator
# - midi_tempo
# - bpm
# - ticks_per_beat
# - missing_beats
# - input_unit
# - voices

class Song():
    def __init__(self, host, data=None):
        self.host = host
        self.state = host.state
        self.data = data
        self.channels = []
        self.reset()

    def reset(self):
        if self.data is not None:
          for t in self.data.tracks: t.clear()
          self.data.tracks.clear()

        self.data = MidiFile(ticks_per_beat=self.host.get('ticks_per_beat')) # TODO: internal state
        # gc.collect()

        # TODO: Internal State
        host = self.host
        host.set('playhead', 0)
        host.set('last_end_time', 0) # Channels
        if host.get('midi_tempo') is None: host.set('midi_tempo', mido.bpm2tempo(host.get('bpm'))) 

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

    def load(self, filename, max_len=None, max_len_units=None):
        """ Load midi from a file onto the host's history
            optionally cropping it to a max_ticks length
        """
        mid = MidiFile(filename) # This checks if the file exists, before anything

        self.reset()
        self.host.set('ticks_per_beat', mid.ticks_per_beat) # TODO: Set self
        # if self.host.get('batch_mode'): self.host.bridge.notify_task_complete()

        for i, file_track in enumerate(mid.tracks):
          # index = i + 1 if len(mid.tracks) < 2 else i
          ticks_so_far = 0
          offset = 0
          
          track = MidiTrack()

          for msg in file_track:
            if max_len is not None: 
              max_ticks = self.to_ticks(max_len, max_len_units) + offset
              if ticks_so_far >= max_ticks:
                continue

            track.append(msg)

            if msg.is_meta:
                if msg.type == 'track_name':
                    self.host.set('track_name', msg.name)
                if msg.type == 'set_tempo':
                    self.host.set('midi_tempo', msg.tempo)
                    self.host.set('bpm', tempo2bpm(msg.tempo))
                if msg.type == 'time_signature':
                    self.host.set('time_signature_numerator', msg.numerator)
                    self.host.set('time_signature_denominator', msg.denominator)
                continue
            
            if (ticks_so_far == 0 and msg.time > 0): offset = msg.time
            ticks_so_far = ticks_so_far + msg.time
          self.data.tracks.append(track)


    def init_conductor(self):
        host = self.host
        if len(self.data.tracks): return
        track = MidiTrack()
        track.append(MetaMessage('track_name', name=host.get('track_name')))
        track.append(MetaMessage('set_tempo', tempo=host.get('midi_tempo')))
        track.append(MetaMessage('time_signature',
              numerator=host.get('time_signature_numerator'),
            denominator=host.get('time_signature_denominator')))
        self.data.tracks.append(track)

    def buffer(self, ticks):
        # TODO: take conductor into acccount
        # return [:1] + [crop(t, ticks) for t in self.data.tracks[1:]]
        out = []

        for track in self.data.tracks:
          curticks = 0
          out.append([])

          for msg in reversed(list(track)):
            if curticks > ticks: break
            curticks += msg.time
            out[-1].append(msg)

        return out
        # return [ticks_from_end(t, ticks) for t in self.data.tracks]









    # TODO: Units
    def get_measure_length(self, unit):
        length = 1
        if (unit == 'measures'): return length
        return self.get_beat_length(length, unit)

    def get_beat_length(self, length, unit):
        host = self.host
        length = length * 4 * host.get('time_signature_numerator') / host.get('time_signature_denominator')
        if (unit == 'beats'): return length

        length = length * host.state('ticks_per_beat')
        if (unit == 'ticks'): return length
        
        if (unit == 'seconds'):
          return mido.tick2second(length,
            host.state('ticks_per_beat'),
            host.state('midi_tempo'))
        return None

    # Time Conversion
    def from_ticks(self, length, unit):
        host = self.host
        if unit not in units:
          host.io.log(f'unknown unit: \'{unit}\'')
        if (length is None): return None
        if (unit == 'ticks'): return length

        if (unit == 'seconds'):
          return mido.tick2second(length,
            host.get('ticks_per_beat'),
            host.get('midi_tempo'))

        length = length / host.get('ticks_per_beat')
        if (unit == 'beats'):
          return length

        length = length / (4 * host.get('time_signature_numerator') / host.get('time_signature_denominator'))
        if (unit in ['measures', 'bars']): 
          return length

        return None

    def to_ticks(self, length, unit):
        host = self.host
        if unit not in units:
          host.io.log(f'unknown unit: \'{unit}\'')
        if (length is None): return None
        if (unit == 'seconds'): return mido.second2tick(length,
            host.get('ticks_per_beat'),
            host.get('midi_tempo'))

        if (unit == 'ticks'): return length

        length = length * host.get('ticks_per_beat')
        if (unit == 'beats'): return length

        length = length * 4 * host.get('time_signature_numerator') / host.get('time_signature_denominator')
        if (unit in ['measures', 'bars']): return length
        return None


    # Move to... bridge? maybe
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
      host.io.log(f'   tempo: {host.get("midi_tempo")} | bpm: {host.get("bpm")} | tpb: {host.get("ticks_per_beat")}')
      host.io.log(f'   missing beats: {host.get("missing_beats")} | unit: {host.get("input_unit")}')








    # TODO: When are these used? Are they necessary?

    # Song (rename: get_channel)
    def get_voice(self, voice_index=None):
      if voice_index is None:
        voice_index = self.host.get('voices')[0]
      # print(f'voice_index: {voice_index}')
      return self.host.get('voices')[voice_index]

    # Song
    # TODO: get_voice(idx): return self.get('history')[voices[idx]] if idx < len(voices) && voices[idx] < len(self.get('history')) else None
    def has_history(self, voice_id=None):
      if voice_id is None:
        voice_id = self.host.get('voices')[0]
      hist = self.get_voice(voice_id)
      # return np.any(hist) and np.any(hist[0])
      # print(f'hist({self.host.get("voices")[0]}): {True if hist and any(hist) else False}')
      # print(hist)
      return True if hist and any(hist) else False
