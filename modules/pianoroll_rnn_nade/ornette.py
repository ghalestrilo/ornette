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
from note_seq import NoteSequence, PianorollSequence
from note_seq.protobuf import generator_pb2

class OrnetteModule():
    def __init__(self, host, checkpoint='rnn-nade_attn'):
        bundle_path = os.path.normpath(f'/ckpt/{checkpoint}')
        config = default_configs[checkpoint]
        bundle_file = sequence_generator_bundle.read_bundle_file(bundle_path)

        self.server_state = host.state
        self.host = host
        self.host.set('history', [[]])
        self.host.set('generation_unit', 'seconds')
        self.host.set('last_end_time', 0.125)

        self.model = PianorollRnnNadeSequenceGenerator(
          model=PianorollRnnNadeModel(config),
          details=config.details,
          steps_per_quarter=config.steps_per_quarter,
          bundle=bundle_file)

    def generate(self, history=None, length_seconds=4):
        init_pitch = 55
        step_length = 1 / self.host.get('steps_per_quarter')

        # Get first voice
        primer_sequence = history[0] if history and any(history[0]) else [(init_pitch,)] 

        # Get last end time
        last_end_time = (len(primer_sequence) * step_length
          if primer_sequence != None and any(primer_sequence)
          else 0 )

        primer_pianoroll = PianorollSequence(
          events_list=primer_sequence,
          steps_per_quarter=self.host.get('steps_per_quarter'),
          shift_range=True)
        primer_sequence = primer_pianoroll.to_sequence(qpm=self.host.get('bpm'))

        generator_options = generator_pb2.GeneratorOptions()
        generator_options.generate_sections.add(
            start_time=last_end_time,
            end_time=last_end_time + length_seconds)

        
        seq = self.model.generate(primer_sequence, generator_options).notes

        # return seq
        return [(note.pitch,) for note in seq]

    def decode(self, token):
        step_length = 1 / self.host.get('steps_per_quarter')
        return [('note_on', token[0], 127, step_length)]

    def encode(self, message):
        ''' Receives a mido message, must return a model-compatible token '''
        last_end_time = self.host.get('last_end_time')
        step_length = 1 / self.host.get('steps_per_quarter')

        note = (message.note,)

        self.host.set('last_end_time', last_end_time + step_length)
        return note

    def close(self):
      return None