import os
# import gc # TODO: clear 
import sys
import mido
import data
from os.path import normpath, join
from mido import MidiFile, MidiTrack, Message, MetaMessage, tempo2bpm
from datetime import datetime

# TODO: Make FastEnum
units = ['measures', 'bars', 'seconds', 'ticks', 'beats']

# Sets
# - playhead
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
        if data is not None:
          for t in self.data.tracks: t.clear()
          self.data.tracks.clear()

        self.data = MidiFile(ticks_per_beat=self.host.get('ticks_per_beat')) # TODO: internal state
        # gc.collect()

        # TODO: Internal State
        host = self.host
        host.set('playhead', 0)
        host.set('last_end_time', 0) # Channels
        if host.get('midi_tempo') is None: host.set('midi_tempo', mido.bpm2tempo(host.get('bpm'))) 


    # TODO: load()
    # TODO: save

    def empty(self):
        """ Returns true if song has no musical data
        """
        return len(self.data.tracks) < 1 or all(len(t) < 1 for t in self.data.tracks)

    def save(self, filename=f'session-{datetime.now()}'):
        """ Save the output generated by a model as a midi file
            Receives: the mido-encoded representation of the improvisation history
        """
        data = self.data

        # TODO: Create wrapper for output dir
        filename = join('/output', f'{filename}.mid')

        # TODO: throw an event instead of callling host
        host = self.host
        if (self.empty()):
            host.io.log(f'[error] No data to write in file: {filename}')
            return
        host.io.log(f'Saving data to: {filename}')

        # mid.save(normpath(filename))
        data.save(normpath(filename))
        while not os.path.exists(filename):
            # print(f'{filename} does not exist')
            pass

        # TODO: throw an event instead of callling host
        host = self.host
        if host is not None: host.bridge.notify_task_complete()










































    def get_buffer(self, ticks):
        # TODO:
        # self.data.messages
        # reverse
        # takewhile < ticks
        # reverse
        pass










    # TODO: delete output_data, save file data internally
    def add_message(self, state, message, voice = 0):
        ''' Adds a Mido message to a voice in the state's 'output_data' '''
        host = self.host
        if (host.get('output_data') is None): self.init_conductor(host.state)
        host.state['output_data'].tracks[voice].append(message)


    def load_midi(self, host, filename, max_len=None, max_len_units=None):
        """ Load midi from a file onto the host's history
            optionally cropping it to a max_ticks length
        """
        
        # self.host.io.log(f' loading {name}')
        # self.host.song.load_midi(self, name, barcount, 'bars')

        if self.host.get('batch_mode'): self.host.bridge.notify_task_complete()
        if not any(self.host.get('history')): self.host.set("history",[[]])
        # self.host.io.log(f' loaded {sum([len(v) for v in self.host.get("history")])} tokens to history')

        mid = MidiFile(filename)
        host.reset()
        host.set('ticks_per_beat', mid.ticks_per_beat)

        # output_data = host.state['output_data']
        # output_data = MidiFile(ticks_per_beat=host.state['ticks_per_beat'])
        self.init_conductor(host.state)
        output_data = host.state['output_data']
        history = []

        # Add Conductor Track if not present
        if len(mid.tracks) < 2:
          output_data.tracks.append(MidiTrack())
          history.append([])

        for i, file_track in enumerate(mid.tracks):
        # for file_track in mid.tracks:
          index = i + 1 if len(mid.tracks) < 2 else i
          ticks_so_far = 0
          offset = 0
          history.append([])
          
          # is_new_track = i >= len(output_data.tracks)
          # track = MidiTrack() if is_new_track else output_data.tracks[i]
          track = MidiTrack()

          for msg in file_track:
            # print(f'host.to_ticks({max_len}, {max_len_units}) = {host.to_ticks(max_len, max_len_units)}')
            if max_len is not None: 
              max_ticks = host.to_ticks(max_len, max_len_units) + offset
              if ticks_so_far >= max_ticks:
                continue

            track.append(msg)

            if msg.is_meta:
                if msg.type == 'track_name':
                    host.set('track_name', msg.name)
                if msg.type == 'set_tempo':
                    host.set('midi_tempo', msg.tempo)
                    host.set('bpm', tempo2bpm(msg.tempo))
                if msg.type == 'time_signature':
                    host.set('time_signature_numerator', msg.numerator)
                    host.set('time_signature_denominator', msg.denominator)
                continue
            
            if (ticks_so_far == 0 and msg.time > 0): offset = msg.time
            ticks_so_far = ticks_so_far + msg.time

            if msg.type in ['note_on']: history[index].append(host.model.encode(msg))
          
          # if is_new_track: output_data.tracks.append(track)
          output_data.tracks.append(track)

        host.set('history', history, silent=True)
        host.set('voices', host.get('voices'))
        return history





    # Depr: move relevant code to reset
    def init_conductor(self, state):
        track = MidiTrack()
        track.append(MetaMessage('track_name', name=state['track_name']))
        track.append(MetaMessage('set_tempo', tempo=state['midi_tempo']))
        track.append(MetaMessage('time_signature',
              numerator=state['time_signature_numerator'],
            denominator=state['time_signature_denominator']))
        self.data.tracks.append(track)






    # TODO: This is a lot of code that does similar stuff
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



    # Query Methods

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
