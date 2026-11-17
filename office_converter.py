"""Local document conversions through LibreOffice in an isolated profile."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import sys

TEXT_EXTENSIONS = {".doc", ".docx", ".odt", ".rtf", ".txt"}
DOCUMENT_EXTENSIONS = TEXT_EXTENSIONS
TEXT_TARGETS = ("DOCX", "DOC", "ODT", "RTF", "TXT", "PDF")
FILTERS = {
    "DOCX": "docx:Office Open XML Text", "DOC": "doc:MS Word 97",
    "ODT": "odt:writer8", "RTF": "rtf:Rich Text Format",
    "TXT": "txt:Text (encoded):UTF8",
    "PDF": "pdf",
}


def find_libreoffice():
    bundled = Path(sys.executable).parent / "office/program/soffice.exe"
    if getattr(sys, "frozen", False) and bundled.is_file():
        return bundled
    found = shutil.which("soffice")
    if found:
        return Path(found)
    for variable in ("ProgramFiles", "ProgramFiles(x86)"):
        path = Path(os.environ.get(variable, "C:/Program Files")) / "LibreOffice/program/soffice.exe"
        if path.is_file():
            return path
    return None


def targets_for(path):
    return TEXT_TARGETS if path.suffix.lower() in DOCUMENT_EXTENSIONS else ()


def convert_document(source, target, destination):
    if target not in targets_for(source):
        raise ValueError(f"Формат {target} недоступен для {source.suffix}")
    executable = find_libreoffice()
    if executable is None:
        raise RuntimeError("Для документов установите бесплатный LibreOffice и перезапустите программу.")
    with tempfile.TemporaryDirectory(prefix="converter-office-") as directory:
        workspace = Path(directory)
        output = workspace / "output"
        output.mkdir()
        profile = (workspace / "profile").as_uri()
        completed = subprocess.run([
            str(executable), f"-env:UserInstallation={profile}",
            "--headless", "--convert-to", FILTERS[target], "--outdir",
            str(output), str(source.resolve()),
        ], capture_output=True, timeout=180, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        result = output / (source.stem + "." + target.lower())
        if completed.returncode or not result.is_file():
            raise RuntimeError("LibreOffice не смог преобразовать документ. Проверьте, что файл открывается и не защищён паролем.")
        shutil.copyfile(result, destination)
