import unittest
import sys
from os import path
import os
from mido import MidiFile, Message
from pprint import pprint

# docker run -it -v $(pwd):/ornette ornette/melody_rnn bash -c "python -m unittest tests/filters/magenta.py"

sys.path.append(os.path.abspath('server'))
from server.filter_defs.magenta import filters
from server.host import Host
from tests.common import args

from note_seq import NoteSequence

def make_note_sequence(list_of_tuples):
  return [
        NoteSequence.Note(instrument=0,program=0,start_time=round(start_time,2),end_time=round(end_time,2),velocity=velocity,pitch=pitch)
        for (pitch, velocity, start_time, end_time)
        in list_of_tuples
      ]

def make_noteseq(list_of_tuples, spq):
  return NoteSequence(
        notes=make_note_sequence(list_of_tuples),
        quantization_info={ 'steps_per_quarter': spq, },
        tempos=[{ 'time': 0, 'qpm': 120 }],
        total_quantized_steps=6 * 4
      )

sample_track = [ (65, 29, 1.5000, 3.0000)
        , (63, 25, 3.0100, 3.7900)
        , (55, 45, 3.2000, 3.2900)
        , (46, 25, 3.2500, 3.8900)
        , (39, 25, 3.2600, 3.3100)
        , (57, 53, 3.7900, 3.8900)
        , (60, 53, 3.8800, 6.0000)
        , (44, 29, 4.6500, 4.7200)
        , (39, 25, 4.6600, 4.7200)
        , (45, 41, 4.7200, 5.7300)
        , (39, 49, 4.7300, 5.7300)
        , (37, 49, 5.5100, 5.5600)
        , (37, 49, 5.5600, 5.7300)
        , (38, 45, 5.6600, 6.0000)
        ]

