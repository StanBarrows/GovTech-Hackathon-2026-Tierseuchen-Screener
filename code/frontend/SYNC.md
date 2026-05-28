# Mirrored repository

This Laravel application lives in the monorepo at `code/frontend/`:

**Source (fork):** [StanBarrows/GovTech-Hackathon-2026-Tierseuchen-Screener](https://github.com/StanBarrows/GovTech-Hackathon-2026-Tierseuchen-Screener) (fork of [BLV-OSAV-USAV/GovTech-Hackathon-2026-Tierseuchen-Screener](https://github.com/BLV-OSAV-USAV/GovTech-Hackathon-2026-Tierseuchen-Screener))

**Public mirror:** [StanBarrows/GovTech-Hackathon-2026-Tierseuchen-Screener-Laravel](https://github.com/StanBarrows/GovTech-Hackathon-2026-Tierseuchen-Screener-Laravel)

Changes pushed to `main` under `code/frontend/` are copied automatically by the workflow [`.github/workflows/stanbarrows-push-laravel.yml`](../../.github/workflows/stanbarrows-push-laravel.yml) in the monorepo root.

## Contributing

Edit the app in the monorepo (`code/frontend/`). Do not treat the public Laravel repo as the source of truth; changes there will be overwritten on the next sync.

## Maintainer setup

The **fork** needs an Actions secret (the workflow is skipped on upstream):

| Secret | Description |
|--------|-------------|
| `MY_GITHUB_TOKEN` | PAT for **StanBarrows** with **Contents: Read and write** on the public Laravel repo only |

Trigger a manual sync from the fork: **Actions → stanbarrows-push-laravel → Run workflow**.
