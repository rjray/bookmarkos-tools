# Agent Guidelines for BookmarkOS Tools

## Build, Lint, and Test

- Install test dependencies: `make install-test-deps`
- Run all tests: `make test-all` or `pytest tests/`
- Run a single test: `pytest tests/unit/bookmarkos/data/test_bookmarks.py::TestBookmark::test_bookmark_fill_basic_markup`
- Run unit/integration tests: `make test-unit` / `make test-integration`
- Run tests in parallel: `make test-parallel`
- Generate coverage: `make coverage`
- Linting: `make lint`

## Code Style

- Use PEP8 formatting; 4 spaces per indent.
- Imports: standard lib, then 3rd-party, then local (each group separated by a blank line).
- Type hints required for all public functions/classes.
- Use `@dataclass` for data models; prefer immutable fields where possible.
- Naming: snake_case for functions/vars, PascalCase for classes, UPPER_CASE for constants.
- Error handling: raise `ValueError` with descriptive messages for malformed input; prefer explicit exceptions.
- All file I/O must auto-detect gzip by extension.
- UTF-8 encoding enforced throughout.
- Tests: use pytest, pytest-mock, and pytest-xdist; mark slow/integration/parser/metrics/io/cli tests with pytest markers.
- Follow Copilot instructions in `.github/copilot-instructions.md` for architecture and extension patterns.
- Configuration: TOML in `config/`, but tools use CLI args by default.
- All timestamps are UNIX epoch seconds; use UTC for conversions.
