import argparse

def get_args():
      # Parse CLI Args
    parser = argparse.ArgumentParser()

    parser.add_argument('--max_seq',    type=int  default=256,          help='maximum buffer length')

    parser.add_argument('--state',      type=str   default="0",         help='the initial state of the improv')
    parser.add_argument("--ip",                    default="127.0.0.1", help="The ip to listen on")
    parser.add_argument("--port",       type=int,  default=5005,        help="The port to listen on")

    parser.add_argument("--module", type=str,  default=None,        help="The model to use (music-transformer, remi)")
    parser.add_argument("--checkpoint", type=str,  default=None,        help="The checkpoint you wish to load")
    parser.add_argument("--sc-ip",      type=str,  default="127.0.0.1", help="The supercollider server ip")
    parser.add_argument("--sc-port",    type=int,  default=57120,       help="The supercollider server ip")

    parser.add_argument("--playback",   type=bool, default=True,        help="Use supercollider for sound playback")
    return parser.parse_args()