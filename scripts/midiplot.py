# %%
from visual_midi import Plotter
from visual_midi import Preset
from pretty_midi import PrettyMIDI

dirr = f'/home/ghales/git/tg-server/'

#midi_infile = f'{dirr}tests/tantan.mid'
midi_infile = f'{dirr}tests/dire.mid'

# Loading a file on disk using PrettyMidi, and show
pm = PrettyMIDI(midi_infile)
plotter = Plotter()
plotter.show(pm, "{dirr}dire.html")
plotter.show_notebook(pm)

# # Converting to PrettyMidi from another library, like Magenta note-seq
# import magenta.music as mm
# pm = mm.midi_io.note_sequence_to_pretty_midi(sequence)
# plotter = Plotter()
# plotter.show(pm, "/tmp/examfple-02.html")


# %%
# Load and format form answers
track = m_gt.get_singletrack_by_name("09_XX_BASS")

plots = midiprocessing.Pianoroll()
track = midi.get_singletrack_by_name("09_XX_BASS")
plots.plot_singletrack_pianoroll(track, axis='time'         plot_title="Track n. {}".format(track["n_track"]))
    
plots.plot_all_tracks(all_tracks, axis='bar')
