import unittest
import sys
from os import path, listdir
from mido import Message

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
        self.file = path.join(self.datadir, files[11])

        self.song = Song(self.host)
        self.song.load(self.file)
        print(f'testing with file: {self.file}')

    # @classmethod
    def tearDown(self):
        pass

    def test_total_ticks(self):
      self.assertEqual(8159, self.song.total_ticks())

    def test_drop_primer_no_generation(self):
      self.assertEqual(8159, self.song.total_ticks())
      self.song.drop_primer()
      self.assertEqual(0, self.song.total_ticks())

    def test_drop_primer(self):
      self.assertEqual(8159, self.song.total_ticks())
      self.song.drop_primer()
      for i in range(10):
        self.song.append(Message('note_on', note=64, time=480, velocity=80), 0)
      self.assertEqual(4800, self.song.total_ticks())

    def test_crop_from_start(self):
      """ A crop should remove exactly the requested number of bars from the start of the song
      """
      
      self.song.crop('bars', 3, 4)
      print(self.song.total_ticks())
      self.assertLessEqual(self.song.to_ticks(1, 'bars'), self.song.total_ticks())

    # def test_drop_primer(self):
      # Load primer, save length
      # add many MidiMessage note_on/offs
      # call drop_primer
      # check total_ticks
      # pass

    # def test_crop_from_end(self):
    #   """ A crop should remove exactly the requested number of bars from the start of the song
    #   """
    #   # song = Song(self.host, self.file)
    #   self.assertEqual('foo'.upper(), 'FOO')
    
    # def test_buffer(self):
    #   """ IF a buffer longer than the current song is requested
    #       It should return the entire song
    #   """
    #   self.assertEqual('foo'.upper(), 'FOO')
