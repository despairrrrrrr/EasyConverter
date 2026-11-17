"""EasyConverter — приложение для конвертации изображений и документов.

Запуск:  python app.py
"""

from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageOps

import converter
from app_info import APP_NAME, VERSION

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD

    DND_AVAILABLE = True
except Exception:  # pragma: no cover - приложение работает и без drag&drop
    DND_AVAILABLE = False
    DND_FILES = "DND_Files"

# ---------------------------------------------------------------------------
# Палитра и оформление
# ---------------------------------------------------------------------------

BG = "#0B0F14"
CARD = "#121820"
CARD_2 = "#18212B"
CARD_3 = "#202B37"
BORDER = "#232E3A"
TEXT = "#E8EEF5"
MUTED = "#8B98A6"
DIM = "#5F6C7A"
ACCENT = "#5B8DEF"
ACCENT_HOVER = "#74A2F5"
ACCENT_SOFT = "#17263D"
SUCCESS = "#46C37B"
WARNING = "#E3B341"
DANGER = "#F06A6A"

FONT_FAMILY = "Segoe UI"
ASSETS_DIR = Path(__file__).with_name("assets")


def human_size(size: int) -> str:
    value = float(size)
    for unit in ("Б", "КБ", "МБ", "ГБ"):
        if value < 1024 or unit == "ГБ":
            if unit == "Б":
                return f"{value:.0f} {unit}"
            return f"{value:.1f} {unit}".replace(".", ",")
        value /= 1024
    return f"{value:.1f} ГБ"


