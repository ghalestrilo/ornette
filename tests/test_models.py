import unittest
import sys
import os

from unittest.mock import MagicMock, ANY

sys.path.append(os.path.abspath(os.path.join('server')))
from server.data import load_model
from server.host import Host
from tests.common import args
from math import ceil


# python -m unittest tests.models

models = [  # Melody RNN
    {'name': 'melody_rnn', 'bundle': 'basic_rnn'},
    {'name': 'melody_rnn', 'bundle': 'mono_rnn'},
    {'name': 'melody_rnn', 'bundle': 'attention_rnn'},
    {'name': 'melody_rnn', 'bundle': 'lookback_rnn'},

    # Performance RNN
    {'name': 'performance_rnn', 'bundle': 'performance.mag'},
    {'name': 'performance_rnn',
     'bundle': 'density_conditioned_performance_with_dynamics'},
    {'name': 'performance_rnn', 'bundle': 'performance_with_dynamics'},
    {'name': 'performance_rnn',
     'bundle': 'pitch_conditioned_performance_with_dynamics'},
    {'name': 'performance_rnn', 'bundle': 'performance'},
    {'name': 'performance_rnn', 'bundle': 'polyphony_rnn'},
    {'name': 'performance_rnn',
     'bundle': 'multiconditioned_performance_with_dynamics'},
    {'name': 'performance_rnn',
     'bundle': 'performance_with_dynamics_and_modulo_encoding'},

    # Pianoroll RNN
    {'name': 'pianoroll_rnn_nade', 'bundle': 'rnn-nade_attn'},
    {'name': 'pianoroll_rnn_nade', 'bundle': 'rnn-nade'},
    {'name': 'pianoroll_rnn_nade', 'bundle': 'pianoroll_rnn_nade'},
    {'name': 'pianoroll_rnn_nade', 'bundle': 'pianoroll_rnn_nade-bach'},

    # Polyphony RNN
    {'name': 'polyphony_rnn', 'bundle': 'polyphony_rnn'},
]


class TestModels(unittest.TestCase):
    def setUp(self):
      model = models[0]
      self.host = Host(args)
      self.model = load_model(self.host,model['bundle'],f'modules/{model["name"]}')
      self.host.model = self.model
      self.total_length = lambda: int(ceil(self.host.song.total_length()))
      self.generate = self.host.engine.generate

    def test_resetting_and_generating(self):
      """ WHEN resetting a song
          SHOULD generate without issues
      """
      self.host.reset()
      self.host.set('output_tracks', 2)
      self.generate(1,'bars')
      self.assertEqual(1, self.total_length())

    # Mock tests
    def test_consecutive_generation(self):
      """ WHEN Generating 1 at a time, 5 times
          SHOULD generate exactly 5 bars
      """
      self.generate(1,'bars')
      self.generate(1,'bars')
      self.generate(1,'bars')
      self.generate(1,'bars')
      self.generate(1,'bars')
      self.assertEqual(5, self.total_length())

    def test_different_sizes(self):
      """ WHEN Generating different-sized chunks
          SHOULD generate exactly the required amount
      """
      self.generate(1,'bars')
      self.generate(2,'bars')
      self.generate(4,'bars')
      self.assertEqual(7, self.total_length())

    def test_isupper(self):
        self.assertEqual(True, True)



class TestModelCall(unittest.TestCase):
    def setUp(self):
      self.host = Host(args)
      self.host.model.generate = MagicMock()
      
    def test_generate_call(self):
      self.host.engine.generate(1,'bars')
      self.host.model.generate.assert_called_with(ANY, 4, ANY)