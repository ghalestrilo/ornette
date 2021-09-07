import unittest
import sys
from os import path, listdir
from mido import Message

# Load server folder
sys.path.append(path.abspath(path.join('server')))

from server.song import Song
from server.host import Host
from tests.common import args

# python -m unittest tests.song


# TODO: Add these messages, create a new test case
# <meta message time_signature numerator=4 denominator=4 clocks_per_click=24 notated_32nd_notes_per_beat=8 time=0>
# <meta message key_signature key='Eb' time=0>
# <meta message set_tempo tempo=500000 time=0>

# primer_singletrack = 'dataset/clean_mtd-orig/MTD0391_Bach_BWV0847-01.mid'
primer_singletrack = 'dataset/clean_lakh/The_Doobie_Brothers_-_Listen_to_the_Music.1.mid'
primer_multitrack = 'dataset/clean_bach10/01-AchGottundHerr.mid'

class TestSongEmpty(unittest.TestCase):
    def setUp(self):
          self.host = Host(args)
          self.song = Song(self.host)
          self.host.song = self.song
    
    # TODO
    # def init_conductor(self):

    def add_message(self, note=64, time=480):
      self.song.append(Message('note_on', note=note, time=time, velocity=80), 1)
      
    
    def test_buffer_length(self):
      """ Buffer Length should be 0
      """
      self.assertEqual(self.song.get_buffer_length(), 0)
    
    def test_load_track_count(self):
      subject = lambda: len(self.song.data.tracks)
      self.song.load(primer_singletrack, 8000) # Type 1 (conductor + track)
      self.assertEqual(2, subject())
      self.song.load(primer_multitrack, 8000) # Type 1 (conductor + track + track + track + track)
      self.assertEqual(5, subject())

    def test_drop_primer_no_repeat(self):
      """ WHEN calling drop_primer twice in succession SHOULD not crop output again
      """
      num_msgs = 10
      len_msg = 480
      for i in range(num_msgs): self.add_message(i + 64)
      self.song.drop_primer()
      self.song.show()
      self.assertEqual(num_msgs * len_msg, self.song.total_ticks())
      self.song.drop_primer()
      self.song.drop_primer()
      self.song.drop_primer()
      self.song.show()
      self.assertEqual(num_msgs * len_msg, self.song.total_ticks())





    def test_get_track_length_only_track(self):
      """ WHEN there is only one track SHOULD always equal song#total_ticks()
      """
      subject = lambda : self.song.get_track_length(self.song.data.tracks[1])
      self.song.reset()
      for i in range(10):
        self.add_message()
        self.assertEqual(self.song.total_ticks(), subject())
        self.assertEqual((i+1)*480, subject())

class TestSongFile(unittest.TestCase):
    def setUp(self):
        self.host = Host(args)
        self.host.song = Song(self.host)
        # self.datadir = 'dataset/clean_mtd-orig'
        self.datadir = 'dataset/clean_lakh'
        files = listdir(self.datadir)
        self.file = path.join(self.datadir, files[2])

        self.song = self.host.song
        self.song.load(self.file)
        print(f'testing with file: {self.file}')
        # self.host.set('preserve_conductor', False)

    # @classmethod
    def tearDown(self):
        pass

    def test_get_track_length(self):
      self.host.song.reset()
      for i in range(10): self.add_message()
      self.assertEqual(10 * 480, self.host.song.get_track_length(self.host.song.data.tracks[1]))
    
    def test_total_ticks(self):
      self.assertEqual(92160, self.song.total_ticks())

    def test_buffer_length(self):
      """ Buffer Length should be 
      """
      self.host.set('input_length', 4)
      self.host.set('input_unit', 'beats')
      self.assertEqual(self.song.get_buffer_length(unit='bars'), 1)
    
    def test_buffer_length_larger_than_song(self):
      """ WHEN requested buffer is longer than entire song
          SHOULD return total song ticks
      """
      self.host.set('input_length', 400000)
      self.host.set('input_unit', 'bars')
      ticks = int(round(self.song.get_buffer_length(unit='ticks')))
      self.assertEqual(ticks, self.song.total_ticks())

    def test_drop_primer_no_generation(self):
      self.song.drop_primer()
      self.assertEqual(0, self.song.total_ticks())


    def add_message(self, note=64, time=480):
      self.song.append(Message('note_on', note=note, time=time, velocity=80), 1)


    def test_drop_primer_no_repeat(self):
      """ WHEN calling drop_primer twice in succession SHOULD not crop output again
      """
      num_msgs = 10
      len_msg = 480
      for i in range(num_msgs): self.add_message(i + 64)
      self.song.drop_primer()
      # self.song.show()
      self.assertEqual(num_msgs * len_msg, self.song.total_ticks())
      self.song.drop_primer()
      self.assertEqual(num_msgs * len_msg, self.song.total_ticks())
      self.song.drop_primer()
      self.song.drop_primer()
      self.song.show()
      self.assertEqual(num_msgs * len_msg, self.song.total_ticks())






    def test_get_track_length_only_track(self):
      """ WHEN there is only one track SHOULD always equal song#total_ticks()
      """
      subject = lambda : self.song.get_track_length(self.song.data.tracks[1])
      self.song.reset()
      for i in range(10):
        self.add_message()
        self.assertEqual(self.song.total_ticks(), subject())
        self.assertEqual((i+1)*480, subject())










    def test_get_track_length_after_reset(self):
      """ WHEN track has been reset SHOULD return the correct value
      """
      subject = lambda : self.song.get_track_length(self.song.data.tracks[1])
      self.song.reset()
      self.host.set('output_tracks', [1])
      self.assertEqual(0, subject())
      for i in range(10): self.add_message()
      self.assertEqual(4800, subject())

    def test_drop_primer(self):
      """ WHEN music data has been generated SHOULD preserve the generated output """
      subject = lambda : self.song.total_ticks()
      for i in range(10):
        self.song.append(Message('note_on', note=64, time=480, velocity=80), 0)
      self.song.drop_primer()
      self.assertEqual(4800, subject())

    def test_drop_primer_preserve_header(self):
      """ WHEN a track was loaded SHOULD preserve initial meta_messages """
      for msgtype in ['time_signature', 'set_tempo']:
        with self.subTest(msgtype=msgtype):
          self.setUp()
          metamsg = next(msg for msg in self.song.data if msg.type == msgtype)
          self.song.drop_primer()
          self.assertIn(metamsg, self.song.data.tracks[0])

    def test_crop_from_start(self):
      """ A crop should remove exactly the requested number of bars from the start of the song
      """
      
      self.song.crop('bars', 3, 4)
      self.assertLessEqual(self.song.to_ticks(1, 'bars'), self.song.total_ticks())

    def test_crop_from_start_preserve_header(self):
      """ A crop should remove exactly the requested number of bars from the start of the song
      """
      subject = lambda: self.song.data.tracks[0][0:3]
      header_before = subject().copy()
      self.song.crop('bars', 3, 4)
      self.assertSequenceEqual(header_before, subject())

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










