# TODO: Rename: 'Loader'

# import tensorflow as tf
import yaml
import urllib.request as req
import os
import sys
from datetime import datetime

# Data: This module is responsible for managing data stored in the disk
# This includes:
#  - Model Checkpoints
#  - Datasets
#  - Outputs

from os.path import normpath, join
from mido import MidiFile, MidiTrack, Message, MetaMessage
from mido import tempo2bpm


def load_folder(name):
    sys.path.append(os.path.join(sys.path[0], name))


def download_checkpoint(name, url, force=False):
    checkpoint_dir = '/ckpt'
    ckptpath = normpath(f'{checkpoint_dir}/{name}')
    if os.path.exists(ckptpath) and not force:
        return
    response = req.urlopen(url, timeout=5)
    content = response.read()
    with open(ckptpath, 'wb') as f:
        f.write(content)
        f.close()


def prep_module():
    with open(normpath('/model/.ornette.yml')) as file:
        moduleconfig = yaml.load_all(file, Loader=yaml.FullLoader)
        for pair in moduleconfig:
            for k, v in pair.items():
                if k == "checkpoints":
                    for checkpoint_name, checkpoint_url in v.items():
                        print(
                            f'downloading  {checkpoint_name}, "{checkpoint_url}"')
                        download_checkpoint(
                            checkpoint_name, checkpoint_url, False)
                # print(k, ' -> ', v)


def load_model(host, checkpoint=None):
    if checkpoint is None:
        host.log("Please provide a checkpoint for the model to load")
        exit(-1)

    model_path = '/model'
    load_folder(model_path)
    from ornette import OrnetteModule
    return OrnetteModule(host, checkpoint=checkpoint)

















# TODO: Track module
def add_message(state, message, voice = 0):
    ''' Adds a Mido message to a voice in the state's 'output_data' '''
    if (state['output_data'] is None): init_output_data(state, True)
    # print(f'voice: {voice}')
    # print(f'len(tracks) {len(state["output_data"].tracks)}')
    state['output_data'].tracks[voice].append(message)


def load_midi(host, filename, max_len=None, max_len_units=None):
    """ Load midi from a file onto the host's history
        optionally cropping it to a max_ticks length
    """
    mid = MidiFile(filename)
    host.reset()
    host.set('ticks_per_beat', mid.ticks_per_beat)

    # output_data = host.state['output_data']
    # output_data = MidiFile(ticks_per_beat=host.state['ticks_per_beat'])
    init_output_data(host.state, conductor=False)
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


def save_output(filename=None, data=None, tpb=960, host=None):
    """ Save the output generated by a model as a midi file
        Receives: the mido-encoded representation of the improvisation history
    """

    if (filename is None):
        filename = f'session-{datetime.now()}.mid'

    filename = join(os.path.curdir, '/output',f'{filename}.mid')

    if (data is None or (max(len(track) for track in data.tracks)) < 1):
        host.log(f'[error] No data to write in file: {filename}')
        return

    host.log(f'Saving data to: {filename}')

    # mid = MidiFile(ticks_per_beat=tpb)
    # for output_track in data:
    #   track = MidiTrack()
    #   for msg in output_track: track.append(msg)
    #   track.append(MetaMessage('end_of_track'))
    #   mid.tracks.append(track) 

    # mid.save(normpath(filename))
    data.save(normpath(filename))
    while not os.path.exists(filename):
        # print(f'{filename} does not exist')
        pass
    if host is not None: host.notify_task_complete()


def init_output_data(state,conductor=True):
    # if state['output_data']: state['output_data'].clear()
    output = MidiFile(ticks_per_beat=state['ticks_per_beat'])

    # Create Conductor Track
    if conductor:
        track = MidiTrack()
        track.append(MetaMessage('track_name', name=state['track_name']))
        track.append(MetaMessage('set_tempo', tempo=state['midi_tempo']))
        track.append(MetaMessage('time_signature',
              numerator=state['time_signature_numerator'],
            denominator=state['time_signature_denominator']))
        output.tracks.append(track)

    state['output_data'] = output
#/ TODO: Track module