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
        checkpoint_file = host.get_bundle(checkpoint)
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
        self.host.set('input_unit', 'seconds')
        self.host.set('output_unit', 'seconds')
        self.host.set('output_tracks', [0])

        # TODO: Move to yaml
        self.host.include_filters('magenta')
        self.host.add_filter('input', 'midotrack2noteseq')
        self.host.add_filter('output', 'noteseq_trim_start')
        self.host.add_filter('output', 'noteseq_trim_end')
        self.host.add_filter('output', 'noteseq2midotrack')
        self.host.add_filter('output', 'mido_track_sort_by_time')
        self.host.add_filter('output', 'mido_track_subtract_previous_time')

    def generate(self, tracks=None, length_beats=4, output_tracks=[0]):
        last_end_time = self.host.get('last_end_time')
        # self.host.io.log(f'length to generate: length_beats: {length_beats}')
        generator_options = generator_pb2.GeneratorOptions()
        generator_options.generate_sections.add(
            start_time=last_end_time,
            end_time=last_end_time + length_beats)

        output = [self.model.generate(tracks[voice], generator_options) for voice in output_tracks]

        return output

    def close(self):
        pass
      