class TestMagentaFilters(unittest.TestCase):
    def setUp(self):
      self.maxDiff = None
      self.host = Host(args)
      self.host.set('is_velocity_sensitive', True)
      self.orig_notes = sample_track
      self.notes = make_note_sequence(self.orig_notes)

      steps_per_quarter = self.host.get('steps_per_quarter')
      self.noteseq = make_noteseq(self.orig_notes, steps_per_quarter)
      self.host.set('input_length', 4)
      self.host.set('input_unit', 'beats')
      self.host.set('generation_requested_beats', 4)

    def apply_filter(self, seq, filtername):
      """ Apply filter to a single track, return the converted output
      """
      return filters[filtername]([seq], self.host)[0]

    def test_noteseq2midotrack_length(self):
      """ WHEN converting a section with noteseq2midotrack
          SHOULD return the same number of bars
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
      notes = self.apply_filter(notes, 'noteseq2midotrack')
      notes = self.apply_filter(notes, 'mido_track_sort_by_time')
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

    # Large tests (create new case)


    # Mock tests
    def test_noteseq_loop(self):
      """ Converting to-from a noteseq should return the same result
      """
      datadir = os.path.join('dataset', 'clean_mtd-orig')
      testfile = os.listdir(datadir)[0]
      
      mid = MidiFile(os.path.join(datadir, testfile))
      track = mid.tracks[0]
      track = [ msg for msg in track if not msg.is_meta and msg.type in ['note_on', 'note_off'] ]
      output = self.apply_filter(track, 'midotrack2noteseq')
      output = self.apply_filter(output, 'noteseq2midotrack')
      output = self.apply_filter(output, 'mido_track_sort_by_time')
      output = self.apply_filter(output, 'mido_track_subtract_previous_time')
      track = self.apply_filter(track, 'mido_track_add_note_offs')
      # self.assertSequenceEqual(track, output)



    # Default filters
    def test_midotrack_sort_by_time(self):
      datadir = os.path.join('dataset', 'clean_mtd-orig')
      testfile = os.listdir(datadir)[0]
      
      mid = MidiFile(os.path.join(datadir, testfile))
      track = mid.tracks[0]
      track = [ msg for msg in track if not msg.is_meta and msg.type in ['note_on', 'note_off'] ]
      output = self.apply_filter(track, 'midotrack2noteseq')
      output = self.apply_filter(output, 'noteseq2midotrack')
      output = self.apply_filter(output, 'mido_track_sort_by_time')
      track = self.apply_filter(track, 'mido_track_add_note_offs')
      errs = []

      total_time = 0
      for i, note in enumerate(output):
        total_time += track[i].time
        if total_time != note.time:
          errs += [(i, total_time, note.time, note)]
      self.assertSequenceEqual(errs, [])



class TestTrimFilters(unittest.TestCase):
    def setUp(self):
      self.maxDiff = None
      self.host = Host(args)
      self.host.set('is_velocity_sensitive', True)
      self.host.set('input_length', 4)
      self.host.set('input_unit', 'beats')
      self.host.set('generation_requested_beats', 4)

      # Test Subjects
      self.orig_notes = sample_track
      steps_per_quarter = self.host.get('steps_per_quarter')
      self.notes = make_note_sequence(self.orig_notes)
      self.noteseq = make_noteseq(self.orig_notes, steps_per_quarter)
      self.notes_trimmed_at_start = self.apply_filter(self.noteseq, 'noteseq_trim_start')
      self.notes_trimmed_at_end = self.apply_filter(self.noteseq, 'noteseq_trim_end')

      # Test Truth Values
      self.orig_notes_trimmed_at_start = [(n,v,s-4,e-4) for (n,v,s,e) in self.orig_notes[-7:]]
      self.orig_notes_trimmed_at_start = make_noteseq(self.orig_notes_trimmed_at_start, self.host.get('steps_per_quarter'))
      self.orig_notes_trimmed_at_end = self.orig_notes[:7]
      self.orig_notes_trimmed_at_end = make_noteseq(self.orig_notes_trimmed_at_end, self.host.get('steps_per_quarter'))
      self.orig_notes_trimmed_at_end.notes[-1].end_time = 4.0

    def apply_filter(self, seq, filtername):
      """ Apply filter to a single track, return the converted output
      """
      return filters[filtername]([seq], self.host)[0]

    def test_noteseq_trim_start_notecount(self):
      """ WHEN trimming the start of a sequence SHOULD return correct number of notes
      """
      self.assertEqual(len(self.notes_trimmed_at_start.notes), len(self.orig_notes_trimmed_at_start.notes))
    
    def test_noteseq_trim_start_sequence(self):
      """ WHEN trimming the start of a sequence SHOULD return only the end of the original sequence
      """
      self.assertSequenceEqual(self.notes_trimmed_at_start.notes, self.orig_notes_trimmed_at_start.notes)

    def test_noteseq_trim_start_displacement(self):
      """ WHEN trimming the start of a sequence SHOULD left-shift the sequence exactly the requested length
      """
      self.assertEqual(self.notes_trimmed_at_start.notes[0].start_time, self.orig_notes_trimmed_at_start.notes[0].start_time)

    def test_noteseq_trim_interchangeable(self):
      """ WHEN trimming a sequence SHOULD return the same value if trimming start-first or end-first
      """
      end_first = self.apply_filter(self.notes_trimmed_at_end, 'noteseq_trim_start')
      start_first = self.apply_filter(self.notes_trimmed_at_start, 'noteseq_trim_end')
      self.assertEqual(len(start_first.notes), len(end_first.notes))
      self.assertSequenceEqual(start_first.notes, end_first.notes)


    # def test_noteseq_trim_end(self):
    #   """ WHEN a sequence goes beyond the requested generation length SHOULD be trimmed to the requested length
    #   """ 
    #   self.assertEqual(len(self.notes_trimmed_at_start), len(self.orig_notes_trimmed_at_start))
    #   self.assertSequenceEqual(self.notes_trimmed_at_start, self.orig_notes_trimmed_at_start)
