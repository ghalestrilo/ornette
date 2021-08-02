import magenta
from magenta.models.melody_rnn.melody_rnn_model import MelodyRnnModel, default_configs
from magenta.models.melody_rnn.melody_rnn_sequence_generator import MelodyRnnSequenceGenerator
from magenta.models.shared import sequence_generator_bundle
from note_seq.protobuf import generator_pb2

import os

class OrnetteModule():
    def __init__(self, host, checkpoint='attention_rnn'):
        self.config = default_configs[checkpoint]
        config = self.config
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
        self.host.set('input_length', 16)
        self.host.set('input_unit', 'bars')
        self.host.set('output_unit', 'bars')
        self.last_end_time = 0
        self.host.set('last_end_time', 0)
        self.host.set('output_tracks', [1])

        # TODO: Move to yaml
        self.host.include_filters('magenta')
        self.host.add_filter('input', 'midotrack2noteseq')
        self.host.add_filter('output', 'drop_input_length')
        self.host.add_filter('output', 'noteseq2midotrack')
        self.host.add_filter('output', 'mido_track_sort_by_time')
        self.host.add_filter('output', 'mido_track_subtract_last_time')

    def generate(self, tracks=None, length_bars=4, output_tracks=[0]):
        last_end_time = max([max([0, *(note.end_time for note in track.notes if any(track.notes))])
          for track
          in tracks])
        length_bars += self.host.song.get_buffer_length()
        print(f'last_end_time: {last_end_time}')

        generator_options = generator_pb2.GeneratorOptions()
        generator_options.generate_sections.add(
            start_time=last_end_time,
            end_time=last_end_time + length_bars)

        output = [self.model.generate(tracks[voice], generator_options) for voice in output_tracks]

        return output

    def close(self):
        pass
      