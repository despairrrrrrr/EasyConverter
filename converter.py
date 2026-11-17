"""Логика конвертации изображений и PDF.

Модуль не зависит от интерфейса: его можно использовать отдельно.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

import pymupdf
import office_converter
from app_info import APP_NAME
from PIL import Image, ImageOps, UnidentifiedImageError


IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
    ".gif",
    ".tif",
    ".tiff",
    ".ico",
}
PDF_EXTENSIONS = {".pdf"}
INPUT_EXTENSIONS = IMAGE_EXTENSIONS | PDF_EXTENSIONS | office_converter.DOCUMENT_EXTENSIONS

IMAGE_TARGETS = ("PNG", "JPG", "WEBP", "BMP", "PDF")
PDF_TARGETS = ("PNG", "JPG")

TARGET_EXTENSIONS = {
    "PNG": ".png",
    "JPG": ".jpg",
    "WEBP": ".webp",
    "BMP": ".bmp",
    "PDF": ".pdf",
}

# Качество имеет смысл только для форматов с потерями.
LOSSY_TARGETS = {"JPG", "WEBP"}

ProgressCallback = Callable[[int, int, str], None]


@dataclass
class ConversionResult:
    outputs: list[Path] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    folder: Path | None = None

    @property
    def ok_count(self) -> int:
        return len(self.outputs)

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)


def is_image(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTENSIONS


def is_pdf(path: Path) -> bool:
    return path.suffix.lower() in PDF_EXTENSIONS


def is_supported(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in INPUT_EXTENSIONS


def targets_for(paths: Iterable[Path]) -> tuple[str, ...]:
    """Доступные форматы зависят от набора файлов."""
    paths = list(paths)
    documents = [path for path in paths if path.suffix.lower() in office_converter.DOCUMENT_EXTENSIONS]
    if documents:
        choices = office_converter.targets_for(documents[0])
        for path in paths:
            available = (office_converter.targets_for(path)
                         if path in documents else PDF_TARGETS if is_pdf(path) else IMAGE_TARGETS)
            choices = tuple(target for target in choices if target in available)
        return choices
    if any(is_pdf(path) for path in paths):
        return PDF_TARGETS
    return IMAGE_TARGETS


def default_output_dir() -> Path:
    return Path.home() / "Documents" / APP_NAME


def convert_files(
    files: Iterable[Path],
    target: str,
    output_dir: Path,
    *,
    quality: int = 92,
    dpi: int = 150,
    merge_pdf: bool = False,
    progress: ProgressCallback | None = None,
) -> ConversionResult:
    """Конвертирует файлы в папку output_dir.

    progress вызывается после каждого обработанного шага (файл или страница PDF).
    """
    files = [Path(path) for path in files]
    output_dir = Path(output_dir)
    result = ConversionResult(folder=output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    target = target.upper()
    if files and target not in targets_for(files):
        raise ValueError("Выбранный формат недоступен для этого набора файлов. Конвертируйте документы, PDF и изображения отдельно.")
    quality = max(30, min(100, int(quality)))
    dpi = max(72, min(300, int(dpi)))

    total = sum(_count_units(path) for path in files) or 1
    done = 0

    def tick(label: str) -> None:
        nonlocal done
        done += 1
        if progress is not None:
            progress(done, total, label)

    if target == "PDF" and merge_pdf and files and all(is_image(path) for path in files):
        _merge_images_to_pdf(files, output_dir, result, tick)
        return result

    for path in files:
        if not is_supported(path):
            result.errors.append(f"{path.name}: формат не поддерживается")
            done += _count_units(path)
            if progress is not None:
                progress(min(done, total), total, path.name)
            continue

        if path.suffix.lower() in office_converter.DOCUMENT_EXTENSIONS:
            try:
                output = _unique_path(output_dir, path.stem, "." + target.lower())
                office_converter.convert_document(path, target, output)
                result.outputs.append(output)
            except Exception as exc:
                result.errors.append(f"{path.name}: {_describe_error(exc)}")
            tick(path.name)
        elif is_pdf(path):
            _convert_pdf(path, target, output_dir, result, quality, dpi, tick)
        else:
            _convert_image(path, target, output_dir, result, quality)
            tick(path.name)

    return result


def _count_units(path: Path) -> int:
    if is_pdf(path):
        try:
            with pymupdf.open(path) as document:
                return max(1, document.page_count)
        except Exception:
            return 1
    return 1


def _load_image(path: Path) -> Image.Image:
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source)
        image.load()

    if image.mode in ("RGB", "RGBA"):
        return image
    if image.mode == "P" and "transparency" in image.info:
        return image.convert("RGBA")
    return image.convert("RGB")


def _flatten(image: Image.Image) -> Image.Image:
    """Убирает прозрачность, подкладывая белый фон."""
    if image.mode in ("RGBA", "LA") or (
        image.mode == "P" and "transparency" in image.info
    ):
        image = image.convert("RGBA")
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.getchannel("A"))
        return background
    return image.convert("RGB")


def _save_image(image: Image.Image, path: Path, target: str, quality: int) -> None:
    if target == "JPG":
        _flatten(image).save(
            path, "JPEG", quality=quality, optimize=True, progressive=True
        )
    elif target == "WEBP":
        image.save(path, "WEBP", quality=quality, method=4)
    elif target == "PNG":
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGBA" if "transparency" in image.info else "RGB")
        image.save(path, "PNG", optimize=True)
    elif target == "BMP":
        _flatten(image).save(path, "BMP")
    else:
        raise ValueError(f"Неизвестный формат: {target}")


def _unique_path(directory: Path, stem: str, extension: str) -> Path:
    candidate = directory / f"{stem}{extension}"
    counter = 2
    while candidate.exists():
        candidate = directory / f"{stem} ({counter}){extension}"
        counter += 1
    return candidate


def _convert_image(
    path: Path,
    target: str,
    output_dir: Path,
    result: ConversionResult,
    quality: int,
) -> None:
    try:
        image = _load_image(path)

        if target == "PDF":
            output = _unique_path(output_dir, path.stem, ".pdf")
            _flatten(image).save(output, "PDF", resolution=96.0)
        else:
            output = _unique_path(
                output_dir, path.stem, TARGET_EXTENSIONS[target]
            )
            _save_image(image, output, target, quality)

        result.outputs.append(output)
    except Exception as exc:  # noqa: BLE001 - показываем пользователю понятный текст
        result.errors.append(f"{path.name}: {_describe_error(exc)}")


def _convert_pdf(
    path: Path,
    target: str,
    output_dir: Path,
    result: ConversionResult,
    quality: int,
    dpi: int,
    tick: Callable[[str], None],
) -> None:
    try:
        document = pymupdf.open(path)
    except Exception as exc:  # noqa: BLE001
        result.errors.append(f"{path.name}: {_describe_error(exc)}")
        tick(path.name)
        return

    try:
        if document.needs_pass:
            result.errors.append(f"{path.name}: файл защищён паролем")
            for _ in range(max(1, document.page_count)):
                tick(path.name)
            return

        page_count = document.page_count
        for index, page in enumerate(document, start=1):
            try:
                pixmap = page.get_pixmap(dpi=dpi, alpha=False)
                image = Image.frombytes(
                    "RGB", (pixmap.width, pixmap.height), pixmap.samples
                )
                stem = path.stem if page_count == 1 else f"{path.stem}_{index:02d}"
                output = _unique_path(output_dir, stem, TARGET_EXTENSIONS[target])
                _save_image(image, output, target, quality)
                result.outputs.append(output)
                tick(f"{path.name} · стр. {index}")
            except Exception as exc:  # noqa: BLE001
                result.errors.append(
                    f"{path.name} · стр. {index}: {_describe_error(exc)}"
                )
                tick(f"{path.name} · стр. {index}")
    finally:
        document.close()


def _merge_images_to_pdf(
    files: list[Path],
    output_dir: Path,
    result: ConversionResult,
    tick: Callable[[str], None],
) -> None:
    pages: list[Image.Image] = []
    for path in files:
        try:
            pages.append(_flatten(_load_image(path)))
        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"{path.name}: {_describe_error(exc)}")
        tick(path.name)

    if not pages:
        return

    stem = files[0].stem if len(pages) == 1 else "Изображения"
    output = _unique_path(output_dir, stem, ".pdf")
    try:
        pages[0].save(
            output,
            "PDF",
            resolution=96.0,
            save_all=True,
            append_images=pages[1:],
        )
        result.outputs.append(output)
    except Exception as exc:  # noqa: BLE001
        result.errors.append(f"{output.name}: {_describe_error(exc)}")


def _describe_error(exc: Exception) -> str:
    if isinstance(exc, PermissionError):
        return "нет доступа к файлу"
    if isinstance(exc, FileNotFoundError):
        return "файл не найден"
    if isinstance(exc, UnidentifiedImageError):
        return "не удалось распознать изображение"

    text = str(exc).strip()
    lowered = text.lower()
    if "password" in lowered or "encrypted" in lowered:
        return "файл защищён паролем"
    return text or exc.__class__.__name__
