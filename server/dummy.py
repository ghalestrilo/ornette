

class DummyModule():
  def __init__(self, host):
    self.host = host

  def generate(self, tracks=None, length_bars=4, output_tracks=[0]):
    self.host.io.log('Warning: the dummy model has been asked to generate samples. Remove the the --no_module flag to generate data')
    return [[] for track in output_tracks]

  def close(self):
    pass