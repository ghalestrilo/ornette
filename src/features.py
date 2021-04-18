import mido
import pandas as pd
import numpy as np
from itertools import chain, takewhile, accumulate, count

# Extract Features


# Feature Extraction

units = ['bars', 'seconds', 'notes', 'events']

def get_features(midi_data=None):
  if (midi_data is None):
      print("no data passed to get_features")
      return

  # Extract Time Signature numerator
  signature = get_signature(midi_data)
  tempo = get_tempo(midi_data)
  bars = get_bars(midi_data)

  # Print Basic info
  track_1 = midi_data.tracks[1]
  print(f'length: {midi_data.length}')
  print(f'tempo: {tempo}')
  print(f'ticks_per_beat: {midi_data.ticks_per_beat}')
  print(f'signature: {signature}')
  print(f'bars: {len(bars)}')

  # print('\nFull Song Histograms')
  # for track in midi_data.tracks:
  #   print(get_pitch_histogram(track))

  print('\nFirst Bar:\n')
  # print('\n', get_pitch_histogram(track_1).head(40))
  # print('\n', get_length_histogram(track_1).head(40))
  # print('\n', get_pitch_intervals(track_1)[1:])
  # print('\n', get_note_histogram(track_1))
  # print('\n', get_inter_onset_histogram(track_1).head(40))

  # TODO: Build dataframe from this
  
  # print(f'\n\tmean pitch: {get_pitch_histogram(track_1).mean()}')
  # print(f'\tpitch classes: {pitch_count(track_1)}')
  # print(f'\tnote classes: {note_count(track_1)}')
  # print(f'\tmean note length: {get_length_histogram(track_1).mean()}')
  # print(f'\tmean pitch interval: {average_pitch_interval(track_1)}')
  # print(f'\tmean pitch interval (absolute): {average_absolute_pitch_interval(track_1)}')
  # print(f'\tmean pitch count per bar: {average_pitch_count_per_bar(bars)}')
  # print(f'\tmean ioi: {average_inter_onset_interval(track_1)}')
  

  bar_data = [get_bar_features(bar) for bar in bars]

  df = pd.DataFrame(bar_data,columns=get_feature_labels())
  print(df.head(20))

  # print(get_pitch_histogram(bars[1]).head(40))
  # df = pd.DataFrame([get_pitch_histogram(bar) for bar in bars], columns=['pitch_histograms'])
  # print(df.head())
  # ticks_per_beat.numerator
  return

def get_bar_features(bar):
  return [
    get_pitch_histogram(bar).mean(),
    pitch_count(bar),
    note_count(bar),
    get_length_histogram(bar).mean(),
    average_pitch_interval(bar),
    average_absolute_pitch_interval(bar),
    average_inter_onset_interval(bar)
  ]

def get_feature_labels():
  return [
    'avg_pitch',
    'pclasses',
    'nclasses',
    'avg_len',
    'avg_p_dist',
    'avg_p_dist_abs',
    'avg_ioi'
    ]

# NOTE: This returns only the first numerator (only works for constant time signature pieces)
def get_signature(midi_data):
  for msg in midi_data:
    if msg.is_meta:
      if msg.type == 'time_signature':
        return msg.numerator

def get_tempo(midi_data):
  for msg in midi_data:
    if msg.is_meta:
      if msg.type == 'set_tempo':
        return msg.tempo

def get_bars(midi_data):
  signature = get_signature(midi_data)
  tempo = get_tempo(midi_data)
  ticks = 0
  bars = [[]]
  for msg in midi_data:
    if not msg.is_meta:
      
      # print(f'{ticks} > {signature * midi_data.ticks_per_beat} ?')
      
      # Detect New Bar
      if ticks > (signature * midi_data.ticks_per_beat):
        bars.append([])
        ticks = 0
      
      bars[-1].append(msg)
      ticks += mido.second2tick(msg.time,midi_data.ticks_per_beat,tempo)

  return bars














def length(host, sequence, unit='bars'):
  if (unit not in units):
      print(f'[error] unknown unit: {unit}')
      return

