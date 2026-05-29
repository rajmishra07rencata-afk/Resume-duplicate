import time
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials


class AzureOCRExtractor:

    def __init__(self, endpoint: str, key: str, gate):

        self.client = ComputerVisionClient(
            endpoint,
            CognitiveServicesCredentials(key)
        )

        self.gate = gate

    # =========================
    # PUBLIC METHOD (USED OUTSIDE)
    # =========================
    def extract_text_from_image(self, image_stream):

        print(f"🔵 OCR REQUEST TIME: {time.time()}")

        return self._azure_call(image_stream)

    # =========================
    # INTERNAL AZURE CALL
    # =========================
    def _azure_call(self, image_stream):

        # 🔥 GLOBAL THROTTLE
        self.gate.acquire()

        print(f"🟢 OCR PASSED GATE: {time.time()}")

        read_response = self.client.read_in_stream(
            image_stream,
            raw=True
        )

        operation_location = read_response.headers["Operation-Location"]
        operation_id = operation_location.split("/")[-1]

        # =========================
        # POLLING LOOP (FIXED)
        # =========================
        while True:

            result = self.client.get_read_result(operation_id)

            if result.status not in ["notStarted", "running"]:
                break

            time.sleep(0.5)

        # =========================
        # RESULT PARSING
        # =========================
        text = ""

        if result.status == "succeeded":

            for page in result.analyze_result.read_results:
                for line in page.lines:
                    text += line.text + "\n"

        return text.strip()


