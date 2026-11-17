import tempfile
import unittest
from pathlib import Path

from PIL import Image
import pymupdf
import converter
import office_converter


class ConversionTests(unittest.TestCase):
    @unittest.skipUnless(office_converter.find_libreoffice(), "LibreOffice is required")
    def test_document_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "document.txt"
            source.write_text("Hello converter 123", encoding="utf-8")
            word = converter.convert_files([source], "DOCX", root / "word")
            self.assertFalse(word.errors, word.errors)
            pdf = converter.convert_files(word.outputs, "PDF", root / "pdf")
            self.assertFalse(pdf.errors, pdf.errors)
            with pymupdf.open(pdf.outputs[0]) as document:
                self.assertIn("Hello converter 123", document[0].get_text())
            text = converter.convert_files(word.outputs, "TXT", root / "text")
            self.assertFalse(text.errors, text.errors)
            self.assertIn("Hello converter 123", text.outputs[0].read_text(encoding="utf-8-sig"))

    def test_images_pdf_pages_and_existing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "прозрачность.png"
            Image.new("RGBA", (64, 48), (255, 0, 0, 0)).save(source)
            out = root / "результаты"
            for target in ("PNG", "JPG", "WEBP", "BMP", "PDF"):
                result = converter.convert_files([source], target, out)
                self.assertFalse(result.errors, result.errors)
                self.assertEqual(len(result.outputs), 1)
                self.assertTrue(result.outputs[0].is_file())
            with Image.open(out / "прозрачность.jpg") as image:
                self.assertEqual(image.getpixel((0, 0)), (255, 255, 255))
            original = source.read_bytes()
            result = converter.convert_files([source], "PNG", root)
            self.assertNotEqual(result.outputs[0], source)
            self.assertEqual(source.read_bytes(), original)
            merged = converter.convert_files([source, source], "PDF", out, merge_pdf=True)
            self.assertFalse(merged.errors)
            with pymupdf.open(merged.outputs[0]) as document:
                self.assertEqual(document.page_count, 2)
            pages = converter.convert_files(merged.outputs, "PNG", out)
            self.assertFalse(pages.errors)
            self.assertEqual(len(pages.outputs), 2)
            for page in pages.outputs:
                with Image.open(page) as image:
                    image.verify()

    def test_corrupt_image_does_not_stop_batch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bad = root / "broken.png"
            bad.write_bytes(b"broken")
            good = root / "good.png"
            Image.new("RGB", (10, 10)).save(good)
            result = converter.convert_files([bad, good], "JPG", root / "out")
            self.assertEqual(len(result.errors), 1)
            self.assertEqual(len(result.outputs), 1)


if __name__ == "__main__":
    unittest.main()
