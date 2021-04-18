import magenta
from magenta import music as mm
from magenta.models.melody_rnn.melody_rnn_model import MelodyRnnModel, default_configs
from magenta.models.melody_rnn.melody_rnn_sequence_generator import MelodyRnnSequenceGenerator
from magenta.models.shared import sequence_generator_bundle
from note_seq.protobuf import generator_pb2
from note_seq import NoteSequence

import os

class OrnetteModule():
  def __init__(self, host, checkpoint='attention_rnn'):
    config      = default_configs[checkpoint]
    checkpoint_file = os.path.normpath(f'/ckpt/{checkpoint}')
    bundle_file = sequence_generator_bundle.read_bundle_file(checkpoint_file)
    steps_per_quarter = 4
    self.model = MelodyRnnSequenceGenerator(model=MelodyRnnModel(config),
      details=config.details,
      steps_per_quarter=steps_per_quarter,
      bundle=bundle_file)
    self.realtime_ready = True
    self.server_state = host.state
    self.host = host
    self.host.set('history', [[]])
    self.last_end_time = 0

  def generate(self, primer_sequence=None, length=4):
      length_seconds = self.host.steps_to_seconds(length)
      last_end_time = 0
      
      if (primer_sequence != None and any(primer_sequence)):
          last_end_time = max(n.end_time for n in primer_sequence)

      # TODO: Abstract this code
      generator_options = generator_pb2.GeneratorOptions()
      generator_options.generate_sections.add(
          start_time=length_seconds + last_end_time,
          end_time=length_seconds + last_end_time + length)

      noteseq = NoteSequence(
        notes=primer_sequence[:-min(len(primer_sequence),length)],
        quantization_info={
            'steps_per_quarter': 4
            },
        tempos=[ {
          'time': 0,
          'qpm': self.server_state['tempo']
        } ],
        total_quantized_steps=11,
      )

      # generate the output sequence
      return self.model.generate(noteseq, generator_options).notes

  def decode(self, token):
    ''' Must return a mido message (type (note_on), note, velocity, duration)'''
    velocity = 127

    decoded = [
      ('note_on', token.pitch, velocity, token.start_time - self.last_end_time),
      ('note_off', token.pitch, velocity, token.end_time - token.start_time)
    ]

    self.last_end_time = max(0,token.end_time)
    return decoded

  # For Batch-running only
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
