# Copyright 2021 The Magenta Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Lint as: python3
"""Generate pianoroll tracks from a trained RNN-NADE checkpoint.
Uses flags to define operation.
"""
import ast
import os
import time

from magenta.models.pianoroll_rnn_nade.pianoroll_rnn_nade_model import default_configs, PianorollRnnNadeModel
from magenta.models.pianoroll_rnn_nade.pianoroll_rnn_nade_sequence_generator import PianorollRnnNadeSequenceGenerator
from magenta.models.shared import sequence_generator_bundle
from magenta.music.sequences_lib import is_relative_quantized_sequence
from note_seq.protobuf import generator_pb2

class OrnetteModule():
    def __init__(self, host, checkpoint='rnn-nade_attn'):
        bundle_path = os.path.normpath(f'/ckpt/{checkpoint}')
        config = default_configs[checkpoint]
        bundle_file = sequence_generator_bundle.read_bundle_file(bundle_path)

        self.server_state = host.state
        self.host = host
        self.host.set('output_unit', 'bars')
        self.host.set('input_unit', 'bars')
        self.host.set('output_tracks', [1,2])
        self.host.set('init_pitch', 55)

        self.model = PianorollRnnNadeSequenceGenerator(
          model=PianorollRnnNadeModel(config),
          details=config.details,
          steps_per_quarter=host.get('steps_per_quarter'),
          bundle=bundle_file)

        # TODO: Move to YAML
        self.host.include_filters('magenta')
        self.host.add_filter('input', 'midotrack2pianoroll')
        self.host.add_filter('output', 'print_noteseqs')
        self.host.add_filter('output', 'noteseq2midotrack')
        self.host.add_filter('output', 'mido_track_sort_by_time')
        self.host.add_filter('output', 'mido_track_subtract_last_time')

    def generate(self, history=None, length_seconds=4, output_tracks=[1, 2]):
        primer_sequence = history.to_sequence(qpm=120)

        generator_options = generator_pb2.GeneratorOptions()
        generator_options.generate_sections.add(
            start_time=self.host.get('last_end_time'),
            end_time=self.host.get('last_end_time') + length_seconds)

        seq = self.model.generate(primer_sequence, generator_options)

        return [seq]

    def close(self):
      return None