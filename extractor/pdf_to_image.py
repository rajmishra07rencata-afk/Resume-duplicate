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

    @staticmethod
    def convert_first_page(pdf_path, dpi=300):
        """Convert only page 0 — used for contact recovery"""
        doc = fitz.open(pdf_path)
        if len(doc) == 0:
            doc.close()
            return []
        pix = doc[0].get_pixmap(dpi=dpi)
        img = pix.tobytes("png")
        doc.close()
        return [img]

    @staticmethod
    def convert_page_range(pdf_path, start=0, end=1, dpi=300):
        """Convert specific page range"""
        doc = fitz.open(pdf_path)
        images = []
        for i in range(start, min(end, len(doc))):
            pix = doc[i].get_pixmap(dpi=dpi)
            images.append(pix.tobytes("png"))
        doc.close()
        return images