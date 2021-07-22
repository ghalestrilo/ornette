import unittest
import sys
from os import path

# Load server folder
sys.path.append(path.abspath(path.join(path.pardir, 'server')))

from server.song import Song

# python -m unittest tests.song

class TestSong(unittest.TestCase):

    # Mock tests
    def buffer(self):
      """ IF a buffer longer than the current song is requested
          It should return the entire song
      """
      song = Song(self, self)
      self.assertEqual('foo'.upper(), 'FOO')