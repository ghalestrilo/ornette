import unittest
import sys
import os

from unittest.mock import MagicMock, ANY

sys.path.append(os.path.abspath(os.path.join('server')))
from server.data import load_model
from server.host import Host
from server.song import Song
from server import host, data
from tests.common import args
from math import ceil
from importlib import reload


# python -m unittest tests.models

output = lambda *path: os.path.abspath(os.path.join(os.path.curdir, 'output', *path))
dataset = lambda *path: os.path.abspath(os.path.join(os.path.curdir, 'dataset', *path))

models = [  # Melody RNN
    # {'name': 'melody_rnn', 'bundle': 'basic_rnn', 'primer': None },
    # {'name': 'melody_rnn', 'bundle': 'mono_rnn', 'primer': None },
    {'name': 'melody_rnn', 'bundle': 'attention_rnn', 'primer': dataset('clean_lakh', 'Scorpions_-_Johnny_B._Goode.mid') },
    # {'name': 'melody_rnn', 'bundle': 'lookback_rnn', 'primer': None },

    # Performance RNN
    # {'name': 'performance_rnn', 'bundle': 'performance_with_dynamics', 'primer': 'dataset/clean_piano-e-comp/MIDI-Unprocessed_17_R2_2008_01-04_ORIG_MID--AUDIO_17_R2_2008_wav--2.midi' },
    # {'name': 'performance_rnn', 'bundle': 'density_conditioned_performance_with_dynamics', 'primer': None },
    # {'name': 'performance_rnn', 'bundle': 'pitch_conditioned_performance_with_dynamics', 'primer': None },
    # {'name': 'performance_rnn', 'bundle': 'performance', 'primer': None },
    # {'name': 'performance_rnn', 'bundle': 'polyphony_rnn', 'primer': None },
    # {'name': 'performance_rnn', 'bundle': 'multiconditioned_performance_with_dynamics', 'primer': None },
    # {'name': 'performance_rnn', 'bundle': 'performance_with_dynamics_and_modulo_encoding', 'primer': None },

    # Pianoroll RNN
    # {'name': 'pianoroll_rnn_nade', 'bundle': 'rnn-nade_attn', 'primer': 'dataset/clean_jsb-chorales/000206b_.mid' },
    # {'name': 'pianoroll_rnn_nade', 'bundle': 'rnn-nade', 'primer': None },
    # {'name': 'pianoroll_rnn_nade', 'bundle': 'pianoroll_rnn_nade', 'primer': 'dataset/clean_jsb-chorales/000206b_.mid' },
    # {'name': 'pianoroll_rnn_nade', 'bundle': 'pianoroll_rnn_nade-bach', 'primer': None },

    # Polyphony RNN
    # {'name': 'polyphony_rnn', 'bundle': 'polyphony_rnn', 'primer': 'dataset/clean_jsb-chorales/000206b_.mid' },
]


# models = models[:4] # melody_rnn
# models = [models[-1]] + models[:4]
# models = [models[-1]]

# models = [{'name': 'pianoroll_rnn_nade', 'bundle': 'rnn-nade_attn', 'primer': None }]
# models = [model for model in models if model['name'] == 'pianoroll_rnn_nade']
# models = [{'name': 'performance_rnn', 'bundle': 'performance_with_dynamics', 'primer': None }]

base_sys_path = sys.path.copy()

class TestModelGeneration(unittest.TestCase):
    def setUp(self):
      for model in models:
        for primer in [None, model['primer']]:
          with self.subTest(model=model):
            self.host = Host(args)
            # if primer:
            #   self.host.song = Song(self.host)
            #   self.host.song.load(primer)
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
            for _ in range(16): self.generate(1,'bars')
            self.assertEqual(16, self.total_length())
    


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


# # TODO: Move to test_engine
# class TestModelCall(unittest.TestCase):
#     def setUp(self):
#       self.host = Host(args)
#       self.host.model.generate = MagicMock()
#       
#     def test_generate_call(self):
#       self.host.engine.generate(1,'bars')
#       self.host.model.generate.assert_called_with(ANY, 4, ANY)















class TestModelGenerationFromPrimer(unittest.TestCase):
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
      self.host.set('input_length', 4)
      
      primer = model['primer']
      self.host.song = Song(self.host)
      self.host.song.load(primer, 4, 'bars')
    
    def test_repeated_generation(self):
      """ WHEN Generating 1 bar at a time, 16 times SHOULD generate exactly 16 bars """
      for model in models:
        for repetition in range(2):
          with self.subTest(model=model, repetition=repetition):
            self.host.song.reset()
            self.initialize(model)
            self.host.song.show()
            self.assertEqual(4, self.host.song.total_length('bars'))
            self.initialize(model)
            for _ in range(16): self.generate(1,'bars')
            self.host.song.drop_primer()
            self.assertEqual(16, self.total_length())


class TestAllPrimers(unittest.TestCase):
    def setUp(self):
      for model in models:
        with self.subTest(model=model):
          self.host = Host(args)
          self.model = None
          self.total_length = None
          self.generate = None
          sys.path = base_sys_path.copy()
          args.module = model["name"]
          args.checkpoint = model["bundle"]
          reload(host)
          reload(data)
          self.model = load_model(self.host,args.checkpoint,f'modules/{args.module}')
          self.host.model = self.model
          self.host.song = Song(self.host)

    def test_generate_ok(self):
      unit = 'bars'
      for model in models:
        dataset = '/' + os.path.join(*model['primer'].split('/')[:-1])
        self.assertTrue(os.path.exists(dataset))
        for primer in os.listdir(dataset):
          with self.subTest(model=model, primer=primer):
            self.host.song.load(os.path.join(dataset,primer))
            self.host.engine.generate_to(16, unit)
            self.host.song.drop_primer()

            real_length = self.host.song.total_length(unit)
            real_length = int(round(real_length))
            self.assertEquals(real_length, 16)
            # self.assertGreater(len(os.listdir(dataset)), 1)
