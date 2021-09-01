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
        bundle_path = host.get_bundle(checkpoint)
        bundle_file = sequence_generator_bundle.read_bundle_file(bundle_path)

        self.host = host

        self.host.set('input_unit', 'seconds')
        self.host.set('input_length', 3)
        self.host.set('output_unit', 'seconds')
        self.host.set('output_length', 16)

        self.host.set('is_velocity_sensitive', True)
        self.host.set('steps_per_quarter', config.steps_per_quarter)
        self.host.set('output_tracks', [1])

        # self.host.set('scaling_factor', 2)

        # TODO: Move to yaml
        self.host.include_filters('magenta')
        self.host.add_filter('input', 'mido_no_0_velocity')
        # self.host.add_filter('input', 'print_midotracks')
        self.host.add_filter('input', 'midotrack2noteseq')
        # self.host.add_filter('input', 'print_noteseqs')
        self.host.add_filter('input', 'debug_generation_request')
        # Here, the sequence already starts at ~1.0 to ~1.5
        self.host.add_filter('output', 'noteseq_trim_start')
        self.host.add_filter('output', 'noteseq_trim_end')
        self.host.add_filter('output', 'noteseq2midotrack')
        self.host.add_filter('output', 'mido_track_sort_by_time')
        self.host.add_filter('output', 'mido_track_subtract_previous_time')

        # This offset helps ensure the output of the model will fulfill the desired region. Excess is cropped
        self.offset = 1.1


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

    def sample(self, track, generator_options):
      seq = self.model.generate(track, generator_options)
      for note in seq.notes:
        note.start_time -= self.offset
        note.end_time -= self.offset
        if note.start_time < 0: seq.notes.remove(note)
      return seq


    def generate(self, tracks=None, length_seconds=4, output_tracks=[0]):

        # last_end_time is always 0!
        last_end_time = self.host.get('last_end_time')
        print(f'let: {last_end_time} | ength_seconds: {length_seconds}')

        track_idx = output_tracks[0]
        track = tracks[track_idx]

        # Define Generation Range
        start_time = last_end_time
        end_time = last_end_time + length_seconds + self.offset

        generator_options = generator_pb2.GeneratorOptions()
        generator_options.generate_sections.add(start_time=start_time, end_time=end_time)

        seq = self.sample(track, generator_options)

        while len(seq.notes) < 2: seq = self.sample(track, generator_options)

        return [seq]

    def close(self):
        pass
