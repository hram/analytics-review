# Confluence Review Toolkit

Набор скриптов для:

- выгрузки страницы Confluence и ее дочерних страниц;
- конвертации страниц в Markdown;
- генерации единого review-документа через `codex`;
- сборки HTML-бандла для чтения результата и переходов между страницами.

## Требования

- Linux/macOS shell с `bash`
- Python 3
- установленный `codex` CLI
- доступ к Confluence
- учетные данные Confluence в виде заголовка `Authorization`

## Установка

Создать виртуальное окружение и установить зависимости:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## Настройка

1. Скопировать шаблон переменных окружения:

```bash
cp .env.example .env
```

2. Заполнить `.env`:

```env
CONF_BASE_URL='http://confluence.example.local:8090'
CONF_AUTH='Basic REPLACE_ME'
```

`CONF_AUTH` должен содержать готовое значение заголовка `Authorization`, например `Basic ...`.

При необходимости можно использовать другой env-файл через переменную `CONF_ENV_FILE`.

Для HTTPS Confluence с внутренним сертификатом есть два варианта:

- рекомендованный: указать корневой сертификат через `CONF_CA_FILE`;
- временный обходной путь: отключить проверку через `CONF_INSECURE_SKIP_VERIFY=true`.

Пример:

```env
CONF_BASE_URL='https://confluence.example.local'
CONF_AUTH='Basic REPLACE_ME'
CONF_CA_FILE='/etc/ssl/certs/company-root-ca.pem'
```

Небезопасный вариант только для локальной диагностики:

```env
CONF_INSECURE_SKIP_VERIFY='true'
```

## Быстрый запуск

Полный сценарий: выгрузить страницы, сгенерировать review и собрать HTML.

```bash
./run_confluence_review.sh <page_id>
```

Пример:

```bash
./run_confluence_review.sh 247562637
```

По умолчанию результат будет записан в `out/<page_id>/`.

## Основные команды

### 1. Выгрузить страницы Confluence в Markdown

```bash
.venv/bin/python fetch_confluence_page_md.py <page_id> [output_dir]
```

Пример:

```bash
.venv/bin/python fetch_confluence_page_md.py 244908187 ./pages
```

Что делает:

- получает корневую страницу;
- рекурсивно получает дочерние страницы;
- сохраняет каждую страницу в отдельный `*.md`;
- пишет `metadata.json` с названиями, slug и ссылками.

### 2. Сгенерировать review по уже выгруженным страницам

```bash
./review_confluence_pages.sh <pages_dir> <output_file> [prompt_file]
```

Пример:

```bash
./review_confluence_pages.sh ./pages ./review.md ./prompt_pragmatic.md
```

Что делает:

- читает все `*.md` из каталога;
- объединяет их в один входной документ;
- добавляет системный prompt;
- запускает `codex exec`;
- сохраняет итоговый review в Markdown.

### 3. Собрать HTML из Markdown

```bash
.venv/bin/python render_markdown_html.py <input_md> <output_html>
```

Пример:

```bash
.venv/bin/python render_markdown_html.py ./review.md ./review.html
```

### 4. Собрать финальный HTML-бандл review + страницы

```bash
.venv/bin/python decorate_review_bundle.py <pages_dir> <review_md> <review_html>
```

Пример:

```bash
.venv/bin/python decorate_review_bundle.py ./pages ./review.md ./review.html
```

Что делает:

- рендерит HTML для каждой страницы;
- добавляет ссылки на Confluence и обратную ссылку на review;
- заменяет упоминания `page id` в review на ссылки на HTML-страницы;
- сохраняет итоговый HTML review.

## Prompt-файлы

- `prompt.md` — более жесткое и подробное ревью.
- `prompt_pragmatic.md` — более практичное ревью с делением на `BLOCKER`, `IMPORTANT`, `OPTIONAL`.

Можно передать свой prompt третьим аргументом в `run_confluence_review.sh` или `review_confluence_pages.sh`.

Пример:

```bash
./run_confluence_review.sh 244908187 ./out ./prompt_pragmatic.md
```

## Структура результата

После запуска `run_confluence_review.sh` создается каталог:

```text
out/<page_id>/
  pages/
    metadata.json
    <page_id>.md
    <page_id>-<slug>.html
  review_<page_id>.md
  review_<page_id>.html
```

Где:

- `pages/*.md` — выгруженные страницы в Markdown;
- `pages/*.html` — HTML-версии отдельных страниц;
- `review_<page_id>.md` — итоговое ревью;
- `review_<page_id>.html` — HTML-версия ревью с ссылками на страницы.

## Типовые сценарии

Сгенерировать review в отдельную директорию:

```bash
./run_confluence_review.sh 244908187 ./out_pragmatic ./prompt_pragmatic.md
```

Только обновить выгрузку страниц:

```bash
.venv/bin/python fetch_confluence_page_md.py 244908187 ./tmp/pages
```

Переиспользовать уже выгруженные страницы и пересобрать review с другим prompt:

```bash
./review_confluence_pages.sh ./tmp/pages ./tmp/review.md ./prompt_pragmatic.md
.venv/bin/python decorate_review_bundle.py ./tmp/pages ./tmp/review.md ./tmp/review.html
```

## Возможные проблемы

`CONF_AUTH is required in .env`

- Проверьте, что `.env` существует.
- Проверьте, что в нем задан `CONF_AUTH`.

`Prompt file not found`

- Проверьте путь к prompt-файлу.

`Pages directory not found`

- Сначала выполните выгрузку страниц или укажите корректный каталог.

`codex: command not found`

- Установите и настройте `codex` CLI.

`HTTP error` или `Request failed`

- Проверьте `CONF_BASE_URL`.
- Проверьте сетевой доступ до Confluence.
- Проверьте корректность `CONF_AUTH`.

`SSL: CERTIFICATE_VERIFY_FAILED`

- Если Confluence использует внутренний CA, укажите путь к сертификату в `CONF_CA_FILE`.
- Если нужно быстро проверить гипотезу локально, задайте `CONF_INSECURE_SKIP_VERIFY='true'`.
- Для постоянного использования лучше не отключать валидацию сертификата, а настроить корректный CA.

## Основные файлы проекта

- `run_confluence_review.sh` — полный end-to-end запуск.
- `fetch_confluence_page_md.py` — выгрузка страниц из Confluence в Markdown.
- `review_confluence_pages.sh` — генерация review через `codex`.
- `decorate_review_bundle.py` — сборка итогового HTML-бандла.
- `render_markdown_html.py` — рендер Markdown в HTML.
