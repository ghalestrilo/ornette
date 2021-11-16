from pythonosc import udp_client
from pythonosc.dispatcher import Dispatcher

class FrontClient():
    client = None
    logger = print

    def __init__(self, options):
        sc_ip = options.get('sc_ip')
        sc_port = options.get('sc_port')
        self.client = udp_client.SimpleUDPClient(sc_ip, sc_port)

    def set_logger(self, logger):
      self.logger = logger

    def send(self, message):
      try:
        self.client.send_message(message[0], message[1:])
      except Exception as e:
        self.logger(str(e))
