# Сторонние компоненты EasyConverter

Исходники EasyConverter лицензируются под GNU AGPL v3.0 only (файл `LICENSE`).
Сторонние библиотеки и отдельный исполняемый движок LibreOffice сохраняют
собственные лицензии. Они не являются авторской разработкой EasyConverter.

| Компонент | Исходники и лицензии |
| --- | --- |
| Python | https://www.python.org/downloads/source/ — PSF License и включённые уведомления |
| CustomTkinter | https://github.com/TomSchimansky/CustomTkinter — лицензия из установленного пакета |
| Pillow | https://github.com/python-pillow/Pillow — HPND и включённые лицензии |
| PyMuPDF / MuPDF | https://github.com/pymupdf/PyMuPDF и https://mupdf.com/ — GNU AGPL v3 |
| tkinterdnd2 / TkDnD | https://github.com/Eliav2/tkinterdnd2 — MIT и уведомления TkDnD |
| LibreOffice | https://www.libreoffice.org/licenses/ и https://download.documentfoundation.org/libreoffice/src/ — MPL 2.0 / LGPL и лицензии включённых компонентов |
| NumPy | https://github.com/numpy/numpy — BSD и включённые лицензии |
| ONNX Runtime | https://github.com/microsoft/onnxruntime — MIT и уведомления сторонних компонентов |
| psutil | https://github.com/giampaolo/psutil — BSD |
| NetworkX | https://github.com/networkx/networkx — BSD |
| PyYAML | https://github.com/yaml/pyyaml — MIT |
| tabulate | https://github.com/astanin/python-tabulate — MIT |
| setuptools / packaging / darkdetect | https://github.com/pypa/setuptools, https://github.com/pypa/packaging, https://github.com/albertosottile/darkdetect — лицензии из пакетов |
| Tcl/Tk | https://www.tcl-lang.org/software/tcltk/ — включённые лицензии Tcl/Tk |
| PyInstaller (сборщик и загрузчик) | https://github.com/pyinstaller/pyinstaller — GPL с исключением для загрузчика |

Готовая сборка содержит:

- `licenses/` — лицензионные тексты и сведения о версиях Python-пакетов;
- `office/license.txt`, `office/LICENSE.html`, `office/NOTICE` — уведомления LibreOffice;
- `EasyConverter-source.zip` — исходники приложения и скрипты сборки;
- лицензионные файлы библиотек внутри `_internal` и `office`.

LibreOffice включается без изменений из установленного дистрибутива.
Версия и идентификатор исходной сборки находятся в `office/program/version.ini`
и `office/readmes/readme_en-US.txt`. Исходные архивы соответствующей версии
доступны в каталоге исходников The Document Foundation, указанном выше.

Windows runtime-компоненты сохраняют условия их правообладателей.
Полные уведомления скопированных зависимостей имеют приоритет над краткой таблицей.
