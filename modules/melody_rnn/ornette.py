import magenta
from magenta.models.melody_rnn.melody_rnn_model import MelodyRnnModel, default_configs
from magenta.models.melody_rnn.melody_rnn_sequence_generator import MelodyRnnSequenceGenerator
from magenta.models.shared import sequence_generator_bundle
from note_seq.protobuf import generator_pb2

import os

class OrnetteModule():
    def __init__(self, host, checkpoint='attention_rnn'):
        config = default_configs[checkpoint]
        checkpoint_file = os.path.normpath(f'/ckpt/{checkpoint}')
        bundle_file = sequence_generator_bundle.read_bundle_file(
            checkpoint_file)
        self.model = MelodyRnnSequenceGenerator(model=MelodyRnnModel(config),
                                                details=config.details,
                                                steps_per_quarter=config.steps_per_quarter,
                                                bundle=bundle_file)
        self.server_state = host.state
        self.host = host
        self.host.set('steps_per_quarter', config.steps_per_quarter)
        self.host.set('generation_unit', 'seconds')
        self.last_end_time = 0
        self.host.set('last_end_time', 0)
        self.host.set('voices', [1])

    def generate(self, tracks=None, length_seconds=4, voices=[0]):
        output = []

        last_end_time = max([max([0, *(note.end_time for note in track.notes if any(track.notes))]) for track in tracks])

        for voice in voices:
          # Get last end time

          generator_options = generator_pb2.GeneratorOptions()
          generator_options.generate_sections.add(
              start_time=last_end_time,
              end_time=last_end_time + length_seconds)

          notes = self.model.generate(tracks[voice], generator_options).notes
          output.append(notes)
        return output

    def close(self):
        pass
      