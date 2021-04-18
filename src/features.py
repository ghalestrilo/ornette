import mido
import pandas as pd
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
  print('\n', get_inter_onset_histogram(track_1).head(40))

  # print(f'\n mean pitch: {get_pitch_histogram(track_1).mean()}')
  # print(f'\n mean length: {get_length_histogram(track_1).mean()}')
  # print(f'\n mean interval: {get_pitch_intervals(track_1).mean()}')
  print(f'\n mean pitch count per bar: {average_pitch_count_per_bar(bars)}')

  # TODO: Fix IOI calculation
  print(f'\n mean ioi: {get_inter_onset_histogram(track_1).mean()}')
  

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

def average_inter_onset_interval(host, sequence):
  # (RL-Duet) IOI: Intervalo médio entre onsets (?)
  # Pergunta: consecutivos apenas ou NxN
  pass



def ticks_until_note_event(name, note=None, sequence=[]):
    msgs = takewhile(lambda m: (m.type != name)
      if note is None
      else (m.type != name or m.note != note), sequence)
    msgcount = len(list(msgs))
    return list(accumulate(sequence[1:1+msgcount],
      func=lambda t, m: int(t) + int(m.time),
      initial=0))[-1]

def ticks_until_note_off(note, sequence):
    return ticks_until_note_event('note_off', note=note, sequence=sequence)

def ticks_until_next_onset(sequence):
    return ticks_until_note_event('note_on', note=None, sequence=sequence)

def get_histogram(label, sequence):
  df = pd.DataFrame(sequence, columns=[label])
  return df.groupby(label)[label].count()

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
    return pd.Series(sequence, name=name).diff()

def get_pitch_intervals(sequence):
    return get_difflist('intervals', [msg.note for msg in sequence if msg.type == 'note_on'])

# TODO: Fix IOI calculation
def get_inter_onset_histogram(sequence):
  return get_difflist('ioi', [ ticks_until_next_onset(sequence[index:])
        for (index, msg) 
        in enumerate(sequence)
        if msg.type == 'note_on'])
  # return get_histogram('ioi', chain.from_iterable([
  #     accumulate(sequence[1:1+len(list(takewhile(lambda submsg: submsg.type != 'note_on', sequence[index:])))],
  #       func=lambda length, note_on_index: length + note_on_index.time,
  #       initial=0)
  #     for (index, msg)
  #     in enumerate(sequence)
  # ]))




# Opcionalmente, generate(count=1, unit='bars') # enum unit: ['bar','note','event','seconds']
#- generate_bars(number=1):
#    calcula o tempo de um compasso
#
#- length(filename, scale='bar'): # enum unit: ['bar','note','event','seconds']
#    retorna o comprimento dos dados contidos no arquivo na unidade desejada




# chain.from_iterable([
#     accumulate(takewhile(lambda submsg: submsg.type != 'note_on', track[index:]),
#       func=lambda length, note_on_index: length + note_on_index.time,
#       initial=0)
#     for (index, msg)
#     in enumerate(track)
# ])
# 