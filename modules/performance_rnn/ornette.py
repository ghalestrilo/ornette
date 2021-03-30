import magenta
from magenta import music as mm
from note_seq.protobuf import generator_pb2
from note_seq import NoteSequence

from magenta.models.performance_rnn.performance_model import default_configs, PerformanceRnnModel
from magenta.models.performance_rnn.performance_sequence_generator import PerformanceRnnSequenceGenerator
from magenta.models.shared import sequence_generator
from magenta.models.shared import sequence_generator_bundle

class OrnetteModule():
  def __init__(self, state={}, checkpoint='performance_rnn'):
    
    # config_id = bundle.generator_details.id if bundle else FLAGS.config
    config_id = 'performance'
    config = default_configs[config_id]

    self.generator = PerformanceRnnSequenceGenerator(
        model=PerformanceRnnModel(config),
        details=config.details,
        steps_per_second=config.steps_per_second,
        num_velocity_bins=config.num_velocity_bins,
        control_signals=config.control_signals,
        optional_conditioning=config.optional_conditioning,
        checkpoint=get_checkpoint(),
        bundle=bundle,
        note_performance=config.note_performance)
  
  def generate(self, primer_sequence=None):
    return []

  def tick(self, topk=1):
    return self.generate(self.server_state['history'][0]).notes

  def get_action(self,token):
    return [('play', token.pitch), ('wait', token.end_time - token.start_time)]
  
  def decode(self, token):
    return (token.pitch, token.end_time - token.start_time)

  def close(self):
    pass