# EasyConverter

**Офлайн-конвертер изображений и документов для Windows.**

Добавьте файлы, выберите нужный формат и папку сохранения. EasyConverter
обрабатывает файлы на компьютере, без загрузки в облако и регистрации.
Интерфейс — на русском языке.

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
.\.venv\Scripts\python.exe -m unittest -v test_converter
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

## Устройство проекта

| Файл | Назначение |
| --- | --- |
| `app.py` | Интерфейс CustomTkinter |
| `converter.py` | Конвертация изображений и PDF |
| `office_converter.py` | Обработка документов через LibreOffice |
| `app_info.py` | Название и версия |
| `build.py` | Сборка Windows-приложения и комплектование зависимостей |
| `package_release.py` | ZIP для выпуска и SHA-256 |
| `test_converter.py` | Проверки конвертации и сохранности оригиналов |

## Лицензия

EasyConverter распространяется под **GNU AGPL-3.0-only** — см. [LICENSE](LICENSE).
PyMuPDF используется на условиях AGPL. LibreOffice и остальные сторонние компоненты
сохраняют собственные лицензии; ссылки на исходники и сведения приведены в
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Это независимый проект,
не связанный с разработчиками LibreOffice, PyMuPDF и Microsoft Word.
