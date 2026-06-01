import time
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential


class AzureDocIntelligenceExtractor:

    def __init__(self, endpoint: str, key: str):

        self.client = DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key)
        )

    # =========================================
    # MAIN METHOD — accepts image bytes directly
    # =========================================

    def extract_text_from_bytes(self, image_bytes: bytes) -> str:

        try:
            print(f"[DocIntelligence] Sending image: {len(image_bytes)} bytes")

            poller = self.client.begin_analyze_document(
                model_id="prebuilt-read",
                body=image_bytes,
                content_type="image/png"
            )

            result = poller.result()

            text = ""

            if result.content:
                text = result.content

            print(f"[DocIntelligence] Extracted: {len(text)} chars")
            return text.strip()

        except Exception as e:
            print(f"[DocIntelligence ERROR] {e}")
            return ""