import unittest

# python -m unittest tests.models

models = [  # Melody RNN
    {'name': 'melody_rnn', 'bundle': 'basic_rnn'},
    {'name': 'melody_rnn', 'bundle': 'mono_rnn'},
    {'name': 'melody_rnn', 'bundle': 'attention_rnn'},
    {'name': 'melody_rnn', 'bundle': 'lookback_rnn'},

    # Performance RNN
    {'name': 'performance_rnn', 'bundle': 'performance.mag'},
    {'name': 'performance_rnn',
     'bundle': 'density_conditioned_performance_with_dynamics'},
    {'name': 'performance_rnn', 'bundle': 'performance_with_dynamics'},
    {'name': 'performance_rnn',
     'bundle': 'pitch_conditioned_performance_with_dynamics'},
    {'name': 'performance_rnn', 'bundle': 'performance'},
    {'name': 'performance_rnn', 'bundle': 'polyphony_rnn'},
    {'name': 'performance_rnn',
     'bundle': 'multiconditioned_performance_with_dynamics'},
    {'name': 'performance_rnn',
     'bundle': 'performance_with_dynamics_and_modulo_encoding'},

    # Pianoroll RNN
    {'name': 'pianoroll_rnn_nade', 'bundle': 'rnn-nade_attn'},
    {'name': 'pianoroll_rnn_nade', 'bundle': 'rnn-nade'},
    {'name': 'pianoroll_rnn_nade', 'bundle': 'pianoroll_rnn_nade'},
    {'name': 'pianoroll_rnn_nade', 'bundle': 'pianoroll_rnn_nade-bach'},

    # Polyphony RNN
    {'name': 'polyphony_rnn', 'bundle': 'polyphony_rnn'},
]


class TestModels(unittest.TestCase):

    # Mock tests
    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')

    def test_isupper(self):
        self.assertTrue('FOO'.isupper())
        self.assertFalse('Foo'.isupper())

    def test_split(self):
        s = 'hello world'
        self.assertEqual(s.split(), ['hello', 'world'])
        # check that s.split fails when the separator is not a string
        with self.assertRaises(TypeError):
            s.split(2)
