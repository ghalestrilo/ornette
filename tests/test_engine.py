import unittest
import sys
from os import path
import os
import mido

sys.path.append(os.path.abspath('server'))
from server.host import Host
from server.song import Song
from tests.common import args

from unittest.mock import MagicMock, ANY

class TestEngine(unittest.TestCase):
    def setUp(self):
      self.host = Host(args)
      self.host.model.generate = MagicMock()
      self.host.set('guarantee_two_notes', False)

    def test_generate_interval_successive_generations(self):
      # self.host.model.generate = MagicMock()
      self.host.engine.generate(2,'bars')
      self.host.model.generate.assert_called_with(ANY, 8, ANY)
      self.host.engine.generate(3,'bars')
      self.host.model.generate.assert_called_with(ANY, 12, ANY)
      self.assertEqual(self.host.get('generation_start'), 20)


    def test_get_quantized_steps(self):
      self.host.engine.generate(3,'bars')
      self.assertEqual(self.host.engine.get_quantized_steps(), 12)
    
    def test_generate_add_(self):
      self.host.engine.generate(3,'bars')
      self.assertEqual(self.host.engine.get_quantized_steps(), 12)


class TestGenerateCall(unittest.TestCase):
    def setUp(self):
      self.host = Host(args)
      self.host.model.generate = MagicMock()
      self.host.set('guarantee_two_notes', False)
      
    def test_correct_length_requested(self):
      self.host.engine.generate(1,'bars')
      self.host.model.generate.assert_called_with(ANY, 4, ANY)


class TestGenerationRange(unittest.TestCase):
    def setUp(self):
      self.host = Host(args)
      self.host.song = Song(self.host)
      self.host.set('guarantee_two_notes', False)
      self.host.model.generate = MagicMock()
      self.generated_output = [[mido.Message('note_on' if i % 2 == 0 else 'note_off', note= 60 + (i % 20), time = 1000) for i in range(100)]]
      self.host.model.generate.return_value = self.generated_output

    def test_initial_generation_start(self):
      self.assertEqual(self.host.get('generation_start'), 0)

    def test_generate_interval(self):
      self.host.engine.generate(3,'bars')
      self.assertEqual(self.host.get('generation_start'), 12)

    def test_engine_reset_generation_start(self):
      self.host.engine.generate(3,'bars')
      self.host.engine.generate(3,'bars')
      self.host.reset()
      self.assertEqual(self.host.get('generation_start'), 0)

    def test_correct_length_requested(self):
      self.host.engine.generate(1,'bars')
      self.host.model.generate.assert_called_with(ANY, 4, ANY)

    def test_output_larger_than_requested(self):
      """ WHEN generated output is longer than expected SHOULD trim it to fulfill exactly the desired length
      """
      self.host.engine.generate(3,'bars')
      self.host.model.generate.assert_called()
      self.assertEqual(self.host.get('generation_start'), 3*4)
      self.assertEqual(self.host.song.total_length('bars'), 3)

    def test_output_shorter_than_expected(self):
      """ WHEN generated output is shorter than expected SHOULD pad it to fulfill exactly the desired length
      """
      self.host.model.generate.return_value = [tr[:4] for tr in self.generated_output]
      self.host.engine.generate(3, 'bars')
      self.host.song.show()
      print(self.host.song.get_track_length(self.host.song.data.tracks[0]))
      print(self.host.song.get_track_length(self.host.song.data.tracks[1]))
      self.host.model.generate.assert_called()
      self.assertEqual(self.host.get('generation_start'), 3*4)
      self.assertEqual(self.host.song.total_length('bars'), 3)





class TestGenerateTo(unittest.TestCase):
  # mock.assert_has_calls(calls, any_order=True)
    def setUp(self):
      self.host = Host(args)
      self.host.song = Song(self.host)
      self.host.model.generate = MagicMock()
      self.host.set('guarantee_two_notes', False)
      beatlen = self.host.song.to_ticks(1, 'beats')
      self.generated_output = self.create_note_sequence(50, beatlen)
    
    def create_note_sequence(self, notecount, beatlen):
      return [[mido.Message('note_on' if i % 2 == 0 else 'note_off', note= 60 + (i % 20), time = beatlen) for i in range(notecount*2)]]

    def test_output_shorter_than_expected(self):
      for beatlen in [50, 100, 69, 134]:
      # for beatlen in [69, 134]:
      # for beatlen in range(1,199):
        for length in [4,8,9,16]:
          with self.subTest(length=length, beatlen=beatlen):
            self.host.song.reset()
            self.host.model.generate.return_value = self.create_note_sequence(8,beatlen)
            self.host.engine.generate_to(length)
            # self.host.song.show()
            self.assertEquals(self.host.song.total_length('bars'),length)