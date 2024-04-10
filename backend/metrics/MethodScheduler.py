import threading
import time

class MethodScheduler(threading.Thread):
    def __init__(self, target_method, interval=30):
        super().__init__()
        self._target_method = target_method
        self._interval = interval
        self.daemon = True
        self.start()

    def run(self):
        while True:
            self._target_method()
            time.sleep(self._interval)
