import os
import pythoncom
import win32com.client


class DOCExtractor:

    def extract_text(self, doc_path):

        doc = None
        word = None

        try:
            pythoncom.CoInitialize()

            word = win32com.client.DispatchEx("Word.Application")
            word.Visible = False
            word.DisplayAlerts = 0

            doc_path = os.path.abspath(doc_path)

            doc = word.Documents.Open(doc_path, ReadOnly=True)

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

            try:
                if word:
                    word.Quit()
            except:
                pass

            pythoncom.CoUninitialize()