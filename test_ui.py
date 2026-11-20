"""Regression checks for real CustomTkinter click bindings and native-dialog reentry."""
import time
import tkinter as tk
import unittest
from unittest.mock import patch

from app import ConverterApp, walk_widgets


class DialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ConverterApp()
        cls.app.update()
        cls.app.dropzone._bind_interactions()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    def setUp(self):
        self.app._file_dialog_open = False
        self.app._file_dialog_next_allowed = 0

    def test_each_dropzone_surface_opens_once(self):
        zone = self.app.dropzone
        zone._bind_interactions()  # Rebinding must also be harmless.
        count = 0
        for widget in walk_widgets(zone):
            path = str(widget)
            if path == str(zone.choose_button) or path.startswith(str(zone.choose_button) + '.'):
                continue
            if not isinstance(widget, (tk.Canvas, tk.Label)):
                continue
            self.app._file_dialog_next_allowed = 0
            with self.subTest(widget=path), patch('app.filedialog.askopenfilenames', return_value=()) as dialog:
                widget.event_generate('<Button-1>', x=2, y=2)
                self.app.update()
                self.assertEqual(dialog.call_count, 1)
                count += 1
        self.assertGreater(count, 3)

    def test_double_click_does_not_reopen_dialog(self):
        surface = self.app.dropzone._canvas
        with patch('app.filedialog.askopenfilenames', return_value=()) as dialog:
            for _ in range(2):
                surface.event_generate('<Button-1>', x=2, y=2)
                self.app.update()
            self.assertEqual(dialog.call_count, 1)

    def test_dialog_blocks_nested_shortcut(self):
        def nested_dialog(**kwargs):
            self.app._choose_files()
            return ()
        with patch('app.filedialog.askopenfilenames', side_effect=nested_dialog) as dialog:
            self.app._choose_files()
            self.assertEqual(dialog.call_count, 1)
        self.assertFalse(self.app._file_dialog_open)

    def test_new_click_after_cooldown_and_selection(self):
        with patch('app.filedialog.askopenfilenames', return_value=('selected.png',)) as dialog:
            with patch.object(self.app, '_accept_paths') as accept:
                self.app._choose_files()
                accept.assert_called_once()
            self.app._file_dialog_next_allowed = time.monotonic() - 1
            with patch.object(self.app, '_accept_paths'):
                self.app._choose_files()
            self.assertEqual(dialog.call_count, 2)

    def test_dialog_guard_recovers_after_failure(self):
        with patch('app.filedialog.askopenfilenames', side_effect=tk.TclError('test')):
            with self.assertRaises(tk.TclError):
                self.app._choose_files()
        self.assertFalse(self.app._file_dialog_open)

    def test_controls_fit_minimum_window(self):
        from pathlib import Path
        original = self.app.geometry()
        try:
            self.app.geometry('980x720')
            for filename, target in (('photo.png', 'JPG'), ('pages.pdf', 'JPG'), ('text.docx', 'DOCX')):
                self.app.files = [Path(filename)]
                self.app.target = target
                self.app._refresh_controls()
                self.app.update()
                with self.subTest(target=target, filename=filename):
                    for widget in (self.app.target_seg, self.app.convert_btn, self.app.status_label):
                        bottom = widget.winfo_rooty() + widget.winfo_height()
                        self.assertLessEqual(bottom, self.app.winfo_rooty() + self.app.winfo_height())
                        self.assertLessEqual(widget.winfo_rootx() + widget.winfo_width(), self.app.winfo_rootx() + self.app.winfo_width())
        finally:
            self.app.files = []
            self.app.target = 'PNG'
            self.app._refresh_controls()
            self.app.geometry(original)
            self.app.update()


if __name__ == '__main__':
    unittest.main()
