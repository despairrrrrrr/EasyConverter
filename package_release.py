"""Create the Windows ZIP, source ZIP and SHA-256 checksum file."""
import hashlib
from pathlib import Path
import zipfile

from app_info import APP_NAME, VERSION
from release_tools import ROOT, source_archive


def main():
    application = ROOT / "dist" / APP_NAME
    for name in (f"{APP_NAME}.exe", "office/program/soffice.exe", "LICENSE"):
        if not (application / name).is_file():
            raise SystemExit("Run python build.py before packaging a release.")
    releases = ROOT / "releases"
    releases.mkdir(exist_ok=True)
    binary = releases / f"{APP_NAME}-{VERSION}-windows-x64.zip"
    with zipfile.ZipFile(binary, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(application.rglob("*")):
            if path.is_file():
                archive.write(path, Path(APP_NAME) / path.relative_to(application))
    source = releases / f"{APP_NAME}-{VERSION}-source.zip"
    source_archive(source)
    checksums = []
    for path in (binary, source):
        with path.open("rb") as stream:
            checksum = hashlib.file_digest(stream, "sha256").hexdigest()
        checksums.append(f"{checksum}  {path.name}")
        print(f"{path.name}: {path.stat().st_size / 1024**2:.1f} MiB")
    (releases / "SHA256SUMS.txt").write_text("\n".join(checksums) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
