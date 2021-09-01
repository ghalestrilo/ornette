import unittest
import sys
import os

from unittest.mock import MagicMock, ANY

sys.path.append(os.path.abspath(os.path.join('server')))
from server.data import load_model
from server.host import Host
from server import host, data
from tests.common import args
from math import ceil
from importlib import reload


# python -m unittest tests.models

models = [  # Melody RNN
    # {'name': 'melody_rnn', 'bundle': 'basic_rnn'},
    # {'name': 'melody_rnn', 'bundle': 'mono_rnn'},
    # {'name': 'melody_rnn', 'bundle': 'attention_rnn'},
    # {'name': 'melody_rnn', 'bundle': 'lookback_rnn'},

    # Performance RNN
    # {'name': 'performance_rnn', 'bundle': 'performance_with_dynamics'},
    # {'name': 'performance_rnn', 'bundle': 'density_conditioned_performance_with_dynamics'},
    # {'name': 'performance_rnn', 'bundle': 'pitch_conditioned_performance_with_dynamics'},
    # {'name': 'performance_rnn', 'bundle': 'performance'},
    # {'name': 'performance_rnn', 'bundle': 'polyphony_rnn'},
    # {'name': 'performance_rnn', 'bundle': 'multiconditioned_performance_with_dynamics'},
    # {'name': 'performance_rnn', 'bundle': 'performance_with_dynamics_and_modulo_encoding'},

    # Pianoroll RNN
    # {'name': 'pianoroll_rnn_nade', 'bundle': 'rnn-nade_attn'},
    # {'name': 'pianoroll_rnn_nade', 'bundle': 'rnn-nade'},
    # {'name': 'pianoroll_rnn_nade', 'bundle': 'pianoroll_rnn_nade'},
    # {'name': 'pianoroll_rnn_nade', 'bundle': 'pianoroll_rnn_nade-bach'},

    # Polyphony RNN
    {'name': 'polyphony_rnn', 'bundle': 'polyphony_rnn'},
]


# models = models[:4] # melody_rnn
# models = [models[-1]] + models[:4]
# models = [models[-1]]

# models = [{'name': 'pianoroll_rnn_nade', 'bundle': 'rnn-nade_attn'}]
# models = [model for model in models if model['name'] == 'pianoroll_rnn_nade']
# models = [{'name': 'performance_rnn', 'bundle': 'performance_with_dynamics'}]

base_sys_path = sys.path.copy()

class TestModelGeneration(unittest.TestCase):
    def setUp(self):
      for model in models:
        with self.subTest(model=model):
          self.host = Host(args)
          self.model = None
          self.total_length = None
          self.generate = None
          self.initialize(models[0])

    def initialize(self, model):
      sys.path = base_sys_path.copy()
      args.module = model["name"]
      args.checkpoint = model["bundle"]
      reload(host)
      reload(data)
      self.host = Host(args)
      self.model = load_model(self.host,args.checkpoint,f'modules/{args.module}')
      self.host.model = self.model
      self.total_length = lambda: int(ceil(self.host.song.total_length()))
      self.generate = self.host.engine.generate
      print(sys.path)

    def test_resetting_and_generating(self):
      """ WHEN resetting a song
          SHOULD generate without issues
      """
      for model in models:
        with self.subTest(model=model):
          self.initialize(model)
          self.host.reset()
          self.host.set('output_tracks', 1)
          self.generate(1,'bars')
          self.assertEqual(1, self.total_length())

    def test_generate_exact_barcount(self):
      """ WHEN generating from a clean file
          SHOULD generate exactly the requested amount of bars
      """
      subject = lambda: self.total_length()
      for model in models:
        with self.subTest(model=model):
          self.initialize(model)
          for i in range(8):
            with self.subTest(barcount=i+1):
              self.host.reset()
              self.host.set('output_tracks', 1)
              self.generate(i+1, 'bars')
              self.assertEqual(i+1, subject())


    def test_repeated_generation(self):
      """ WHEN Generating 1 at a time, 5 times SHOULD generate exactly 5 bars """
      for model in models:
        for repetition in range(2):
          with self.subTest(model=model, repetition=repetition):
            self.initialize(model)
            for _ in range(12): self.generate(1,'bars')
            self.assertEqual(12, self.total_length())
    


    # TODO: Move this to test_engine
    def test_repeated_generation_end_of_track(self):
      """ WHEN Generating many times over SHOULD have 'end_of_track' at the end of every track """
      for model in models:
        self.initialize(model)
        for repetition in range(2):
          with self.subTest(model=model, repetition=repetition):
            for _ in range(5): self.generate(1,'bars')
            # self.host.song.show()
            for i, track in enumerate(self.host.song.data.tracks):
              print(f'track {i}')
              self.assertGreaterEqual(len(track), 1)
              self.assertEqual('end_of_track', track[-1].type)
    
    # TODO: Move this to test_engine
    def test_repeated_generation_no_extra_end_of_track(self):
      """ WHEN Generating many times over SHOULD have 'end_of_track' at the end of every track """
      for model in models:
        self.initialize(model)
        for repetition in range(10):
          with self.subTest(model=model, repetition=repetition):
            for _ in range(5): self.generate(1,'bars')
            for track in self.host.song.data.tracks:
              self.assertNotIn('end_of_track', map(lambda msg: msg.type, track[:-1]))

    def test_different_sizes(self):
      """ WHEN Generating different-sized chunks
          SHOULD generate exactly the required amount
      """
      for model in models:
        with self.subTest(model=model):
          self.initialize(model)
          self.generate(1,'bars')
          self.generate(2,'bars')
          self.generate(4,'bars')
          self.assertEqual(7, self.total_length())


# TODO: Move to test_engine
class TestModelCall(unittest.TestCase):
    def setUp(self):
      self.host = Host(args)
      self.host.model.generate = MagicMock()
      
    def test_generate_call(self):
      self.host.engine.generate(1,'bars')
      self.host.model.generate.assert_called_with(ANY, 4, ANY)