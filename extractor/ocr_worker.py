# import threading
# import queue


# class OCRWorker:

#     def __init__(self, azure_ocr):

#         self.azure_ocr = azure_ocr
#         self.queue = queue.Queue()
#         self.thread = threading.Thread(
#             target=self._run,
#             daemon=True
#         )
#         self.thread.start()

#     def _run(self):

#         while True:

#             image_stream, result_holder, event = self.queue.get()

#             try:

#                 text = self.azure_ocr._azure_call(image_stream)
#                 result_holder.append(text)

#             except Exception as e:
#                 # THIS IS THE FIX: print the actual Azure error so you can see it
#                 import traceback
#                 print(f"[OCRWorker ERROR] {e}")
#                 traceback.print_exc()          # <-- add this line
#                 result_holder.append("")
#             finally:

#                 # Signal that work is done
#                 event.set()

#                 self.queue.task_done()

#     def submit(self, image_stream, result_holder):

#         event = threading.Event()

#         self.queue.put((image_stream, result_holder, event))

#         # =========================================
#         # TIMEOUT: don't hang forever
#         # 60s is safe for Azure OCR per page
#         # =========================================
#         finished = event.wait(timeout=60)

#         if not finished:
#             print("[OCRWorker] Timeout waiting for OCR result")
#             result_holder.append("")


import threading
import queue
import traceback


class OCRWorker:

    def __init__(self, azure_ocr, doc_intel=None):

        self.azure_ocr = azure_ocr
        self.doc_intel = doc_intel          # NEW — optional fallback
        self.queue = queue.Queue()
        self.thread = threading.Thread(
            target=self._run,
            daemon=True
        )
        self.thread.start()

    def _run(self):

        while True:

            image_bytes, image_stream, result_holder, event = self.queue.get()

            try:
                # =========================================
                # PRIMARY — Azure Vision OCR
                # =========================================
                text = self.azure_ocr._azure_call(image_stream)

                # =========================================
                # FIX: log real errors instead of swallowing
                # =========================================
                print(f"[OCRWorker] Vision result: {len(text)} chars")

                # =========================================
                # FALLBACK — if Vision returns empty text
                # switch to Document Intelligence
                # =========================================
                if not text.strip() and self.doc_intel is not None:
                    print("[OCRWorker] Vision returned empty — trying Document Intelligence")
                    text = self.doc_intel.extract_text_from_bytes(image_bytes)

                result_holder.append(text)

            except Exception as e:
                # =========================================
                # FIX: Vision threw exception — log it fully
                # then try Document Intelligence fallback
                # =========================================
                print(f"[OCRWorker ERROR] Vision OCR failed: {e}")
                traceback.print_exc()

                fallback_text = ""

                if self.doc_intel is not None:
                    print("[OCRWorker] Trying Document Intelligence fallback")
                    try:
                        fallback_text = self.doc_intel.extract_text_from_bytes(
                            image_bytes
                        )
                        print(
                            f"[OCRWorker] Doc Intelligence result: "
                            f"{len(fallback_text)} chars"
                        )
                    except Exception as fe:
                        print(f"[OCRWorker] Doc Intelligence also failed: {fe}")
                        traceback.print_exc()

                result_holder.append(fallback_text)

            finally:
                event.set()
                self.queue.task_done()

    def submit(self, image_stream, result_holder):
        """
        image_stream must be a fresh io.BytesIO(img).
        We read the bytes once here for the fallback,
        then rewind the stream for Vision OCR.
        """
        # =========================================
        # Read bytes ONCE for potential fallback use
        # Rewind stream so Vision OCR reads from start
        # =========================================
        image_bytes = image_stream.read()
        image_stream.seek(0)

        event = threading.Event()

        self.queue.put((image_bytes, image_stream, result_holder, event))

        finished = event.wait(timeout=60)

        if not finished:
            print("[OCRWorker] Timeout waiting for OCR result")
            result_holder.append("")