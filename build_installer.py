"""Build one offline Windows installer from the existing application folder."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess

from app_info import APP_NAME, VERSION
from release_tools import ROOT, source_archive


def find_compiler():
    explicit = os.environ.get('INNO_SETUP_COMPILER')
    candidates = [Path(explicit)] if explicit else []
    candidates.append(ROOT / '.build-tools' / 'InnoSetup' / 'ISCC.exe')
    found = shutil.which('ISCC.exe')
    if found:
        candidates.append(Path(found))
    for variable in ('ProgramFiles', 'ProgramFiles(x86)', 'LOCALAPPDATA'):
        prefix = Path(os.environ.get(variable, 'C:/Program Files'))
        for version in ('Inno Setup 7', 'Inno Setup 6'):
            candidates.extend((prefix / version / 'ISCC.exe', prefix / 'Programs' / version / 'ISCC.exe'))
    return next((path for path in candidates if path.is_file()), None)


def main():
    application = ROOT / 'dist' / APP_NAME
    for name in ('EasyConverter.exe', '_internal/python312.dll', 'office/program/soffice.exe', 'LICENSE'):
        if not (application / name).is_file():
            raise SystemExit('Run python build.py before building the installer.')
    compiler = find_compiler()
    if compiler is None:
        raise SystemExit('Install Inno Setup 6.3+ or set INNO_SETUP_COMPILER to ISCC.exe.')
    # Keep the distributed sources and instructions current without rebuilding Python.
    for name in ('ИНСТРУКЦИЯ.txt', 'README.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md'):
        shutil.copy2(ROOT / name, application / name)
    source_archive(application / f'{APP_NAME}-source.zip')
    subprocess.run([
        str(compiler), f'/DAppVersion={VERSION}',
        str(ROOT / 'installer' / 'EasyConverter.iss'),
    ], cwd=ROOT, check=True)
    installer = ROOT / 'releases' / f'{APP_NAME}Setup-{VERSION}.exe'
    with installer.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    checksum = installer.with_suffix('.exe.sha256')
    checksum.write_text(f'{digest}  {installer.name}\n', encoding='utf-8')
    print(f'Installer: {installer.name} ({installer.stat().st_size / 1024**2:.1f} MiB)')
    print(f'SHA256: {digest}')


if __name__ == '__main__':
    main()
