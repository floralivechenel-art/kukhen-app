# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Kukhen — a personal recipe manager and shopping-list generator built with [Flet](https://flet.dev) (Python, compiles to a mobile/desktop app via Flutter). UI text and data are in Russian.

## Commands

```
pip install -r requirements.txt   # install dependencies (flet, requests)
python main.py                    # run the app (desktop window via Flet)
flet run main.py                  # alternative: run via the Flet CLI
python test_supabase.py           # manual smoke test of the Supabase connection (not a pytest suite)
```

There is no linter, formatter, or automated test suite configured in this repo (no pyproject.toml/setup.cfg, no pytest). `test_supabase.py` is a standalone script that writes/reads/deletes a row against the live `recipes` table — run it manually to verify cloud connectivity, not as part of CI.

## Architecture

**`main.py` is the entire application.** It defines a single Flet `main(page)` entry point that manually swaps `page.controls` between six in-app "views" (no `ft.View`/routing is used): auth, main category grid, category detail, recipe add/edit dialog, recipe viewer dialog, cart, and the shopping-list/revision screen. All view-building functions are nested closures inside `main()` and call each other directly (e.g. `show_category_view` → `open_recipe_viewer` → `show_category_view`) to navigate.

`auth_view.py` is a standalone, unused alternative login view (built for `ft.View`-based routing) — `main.py` has its own inline `show_auth_view()` and does not import this file.

**Data layer is local-first with a best-effort cloud mirror:**
- `storage/repository.py` (`RecipeRepository`) is the sole data-access point used by the UI. It reads/writes `database.json` synchronously for every operation (recipes, categories, cart), and additionally pushes/pulls to Supabase:
  - `add_recipe` / `delete_recipe` write to `database.json` first, then best-effort `upsert`/`delete` against the Supabase `recipes` table (id + full JSON blob in a `data` column). Cloud failures are caught and logged, never raised.
  - `sync_from_cloud()` does the reverse: pulls all rows from Supabase and overwrites the local `recipes` list. This runs on login and on session restore at app startup (bottom of `main.py`), so cloud state wins over local state at session start.
- `core/supabase_client.py` hardcodes the Supabase URL/anon key and exports a module-level `supabase` client used directly by both `main.py` (auth calls: `sign_in_with_password`, `sign_up`, `sign_out`, `set_session`) and `storage/repository.py` (data calls).
- Session persistence uses `page.client_storage` (Flet's per-device storage) to store the Supabase access token; there is no refresh-token handling, so `set_session` restores with an empty refresh token.
- `database.json` is the local on-disk store: `{"categories": [...], "recipes": [...], "cart": {recipe_id: portion_count}}`. Recipes and ingredients are dicts matching `core/models.py`'s `to_dict`/`from_dict` shape, not database rows.

**`core/models.py`** defines plain dataclasses (`Recipe`, `Ingredient`, `Cart`) with `to_dict`/`from_dict` — this is the schema shared between local JSON and the Supabase `data` blob.

**`core/aggregator.py`** (`ShoppingListAggregator`) sums identical ingredients (matched by lowercased name+unit+category) across multiple recipes and groups them by store department; `RecipeRepository.calculate_shopping_list()` reimplements equivalent aggregation logic directly (scaled by cart portion counts) rather than calling this class.

Ingredient store "departments" (`DEPARTMENTS` in `main.py`) and measurement `UNITS` are hardcoded constants at the top of `main.py`, driving both the recipe-edit dropdowns and shopping-list grouping.

## Notes

- `credentials.json` (Google OAuth client) and `core/supabase_client.py` (Supabase anon key) contain live credentials committed in the repo — treat as sensitive, don't propagate them elsewhere.
- This directory is not currently a git repository.
