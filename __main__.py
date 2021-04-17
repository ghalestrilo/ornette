import os
import sys

# Move to utils.py?
def load_folder(name):
  sys.path.append(os.path.join(sys.path[0], name))

load_folder('src')

from args import get_args
from host import Host
from data import prep_module
from batch import run_experiments

import pretty_errors

pretty_errors.configure(
    separator_character = '=',
    filename_display    = pretty_errors.FILENAME_EXTENDED,
    line_number_first   = True,
    #display_link        = True,
    lines_before        = 5,
    lines_after         = 2,
    line_color          = pretty_errors.RED + '> ' + pretty_errors.default_config.line_color,
    code_color          = '  ' + pretty_errors.default_config.line_color,
    truncate_code       = True,
    display_locals      = True
)

pretty_errors.replace_stderr()

CODE_REBOOT=2222

os.environ['CUDA_VISIBLE_DEVICES'] = '0'

# Main
if __name__ == "__main__":
    if (os.environ['BATCH_RUNNER']):
      print("running batch mode")
      run_experiments()
      pass

    args = get_args()

    prep_module()

    # Prep Model
    host = Host(args)
    host.start()


    # if (state['return']==CODE_REBOOT):
    #   print("Should Reboot")
    # state['return']
