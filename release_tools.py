"""Helpers shared by the build and release scripts."""
from importlib import metadata
from pathlib import Path
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parent
SOURCE_FILES = (
    "app.py", "app_info.py", "ui_layout.py", "theme.py", "converter.py", "office_converter.py",
    "build.py", "build_installer.py", "installer/EasyConverter.iss",
    "release_tools.py", "package_release.py", "test_converter.py", "test_ui.py",
    "requirements.txt", "requirements-build.txt", "run.bat", "windows-version.txt",
    "README.md", "CHANGELOG.md", "LICENSE", "THIRD_PARTY_NOTICES.md",
    "ИНСТРУКЦИЯ.txt", ".gitignore", ".gitattributes", ".github/workflows/tests.yml",
    "assets/icon.ico", "assets/logo.png",
)


def source_archive(destination):
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in SOURCE_FILES:
            archive.write(ROOT / name, f"EasyConverter/{name}")


def collect_licenses(destination):
    destination.mkdir(parents=True, exist_ok=True)
    packages = (
        "customtkinter", "Pillow", "PyMuPDF", "tkinterdnd2", "darkdetect",
        "numpy", "onnxruntime", "psutil", "networkx", "PyYAML", "tabulate",
        "setuptools", "packaging", "PyInstaller",
    )
    versions = [f"Python=={sys.version.split()[0]}"]
    for name in packages:
        try:
            distribution = metadata.distribution(name)
        except metadata.PackageNotFoundError:
            continue
        versions.append(f"{distribution.metadata['Name']}=={distribution.version}")
        for file in distribution.files or ():
            if not any(token in file.name.lower() for token in ("license", "copying", "notice", "copyright")):
                continue
            source = Path(distribution.locate_file(file))
            if source.is_file():
                target = destination / name / str(file)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
    python_license = Path(sys.base_prefix) / "LICENSE.txt"
    if python_license.is_file():
        shutil.copy2(python_license, destination / "Python-LICENSE.txt")
    for folder in (Path(sys.base_prefix) / "tcl").glob("*"):
        if folder.is_dir():
            for source in folder.glob("license*"):
                if source.is_file():
                    shutil.copy2(source, destination / f"{folder.name}-{source.name}")
    (destination / "VERSIONS.txt").write_text("\n".join(versions) + "\n", encoding="utf-8")
