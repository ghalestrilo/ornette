import mido
import pandas as pd
from itertools import chain, takewhile, accumulate

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
  print(get_pitch_histogram(track_1).head(40))
  print(get_length_histogram(track_1).head(40))

  # print(get_pitch_histogram(bars[1]).head(40))
  # df = pd.DataFrame([get_pitch_histogram(bar) for bar in bars], columns=['pitch_histograms'])
  # print(df.head())
  # ticks_per_beat.numerator
  return

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
  df = pd.DataFrame([msg.note for msg in sequence if msg.type == 'note_on'], columns=['note'])
  return df.groupby('note')['note'].count()

def ticks_until_note_off(note, sequence):
    msgs = takewhile(lambda m: not (m.type == 'note_off' and m.note == note), sequence)
    return list(accumulate(msgs,func=lambda t, m: int(t) + int(m.time), initial=0))[-1]

def get_length_histogram(sequence):
  # (RL-Duet) Histograma de Comprimento - Diferença de Wasserstein contra Ground-Truth
  df = pd.DataFrame([ ticks_until_note_off(msg.note, sequence[index:])
        for (index, msg) 
        in enumerate(sequence)
        if msg.type == 'note_on'], columns=['length'])
  return df.groupby('length')['length'].count()

  # return [ ticks_until_note_off(msg.note, sequence[index:])
  #       for (index, msg) 
  #       in enumerate(sequence)
  #       if msg.type == 'note_on']

def for_each_bar(host, sequence, method):
  # receives a function, builds a dataframe using provided method for each bar of the sequence
  pass


# Opcionalmente, generate(count=1, unit='bars') # enum unit: ['bar','note','event','seconds']
#- generate_bars(number=1):
#    calcula o tempo de um compasso
#
#- length(filename, scale='bar'): # enum unit: ['bar','note','event','seconds']
#    retorna o comprimento dos dados contidos no arquivo na unidade desejada