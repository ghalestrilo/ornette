import unittest, os, sys, shutil, mido

# Load server folder
sys.path.append(os.path.abspath(os.path.join('server')))
from scripts.analysis_scripts import preprocess, extract_metrics, script_output_bpm, desired_seconds




def get_file_length(filename):
  return mido.MidiFile(filename).length

def get_file_tempo(filename):
  return next(msg for msg in mido.MidiFile(filename) if msg.type == 'set_tempo').tempo

def get_file_bpm(filename):
  return mido.tempo2bpm(get_file_tempo(filename))


data = lambda *args: os.path.abspath(os.path.join(os.curdir, 'tests', 'data', *args))
files = []
for dirr in ['generated', 'dataset']:
  files += [(dirr, filename) for filename in os.listdir(data(dirr))]

metricsfile = data('metrics')



class TestPreprocessScript(unittest.TestCase):
    @classmethod
    def setUpClass(self):
      if os.path.exists(metricsfile): os.remove(metricsfile)
      for folder in ['preprocessed', 'datasetp']:
        path = data(folder)
        if os.path.exists(path):
          shutil.rmtree(path)
        os.mkdir(path)
      for (folder, filename) in files:
        input_file=data(folder, filename)
        output_file=data('preprocessed', filename)
        preprocess(input_file, output_file)

    def output(self, filename):
      return data('preprocessed', filename)

    def test_timesig(self):
      for (_, filename) in files:
        with self.subTest(input_file=filename):
          tss = [msg for msg in mido.MidiFile(self.output(filename)) if msg.type == 'time_signature']
          # self.assertEqual(tss[0], mido.MetaMessage('time_signature',numerator=4,denominator=4,time=0))
          self.assertEqual(tss[0].numerator, 4)


    def test_tempo(self):
      """ After preprocessing, file tempo should be 120bpm """
      for (_, filename) in files:
        with self.subTest(input_file=filename):
          self.assertEqual(script_output_bpm, get_file_bpm(self.output(filename)))

    def test_duration(self):
      """ After preprocessing, file duration should be 32 seconds (16 bars) """
      for (_, filename) in files:
        with self.subTest(input_file=filename):
          self.assertAlmostEqual(desired_seconds, get_file_length(self.output(filename)),delta=1)
          # self.assertEqual(desired_seconds, get_file_length(output_file))




# datasetfiles = random.shuffle([filename for dataset in os.listdir('dataset') for filename in os.listdir(os.path.join('dataset',dataset))])






class TestExtraction(unittest.TestCase):
    @classmethod
    def setUpClass(self):
      if os.path.exists(metricsfile): os.remove(metricsfile)
      for folder in ['preprocessed', 'datasetp']:
        path = data(folder)
        if os.path.exists(path):
          shutil.rmtree(path)
        os.mkdir(path)

      # for (folder, filename) in files:
      #   out = None
      #   if folder == 'dataset': out = 'datasetp'
      #   if folder == 'generation': out = 'preprocessed'
      #   if not out: continue
      #   input_file=data(folder, filename)
      #   output_file=data(out, filename)
      #   preprocess(input_file, output_file)

    def test_extraction(self):
      """ After preprocessing, should be able to extract metrics """

      for filename in os.listdir(data('generated')):
        input_file=data('generated', filename)
        output_file=data('preprocessed', filename)
        preprocess(input_file, output_file)

      # Prep dataset
      for filename in os.listdir(data('dataset')):
        input_file=data('dataset', filename)
        output_file=data('datasetp', filename)
        preprocess(input_file, output_file)

      extract_metrics(data('preprocessed'), data('datasetp'),metricsfile)
      self.assertEqual(True, os.path.exists(metricsfile))