import math
import magenta
from note_seq.protobuf import generator_pb2

from magenta.models.performance_rnn.performance_model import default_configs, PerformanceRnnModel
from magenta.models.performance_rnn.performance_sequence_generator import PerformanceRnnSequenceGenerator
from magenta.models.shared import sequence_generator_bundle

import os

class OrnetteModule():
    def __init__(self, host, checkpoint='performance_with_dynamics'):
        config = default_configs[checkpoint]

        # TODO: improve checkpoint-loading logic
        bundle_path = os.path.normpath(f'/ckpt/{checkpoint}')
        bundle_file = sequence_generator_bundle.read_bundle_file(bundle_path)

        self.server_state = host.state
        self.host = host

        # self.host.set('input_unit', 'seconds')
        self.host.set('input_unit', 'bars')
        # self.host.set('output_unit', 'seconds')
        self.host.set('output_unit', 'bars')

        self.host.set('last_end_time', 0)
        self.host.set('is_velocity_sensitive', True)
        self.host.set('steps_per_quarter', config.steps_per_quarter)  
        # self.host.set('steps_per_quarter', 8)
        self.host.set('voices', [1])

        # TODO: Move to yaml
        self.host.include_filters('magenta')
        self.host.add_filter('input', 'mido_no_0_velocity')
        self.host.add_filter('input', 'midotrack2noteseq')

        # self.host.add_filter('output', 'filter_test')
        self.host.add_filter('output', 'noteseq2midotrack_performance_rnn')

        # mido_track_subtract_last_time: Notas ficam muito pequenas e frases soam mal
        # self.host.add_filter('output', 'mido_track_sort_by_time')
        # self.host.add_filter('output', 'mido_track_subtract_last_time')

        self.model = PerformanceRnnSequenceGenerator(
            model=PerformanceRnnModel(config),
            details=config.details,
            steps_per_second=config.steps_per_second,
            num_velocity_bins=config.num_velocity_bins,
            control_signals=config.control_signals,
            optional_conditioning=config.optional_conditioning,
            # checkpoint=os.path.normpath(f'/ckpt/{checkpoint}'),
            bundle=bundle_file,
            note_performance=config.note_performance)

    def generate(self, tracks=None, length_seconds=4, voices=[0]):
        output = []

        for voice in voices:
            last_end_time = max([max([0, *(note.end_time for note in track.notes if any(track.notes))]) for track in tracks])
            print(f'last_end_time  {last_end_time}')

            generator_options = generator_pb2.GeneratorOptions()
            generator_options.generate_sections.add(
                start_time=last_end_time,
                end_time=last_end_time + length_seconds)

            seq = self.model.generate(tracks[voice], generator_options).notes
            output.append(seq)
        return output

    def close(self):
        pass
