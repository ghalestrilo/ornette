import unittest
import sys
from os import path
import os
from mido import MidiFile
from pprint import pprint

# docker run -it -v $(pwd):/ornette ornette/melody_rnn bash -c "python -m unittest tests/filters/magenta.py"

sys.path.append(os.path.abspath('server'))
from server.filter_defs.magenta import filters
from server.host import Host
from tests.common import args

from note_seq import NoteSequence

class TestMagentaFilters(unittest.TestCase):
    def setUp(self):
      self.host = Host(args)
      self.host.set('is_velocity_sensitive', True)
      self.notes = (
        [ (65, 29, 1.5000, 3.0000)
        , (55, 45, 3.2000, 3.2900)
        , (39, 25, 3.2600, 3.3100)
        , (63, 25, 3.0100, 3.7900)
        , (46, 25, 3.2500, 3.8900)
        , (57, 53, 3.7900, 3.8900)
        , (44, 29, 4.6500, 4.7200)
        , (39, 25, 4.6600, 4.7200)
        , (37, 49, 5.5100, 5.5600)
        , (37, 49, 5.5600, 5.7300)
        , (39, 49, 4.7300, 5.7300)
        , (45, 41, 4.7200, 5.7300)
        , (60, 53, 3.8800, 6.0000)
        , (38, 45, 5.6600, 6.0000)
        ]
      )
      self.notes = [
        NoteSequence.Note(instrument=0,program=0,start_time=start_time,end_time=end_time,velocity=velocity,pitch=pitch)
        for (pitch, velocity, start_time, end_time)
        in self.notes
      ]

      steps_per_quarter = self.host.get('steps_pe_quarter')
      self.noteseq = NoteSequence(
        notes=self.notes,
        quantization_info={ 'steps_per_quarter': steps_per_quarter, },
        tempos=[{ 'time': 0, 'qpm': 120 }],
        total_quantized_steps=6 * 4
      )

    def test_noteseq2midotrack_length(self):
      """ Barcount of output sequence should be equal to the input
      """
      song = self.host.song
      input_length = max(note.end_time for note in self.notes)
      input_length = song.convert(input_length, 'beats', 'bars')
      notes = filters['noteseq2midotrack']([self.noteseq], self.host)[0]
      notes = filters['mido_track_sort_by_time']([notes], self.host)[0]
      notes = filters['mido_track_subtract_previous_time']([notes], self.host)[0]
      output_length = sum(msg.time for msg in notes)
      output_length = song.from_ticks(output_length, 'bars')
      self.assertEqual(input_length, output_length)

    def test_press_release_count(self):
      notes = self.noteseq
      notes = self.applyFilter(notes, 'noteseq2midotrack')
      notes = self.applyFilter(notes, 'mido_track_sort_by_time')
      note_ons = [msg for msg in notes if not msg.is_meta and msg.type == 'note_on']
      note_offs = [msg for msg in notes if not msg.is_meta and msg.type == 'note_off']
      self.assertEqual(len(note_ons), len(note_offs))

    def test_press_release(self):
      """ Notes should have a `note_on` event before a `note_off`
      """
      notes = filters['noteseq2midotrack']([self.noteseq], self.host)[0]
      notes = filters['mido_track_sort_by_time']([notes], self.host)[0].copy()
      errs = []
      presses = enumerate(filter(lambda msg: msg.type == 'note_on', notes))
      for i, press in presses:
        # Search rest of buffer
        note_matched = False
        for release in filter(lambda msg: msg.time > press.time, notes):
          # If a release was found
          if release.note == press.note:
            notes.remove(release)
            note_matched = True
            break

        # If no release was found
        if not note_matched: errs += [(i, press)]


      self.assertEqual(errs, [])


    def applyFilter(self, seq, filtername):
      """ Apply filter to a single track, return the converted output
      """
      return filters[filtername]([seq], self.host)[0]




    # Large tests (create new case)


    # Mock tests
    def test_noteseq_loop(self):
      """ Converting to-from a noteseq should return the same result
      """
      datadir = os.path.join('dataset', 'clean_mtd-orig')
      testfile = os.listdir(datadir)[0]
      
      mid = MidiFile(os.path.join(datadir, testfile))
      self.maxDiff = None
      track = mid.tracks[0]
      track = [ msg for msg in track if not msg.is_meta and msg.type in ['note_on', 'note_off'] ]
      output = self.applyFilter(track, 'midotrack2noteseq')
      output = self.applyFilter(output, 'noteseq2midotrack')
      output = self.applyFilter(output, 'mido_track_sort_by_time')
      output = self.applyFilter(output, 'mido_track_subtract_previous_time')
      # output = list(filter(lambda msg: msg.type == 'note_on', output))
      # pprint(output)
      track = self.applyFilter(track, 'mido_track_add_note_offs')
      # pprint(track)
      # self.assertSequenceEqual(len(track), len(output))
      self.assertSequenceEqual(track, output)



    # Default filters
    def test_midotrack_sort_by_time(self):
      datadir = os.path.join('dataset', 'clean_mtd-orig')
      testfile = os.listdir(datadir)[0]
      
      mid = MidiFile(os.path.join(datadir, testfile))
      self.maxDiff = None
      track = mid.tracks[0]
      track = [ msg for msg in track if not msg.is_meta and msg.type in ['note_on', 'note_off'] ]
      output = self.applyFilter(track, 'midotrack2noteseq')
      output = self.applyFilter(output, 'noteseq2midotrack')
      output = self.applyFilter(output, 'mido_track_sort_by_time')
      track = self.applyFilter(track, 'mido_track_add_note_offs')
      pprint(track)
      errs = []

      total_time = 0
      for i, note in enumerate(output):
        total_time += track[i].time
        if total_time != note.time:
          errs += [(i, total_time, note.time, note)]
      self.assertSequenceEqual(errs, [])
