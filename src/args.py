import argparse

def get_args():
      # Parse CLI Args
    parser = argparse.ArgumentParser()

    parser.add_argument('--max_seq',    type=int,  default=256,         help='maximum buffer length')
    
    parser.add_argument("--ip",         type=str,  default="127.0.0.1", help="The ip to listen on")
    parser.add_argument("--port",       type=int,  default=5005,        help="The port to listen on")
    parser.add_argument("--sc-ip",      type=str,  default="127.0.0.1", help="The supercollider server ip")
    parser.add_argument("--sc-port",    type=int,  default=57120,       help="The supercollider server ip")

    parser.add_argument("--module",     type=str,  default=None,        help="The model to use (music-transformer, remi)")
    parser.add_argument("--checkpoint", type=str,  default=None,        help="The checkpoint you wish to load")
    parser.add_argument('--state',      type=str,  default="0",         help='the initial state of the improv')

    parser.add_argument("--playback",   type=bool, default=True,        help="Use supercollider for sound playback")
    parser.add_argument("--batch-mode", type=bool, default=False,        help="Use supercollider for sound playback")
    return parser.parse_args()




def get_batch_args():
    # Parse CLI Args
    parser = argparse.ArgumentParser()

    parser.add_argument("--ip",         type=str,  default="127.0.0.1", help="The IP address the ornette host is running on")
    parser.add_argument("--port",       type=int,  default=5005,        help="The port to listen on")
    parser.add_argument('--port-in',    type=str,  default=57120,       help='Port to listen to proceed messages (\'/ok\')')

    parser.add_argument('--state',      type=str,  default="0",         help='the initial state of the improv')

    parser.add_argument("--playback",   type=bool, default=True,        help="Use supercollider for sound playback")
    parser.add_argument("--batch-mode", type=bool, default=False,       help="Use supercollider for sound playback")

    parser.add_argument('--block-size', type=int,  default=16,          help='Length of increment to the server\'s buffer_size at each iteration of an experiment')

    parser.add_argument('--iterations', type=int,  default=1,          help='Number of times to run the experiment')
    parser.add_argument('--experiment', type=str,  default='all',       choices=['all', 'guess'], help='Which experiment to run')
    parser.add_argument('--skip-generation', type=bool,  default=False, help='Skip sample generation, just analyze generated data')

    return parser.parse_args()