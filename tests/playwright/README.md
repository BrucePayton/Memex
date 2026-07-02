# Playwright E2E

This directory contains an isolated Playwright test project for the Memex dashboard.

## Setup

```bash
cd tests/playwright
npm install
npm run install:browsers
```

## Run

```bash
cd tests/playwright
npm test
```

Useful variants:

```bash
npm run test:headed
npm run test:ui
```

## Notes

- The Playwright config starts the dashboard server automatically with:
  - `python -m dashboard.server`
- The test server port defaults to `8091` to avoid conflicting with a manually started dashboard.
- Override runtime settings when needed:

```bash
MEMEX_PLAYWRIGHT_PORT=8092 npm test
MEMEX_BASE_URL=http://127.0.0.1:8092 npm test
```
