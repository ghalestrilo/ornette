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
    
    # config_id = bundle.generator_details.id if bundle else FLAGS.config
    # config_id = 'performance_with_dynamics'
    config = default_configs[checkpoint]
    
    bundle_path = os.path.normpath(f'/ckpt/{checkpoint}') # TODO: improve checkpoint-loading logic
    bundle_file = sequence_generator_bundle.read_bundle_file(bundle_path)

    self.server_state = host.state
    self.host = host

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
  def generate(self, primer_sequence=None):
    # TODO: Move this logic to the server
    qpm = self.server_state['tempo']
    length = self.server_state['buffer_length']
    length_seconds = _steps_to_seconds(length, qpm)

    # TODO: last_end_time / last_start_time could be a state field
    if (primer_sequence != None and any(primer_sequence)):
      last_end_time = max(n.end_time for n in primer_sequence)
    else: last_end_time = 0

    # TODO: Abstract this code
    
    # self.host.steps_to_seconds(length, qpm)
    # self.host.buffer_length_seconds (= steps_to_seconds(length, qpm))
    length_seconds = _steps_to_seconds(length, qpm)
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
      tempos=[ { 'time': 0, 'qpm': qpm } ],
      total_quantized_steps=11,
    )

    # self.model.generate(noteseq, generator_options)
    return self.model.generate(noteseq, generator_options)

  def tick(self):
    def by_start_time(e): return e.start_time if e is not None else []
    seq = self.generate(self.server_state['history'][0]).notes
    seq.sort(key=by_start_time)
    return seq

  def get_action(self,token):
    next_note = self.host.peek()
    wait = max(0, next_note.start_time - token.start_time if next_note is not None else 0)
    sus = token.end_time - token.start_time
    return [('play', token.pitch), ('wait', wait*10)]
    # return [('play', token.pitch), ('wait', token.end_time - token.start_time)]
  
  def decode(self, token):
    return (token.pitch, token.end_time - token.start_time)

  def close(self):
    pass