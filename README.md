# MyTradingSystem

Advanced modular trading, quantitative research, backtesting, paper-trading, and risk-management platform.

## Status

Phase 0 foundation is being built incrementally. Live trading is intentionally disabled until the platform, risk controls, paper trading, and reconciliation layers are validated.

## Architecture

- `backend/` — FastAPI application
- `frontend/` — Next.js trading interface
- `docs/` — architecture and operational documentation
- `strategies/` — strategy definitions and examples
- `data/` — local development data (not committed)
- `deployment/` — deployment configuration
- `.github/workflows/` — CI/CD

## Development

The development environment is designed to run with Docker Compose.

See `.env.example` for configuration. Never commit credentials, broker secrets, or API keys.

## Trading Safety

The initial platform operates in development/paper mode. Any future live execution must pass through strategy validation, risk checks, order validation, broker execution, and reconciliation.
