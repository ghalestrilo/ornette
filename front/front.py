from front.ui import dropdown, display, rich_task
from front.container_manager import build_image, assert_image, run_image, run_client, ContainerManager
import threading
from queue import Queue

class Front():
  def __init__(self,options):
    self.queue = Queue()
    self.stop_flag = threading.Event()
    self.display_thread = threading.Thread(target=rich_task, args=(self.queue, self.stop_flag))
    self.docker_thread = threading.Thread(target=run_image, args=(self.queue, options, self.stop_flag))
    pass

  def start(self):
    self.display_thread.start()
    self.docker_thread.start()

  def stop(self):
    self.stop_flag.set()
    self.display_thread.join()
    self.docker_thread.join()
    pass
