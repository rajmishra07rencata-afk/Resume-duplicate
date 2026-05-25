import time
import threading
import queue


class OCRWorker:

    def __init__(self, azure_ocr):

        self.azure_ocr = azure_ocr
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):

        while True:

            image_stream, result_holder = self.queue.get()

            try:

                text = self.azure_ocr._azure_call(image_stream)
                result_holder.append(text)

            except Exception as e:
                result_holder.append("")

            self.queue.task_done()

    def submit(self, image_stream, result_holder):

        self.queue.put((image_stream, result_holder))