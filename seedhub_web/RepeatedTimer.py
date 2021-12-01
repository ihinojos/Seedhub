import threading 
import time

class RepeatedTimer(object):
  def __init__(self, interval, function, plant_id, *args, **kwargs):
    self._timer = None
    self.interval = interval
    self.function = function
    self.plant_id = plant_id
    self.args = args
    self.kwargs = kwargs
    self.is_running = False
    self.next_call = time.time()
    self.start()
    print("Daemon started")

  def _run(self):
    self.is_running = False
    self.start()
    self.function(*self.args, **self.kwargs)

  def start(self):
    if not self.is_running:
      self.next_call += self.interval
      self._timer = threading.Timer(self.next_call - time.time(), self._run)
      self._timer.start()
      self.is_running = True

  def stop(self):
    self._timer.cancel()
    self.is_running = False