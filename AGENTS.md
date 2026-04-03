# AGENTS.md

Этот файл нужен как короткая оперативная память по проекту для следующих сессий.

## Что это за проект

Локальный toolkit для ревью постановок из Confluence.

Пайплайн:

1. Скачать страницу Confluence и дочерние страницы.
2. Конвертировать HTML Confluence в Markdown.
3. Собрать единый prompt со всеми страницами.
4. Запустить `codex exec` и получить review в Markdown.
5. Сгенерировать HTML-бандл с review и HTML-версиями страниц.

Проект не является backend-сервисом. Это набор shell/python-скриптов для локальной работы.

## Главные точки входа

- `run_confluence_review.sh` — полный end-to-end запуск.
- `fetch_confluence_page_md.py` — выгрузка страницы и child pages в Markdown.
- `review_confluence_pages.sh` — генерация review через `codex`.
- `decorate_review_bundle.py` — сборка HTML-бандла и линковка review с page id.
- `render_markdown_html.py` — рендер Markdown в HTML.

## Как запускать

Полный запуск:

```bash
./run_confluence_review.sh <page_id>
```

Артефакты по умолчанию:

```text
out/<page_id>/
  pages/
  review_<page_id>.md
  review_<page_id>.html
```

Для открытия результата:

```bash
xdg-open out/<page_id>/review_<page_id>.html
```

## Важные переменные окружения

Используется `.env` в корне проекта.

Основные переменные:

- `CONF_BASE_URL`
- `CONF_AUTH`
- `CONF_CA_FILE`
- `CONF_INSECURE_SKIP_VERIFY`
- `CONF_ENV_FILE`

## Критичный контекст по SSL

Была реальная проблема с `SSL: CERTIFICATE_VERIFY_FAILED` при доступе к Confluence по HTTPS.

Что уже сделано:

- в `fetch_confluence_page_md.py` добавлена поддержка `CONF_CA_FILE`;
- в `fetch_confluence_page_md.py` добавлена поддержка `CONF_INSECURE_SKIP_VERIFY=true`;
- в `fetch_confluence_page.sh` добавлены такие же настройки для `curl`.

Важно:

- `load_env()` в `fetch_confluence_page_md.py` специально переопределяет переменные из `.env`, а не использует `setdefault`;
- это сделано потому, что раньше shell environment мог незаметно перекрывать `.env` и ломать диагностику.

Текущее локальное поведение настроено так, чтобы у пользователя работал HTTPS Confluence с self-signed/internal CA.

## Недавние изменения

В проект уже были добавлены:

- `README.md` с инструкцией по установке и использованию;
- `.gitignore`, чтобы не коммитить `.env`, `.venv`, `out/` и локальные артефакты;
- git-репозиторий и push в `main` на GitHub.

## Что не коммитить

Нельзя тащить в git:

- `.env`
- `.venv/`
- `out/`
- `out_pragmatic/`
- временные выгрузки страниц
- любые файлы с реальными auth-данными

Если встречается `.env.no_cookie` или похожий файл с секретами, его тоже не коммитить.

## Технические особенности

- Проект опирается на внешний `codex` CLI.
- `review_confluence_pages.sh` вызывает:

```bash
codex --dangerously-bypass-approvals-and-sandbox exec --skip-git-repo-check
```

- Если `codex` не установлен или меняется его CLI, пайплайн ломается.
- `decorate_review_bundle.py` делает post-processing review регулярками; это хрупкое место.
- В уже сгенерированных review бывали кривые или вложенные markdown-ссылки.

## Где смотреть при проблемах

Если не скачиваются страницы:

- проверить `.env`;
- проверить `CONF_BASE_URL`;
- проверить `CONF_AUTH`;
- проверить SSL-настройки `CONF_CA_FILE` / `CONF_INSECURE_SKIP_VERIFY`.

Если нет review:

- проверить, установлен ли `codex`;
- проверить, что `review_confluence_pages.sh` видит `pages_dir` и `prompt`;
- проверить, не упал ли `codex exec`.

Если review есть, но HTML-кросссылки кривые:

- смотреть `decorate_review_bundle.py`;
- смотреть `replace_page_ids`, `normalize_nested_links`, `normalize_known_page_links`.

## Практические правила для следующих изменений

- Сохранять проект простым: это утилита, а не платформа.
- Не убирать поддержку `.env`.
- Не возвращать поведение с `os.environ.setdefault()` в `fetch_confluence_page_md.py`.
- Если меняется формат review, проверять, не сломалась ли линковка page id в HTML.
- Перед коммитом полезно прогонять:

```bash
.venv/bin/python -m py_compile fetch_confluence_page_md.py render_markdown_html.py decorate_review_bundle.py
```

## Минимальный чек-лист перед релизом изменений

1. Локально проходит `py_compile`.
2. `./run_confluence_review.sh <page_id>` стартует без ошибок окружения.
3. Появляются `review_<page_id>.md` и `review_<page_id>.html`.
4. HTML review открывается и ссылки на страницы работают хотя бы для базового кейса.
