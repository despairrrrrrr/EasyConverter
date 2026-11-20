# EasyConverter

**Офлайн-конвертер изображений и документов для Windows.**

Добавьте файлы, выберите нужный формат и папку сохранения. EasyConverter
обрабатывает файлы на компьютере, без загрузки в облако и регистрации.
Интерфейс — на русском языке, в светлом оформлении EasyConverter Online:
файлы слева, настройки и папка результата справа.

## Возможности

| Что конвертируем | Входные форматы | Результат |
| --- | --- | --- |
| Изображения | PNG, JPG/JPEG, WEBP, BMP, GIF, TIFF, ICO | PNG, JPG, WEBP, BMP, PDF |
| Текстовые документы | DOC, DOCX, ODT, RTF, TXT | DOC, DOCX, ODT, RTF, TXT, PDF |
| Страницы PDF | PDF | PNG, JPG |

- Пакетная обработка и перетаскивание файлов в окно.
- Несколько изображений можно объединить в один PDF.
- Настройки качества JPG/WEBP и разрешения страниц PDF.
- Оригиналы сохраняются; совпадающие имена получают числовой суффикс.
- LibreOffice включён в готовую сборку: Word и Python устанавливать не нужно.

## Скачать и запустить

**[Скачать EasyConverter 1.1.0 для Windows](https://github.com/despairrrrrrr/EasyConverter/releases/download/v1.1.0/EasyConverterSetup-1.1.0.exe)** — один установочный EXE, около 302 МиБ.
Запустите установщик, выберите папку и установите программу. Он добавляет ярлык
в меню «Пуск» и, по выбору, на рабочий стол. Python, Word, отдельная установка
LibreOffice и интернет не требуются. Программа устанавливается для текущего
пользователя и удаляется через список установленных приложений Windows.

Ранее опубликованный portable-выпуск также доступен:

1. В разделе **Releases** скачайте `EasyConverter-1.0.0-windows-x64.zip`.
2. Полностью распакуйте архив в обычную папку.
3. Запустите `EasyConverter.exe`.

Переносите папку целиком: рядом с EXE должны оставаться `_internal` и `office`.
Сборка предназначена для Windows x64, проверена на Windows 10.
Цифровой подписи нет. Значительный размер сборки связан со встроенным LibreOffice.

`Ctrl+O` — добавить файлы, `Ctrl+Enter` — начать конвертацию.

## Ограничения

- PDF → Word, OCR и таблицы Excel пока не поддерживаются.
- Для GIF/TIFF используется первый кадр/страница.
- TXT содержит только текст, без оформления. Сложная вёрстка документов и шрифты
  могут измениться при конвертации через LibreOffice.
- Документы с паролем не поддерживаются.

## Запуск из исходников

Нужны Windows, Python 3.12 и [LibreOffice](https://www.libreoffice.org/download/download-libreoffice/)
для обработки документов. Конвертация изображений и PDF работает без LibreOffice.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Также можно использовать `run.bat` после установки зависимостей.

## Проверка и сборка

```powershell
.\.venv\Scripts\python.exe -m unittest -v test_converter test_ui
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe build.py
```

На компьютере сборки должен быть установлен LibreOffice. Сборщик копирует его
в `dist/EasyConverter/office`, сохраняет лицензии и добавляет архив исходников.
Для создания ZIP и контрольной суммы:

```powershell
.\.venv\Scripts\python.exe package_release.py
```

Результаты: `dist/EasyConverter/` и `releases/`. Сборки и зависимости исключены
из Git; в репозитории хранятся исходники. CI проверяет конвертацию на Windows.

### Один установочный EXE

Установите [Inno Setup](https://jrsoftware.org/inno-setup) версии 6.3 или новее
и выполните после `build.py`:

```powershell
.\.venv\Scripts\python.exe build_installer.py
```

Если компилятор установлен в нестандартную папку, укажите полный путь к `ISCC.exe`
в переменной `INNO_SETUP_COMPILER`. Компилятор также ищется в `.build-tools/InnoSetup/`.
Результат — `releases/EasyConverterSetup-1.1.0.exe` и файл с SHA-256.
Установщик включает все компоненты и не скачивает дополнительные файлы.

## Онлайн-сайт

[EasyConverter Online](https://easyconverter-online.grainyslug7.chatgpt.site/)
позволяет конвертировать изображения, менять размер и поворот, собирать и объединять
PDF прямо в браузере. Онлайн-версия развивается отдельно от настольного приложения.

## Файлы настольного приложения

| Файл | Назначение |
| --- | --- |
| `app.py` | Интерфейс CustomTkinter |
| `converter.py` | Конвертация изображений и PDF |
| `office_converter.py` | Обработка документов через LibreOffice |
| `app_info.py` | Название и версия |
| `build.py` | Сборка Windows-приложения и комплектование зависимостей |
| `build_installer.py` | Сборка единого офлайн-установщика EXE |
| `installer/EasyConverter.iss` | Настройки установки, ярлыков и удаления |
| `ui_layout.py`, `theme.py` | Компоновка и светлое оформление |
| `package_release.py` | ZIP для выпуска и SHA-256 |
| `test_converter.py` | Проверки конвертации и сохранности оригиналов |
| `test_ui.py` | Проверки выбора файлов и компоновки окна |

## Лицензия

EasyConverter распространяется под **GNU AGPL-3.0-only** — см. [LICENSE](LICENSE).
PyMuPDF используется на условиях AGPL. LibreOffice и остальные сторонние компоненты
сохраняют собственные лицензии; ссылки на исходники и сведения приведены в
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Это независимый проект,
не связанный с разработчиками LibreOffice, PyMuPDF и Microsoft Word.
