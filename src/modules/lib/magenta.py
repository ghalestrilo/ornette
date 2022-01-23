import abc
import math
import magenta
from note_seq.protobuf import generator_pb2

class MagentaModelHost():
  def get_bundle_file():
    # checkpoint = ENV['checkpoint']
    # config = default_configs[checkpoint]
    # bundle_path = host.get_bundle(checkpoint)
    # bundle_file = sequence_generator_bundle.read_bundle_file(bundle_path)
    return

  def get_config():
    return

  def start(self):
    self.model.start()

  @abc.abstractmethod(callable)
  def generate(self, tracks=None, length_seconds=4, output_tracks=[0]):
    """Method documentation"""
    return

  @abc.abstractmethod(callable)
  def init_model(self):
    return