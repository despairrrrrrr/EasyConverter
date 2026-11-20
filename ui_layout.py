"""Desktop workspace styled after the EasyConverter Online website."""
import customtkinter as ctk
from app_info import APP_NAME, VERSION
from theme import (
    BG, CARD, CARD_2, CARD_3, BORDER, TEXT, MUTED, DIM, ACCENT,
    ACCENT_HOVER, ACCENT_SOFT, SUCCESS,
)
import converter


def label(parent, app, text, style="body", color=TEXT, **kwargs):
    kwargs.setdefault("height", {"hero": 40, "h1": 32, "section": 24, "tiny_bold": 18}.get(style, 20))
    return ctk.CTkLabel(parent, text=text, font=app.fonts[style], text_color=color, **kwargs)


def secondary(parent, app, text, command, **kwargs):
    return ctk.CTkButton(
        parent, text=text, command=command, height=34, corner_radius=8,
        fg_color=CARD, hover_color=ACCENT_SOFT, border_width=1,
        border_color=BORDER, text_color=TEXT, font=app.fonts["small"], **kwargs,
    )


def build_ui(app, dropzone_class):
    main = ctk.CTkFrame(app, fg_color=BG, corner_radius=0)
    main.pack(fill="both", expand=True, padx=32, pady=(22, 18))
    main.grid_columnconfigure(0, weight=1)
    main.grid_rowconfigure(2, weight=1)

    header = ctk.CTkFrame(main, fg_color="transparent")
    header.grid(row=0, column=0, sticky="ew")
    mark = ctk.CTkFrame(header, width=42, height=42, corner_radius=12, fg_color=ACCENT)
    mark.pack(side="left")
    mark.pack_propagate(False)
    label(mark, app, "ec", "h1", "#FFFFFF").place(relx=.5, rely=.5, anchor="center")
    label(header, app, APP_NAME, "h1").pack(side="left", padx=(12, 8))
    label(header, app, "desktop", "small", ACCENT, fg_color=ACCENT_SOFT,
          corner_radius=5, width=64, height=25).pack(side="left")
    label(header, app, "✓  Файлы остаются на устройстве", "small", SUCCESS).pack(side="right")

    intro = ctk.CTkFrame(main, fg_color="transparent")
    intro.grid(row=1, column=0, sticky="ew", pady=(18, 14))
    label(intro, app, "ВАШИ ФАЙЛЫ. ВАШ ФОРМАТ.", "tiny_bold", ACCENT).pack(anchor="w")
    label(intro, app, "Что сделаем с файлами?", "hero").pack(anchor="w", pady=(5, 0))
    label(intro, app, "Изображения и документы — в нужный формат, без интернета.",
          "body", MUTED).pack(anchor="w", pady=(5, 0))

    workspace = ctk.CTkFrame(main, fg_color=CARD, border_width=1, border_color=BORDER, corner_radius=17)
    workspace.grid(row=2, column=0, sticky="nsew")
    workspace.grid_columnconfigure(0, weight=1)
    workspace.grid_columnconfigure(1, weight=0, minsize=326)
    workspace.grid_rowconfigure(0, weight=1)
    files = ctk.CTkFrame(workspace, fg_color="transparent")
    files.grid(row=0, column=0, sticky="nsew", padx=22, pady=22)
    files.grid_columnconfigure(0, weight=1)
    files.grid_rowconfigure(1, weight=1)
    app.dropzone = dropzone_class(files, app.fonts, app._choose_files, app._accept_paths, app.dnd_ready)
    app.dropzone.grid(row=0, column=0, sticky="ew")

    queue = ctk.CTkFrame(files, fg_color="transparent")
    queue.grid(row=1, column=0, sticky="nsew", pady=(18, 0))
    queue.grid_columnconfigure(0, weight=1)
    queue.grid_rowconfigure(1, weight=1)
    queue_header = ctk.CTkFrame(queue, fg_color="transparent")
    queue_header.grid(row=0, column=0, sticky="ew", pady=(0, 6))
    label(queue_header, app, "Ваши файлы", "section").pack(side="left")
    app.count_badge = label(queue_header, app, "0", "tiny_bold", ACCENT,
                            width=25, height=22, corner_radius=6, fg_color=ACCENT_SOFT)
    app.count_badge.pack(side="left", padx=8)
    app.clear_btn = ctk.CTkButton(
        queue_header, text="Очистить", command=app._clear_files, width=75, height=26,
        fg_color="transparent", hover_color=ACCENT_SOFT, text_color=MUTED,
        text_color_disabled=DIM, font=app.fonts["small"], state="disabled",
    )
    app.clear_btn.pack(side="right")
    app.scroll = ctk.CTkScrollableFrame(
        queue, fg_color="transparent", corner_radius=0, scrollbar_fg_color="transparent",
        scrollbar_button_color=CARD_3, scrollbar_button_hover_color="#B9C8E5", height=100,
    )
    app.scroll.grid(row=1, column=0, sticky="nsew")
    app._scrollbar_visible = True
    app.scroll._parent_canvas.bind("<Configure>", lambda _event: app.after_idle(app._update_scrollbar), add="+")
    app._rebuild_files()

    sidebar = ctk.CTkFrame(workspace, fg_color="#FCFDFF", corner_radius=14, width=326)
    sidebar.grid(row=0, column=1, sticky="nsew", padx=(0, 2), pady=2)
    sidebar.grid_columnconfigure(0, weight=1)
    sidebar.grid_rowconfigure(1, weight=1)
    inner = ctk.CTkFrame(sidebar, fg_color="transparent")
    inner.grid(row=0, column=0, sticky="new", padx=22, pady=(22, 0))
    inner.grid_columnconfigure(0, weight=1)
    app.settings_inner = inner
    label(inner, app, "Настройки конвертации", "section").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))
    label(inner, app, "Формат результата", color=MUTED).grid(row=1, column=0, columnspan=2, sticky="w")
    app.target_seg = ctk.CTkOptionMenu(
        inner, values=list(converter.IMAGE_TARGETS), command=app._on_target_change,
        height=40, corner_radius=8, fg_color=CARD_2, button_color=CARD_3,
        button_hover_color=ACCENT_SOFT, text_color=TEXT, text_color_disabled=DIM,
        dropdown_fg_color=CARD, dropdown_text_color=TEXT, dropdown_hover_color=ACCENT_SOFT,
        font=app.fonts["body"], dropdown_font=app.fonts["body"], dynamic_resizing=False,
    )
    app.target_seg.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))
    app.target_seg.set(app.target)
    app.quality_label = label(inner, app, "Качество", color=MUTED)
    app.quality_label.grid(row=3, column=0, sticky="w", pady=(12, 0))
    app.quality_value = label(inner, app, f"{app.quality}%", "value", ACCENT)
    app.quality_value.grid(row=3, column=1, sticky="e", pady=(12, 0))
    app.quality_slider = ctk.CTkSlider(
        inner, from_=30, to=100, number_of_steps=70, height=18,
        fg_color=CARD_3, progress_color=ACCENT, button_color=ACCENT,
        button_hover_color=ACCENT_HOVER, command=app._on_quality_change,
    )
    app.quality_slider.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(10, 0))
    app.quality_slider.set(app.quality)
    app.dpi_label = label(inner, app, "Разрешение PDF", color=MUTED)
    app.dpi_label.grid(row=5, column=0, sticky="w", pady=(12, 0))
    app.dpi_unit = label(inner, app, "DPI", "small", DIM)
    app.dpi_unit.grid(row=5, column=1, sticky="e", pady=(12, 0))
    app.dpi_seg = ctk.CTkSegmentedButton(
        inner, values=["96", "150", "300"], command=app._on_dpi_change,
        height=34, fg_color=CARD_3, selected_color=ACCENT, selected_hover_color=ACCENT_HOVER,
        unselected_color=CARD_2, unselected_hover_color=ACCENT_SOFT,
        text_color=TEXT, font=app.fonts["body"],
    )
    app.dpi_seg.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(8, 0))
    app.dpi_seg.set(str(app.dpi))
    app.merge_check = ctk.CTkCheckBox(
        inner, text="Собрать в один PDF", variable=app.merge_var, command=app._update_hint,
        font=app.fonts["body"], text_color=TEXT, checkbox_width=18, checkbox_height=18,
        border_width=2, border_color=BORDER, fg_color=ACCENT, hover_color=ACCENT_HOVER,
        checkmark_color="#FFFFFF",
    )
    app.merge_check.grid(row=7, column=0, columnspan=2, sticky="w", pady=(18, 0))
    app.hint_label = label(inner, app, "", "small", DIM, justify="left", wraplength=270, anchor="w")
    app.hint_label.grid(row=8, column=0, columnspan=2, sticky="w", pady=(10, 0))

    output = ctk.CTkFrame(sidebar, fg_color="transparent")
    output.grid(row=2, column=0, sticky="ew", padx=22, pady=(12, 8))
    output.grid_columnconfigure((0, 1), weight=1)
    label(output, app, "Сохранить в", color=MUTED).grid(row=0, column=0, columnspan=2, sticky="w")
    app.folder_label = label(output, app, "", "small", TEXT, wraplength=270, justify="left", anchor="w")
    app.folder_label.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 10))
    app._update_folder_label()
    app.change_btn = secondary(output, app, "Изменить", app._choose_output_dir, width=125)
    app.change_btn.grid(row=2, column=0, sticky="ew", padx=(0, 4))
    app.open_btn = secondary(output, app, "Открыть", app._open_output_dir, width=125)
    app.open_btn.grid(row=2, column=1, sticky="ew", padx=(4, 0))

    bottom = ctk.CTkFrame(sidebar, fg_color="transparent")
    bottom.grid(row=3, column=0, sticky="ew", padx=22, pady=(4, 16))
    bottom.grid_columnconfigure(0, weight=1)
    app.convert_btn = ctk.CTkButton(
        bottom, text="Конвертировать", height=44, corner_radius=8, fg_color=ACCENT,
        hover_color=ACCENT_HOVER, text_color="#FFFFFF", text_color_disabled="#D9E4FF",
        font=app.fonts["big_button"], command=app._start_conversion, state="disabled",
    )
    app.convert_btn.grid(row=0, column=0, sticky="ew")
    app.status_label = label(bottom, app, "Добавьте файлы, чтобы начать", "small", MUTED,
                             wraplength=270, justify="left", anchor="w")
    app.status_label.grid(row=1, column=0, sticky="ew", pady=(12, 0))
    app.progress = ctk.CTkProgressBar(bottom, height=5, fg_color=CARD_3, progress_color=ACCENT)
    app.progress.grid(row=2, column=0, sticky="ew", pady=(10, 0))
    app.progress.set(0)
    app.progress.grid_remove()
    app._update_visibility()
    footer = ctk.CTkFrame(main, fg_color="transparent")
    footer.grid(row=3, column=0, sticky="ew", pady=(12, 0))
    label(footer, app, "Без загрузки в облако. Без регистрации.", "small", MUTED).pack(side="left")
    label(footer, app, f"Версия {VERSION} · Windows", "small", DIM).pack(side="right")