class TestBuffer(unittest.TestCase):
    def setUp(self):
      self.host = Host(args)
      self.song = Song(self.host)
      self.host.song = self.song

      # Load a song
      # self.datadir = 'dataset/clean_mtd-orig'
      self.datadir = 'dataset/clean_lakh'
      files = listdir(self.datadir)
      self.file = path.join(self.datadir, files[3])
      self.song.load(self.file)
      self.maxDiff = None
      # print(f'testing with file: {self.file}')
    
    def tearDown(self):
        pass

    def test_buffer_all_tracks(self):
      """ WHEN generating a buffer SHOULD include all song tracks
      """
      subject = lambda: self.host.song.buffer(100000)
      self.assertEqual(len(self.song.data.tracks), 2)
      self.assertEqual(len(subject()), len(self.song.data.tracks))

    def test_buffer_consistent(self):
      """ WHEN generating a buffer with the same parameters SHOULD return the same buffer
      """
      for i in range(10):
        subject = lambda: self.host.song.buffer(100 * i)
        self.assertSequenceEqual(subject(), subject())
    
    def test_buffer_not_empty(self):
      """ WHEN generating a buffer from tracks with data SHOULD return data
      """
      self.song.load(self.file)
      self.assertEqual(len(self.song.data.tracks), 2)
      buffer = self.host.song.buffer(100000)
      self.assertGreater(len(buffer), 0)
      for track in buffer: self.assertGreater(len(track), 0)


    def test_buffer_one_sequence_longer_than_others(self):
      """ WHEN one track has more messages than others SHOULD pad other sequences
      """
      subject = lambda: self.host.song.buffer(1000) # Few final notes
      self.host.set('output_tracks', 2)        # Add an empty track

      for _ in range(10):  self.song.append(Message('note_on', note=64, time=200, velocity=80), 1) # Populate first track (non-conductor)
      self.assertEqual(3,len(subject()))                                                           # Should have 3 tracks (conductor + track + track)
      self.assertIn(subject()[0][-1], subject()[0])                                                # Assert conductor is not empty or corrupted

      last_track = subject()[-1]

      self.assertEqual(False, any(filter(lambda msg: msg.type != 'end_of_track', last_track)))         # Only the `end_of_track` message should be present
      # self.assertEqual(self.song.get_buffer_length('ticks'), sum(msg.time for msg in last_track)) # The `end_of_track` message should have the buffer length
      self.assertEqual(0, sum(msg.time for msg in last_track))



    def test_buffer_entire_song(self):
      """ IF a buffer longer than the current song is requested
          It should return the entire song
      """
      subject = lambda: self.host.song.buffer(10000000)
      get_notes = lambda seqs: [[msg for msg in seq if hasattr(msg, 'type') and msg.type.startswith('note_')] for seq in seqs]
      notes_song  = get_notes(self.song.data.tracks)
      notes_buffer = get_notes(subject())
      self.assertSequenceEqual(notes_song, notes_buffer)