import unittest
import sys
from os import path
import os

sys.path.append(os.path.abspath('server'))
from server.host import Host
from tests.common import args

from unittest.mock import MagicMock, ANY

class TestEngine(unittest.TestCase):
    def setUp(self):
      self.host = Host(args)
      self.host.model.generate = MagicMock()


    def test_initial_last_end_time(self):
      self.assertEqual(self.host.get('last_end_time'), 0)

    def test_generate_interval(self):
      self.host.engine.generate(3,'bars')
      self.assertEqual(self.host.get('last_end_time'), 12)

    def test_engine_reset_index(self):
      self.host.engine.generate(3,'bars')
      self.host.engine.generate(3,'bars')
      self.host.reset()
      self.assertEqual(self.host.get('last_end_time'), 0)

    def test_generate_interval_successive_generations(self):
      # self.host.model.generate = MagicMock()
      self.host.engine.generate(2,'bars')
      self.host.model.generate.assert_called_with(ANY, 8, ANY)
      self.host.engine.generate(3,'bars')
      self.host.model.generate.assert_called_with(ANY, 12, ANY)
      self.assertEqual(self.host.get('last_end_time'), 20)


    def test_get_quantized_steps(self):
      self.host.engine.generate(3,'bars')
      self.assertEqual(self.host.engine.get_quantized_steps(), 12)
    
    def test_generate_add_(self):
      self.host.engine.generate(3,'bars')
      self.assertEqual(self.host.engine.get_quantized_steps(), 12)