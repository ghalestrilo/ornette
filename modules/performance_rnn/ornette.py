import math
import magenta
from magenta import music as mm
from note_seq.protobuf import generator_pb2
from note_seq import NoteSequence

from magenta.models.performance_rnn.performance_model import default_configs, PerformanceRnnModel
from magenta.models.performance_rnn.performance_sequence_generator import PerformanceRnnSequenceGenerator
from magenta.models.shared import sequence_generator
from magenta.models.shared import sequence_generator_bundle

import os



class OrnetteModule():
  def __init__(self, host, checkpoint='performance_with_dynamics'):
    config = default_configs[checkpoint]
    
    bundle_path = os.path.normpath(f'/ckpt/{checkpoint}') # TODO: improve checkpoint-loading logic
    bundle_file = sequence_generator_bundle.read_bundle_file(bundle_path)

    self.server_state = host.state
    self.host = host
    self.host.set('history', [[]])
    self.last_end_time = 0

    self.model = PerformanceRnnSequenceGenerator(
        model=PerformanceRnnModel(config),
        details=config.details,
        steps_per_second=config.steps_per_second,
        num_velocity_bins=config.num_velocity_bins,
        control_signals=config.control_signals,
        optional_conditioning=config.optional_conditioning,
        #checkpoint=os.path.normpath(f'/ckpt/{checkpoint}'),
        bundle=bundle_file,
        note_performance=config.note_performance)
  
  # update Module#generate to receive only number of tokens
  def generate(self, primer_sequence=None, length=4):
    length_seconds = self.host.steps_to_seconds(length)
    last_end_time = 0
      
    if (primer_sequence != None and any(primer_sequence)):
        last_end_time = max(n.end_time for n in primer_sequence)
    
    generator_options = generator_pb2.GeneratorOptions()
    generator_options.generate_sections.add(
        start_time=length_seconds + last_end_time,
        end_time=length_seconds + last_end_time + length)
    
    # TEMP: Constructing noteseq dict to feed into the model
    # TODO: bind 'notes' value to self.history
    noteseq = NoteSequence(
      notes=primer_sequence[-16:],
      quantization_info={
          'steps_per_quarter': 4
          },
      tempos=[ {
        'time': 0,
        'qpm': self.server_state['tempo']
      } ],
      total_quantized_steps=11,
    )

    def by_start_time(e): return e.start_time if e is not None else []
    seq = self.model.generate(noteseq, generator_options).notes
    seq.sort(key=by_start_time)
    return seq

  def decode(self, token):
    ''' Must return a mido message (type (note_on), note, velocity, duration)'''
    velocity = 127

    decoded = [
      ('note_on', token.pitch, velocity, token.start_time - self.last_end_time),
      ('note_off', token.pitch, velocity, token.end_time - token.start_time)
    ]
    
    self.last_end_time = max(0,token.end_time)
    return decoded

  def encode(self, message):
    ''' Receives a mido message, must return a model-compatible token '''

    next_start_time = self.last_end_time + message.time

    note = NoteSequence.Note(
      instrument=0,
      program=0,
      start_time=self.last_end_time,
      end_time=next_start_time,
      velocity=message.velocity,
      pitch=message.note,
    )

    self.last_end_time = next_start_time
    return note

  def close(self):
    pass