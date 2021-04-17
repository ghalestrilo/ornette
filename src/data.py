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

from os.path import normpath
from mido import MidiFile, MidiTrack


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


def load_midi(host, filename):
    print(f'loading file: {filename}')
    mid = MidiFile(filename)

    host.reset()

    # This logic 'could' go into the host
    host.state['history'] = []
    for i, track in enumerate(mid.tracks):
      host.state['history'].append([])
      for msg in track:
        if msg.is_meta: continue
        host.state['history'][i].append(host.model.encode(msg))

    host.print('history')


# load_bars(start, end):
#   carrega midi para a memória
#   calcula comprimento (s) de cada compasso
#   ignora as primeiras tokens até o começo do compasso desejado
#       - pula token, acumula o tempo
#   carrega para o histórico tokens até o fim do último compasso desejado
#       - salva token, acumula o tempo


def save_output(filename=None, data=[]):
    """ Save the output generated by a model as a midi file
        Receives: the mido-encoded representation of the improvisation history
    """

    if (filename is None):
        filename = f'session-{datetime.now()}.mid'

    filename = normpath(f'output/{filename}.mid')

    if (data is None or len(data) < 1):
        print(f'[error] No data to write in file: {filename}')
        return

    print(f'Saving data to: {filename}')

    mid = MidiFile()
    mid.tracks.append(data)
    mid.save(normpath(filename))




















# Feature Extraction

units = ['bars', 'seconds', 'notes', 'events']

def length(host, sequence, unit='bars'):
  if (unit not in units):
      print(f'[error] unknown unit: {unit}')
      return

# (SketchVAE) loss: cross entropy loss of the output with the ground-truth
# (SketchVAE) pitch accuracy: comparing only the pitch tokens between each generation and the ground truth (whether the model generates the correct pitch in the correct position)
# (SketchVAE) rhythm accuracy: comparing the duration and onset (regardless of what pitches it generates).

def length(host, sequence, unit='bars'):
  if (unit not in units):
      print(f'[error] unknown unit: {unit}')
      return

def pitch_count(sequence):
  # Calculate histogram
  # return len(histogram)
  pass

def average_pitch_count_per_bar(host, sequence):
  # (RL-Duet) PC/bar: Pitch count per bar (número de notas distintas por compasso)
  # return len(histogram)
  pass

def average_pitch_interval(host, sequence):
  # (RL-Duet) PI: Intervalo médio entre pitches
  # Pergunta: consecutivos apenas ou NxN
  pass

def average_pitch_interval(host, sequence):
  # Pergunta: consecutivos apenas ou NxN
  pass

def average_inter_onset_interval(host, sequence):
  # (RL-Duet) IOI: Intervalo médio entre onsets (?)
  # Pergunta: consecutivos apenas ou NxN
  pass

def get_pitch_histogram(sequence):
  # (RL-Duet) Histograma de Pitches (Notas) - Diferença de Wasserstein contra Ground-Truth
  pass

def get_length_histogram(sequence):
  # (RL-Duet) Histograma de Comprimento - Diferença de Wasserstein contra Ground-Truth
  pass

def for_each_bar(host, sequence, method):
  # receives a function, builds a dataframe using provided method for each bar of the sequence
  pass


# Opcionalmente, generate(count=1, unit='bars') # enum unit: ['bar','note','event','seconds']
# - generate_bars(number=1):
#     calcula o tempo de um compasso
# 
# - length(filename, scale='bar'): # enum unit: ['bar','note','event','seconds']
#     retorna o comprimento dos dados contidos no arquivo na unidade desejada