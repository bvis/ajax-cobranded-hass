# Contributing

## Development Setup

Everything runs in Docker. No local dependencies needed.

```bash
git clone https://github.com/bvis/ajax-cobranded-hass.git
cd ajax-cobranded-hass

# Build dev container
make build-docker

# Compile protobuf files
make proto

# Run all checks
make check
```

## Commands

| Command | Description |
|---|---|
| `make check` | Run all checks (lint, format, typecheck, tests, dead code) |
| `make test` | Run unit tests with coverage |
| `make test-e2e` | Run E2E tests (requires AJAX_EMAIL + AJAX_PASSWORD) |
| `make lint` | Run linter |
| `make format` | Format code |
| `make typecheck` | Run type checker |
| `make proto` | Compile protobuf files |
| `make cli` | Interactive connection test |

## Commit Conventions

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat(scope):` New feature
- `fix(scope):` Bug fix
- `docs:` Documentation
- `chore:` Maintenance
- `refactor:` Code refactoring
- `test:` Tests

## Adding a New Device Type

1. Find the device's `ObjectType` variant in the proto files
2. Add the mapping to `_DEVICE_TYPE_SENSORS` in `binary_sensor.py`
3. If it has switch/relay capabilities, add to `SWITCH_DEVICE_TYPES` in `switch.py`
4. Write tests for the new mappings
5. Update `README.md` device table

## E2E Testing

```bash
AJAX_EMAIL=your@email.com AJAX_PASSWORD=yourpass make test-e2e
```

Destructive tests (arm/disarm) are skipped by default. To run them:

```bash
AJAX_EMAIL=... AJAX_PASSWORD=... pytest tests/e2e/ -v -m "e2e"
```
