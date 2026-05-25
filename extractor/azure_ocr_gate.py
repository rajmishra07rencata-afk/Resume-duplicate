import time
import threading


class AzureOCRGate:

    def __init__(self, requests_per_sec=2):

        self.interval = 1 / requests_per_sec
        self.lock = threading.Lock()
        self.last = 0

    def acquire(self):

        with self.lock:

            now = time.time()

            wait = self.interval - (now - self.last)

            if wait > 0:
                time.sleep(wait)

            self.last = time.time()