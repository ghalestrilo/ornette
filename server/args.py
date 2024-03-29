import argparse
# import sys

def get_arg_parser():
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
    parser.add_argument("--batch-mode", type=bool, default=False,       help="Run in batch mode")
    
    parser.add_argument("--exec",       type=str,  default="",          help="Semicolon-separated commands to be executed by the server. If defined, once complete, the server will shut down.")
    parser.add_argument("--no-server",  type=bool, default=False,       help="Run the model without starting an OSC server")
    parser.add_argument("--no-module",  type=bool, default=False,       help="Run ornette without loading a model")
    return parser

def get_args():
    return get_arg_parser().parse_args()