def shorten(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def middle_shorten(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    left = (limit - 1) // 2
    right = limit - 1 - left
    return text[:left] + "…" + text[-right:]


def files_word(count: int) -> str:
    if count % 10 == 1 and count % 100 != 11:
        return "файл"
    if count % 10 in (2, 3, 4) and count % 100 not in (12, 13, 14):
        return "файла"
    return "файлов"


def ready_text(count: int) -> str:
    word = files_word(count)
    if word == "файл":
        return f"{count} файл готов к конвертации"
    return f"{count} {word} готовы к конвертации"


def walk_widgets(widget: tk.Misc):
    yield widget
    for child in widget.winfo_children():
        yield from walk_widgets(child)


# ---------------------------------------------------------------------------
# Зона перетаскивания
# ---------------------------------------------------------------------------


class DropZone(ctk.CTkFrame):
    def __init__(self, master, fonts, on_click, on_files, dnd_ready: bool):
        super().__init__(
            master,
            fg_color=CARD,
            border_width=1,
            border_color=BORDER,
            corner_radius=18,
            height=158,
        )
        self.pack_propagate(False)
        self.on_click = on_click
        self.on_files = on_files
        self.dnd_ready = dnd_ready
        self._leave_job: str | None = None

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(expand=True, pady=(14, 12))

        icon_wrap = ctk.CTkFrame(
            content, width=48, height=48, corner_radius=24, fg_color=ACCENT_SOFT
        )
        icon_wrap.pack(pady=(0, 8))
        icon_wrap.pack_propagate(False)
        ctk.CTkLabel(
            icon_wrap,
            text="↓",
            font=fonts["icon"],
            text_color=ACCENT,
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            content,
            text="Перетащите файлы сюда",
            font=fonts["drop_title"],
            text_color=TEXT,
        ).pack()
        ctk.CTkLabel(
            content,
            text="Изображения, PDF и документы Word · нажмите, чтобы выбрать",
            font=fonts["small"],
            text_color=MUTED,
        ).pack(pady=(3, 0))

        self.after(80, self._bind_interactions)

    def _bind_interactions(self) -> None:
        try:
            widgets = list(walk_widgets(self))
        except tk.TclError:
            return

        dnd_widgets = list(widgets)
        for widget in widgets:
            canvas = getattr(widget, "_canvas", None)
            if canvas is not None and canvas not in dnd_widgets:
                dnd_widgets.append(canvas)

        for widget in widgets:
            try:
                widget.configure(cursor="hand2")
            except (tk.TclError, ValueError):
                pass
            try:
                widget.bind("<Button-1>", self._click, add="+")
            except tk.TclError:
                pass

        if not self.dnd_ready:
            return

        for widget in dnd_widgets:
            try:
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind("<<Drop>>", self._drop)
                widget.dnd_bind("<<DropEnter>>", self._drag_enter)
                widget.dnd_bind("<<DropLeave>>", self._drag_leave)
            except Exception:
                pass

    def _click(self, _event=None):
        self.on_click()

    def _drag_enter(self, _event=None):
        if self._leave_job is not None:
            try:
                self.after_cancel(self._leave_job)
            except tk.TclError:
                pass
            self._leave_job = None
        self._set_active(True)
        return "copy"

    def _drag_leave(self, _event=None):
        if self._leave_job is not None:
            try:
                self.after_cancel(self._leave_job)
            except tk.TclError:
                pass
        self._leave_job = self.after(60, self._deactivate_soon)
        return "copy"

    def _deactivate_soon(self):
        self._leave_job = None
        self._set_active(False)

    def _drop(self, event):
        if self._leave_job is not None:
            try:
                self.after_cancel(self._leave_job)
            except tk.TclError:
                pass
            self._leave_job = None
        self._set_active(False)
        try:
            items = self.tk.splitlist(event.data)
        except tk.TclError:
            items = str(event.data).split()
        self.on_files([Path(item) for item in items])
        return "copy"

    def _set_active(self, active: bool) -> None:
        try:
            self.configure(
                border_color=ACCENT if active else BORDER,
                fg_color="#121D2E" if active else CARD,
            )
        except tk.TclError:
            pass


# ---------------------------------------------------------------------------
# Приложение
# ---------------------------------------------------------------------------


class ConverterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        self.title(f"{APP_NAME} — изображения и документы")
        self.configure(fg_color=BG)
        self.minsize(760, 780)

        self.dnd_ready = False
        if DND_AVAILABLE:
            try:
                TkinterDnD._require(self)
                self.dnd_ready = True
            except Exception:
                self.dnd_ready = False

        # Состояние
        self.files: list[Path] = []
        self.target = "PNG"
        self.quality = 92
        self.dpi = 150
        self.output_dir = converter.default_output_dir()
        self.converting = False
        self.queue: queue.Queue = queue.Queue()
        self.thumbs: dict[Path, ctk.CTkImage | None] = {}
        self.remove_buttons: list[ctk.CTkButton] = []
        self.merge_var = tk.BooleanVar(value=False)
        self.logo_image: ctk.CTkImage | None = None

        self._create_fonts()
        self._build_ui()
        self._bind_shortcuts()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(120, self._apply_dark_titlebar)
        self.after(160, self._apply_icon)
        self.after(100, self._poll_queue)

        width, height = 880, 860
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2 - 24)
        self.geometry(f"{width}x{height}+{x}+{y}")

    # -- оформление ---------------------------------------------------------

    def _create_fonts(self) -> None:
        def font(size: int, weight: str = "normal") -> ctk.CTkFont:
            return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)

        self.fonts = {
            "h1": font(24, "bold"),
            "subtitle": font(11),
            "section": font(13, "bold"),
            "body": font(12),
            "small": font(11),
            "tiny": font(10),
            "tiny_bold": font(9, "bold"),
            "button": font(13, "bold"),
            "big_button": font(14, "bold"),
            "icon": font(25, "bold"),
            "big_icon": font(22, "bold"),
            "drop_title": font(15, "bold"),
            "value": font(11, "bold"),
        }

    def _load_logo(self) -> ctk.CTkImage | None:
        path = ASSETS_DIR / "logo.png"
        if not path.exists():
            return None
        try:
            image = Image.open(path).convert("RGBA")
            return ctk.CTkImage(light_image=image, dark_image=image, size=(40, 40))
        except Exception:
            return None

    def _apply_icon(self) -> None:
        path = ASSETS_DIR / "icon.ico"
        if path.exists():
            try:
                self.iconbitmap(str(path))
            except tk.TclError:
                pass

    def _apply_dark_titlebar(self) -> None:
        if os.name != "nt":
            return
        try:
            import ctypes

            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            value = ctypes.c_int(1)
            for attribute in (20, 19):
                result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, attribute, ctypes.byref(value), ctypes.sizeof(value)
                )
                if result == 0:
                    break
        except Exception:
            pass

    # -- интерфейс ----------------------------------------------------------

    def _build_ui(self) -> None:
        main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        main.pack(fill="both", expand=True, padx=30, pady=(24, 22))
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(2, weight=1)

        self._build_header(main)
        self._build_dropzone(main)
        self._build_files_card(main)
        self._build_settings(main)
        self._build_output_row(main)
        self._build_bottom(main)

    def _build_header(self, parent) -> None:
        header = ctk.CTkFrame(parent, fg_color="transparent", height=48)
        header.grid(row=0, column=0, sticky="ew")
        header.pack_propagate(False)

        self.logo_image = self._load_logo()
        if self.logo_image is not None:
            logo = ctk.CTkLabel(header, text="", image=self.logo_image)
            logo.pack(side="left", padx=(0, 12))
        else:
            mark = ctk.CTkFrame(
                header, width=40, height=40, corner_radius=11, fg_color=ACCENT
            )
            mark.pack(side="left", padx=(0, 12))
            mark.pack_propagate(False)
            ctk.CTkLabel(
                mark, text="⇄", font=self.fonts["big_icon"], text_color="#0B1220"
            ).place(relx=0.5, rely=0.5, anchor="center")

        titles = ctk.CTkFrame(header, fg_color="transparent")
        titles.pack(side="left", anchor="w")
        ctk.CTkLabel(
            titles, text=APP_NAME, font=self.fonts["h1"], text_color=TEXT
        ).pack(anchor="w")
        ctk.CTkLabel(
            titles,
            text="Изображения и документы — локально, без загрузок",
            font=self.fonts["subtitle"],
            text_color=MUTED,
        ).pack(anchor="w", pady=(0, 1))

        chip = ctk.CTkFrame(
            header,
            fg_color=CARD,
            corner_radius=13,
            border_width=1,
            border_color=BORDER,
        )
        chip.pack(side="right", pady=10)
        ctk.CTkLabel(
            chip,
            text="●",
            font=self.fonts["tiny"],
            text_color=SUCCESS,
        ).pack(side="left", padx=(11, 0))
        ctk.CTkLabel(
            chip,
            text="Всё остаётся локально",
            font=self.fonts["small"],
            text_color=MUTED,
        ).pack(side="left", padx=(5, 11), pady=4)

    def _build_dropzone(self, parent) -> None:
        self.dropzone = DropZone(
            parent,
            self.fonts,
            on_click=self._choose_files,
            on_files=self._accept_paths,
            dnd_ready=self.dnd_ready,
        )
        self.dropzone.grid(row=1, column=0, sticky="ew", pady=(16, 0))

    def _build_files_card(self, parent) -> None:
        card = ctk.CTkFrame(
            parent,
            fg_color=CARD,
            border_width=1,
            border_color=BORDER,
            corner_radius=18,
        )
        card.grid(row=2, column=0, sticky="nsew", pady=(14, 0))
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 6))

        ctk.CTkLabel(
            header, text="Файлы", font=self.fonts["section"], text_color=TEXT
        ).pack(side="left")
        self.count_badge = ctk.CTkLabel(
            header,
            text="0",
            width=24,
            height=19,
            corner_radius=8,
            fg_color=CARD_2,
            text_color=MUTED,
            font=self.fonts["tiny_bold"],
        )
        self.count_badge.pack(side="left", padx=(8, 0))

        self.clear_btn = ctk.CTkButton(
            header,
            text="Очистить",
            width=72,
            height=26,
            corner_radius=8,
            fg_color="transparent",
            hover_color=CARD_2,
            text_color=MUTED,
            text_color_disabled=DIM,
            font=self.fonts["small"],
            command=self._clear_files,
            state="disabled",
        )
        self.clear_btn.pack(side="right")

        self.scroll = ctk.CTkScrollableFrame(
            card,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_fg_color="transparent",
            scrollbar_button_color=CARD_3,
            scrollbar_button_hover_color="#2B3948",
        )
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=(10, 8), pady=(0, 10))
        self._scrollbar_visible = True
        self.scroll._parent_canvas.bind(
            "<Configure>", lambda _event: self.after_idle(self._update_scrollbar), add="+"
        )
        self.after(200, self._update_scrollbar)

        self.empty_state = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.empty_state.pack(fill="both", expand=True, pady=34)
        ctk.CTkLabel(
            self.empty_state,
            text="Здесь появятся ваши файлы",
            font=self.fonts["body"],
            text_color=MUTED,
        ).pack()
        ctk.CTkLabel(
            self.empty_state,
            text="Изображения, PDF и документы Word",
            font=self.fonts["small"],
            text_color=DIM,
        ).pack(pady=(3, 0))

    def _build_settings(self, parent) -> None:
        card = ctk.CTkFrame(
            parent,
            fg_color=CARD,
            border_width=1,
            border_color=BORDER,
            corner_radius=18,
        )
        card.grid(row=3, column=0, sticky="ew", pady=(14, 0))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=14)
        inner.grid_columnconfigure(1, weight=1)
        self.settings_inner = inner

        label_kwargs = {
            "font": self.fonts["body"],
            "text_color": MUTED,
            "anchor": "w",
        }

        ctk.CTkLabel(inner, text="Формат", **label_kwargs).grid(
            row=0, column=0, sticky="w", padx=(0, 16)
        )

        self.target_seg = ctk.CTkSegmentedButton(
            inner,
            values=list(converter.IMAGE_TARGETS),
            command=self._on_target_change,
            width=440,
            height=34,
            corner_radius=9,
            border_width=2,
            fg_color=CARD,
            selected_color=ACCENT,
            selected_hover_color=ACCENT_HOVER,
            unselected_color=CARD_2,
            unselected_hover_color=CARD_3,
            text_color=TEXT,
            text_color_disabled=MUTED,
            font=self.fonts["body"],
            dynamic_resizing=False,
        )
        self.target_seg.grid(row=0, column=1, sticky="e")
        self.target_seg.set(self.target)

        self.quality_label = ctk.CTkLabel(inner, text="Качество", **label_kwargs)
        self.quality_label.grid(row=1, column=0, sticky="w", pady=(12, 0))
        self.quality_slider = ctk.CTkSlider(
            inner,
            from_=30,
            to=100,
            number_of_steps=70,
            height=16,
            border_width=0,
            fg_color=CARD_2,
            progress_color=ACCENT,
            button_color=ACCENT,
            button_hover_color=ACCENT_HOVER,
            command=self._on_quality_change,
        )
        self.quality_slider.grid(
            row=1, column=1, sticky="ew", padx=(16, 14), pady=(12, 0)
        )
        self.quality_slider.set(self.quality)
        self.quality_value = ctk.CTkLabel(
            inner,
            text=f"{self.quality}%",
            width=40,
            anchor="e",
            font=self.fonts["value"],
            text_color=TEXT,
        )
        self.quality_value.grid(row=1, column=2, sticky="e", pady=(12, 0))

        self.dpi_label = ctk.CTkLabel(inner, text="Разрешение", **label_kwargs)
        self.dpi_label.grid(row=2, column=0, sticky="w", pady=(12, 0))
        self.dpi_seg = ctk.CTkSegmentedButton(
            inner,
            values=["96", "150", "300"],
            command=self._on_dpi_change,
            width=180,
            height=30,
            corner_radius=8,
            border_width=2,
            fg_color=CARD,
            selected_color=ACCENT,
            selected_hover_color=ACCENT_HOVER,
            unselected_color=CARD_2,
            unselected_hover_color=CARD_3,
            text_color=TEXT,
            text_color_disabled=MUTED,
            font=self.fonts["small"],
            dynamic_resizing=False,
        )
        self.dpi_seg.grid(row=2, column=1, sticky="w", padx=(16, 0), pady=(12, 0))
        self.dpi_seg.set(str(self.dpi))
        self.dpi_unit = ctk.CTkLabel(
            inner,
            text="DPI",
            font=self.fonts["tiny"],
            text_color=DIM,
        )
        self.dpi_unit.grid(row=2, column=2, sticky="e", pady=(12, 0))

        self.merge_check = ctk.CTkCheckBox(
            inner,
            text="Собрать все изображения в один PDF",
            variable=self.merge_var,
            command=self._update_hint,
            font=self.fonts["body"],
            text_color=TEXT,
            checkbox_width=18,
            checkbox_height=18,
            corner_radius=5,
            border_width=2,
            border_color=BORDER,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            checkmark_color="#0B1220",
        )
        self.merge_check.grid(
            row=3, column=0, columnspan=3, sticky="w", pady=(12, 0)
        )

        self.hint_label = ctk.CTkLabel(
            inner,
            text="",
            font=self.fonts["small"],
            text_color=DIM,
            anchor="w",
            justify="left",
            wraplength=640,
        )
        self.hint_label.grid(
            row=4, column=0, columnspan=3, sticky="w", pady=(8, 0)
        )

        self.quality_label.grid_remove()
        self.quality_slider.grid_remove()
        self.quality_value.grid_remove()
        self.dpi_label.grid_remove()
        self.dpi_seg.grid_remove()
        self.dpi_unit.grid_remove()
        self.merge_check.grid_remove()
        self.hint_label.grid_remove()

    def _build_output_row(self, parent) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.grid(row=4, column=0, sticky="ew", pady=(14, 0))
        row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            row,
            text="Папка",
            font=self.fonts["body"],
            text_color=MUTED,
        ).grid(row=0, column=0, sticky="w", padx=(0, 12))

        folder_box = ctk.CTkFrame(
            row,
            fg_color=CARD,
            corner_radius=9,
            border_width=1,
            border_color=BORDER,
            height=34,
        )
        folder_box.grid(row=0, column=1, sticky="ew")
        folder_box.pack_propagate(False)

        self.folder_label = ctk.CTkLabel(
            folder_box,
            text="",
            font=self.fonts["small"],
            text_color=MUTED,
            anchor="w",
        )
        self.folder_label.pack(side="left", fill="x", expand=True, padx=12)
        self._update_folder_label()

        self.change_btn = ctk.CTkButton(
            row,
            text="Изменить",
            width=76,
            height=32,
            corner_radius=9,
            fg_color=CARD,
            hover_color=CARD_2,
            border_width=1,
            border_color=BORDER,
            text_color=TEXT,
            font=self.fonts["small"],
            command=self._choose_output_dir,
        )
        self.change_btn.grid(row=0, column=2, padx=(8, 0))

        self.open_btn = ctk.CTkButton(
            row,
            text="Открыть",
            width=76,
            height=32,
            corner_radius=9,
            fg_color=CARD,
            hover_color=CARD_2,
            border_width=1,
            border_color=BORDER,
            text_color=TEXT,
            font=self.fonts["small"],
            command=self._open_output_dir,
        )
        self.open_btn.grid(row=0, column=3, padx=(6, 0))

    def _build_bottom(self, parent) -> None:
        bottom = ctk.CTkFrame(parent, fg_color="transparent")
        bottom.grid(row=5, column=0, sticky="ew", pady=(16, 0))
        bottom.grid_columnconfigure(0, weight=1)

        left = ctk.CTkFrame(bottom, fg_color="transparent")
        left.grid(row=0, column=0, sticky="ew")
        left.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            left,
            text="Добавьте файлы, чтобы начать",
            font=self.fonts["body"],
            text_color=MUTED,
            anchor="w",
            justify="left",
            wraplength=440,
        )
        self.status_label.grid(row=0, column=0, sticky="w")

        self.progress = ctk.CTkProgressBar(
            left,
            height=6,
            corner_radius=3,
            border_width=0,
            fg_color=CARD_2,
            progress_color=ACCENT,
        )
        self.progress.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        self.progress.set(0)
        self.progress.grid_remove()

        self.convert_btn = ctk.CTkButton(
            bottom,
            text="Конвертировать",
            width=196,
            height=46,
            corner_radius=12,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="#0A1220",
            text_color_disabled="#5A6A7E",
            font=self.fonts["big_button"],
            command=self._start_conversion,
            state="disabled",
        )
        self.convert_btn.grid(
            row=0, column=1, rowspan=2, sticky="e", padx=(18, 0)
        )

    # -- настройки и состояние ---------------------------------------------

    def _on_target_change(self, value: str) -> None:
        self.target = value
        self._update_visibility()

    def _on_quality_change(self, value: float) -> None:
        self.quality = int(round(value))
        self.quality_value.configure(text=f"{self.quality}%")

    def _on_dpi_change(self, value: str) -> None:
        self.dpi = int(value)

    def _update_visibility(self) -> None:
        show_quality = self.target in converter.LOSSY_TARGETS
        has_pdf = any(converter.is_pdf(path) for path in self.files)
        show_dpi = has_pdf and self.target not in ("PDF",)
        show_merge = (
            self.target == "PDF"
            and len(self.files) > 1
            and all(converter.is_image(path) for path in self.files)
        )

        for widget in (
            self.quality_label,
            self.quality_slider,
            self.quality_value,
        ):
            if show_quality:
                widget.grid()
            else:
                widget.grid_remove()

        for widget in (self.dpi_label, self.dpi_seg, self.dpi_unit):
            if show_dpi:
                widget.grid()
            else:
                widget.grid_remove()

        if show_merge:
            self.merge_check.grid()
        else:
            self.merge_check.grid_remove()

        self._update_hint_visibility()

    def _update_hint_visibility(self) -> None:
        has_pdf = any(converter.is_pdf(path) for path in self.files)
        has_images = any(converter.is_image(path) for path in self.files)
        has_documents = any(path.suffix.lower() in converter.office_converter.DOCUMENT_EXTENSIONS for path in self.files)

        if has_pdf and self.target != "PDF":
            text = "Страницы PDF будут сохранены отдельными изображениями."
        elif self.target == "PDF" and has_images:
            if len(self.files) > 1 and all(
                converter.is_image(path) for path in self.files
            ):
                text = (
                    "Все изображения будут собраны в один PDF."
                    if self.merge_var.get()
                    else "Каждый файл будет сохранён в отдельный PDF."
                )
            else:
                text = "Каждый файл будет сохранён в отдельный PDF."
        elif has_documents:
            text = "Документы: локальная обработка через LibreOffice. TXT сохраняет текст без оформления."
        else:
            text = ""

        if text:
            self.hint_label.configure(text=text)
            self.hint_label.grid()
        else:
            self.hint_label.grid_remove()

    def _update_hint(self) -> None:
        self._update_hint_visibility()

    def _refresh_targets(self) -> None:
        targets = list(converter.targets_for(self.files))
        if self.target not in targets:
            self.target = targets[0]
        self.target_seg.configure(
            values=targets, width=max(190, len(targets) * 90)
        )
        self.target_seg.set(self.target)
        self._update_visibility()

    def _update_folder_label(self) -> None:
        self.folder_label.configure(
            text=middle_shorten(str(self.output_dir), 56)
        )

    def _refresh_controls(self) -> None:
        count = len(self.files)
        self.count_badge.configure(text=str(count))
        self.clear_btn.configure(state="normal" if count else "disabled")
        self.convert_btn.configure(
            state="normal" if count and not self.converting else "disabled"
        )
        self._refresh_targets()

    def _set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        self.target_seg.configure(state=state)
        self.quality_slider.configure(state=state)
        self.dpi_seg.configure(state=state)
        self.merge_check.configure(state=state)
        self.change_btn.configure(state=state)
        self.clear_btn.configure(
            state="disabled" if busy or not self.files else "normal"
        )
        for button in self.remove_buttons:
            try:
                button.configure(state=state)
            except tk.TclError:
                pass
        if busy:
            self.convert_btn.configure(state="disabled", text="Конвертирую…")
        else:
            self.convert_btn.configure(
                text="Конвертировать",
                state="normal" if self.files else "disabled",
            )

    # -- работа с файлами ---------------------------------------------------

    def _choose_files(self) -> None:
        if self.converting:
            return
        types = [
            (
                "Поддерживаемые файлы",
                "*.png *.jpg *.jpeg *.webp *.bmp *.gif *.tif *.tiff *.ico *.pdf *.doc *.docx *.odt *.rtf *.txt ",
            ),
            (
                "Изображения",
                "*.png *.jpg *.jpeg *.webp *.bmp *.gif *.tif *.tiff *.ico",
            ),
            ("PDF", "*.pdf"),
            ("Документы", "*.doc *.docx *.odt *.rtf *.txt "),
            ("Все файлы", "*.*"),
        ]
        paths = filedialog.askopenfilenames(
            parent=self,
            title="Выберите файлы",
            filetypes=types,
        )
        if paths:
            self._accept_paths([Path(path) for path in paths])

    def _accept_paths(self, paths: list[Path]) -> None:
        if self.converting:
            self._set_status("Дождитесь окончания конвертации", WARNING)
            return

        known = {self._key(path) for path in self.files}
        added = 0
        skipped = 0

        for path in paths:
            try:
                candidates = (
                    sorted(
                        (
                            child
                            for child in path.iterdir()
                            if converter.is_supported(child)
                        ),
                        key=lambda child: child.name.lower(),
                    )
                    if path.is_dir()
                    else [path]
                )
            except OSError:
                skipped += 1
                continue

            for candidate in candidates:
                if not converter.is_supported(candidate):
                    skipped += 1
                    continue
                if self._key(candidate) in known:
                    continue
                if not converter.targets_for([*self.files, candidate]):
                    skipped += 1
                    continue
                self.files.append(Path(candidate))
                known.add(self._key(candidate))
                added += 1

        if added:
            self._rebuild_files()
            self._refresh_controls()
            if skipped:
                self._set_status(
                    f"Добавлено: {added}, пропущено: {skipped}. Разные типы документов конвертируйте отдельно.", WARNING
                )
            else:
                self._set_status(ready_text(len(self.files)), MUTED)
        elif skipped:
            self._set_status("Формат не поддерживается или несовместим с текущим списком. Очистите список.", DANGER)

    @staticmethod
    def _key(path: Path) -> str:
        try:
            resolved = path.resolve()
        except OSError:
            resolved = path.absolute()
        return os.path.normcase(str(resolved))

    def _remove_file(self, path: Path) -> None:
        if self.converting:
            return
        self.files = [item for item in self.files if item != path]
        self._rebuild_files()
        self._refresh_controls()
        if self.files:
            self._set_status(ready_text(len(self.files)), MUTED)
        else:
            self._set_status("Добавьте файлы, чтобы начать", MUTED)

    def _clear_files(self) -> None:
        if self.converting or not self.files:
            return
        self.files.clear()
        self._rebuild_files()
        self._refresh_controls()
        self._set_status("Добавьте файлы, чтобы начать", MUTED)

    def _rebuild_files(self) -> None:
        for child in self.scroll.winfo_children():
            child.destroy()

        self.remove_buttons = []

        if not self.files:
            self.empty_state = ctk.CTkFrame(self.scroll, fg_color="transparent")
            self.empty_state.pack(fill="both", expand=True, pady=34)
            ctk.CTkLabel(
                self.empty_state,
                text="Здесь появятся ваши файлы",
                font=self.fonts["body"],
                text_color=MUTED,
            ).pack()
            ctk.CTkLabel(
                self.empty_state,
                text="Изображения, PDF и документы Word",
                font=self.fonts["small"],
                text_color=DIM,
            ).pack(pady=(3, 0))
            self.after_idle(self._update_scrollbar)
            return

        for path in self.files:
            self._create_file_row(path)
        self.after_idle(self._update_scrollbar)

    def _update_scrollbar(self) -> None:
        try:
            _first, last = self.scroll._parent_canvas.yview()
            needed = last < 0.999
            if needed and not self._scrollbar_visible:
                self.scroll._scrollbar.grid()
                self._scrollbar_visible = True
            elif not needed and self._scrollbar_visible:
                self.scroll._scrollbar.grid_remove()
                self._scrollbar_visible = False
        except (tk.TclError, AttributeError):
            pass

    def _create_file_row(self, path: Path) -> None:
        row = ctk.CTkFrame(self.scroll, fg_color=CARD_2, corner_radius=10, height=54)
        row.pack(fill="x", padx=4, pady=(0, 6))
        row.pack_propagate(False)
        row.grid_columnconfigure(1, weight=1)

        thumb = self._thumbnail(path)
        holder = ctk.CTkFrame(
            row, width=38, height=38, corner_radius=8, fg_color=CARD_3
        )
        holder.grid(row=0, column=0, padx=(9, 10), pady=8)
        holder.pack_propagate(False)
        holder.grid_propagate(False)
        if thumb is not None:
            ctk.CTkLabel(holder, text="", image=thumb).place(
                relx=0.5, rely=0.5, anchor="center"
            )
        else:
            is_pdf = converter.is_pdf(path)
            holder.configure(
                fg_color="#2A1D22" if is_pdf else CARD_3,
            )
            extension = path.suffix.lstrip(".").upper()
            ctk.CTkLabel(
                holder,
                text=shorten(extension, 4),
                font=self.fonts["tiny_bold"],
                text_color="#F08A8A" if is_pdf else MUTED,
            ).place(relx=0.5, rely=0.5, anchor="center")

        text_box = ctk.CTkFrame(row, fg_color="transparent")
        text_box.grid(row=0, column=1, sticky="ew")
        ctk.CTkLabel(
            text_box,
            text=shorten(path.name, 58),
            font=self.fonts["body"],
            text_color=TEXT,
            anchor="w",
        ).pack(anchor="w")
        try:
            size = path.stat().st_size
            meta = f"{path.suffix.lstrip('.').upper()} · {human_size(size)}"
        except OSError:
            meta = path.suffix.lstrip(".").upper()
        ctk.CTkLabel(
            text_box,
            text=meta,
            font=self.fonts["tiny"],
            text_color=MUTED,
            anchor="w",
        ).pack(anchor="w")

        remove = ctk.CTkButton(
            row,
            text="✕",
            width=26,
            height=26,
            corner_radius=8,
            fg_color="transparent",
            hover_color="#2B1A1E",
            text_color=MUTED,
            font=self.fonts["small"],
            command=lambda item=path: self._remove_file(item),
        )
        remove.grid(row=0, column=2, padx=(6, 8))
        self.remove_buttons.append(remove)

    def _thumbnail(self, path: Path) -> ctk.CTkImage | None:
        if path in self.thumbs:
            return self.thumbs[path]

        if converter.is_pdf(path):
            self.thumbs[path] = None
            return None

        try:
            with Image.open(path) as source:
                source = ImageOps.exif_transpose(source)
                source.thumbnail((76, 76), Image.LANCZOS)
                canvas = Image.new("RGBA", (76, 76), (0, 0, 0, 0))
                x = (76 - source.width) // 2
                y = (76 - source.height) // 2
                canvas.paste(source.convert("RGBA"), (x, y))
            image = ctk.CTkImage(
                light_image=canvas, dark_image=canvas, size=(38, 38)
            )
            self.thumbs[path] = image
        except Exception:
            self.thumbs[path] = None

        return self.thumbs[path]

    # -- папка --------------------------------------------------------------

    def _choose_output_dir(self) -> None:
        if self.converting:
            return
        initial = self.output_dir if self.output_dir.exists() else Path.home()
        selected = filedialog.askdirectory(
            parent=self,
            title="Куда сохранять файлы",
            initialdir=str(initial),
        )
        if selected:
            self.output_dir = Path(selected)
            self._update_folder_label()

    def _open_output_dir(self) -> None:
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            if os.name == "nt":
                os.startfile(self.output_dir)  # type: ignore[attr-defined]
            else:  # pragma: no cover
                import subprocess
                import sys

                command = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.Popen([command, str(self.output_dir)])
        except Exception as exc:
            messagebox.showerror(
                "Не удалось открыть папку", str(exc), parent=self
            )

    # -- конвертация --------------------------------------------------------

    def _start_conversion(self) -> None:
        if self.converting or not self.files:
            return

        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            messagebox.showerror(
                "Не удалось создать папку",
                f"{self.output_dir}\n\n{exc}",
                parent=self,
            )
            return

        files = list(self.files)
        target = self.target
        quality = self.quality
        dpi = self.dpi
        output_dir = self.output_dir
        merge = self.merge_var.get() and target == "PDF"

        self.converting = True
        self._set_busy(True)
        self.progress.set(0)
        self.progress.grid()
        self._set_status("Подготовка…", MUTED)
        self.update_idletasks()

        def worker() -> None:
            try:
                result = converter.convert_files(
                    files,
                    target,
                    output_dir,
                    quality=quality,
                    dpi=dpi,
                    merge_pdf=merge,
                    progress=lambda done, total, label: self.queue.put(
                        ("progress", done, total, label)
                    ),
                )
                self.queue.put(("done", result))
            except Exception as exc:  # noqa: BLE001
                self.queue.put(("failed", str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def _poll_queue(self) -> None:
        try:
            while True:
                message = self.queue.get_nowait()
                kind = message[0]
                if kind == "progress":
                    self._show_progress(*message[1:])
                elif kind == "done":
                    self._finish_conversion(message[1])
                elif kind == "failed":
                    self._fail_conversion(message[1])
        except queue.Empty:
            pass

        try:
            self.after(100, self._poll_queue)
        except tk.TclError:
            pass

    def _show_progress(self, done: int, total: int, label: str) -> None:
        if not self.converting:
            return
        fraction = done / total if total else 0
        self.progress.set(max(0.0, min(1.0, fraction)))
        self._set_status(
            f"{done} из {total} · {shorten(label, 44)}", MUTED
        )

    def _finish_conversion(self, result: converter.ConversionResult) -> None:
        self.converting = False
        self._set_busy(False)

        if result.ok_count:
            self.progress.set(1)
            folder_name = result.folder.name if result.folder else ""
            if result.has_errors:
                self._set_status(
                    f"Готово с ошибками · сохранено {result.ok_count}",
                    WARNING,
                )
            else:
                self._set_status(
                    f"Готово · {result.ok_count} {files_word(result.ok_count)}"
                    f" в папке «{folder_name}»",
                    SUCCESS,
                )
            self.after(2600, self._hide_progress_if_idle)
        else:
            self.progress.set(0)
            self._set_status("Не удалось конвертировать", DANGER)
            self.after(1200, self._hide_progress_if_idle)

        if result.has_errors:
            details = "\n".join(result.errors[:12])
            if len(result.errors) > 12:
                details += f"\n…и ещё {len(result.errors) - 12}"
            messagebox.showwarning(
                "Некоторые файлы не удалось обработать",
                details,
                parent=self,
            )

    def _fail_conversion(self, message: str) -> None:
        self.converting = False
        self._set_busy(False)
        self.progress.grid_remove()
        self._set_status("Не удалось конвертировать", DANGER)
        messagebox.showerror("Ошибка конвертации", message, parent=self)

    def _hide_progress_if_idle(self) -> None:
        if not self.converting:
            try:
                self.progress.grid_remove()
            except tk.TclError:
                pass

    def _set_status(self, text: str, color: str = MUTED) -> None:
        self.status_label.configure(text=text, text_color=color)

    # -- прочее -------------------------------------------------------------

    def _bind_shortcuts(self) -> None:
        self.bind("<Control-o>", lambda _event: self._choose_files())
        self.bind("<Control-O>", lambda _event: self._choose_files())
        self.bind("<Control-Return>", lambda _event: self._start_conversion())

    def _on_close(self) -> None:
        if self.converting:
            if not messagebox.askyesno(
                "Конвертация не завершена",
                "Файлы ещё конвертируются. Закрыть приложение?",
                parent=self,
            ):
                return
        self.destroy()


def main() -> None:
    app = ConverterApp()
    app.mainloop()


if __name__ == "__main__":
    main()
