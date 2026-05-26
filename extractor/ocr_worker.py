import threading
import queue


class OCRWorker:

    def __init__(self, azure_ocr):

        self.azure_ocr = azure_ocr
        self.queue = queue.Queue()
        self.thread = threading.Thread(
            target=self._run,
            daemon=True
        )
        self.thread.start()

    def _run(self):

        while True:

            image_stream, result_holder, event = self.queue.get()

            try:

                text = self.azure_ocr._azure_call(image_stream)
                result_holder.append(text)

            except Exception as e:

                print(f"[OCRWorker ERROR] {e}")
                result_holder.append("")

            finally:

                # Signal that work is done
                event.set()

                self.queue.task_done()

    def submit(self, image_stream, result_holder):

        event = threading.Event()

        self.queue.put((image_stream, result_holder, event))

        # =========================================
        # TIMEOUT: don't hang forever
        # 60s is safe for Azure OCR per page
        # =========================================
        finished = event.wait(timeout=60)

        if not finished:
            print("[OCRWorker] Timeout waiting for OCR result")
            result_holder.append("")