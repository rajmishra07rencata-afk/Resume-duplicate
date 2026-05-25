import fitz


class PDFToImage:

    @staticmethod
    def convert(pdf_path, dpi=300):

        doc = fitz.open(pdf_path)

        images = []

        for page in doc:

            pix = page.get_pixmap(dpi=dpi)

            images.append(pix.tobytes("png"))

        doc.close()

        return images