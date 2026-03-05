# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

KannaDB is a Django app for the Fire Emblem Heroes (FEH) hero/skill database. It scrapes data from the FEH Fandom wiki (feheroes.gamepedia.com → feheroes.fandom.com) via MediaWiki Cargo API, parses it, and stores it in PostgreSQL. Hosted at https://kannadb.up.railway.app/

## Development Commands

Dependencies are managed via `uv`. Use `uv run` to execute commands in the project virtualenv.

### Running Tests

Tests require a running PostgreSQL instance:

```bash
docker compose up -d db
DB_IP=$(docker inspect linus_kannadb-db-1 --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
DATABASE_URL="postgres://kannadb_user:kannadb_password@$DB_IP/kannadb_local" uv run pytest linus/ -q
```

Run a single test file:
```bash
DATABASE_URL="..." uv run pytest linus/feh/tests/test_gamepedia.py -q
```

Run a single test by name:
```bash
DATABASE_URL="..." uv run pytest linus/feh/tests/test_gamepedia.py::TestClassName::test_method_name -q
```

### Local Full Stack

```bash
docker compose up
```

Starts nginx, web (Django + Gunicorn), PostgreSQL, and Redis. The web container runs `run.sh` on startup which migrates, scrapes data, imports to DB, and starts Gunicorn.

### Django Management Commands

```bash
uv run python manage.py curl_heroes          # Scrape data from Gamepedia (3 phases)
uv run python manage.py import_heroes        # Parse pkl files and import into PostgreSQL
uv run python manage.py curl_heroes --delay 2.0  # Increase delay if rate-limited
```

Set `SKIP_DB_UPDATE=True` in env to skip curl/import on container startup.

### Code Formatting

Pre-commit hooks handle formatting. Install with:
```bash
pip install pre-commit && pre-commit install
```

## Architecture

### Data Pipeline

Data flows in one direction: Gamepedia API → pkl files → PostgreSQL.

1. **`curl_heroes` management command** calls `CurlAll(phase, pkl_file)` for each of 3 phases:
   - Phase 0: skills and upgrades
   - Phase 1: unit-skills (which hero knows which skill)
   - Phase 2: units and legendary data

   Output is saved to `linus/media/poro/poro.pkl.0`, `.1`, `.2`

2. **`import_heroes` management command** calls `GetKannaURLs()` which calls `LoadPoro()` to read the pkl files, then maps the parsed poro objects to Django models (`Hero`, `Skill`) and bulk-saves them (deleting all existing records first).

### Key Modules

- `linus/feh/poro/porocurler_v2.py` — Gamepedia MediaWiki Cargo API fetcher. `readURL()` includes retry logic, User-Agent header, and rate-limit handling. `CurlAll(phase, file)` executes one phase of the scrape.
- `linus/feh/poro/poroimagecurler.py` — Fetches hero icon URLs from the wiki; also has its own `readURL`.
- `linus/feh/poro/poroparser_v2.py` — Parses raw API dicts from pkl into `poroclasses.py` objects (`Hero`, `Skill`, `Seal`, etc.).
- `linus/feh/poro/poroclasses.py` — Plain Python dataclasses representing scraped FEH entities (separate from Django models).
- `linus/feh/models.py` — Django ORM models: `Hero` and `Skill`. Both use `ArrayField` (PostgreSQL-specific). `Hero.save()` auto-computes `book`, `generation`, and `f2p_level`. Enum-style constants (`AVAILABILITY`, `WEAPON_TYPE`, `MOVEMENT_TYPE`, etc.) are plain Python classes with string codes like `"A_GHB"`, `"W_01"`.
- `linus/feh/views.py` — All views return JSON for the frontend to render. `HeroesListAjax` and `SkillsListAjax` are the main data endpoints. The `CurlHeroesDoPhaseBase` view provides a web-triggered data refresh pipeline.
- `linus/feh/filters.py` + `linus/feh/sliders.py` — Build filter/slider context data for the hero and skill list views.

### Frontend

Pages are single-page-style: the Django template loads all hero/skill data via AJAX (`heroes_ajax.json`, `skills_ajax.json`) and filters/sorts client-side via JavaScript.

### Caching

Views use `cache_page(60 * 10)` (10 minutes). Django cache is backed by Redis. Cache is cleared after a data refresh (`cache.clear()` in `CurlHeroesDoPhaseBase`).

### Test Fixtures

Gamepedia API tests (`linus/feh/tests/test_gamepedia.py`) mock `urllib.request.urlopen`. Key gotcha: XML fixtures must be compact (no whitespace between tags) — BeautifulSoup `.contents` includes `NavigableString` whitespace nodes from indented XML, causing `AttributeError`. Also: `&` in XML attribute values must be `&amp;`, and `urllib.request.Request` normalizes headers to title-case (`User-Agent` → `User-agent`).
