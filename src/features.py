import mido
import pandas

# Extract Features


# Feature Extraction

units = ['bars', 'seconds', 'notes', 'events']

def get_features(midi_data):
  []
  return

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
  pass

def get_length_histogram(sequence):
  # (RL-Duet) Histograma de Comprimento - Diferença de Wasserstein contra Ground-Truth
  pass

def for_each_bar(host, sequence, method):
  # receives a function, builds a dataframe using provided method for each bar of the sequence
  pass


# Opcionalmente, generate(count=1, unit='bars') # enum unit: ['bar','note','event','seconds']
#- generate_bars(number=1):
#    calcula o tempo de um compasso
#
#- length(filename, scale='bar'): # enum unit: ['bar','note','event','seconds']
#    retorna o comprimento dos dados contidos no arquivo na unidade desejada