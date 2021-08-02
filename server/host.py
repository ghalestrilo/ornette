from bridge import Bridge
from engine import Engine
from song import Song
from logger import Logger
from store import Store
from filters import Filters
from threading import Lock
from commands import run_batch
import mido
import data
from os import environ

# WIP: Passing commands via CLI
# Problem: `end` don't end no program
# TODO: Seems like `close` is called before the event loop starts
# Try using a flag (self.ready = Event()) and setting it through load_model / engine start
# Wait for it before issuing any --exec commands

class Host:
    def __init__(self, args):
      self.exec = args.exec
      self.lock = Lock()
      self.state = {}
      self.store = Store(self, args)
      self.io = Logger(self)
      self.data = data
      self.song = Song(self)
      self.bridge = Bridge(self,args)
      self.engine = Engine(self)
      self.filters = Filters(self)
      
      # Method Shorthands
      self.include_filters = self.filters.load_filter_defs

      self.reset()
      self.model = data.load_model(self, args.checkpoint)

    def start(self):
      try:
        if self.exec:
          run_batch(self, self.exec)
        self.bridge.start()
      except KeyboardInterrupt:
        self.close()
        return


    def close(self):
        self.engine.stop()
        self.model.close()
        self.bridge.stop()

    # Host, Song, Engine
    def reset(self):
        self.song.reset()
        self.engine.reset()

    def set(self,field,value,silent=False):
      self.store.set(field,value,silent)
    
    def get(self,field=None):
      if field == 'bpm': return self.song.get_bpm()
      return self.store.get(field)

    def add_filter(self, direction, filtername=None):
      self.filters.append(direction, filtername)

    # Batch (depr)
    def task_ended(self):
      did_it_end = len(self.song.get_voice()) >= self.get('buffer_length')
      return did_it_end
