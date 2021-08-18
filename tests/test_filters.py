import unittest
import sys
from os import path
import os
from mido import MidiFile


sys.path.append(os.path.abspath('server'))
from server.filter_defs.magenta import filters
# from server.song import Song
# from server.logger import Logger
from server.host import Host
from server.args import get_args


from unittest.mock import patch

# with patch('argparse._sys.argv', ['--no-server', 'True', '--model', 'melody_rnn', '--checkpoint', 'attention_rnn']):
# @patch('argparse._sys.argv', ['--no-server', 'True', '--model', 'melody_rnn', '--checkpoint', 'attention_rnn'])
@patch('argparse._sys.argv', ['--no-server', 'True', '--model', 'melody_rnn', '--checkpoint', 'attention_rnn'])
class TestFilters(unittest.TestCase):

    # Mock tests
    def test_noteseq(self):
      """ Converting to-from a noteseq should return the same result
      """
      datadir = os.path.join('dataset', 'clean_mtd-orig')
      testfile = os.listdir(datadir)[0]

      # host = MockHost()
      args = get_args()
      host = Host(args)
      
      mid = MidiFile(os.path.join(datadir, testfile))
      tracks = mid.tracks
      output = filters['midotrack2noteseq'](tracks, host)
      output = filters['noteseq2midotrack'](output, host)
      self.assertSequenceEqual(tracks, output)