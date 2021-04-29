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
"""Generate polyphonic tracks from a trained checkpoint.
Uses flags to define operation.
"""
import os

from magenta.models.polyphony_rnn import polyphony_model
from magenta.models.polyphony_rnn import polyphony_sequence_generator
from magenta.models.shared import sequence_generator
from magenta.models.shared import sequence_generator_bundle
import note_seq
from note_seq.protobuf import generator_pb2
from note_seq.protobuf import music_pb2
import tensorflow.compat.v1 as tf
from note_seq import NoteSequence

tf.disable_v2_behavior()

class OrnetteModule():
  def __init__(self, host, checkpoint='polyphony_rnn'):
      config          = polyphony_model.default_configs['polyphony']
      checkpoint_file = os.path.normpath(f'/ckpt/{checkpoint}')
      bundle_file     = sequence_generator_bundle.read_bundle_file(checkpoint_file)
      self.model      = polyphony_sequence_generator.PolyphonyRnnSequenceGenerator(
        model=polyphony_model.PolyphonyRnnModel(config),
        details=config.details,
        steps_per_quarter=config.steps_per_quarter,
        bundle=bundle_file)
      self.server_state = host.state
      self.host = host
      self.host.set('history', [[]])
      self.host.set('generation_unit', 'seconds')
      self.last_end_time = 0

  def generate(self, history=None, length_seconds=4):
    last_end_time = 0

    # Get first voice
    primer_sequence = [] if history is None else history[0]
    
    # Get last end time
    if (primer_sequence != None and any(primer_sequence)):
        last_end_time = max(n.end_time for n in primer_sequence)

    noteseq = NoteSequence(
        notes=primer_sequence,
        quantization_info={ 'steps_per_quarter': self.server_state['steps_per_quarter'] },
        tempos=[ { 'time': 0, 'qpm': self.server_state['bpm'] } ],
        total_quantized_steps=11,
      )

    self.generator_options = generator_pb2.GeneratorOptions()
    self.generator_options.args['temperature'].float_value = self.host.state['temperature']
    self.generator_options.generate_sections.add(
        start_time= last_end_time + 0,
        end_time= last_end_time + length_seconds)

    notes = self.model.generate(noteseq, self.generator_options).notes
    return notes

  def decode(self, token):
    ''' Must return a mido message (type (note_on), note, velocity, duration)'''
    decoded = [
      ('note_on', token.pitch, token.velocity, max(0, token.start_time - self.last_end_time)),
      ('note_off', token.pitch, token.velocity, token.end_time - token.start_time)
    ]
    self.last_end_time = token.end_time
    return decoded

  def encode(self, message):
    ''' Receives a mido message, must return a model-compatible token '''

    next_start_time = self.last_end_time + message.time

    note = NoteSequence.Note(
      instrument=0,
      program=0,
      start_time=self.last_end_time,
      end_time=next_start_time,
      velocity=message.velocity,
      pitch=message.note,
    )
    self.last_end_time = next_start_time
    return note
  
  def close(self):
    pass