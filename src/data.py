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
from mido import bpm2tempo


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
                print(k, ' -> ', v)


def load_model(host, checkpoint=None):
    if checkpoint is None:
        print("Please provide a checkpoint for the model to load")
        exit(-1)

    model_path = '/model'
    load_folder(model_path)
    from ornette import OrnetteModule
    return OrnetteModule(host, checkpoint=checkpoint)


def add_message(state, message):
    if (state['output_data'] is None):
      state['output_data'] = MidiTrack()
      # TODO: Metamessages

    state['output_data'].append(message)


def load_midi(host, filename, max_len=None, max_len_units=None):
    """ Load midi from a file onto the host's history
        optionally cropping it to a max_ticks length
    """
    mid = MidiFile(filename)

    host.reset()

    host.set('ticks_per_beat', mid.ticks_per_beat)

    # This logic 'could' go into the host
    history = []
    
    for i, track in enumerate(mid.tracks):
      ticks_so_far = 0
      offset = 0
      history.append([])
      # history[i].append(host.model.encode(msg))
      for msg in track:
        max_ticks = host.to_ticks(max_len, max_len_units) + offset
        if max_len is not None and ticks_so_far >= max_ticks:
          continue

        host.state['output_data'].append(msg)

        if msg.is_meta:
          if msg.type == 'track_name':
              host.set('track_name', msg.name)
          if msg.type == 'set_tempo':
              host.set('bpm', msg.tempo)
          if msg.type == 'time_signature':
              host.set('time_signature_numerator', msg.numerator)
              host.set('time_signature_denominator', msg.denominator)
          continue
        
        if (ticks_so_far == 0 and msg.time > 0): offset = msg.time
        ticks_so_far = ticks_so_far + msg.time

        if msg.type in ['note_on']: history[i].append(host.model.encode(msg))

    host.set('history',[voice for voice in history if any(voice)])
    return history


# load_bars(start, end):
#   carrega midi para a memória
#   calcula comprimento (s) de cada compasso
#   ignora as primeiras tokens até o começo do compasso desejado
#       - pula token, acumula o tempo
#   carrega para o histórico tokens até o fim do último compasso desejado
#       - salva token, acumula o tempo


def save_output(filename=None, data=[], tpb=960, host=None):
    """ Save the output generated by a model as a midi file
        Receives: the mido-encoded representation of the improvisation history
    """

    if (filename is None):
        filename = f'session-{datetime.now()}.mid'

    filename = join(os.path.curdir, 'output',f'{filename}.mid')

    if (data is None or len(data) < 1):
        print(f'[error] No data to write in file: {filename}')
        return

    print(f'Saving data to: {filename}')

    mid = MidiFile(ticks_per_beat=tpb)
    track = MidiTrack()
    for msg in data: track.append(msg)
    mid.tracks.append(track) 
    track.append(MetaMessage('end_of_track'))
    mid.save(normpath(filename))
    while not os.path.exists(filename):
        # print(f'{filename} does not exist')
        pass
    if host is not None: host.notify_task_complete()


def init_output_data(state):
    if state['output_data'] is None: state['output_data'] = []
    else: state['output_data'].clear()

    state['output_data'] = state['output_data'] + [
      MetaMessage('track_name', name=state['track_name']),
      MetaMessage('set_tempo', tempo=state['midi_tempo']),
      MetaMessage('time_signature',
            numerator=state['time_signature_numerator'],
            denominator=state['time_signature_denominator']),
    ]

    
    
