from server.args import get_arg_parser

args = get_arg_parser().parse_args(['--module','melody_rnn','--checkpoint','attention_rnn','--no-server','True','--no-module=True'])