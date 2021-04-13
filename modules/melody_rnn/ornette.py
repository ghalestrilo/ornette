import magenta
from magenta import music as mm
from magenta.models.melody_rnn.melody_rnn_model import MelodyRnnModel, default_configs
from magenta.models.melody_rnn.melody_rnn_sequence_generator import MelodyRnnSequenceGenerator
from magenta.models.shared import sequence_generator_bundle
from note_seq.protobuf import generator_pb2
from note_seq import NoteSequence

# TODO: Use in server
def _steps_to_seconds(steps, qpm):
    steps_per_quarter = 4
    return steps * 60.0 / qpm / steps_per_quarter

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
    # self.temperature=1.2
    self.server_state = host.state
    self.host = host
    # self.server_state['history'] = [None] # FIXME: How to properly do this?
    self.server_state['history'] = [[]]

  def generate(self, primer_sequence=None):
      qpm = self.server_state['tempo']
      length = self.server_state['buffer_length']

      # self.host.steps_to_seconds(length, qpm)
      # self.host.buffer_length_seconds (= steps_to_seconds(length, qpm))
      length_seconds = _steps_to_seconds(length, qpm)
      
      # Set the start time to begin on the next step after the last note ends.
      last_end_time = 0
      
      if (primer_sequence != None and any(primer_sequence)):
          last_end_time = max(n.end_time for n in primer_sequence)

      # TODO: Abstract this code
      generator_options = generator_pb2.GeneratorOptions()
      generator_options.generate_sections.add(
          #start_time=last_end_time + _steps_to_seconds(1, qpm),
          start_time=length_seconds + last_end_time,
          end_time=length_seconds + last_end_time + length)

      # TEMP: Constructing noteseq dict to feed into the model
      # TODO: bind 'notes' value to self.history
      noteseq = NoteSequence(
        notes=primer_sequence,
        quantization_info={
            'steps_per_quarter': 4
            },
        tempos=[ { 'time': 0, 'qpm': qpm } ],
        total_quantized_steps=11,
      )

      # generate the output sequence
      return self.model.generate(noteseq, generator_options)

  def tick(self, topk=1):
    return self.generate(self.server_state['history'][0]).notes

  # TODO: move to server
  def peek(self,offset=1):
    return self.server_state['history'][0][self.server_state['playhead'] + offset]

  def get_action(self,token):
    next_note = self.host.peek()
    wait = max(0, next_note.start_time - token.start_time if next_note is not None else 0)
    return [('play', token.pitch), ('wait', wait)]

  def decode(self, token):
    ''' Must return a mido message (type (note_on), note, velocity, duration)'''
    velocity = 127

    # return (name, token.pitch, velocity, token.start_time)
    return (token.pitch, (token.end_time - token.start_time) / 120)

  def close(self):
    pass
