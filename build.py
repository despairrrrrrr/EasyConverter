"""Build the standalone Windows application using locally installed PyInstaller."""
from pathlib import Path
import sys
import shutil
from app_info import APP_NAME
from release_tools import collect_licenses, source_archive

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / ".build-tools"))

if __name__ == "__main__":
    import PyInstaller.__main__

    from office_converter import find_libreoffice
    office = find_libreoffice()
    if office is None:
        raise SystemExit("Install LibreOffice on the build machine to bundle document conversion.")

    PyInstaller.__main__.run([
        str(ROOT / "app.py"),
        f"--name={APP_NAME}", "--noconfirm", "--clean", "--windowed",
        "--onedir", f"--icon={ROOT / 'assets' / 'icon.ico'}",
        f"--version-file={ROOT / 'windows-version.txt'}",
        f"--add-data={ROOT / 'assets'};assets",
        "--collect-all=customtkinter", "--collect-all=tkinterdnd2",
        "--collect-all=pymupdf",
        f"--distpath={ROOT / 'dist'}", f"--workpath={ROOT / 'build'}",
        f"--specpath={ROOT / 'build'}",
    ])
    application = ROOT / "dist" / APP_NAME
    shutil.copytree(office.parent.parent, application / "office", dirs_exist_ok=True)
    for name in ("ИНСТРУКЦИЯ.txt", "README.md", "LICENSE", "THIRD_PARTY_NOTICES.md"):
        shutil.copy2(ROOT / name, application / name)
    collect_licenses(application / "licenses")
    source_archive(application / f"{APP_NAME}-source.zip")
