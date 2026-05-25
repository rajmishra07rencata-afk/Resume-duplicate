import os
import pythoncom
import win32com.client


class DOCExtractor:

    def __init__(self):

        pythoncom.CoInitialize()

        self.word = win32com.client.Dispatch("Word.Application")

        self.word.Visible = False
        self.word.DisplayAlerts = 0

    def extract_text(self, doc_path):

        doc = None

        try:

            # ABSOLUTE PATH VERY IMPORTANT
            doc_path = os.path.abspath(doc_path)

            doc = self.word.Documents.Open(
                doc_path,
                ReadOnly=True
            )

            text = doc.Content.Text

            return text.strip()

        except Exception as e:

            print(f"DOC Extraction Error: {e}")
            return ""

        finally:

            try:
                if doc:
                    doc.Close(False)
            except:
                pass

    def close(self):

        try:
            self.word.Quit()
        except:
            pass

        pythoncom.CoUninitialize()