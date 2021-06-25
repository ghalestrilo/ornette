import importlib

class Filters():
  def __init__(self, host):
    self.host = host
    self._filters = {}
    host.filters = self
    self.input = []
    self.output = []

  def clear(self):
    self.input = []
    self.output = []

  def load_filter_defs(self, filename):
      module = importlib.import_module(f'filter_defs.{filename}')

      for key, value in module.filters.items():
        self._filters[key] = value

  def get(self, filtername):
    filter_ = None
    try:
      filter_ = self._filters[filtername]
    except KeyError:
      self.host.io.log(f'Ignoring unknown filter: {filtername}')

    return filter_

  def append(self, stage, filtername):
    f = self.get(filtername)
    if not f: return

    if stage == 'input': self.input.append(f)
    elif stage == 'output': self.output.append(f)
    else:
      self.host.io.log(f'Unknown filter stage: ({stage}), expected "input" or "output"')

  def set(self, input_filters, output_filters):
    self.clear()

    for filtername in input_filters: self.append('input', filtername)
    for filtername in output_filters: self.append('output', filtername)

