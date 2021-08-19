import unittest
import sys
from os import path, listdir

# Load server folder
sys.path.append(path.abspath(path.join('server')))

from server.song import Song
from server.host import Host
from server.args import get_arg_parser

# TODO: move to 
test_args = get_arg_parser().parse_args(['--module','melody_rnn','--checkpoint','attention_rnn','--no-server','True','--no-module=True'])


# python -m unittest tests.song

class TestSong(unittest.TestCase):
    # @classmethod
    def setUp(self):
        self.host = Host(test_args)
        self.datadir = 'dataset/clean_mtd-orig'
        files = listdir(self.datadir)
        self.file = path.join(self.datadir, files[10])
        print(f'testing with file: {self.file}')
        # self.host.set('log_level', 0)

    # @classmethod
    def tearDown(self):
        pass

    def test_buffer(self):
      """ IF a buffer longer than the current song is requested
          It should return the entire song
      """
      self.assertEqual('foo'.upper(), 'FOO')

    def test_crop_from_start(self):
      """ A crop should remove exactly the requested number of bars from the start of the song
      """
      song = Song(self.host)
      song.load(self.file)
      song.crop('bars', 3, 4)
      print(song.total_ticks())
      self.assertEqual(song.total_ticks(), song.to_ticks(1, 'bars'))

    def test_crop_from_end(self):
      """ A crop should remove exactly the requested number of bars from the start of the song
      """
      # song = Song(self.host, self.file)
      self.assertEqual('foo'.upper(), 'FOO')