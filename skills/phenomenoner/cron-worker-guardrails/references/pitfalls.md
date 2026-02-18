# Cron exec pitfalls → safer replacements

## 1) Command substitution breaks quoting
**Bad (fragile):**
- `TODAY=$(TZ=Asia/Taipei date +%Y-%m-%d)`

**Better:**
- Don’t capture in shell; let a script compute the date.
- Or compute in Python and print JSON (always exit 0).

## 1.5) JSON arguments + nested quotes
**Bad (fragile):**
- `bash -lc '... --meta \'{"lane":"A-fast"}\''` (quotes inside quotes inside quotes)

**Better:**
- Avoid JSON args in shell when you can (omit `--meta`, or use a wrapper script).
- If you must: prefer **double quotes** around the JSON and avoid wrapping the whole command in another quoted `bash -lc '...'.`

## 1.6) `python3 -c '...` with list literals / single quotes
A common self-own is:
- `python3 -c '... subprocess.check_output(['openclaw','cron','list',...]) ...'`

This breaks because the inner `['openclaw', ...]` terminates the outer single-quoted `-c` string.

**Better:**
- scripts-first (put the logic in `tools/*.py`)
- or wrap the `-c` string in **double quotes** if you need single quotes inside.

## 2) Heredocs in generated shell
**Bad (fragile):**
- `python3 - <<"PY" ... PY` (easy to truncate / misquote)

**Better:**
- Put code in `tools/*.py` and run it.

## 3) pipefail + head
**Bad:**
- `set -o pipefail; big_command | head`

**Better:**
- Avoid `pipefail` if you’re piping into `head`.
- Or write a script that reads only what it needs.

## 4) awk/sed embedded in double quotes
**Bad:**
- `bash -lc "awk '{print $1}' file"`

**Better:**
- Use Python for parsing.

## 5) Exec packing
**Bad:**
- One huge `bash -lc '...many steps...'`.

**Better:**
- Multiple short exec calls, or one deterministic script.
- Best: a single scripts-first wrapper that runs argv-list subprocess calls (no shell), and `chdir` to repo root before `uv run --frozen ...`.

### 5.5) OpenClaw `exec` tool invocation format
**Bad:**
- `python3, ~/.openclaw/workspace/tools/foo.py` (comma + `~`)

**Better:**
- `python3 /root/.openclaw/workspace/tools/foo.py` (one string command)

### 5.6) `git commit -m` needs quotes
**Bad:**
- `git commit -m docs: harden ...` (can be parsed as pathspecs)

**Better:**
- `git commit -m "docs: harden ..."`

### 5.7) `uv run -m <module>` is not a thing
A real-world footgun is writing:
- `uv run --python 3.13 --frozen -m openclaw_mem ...`

This fails because `-m` is a **python** flag, not a `uv run` flag.

**Better:**
- `uv run --python 3.13 --frozen -- python -m openclaw_mem ...`

## 6) Test runner drift (pytest vs unittest)
Cron/dev cycles often fail because someone runs a test runner that isn’t installed.

**Bad:**
- `python -m pytest ...` when pytest isn’t installed
- `python -m unittest` with no target/discover (often runs 0 tests / exits non-zero)

**Better:**
- Prefer the project’s native runner.
  - If the repo uses **unittest**:
    - `uv run --python 3.13 --frozen -- python -m unittest discover -s tests -q`
- If you truly need pytest:
  - `cd /path/to/repo`
  - ensure pytest exists
  - `uv run -- python -m pytest -q`

## 7) Output discipline
- Scheduled jobs should be silent by default: `NO_REPLY`.
- If failure: <=6 bullets, include *what failed* + *next action*.