# (SketchVAE) loss: cross entropy loss of the output with the ground-truth
# (SketchVAE) pitch accuracy: comparing only the pitch tokens between each generation and the ground truth (whether the model generates the correct pitch in the correct position)
# (SketchVAE) rhythm accuracy: comparing the duration and onset (regardless of what pitches it generates).

def note_count(sequence):
  ''' Like pitch count, but ignores octaves (only cares about tonal information) '''
  return len(get_note_histogram(sequence))

def pitch_count(sequence):
  # Calculate histogram
  # return len(histogram)
  return len(get_pitch_histogram(sequence))

def average_pitch_count_per_bar(bars):
  # (RL-Duet) PC/bar: Pitch count per bar (número de notas distintas por compasso)
  # return len(histogram)
  return pd.DataFrame([get_pitch_histogram(bar).count()
    for bar
    in bars],columns=['pc_bar']).mean()

def average_pitch_interval(sequence):
  # (RL-Duet) PI: Intervalo médio entre pitches
  # Pergunta: consecutivos apenas ou NxN
  return get_pitch_intervals(sequence).mean()

def average_absolute_pitch_interval(sequence):
  # (RL-Duet) PI: Intervalo médio entre pitches
  # Pergunta: consecutivos apenas ou NxN
  # return get_pitch_intervals(sequence).abs().mean()
  hist = get_pitch_intervals(sequence).abs()
  return hist.mean()

def average_inter_onset_interval(sequence):
  # (RL-Duet) IOI: Intervalo médio entre onsets (?)
  # Pergunta: consecutivos apenas ou NxN
  # TODO: Fix IOI calculation
  hist = get_inter_onset_histogram(sequence).drop(0)
  return (0 
    if hist.empty
    else np.average(hist.keys(), weights=hist.values))



def ticks_until_note_event(name, note=None, sequence=[]):
    msgs = takewhile(lambda m: (m.type != name)
      if note is None
      else (m.type != name or m.note != note), sequence[1:])
    msgcount = len(list(msgs)) + 1
    subseq = sequence[1:1+msgcount]
    # print(list(subseq))
    ticks = list(accumulate(subseq,
      func=lambda t, m: int(t) + int(m.time),
      initial=0))[-1]
    # print(f'{note} lasts {msgcount} events until next {name} ({ticks} ticks)')
    return ticks

def ticks_until_note_off(note, sequence):
    return ticks_until_note_event('note_off', note=note, sequence=sequence)

def ticks_until_next_onset(sequence):
    return ticks_until_note_event('note_on', note=None, sequence=sequence)

def get_histogram(label, sequence):
  df = pd.DataFrame(sequence, columns=[label])
  return df.groupby(label)[label].count()

def get_note_histogram(sequence):
  ''' like get_pitch_histogram, but ignores octaves (only cares about tonal information) '''
  return get_histogram('note', [ msg.note % 12
    for msg
    in sequence
    if msg.type == 'note_on'])

def get_pitch_histogram(sequence):
  # (RL-Duet) Histograma de Pitches (Notas) - Diferença de Wasserstein contra Ground-Truth
  return get_histogram('note', [msg.note for msg in sequence if msg.type == 'note_on'])

def get_length_histogram(sequence):
  # (RL-Duet) Histograma de Comprimento - Diferença de Wasserstein contra Ground-Truth
  return get_histogram('length', [
      ticks_until_note_off(msg.note, sequence[index:])
        for (index, msg) 
        in enumerate(sequence)
        if msg.type == 'note_on'])

def get_difflist(name, sequence):
    # print(sequence)
    return pd.Series(sequence, name=name).diff()

def get_pitch_intervals(sequence):
    difflist = get_difflist('intervals', [msg.note
        for msg
        in sequence
        if msg.type == 'note_on'])
    return difflist

# TODO: Fix IOI calculation
def get_inter_onset_histogram(sequence):
  return get_histogram('ioi', [
      ticks_until_next_onset(sequence[index:])
        for (index, msg) 
        in enumerate(sequence)
        if msg.type == 'note_on'])
