# tests/runner.py
import unittest

# import your test modules
# import player
# import scenario
import sys
import os
# sys.path.append(os.path.abspath(os.path.join(os.path.pardir, 'server')))
sys.path.append(os.path.abspath(os.path.join('server')))
# sys.path.append(os.path.abspath(os.path.join('server', 'tests')))
# from server import filter_defs


# import test_filters
from tests import test_song

# initialize the test suite
loader = unittest.TestLoader()
suite  = unittest.TestSuite()

# add tests to the test suite
# suite.addTests(loader.loadTestsFromModule(test_filters))
suite.addTests(loader.loadTestsFromModule(test_song))

# initialize a runner, pass it your suite and run it
runner = unittest.TextTestRunner(verbosity=3)
result = runner.run(suite)