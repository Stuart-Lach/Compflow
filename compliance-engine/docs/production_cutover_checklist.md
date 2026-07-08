# Production Cutover Checklist

Use this checklist when moving Compflow from staging to production.

## Go/no-go prerequisites

- `main` contains the verified production commit.
- Render service is connected to the GitHub repository.
- Supabase/PostgreSQL database is provisioned.
- Independent database backup and restore rehearsal has been completed.
- `ALERT_WEBHOOK_URL` points to the approved incident channel.
- At least two named administrator users are configured in `ADMIN_USERS`.
- One administrator has role `admin`; at least one backup operator has role
  `operator`.

## Required Render secrets

- `DATABASE_URL`
- `CORS_ORIGINS`
- `API_KEY_BINDINGS`
- `ADMIN_USERS`
- `ADMIN_SESSION_SECRET`
- `ALERT_WEBHOOK_URL`

## Required Render values

- `APP_ENV=production`
- `DEBUG=false`
- `AUTO_CREATE_SCHEMA=false`
- `FILE_STORAGE_BACKEND=database`
- `ADMIN_COOKIE_SECURE=true`
- `ALERT_SEVERITIES=critical,warning`

## Cutover sequence

1. Confirm the latest CI/test run is green.
2. Create a fresh logical database backup.
3. Deploy Render from `main`.
4. Confirm `alembic upgrade head` completed.
5. Confirm `/ready` returns HTTP 200.
6. Log into `/admin` as an `admin`.
7. Confirm database, ruleset, alert delivery, and recent audit cards load.
8. Send a test alert and confirm delivery in the incident channel.
9. Run one anonymized payroll smoke upload with a company-bound API key.
10. Confirm the run appears in `/admin` recent runs.
11. Confirm the admin audit table records login and maintenance actions.
12. Enable production traffic.

## No-go conditions

- `/ready` is not ready.
- Admin login fails.
- Alert test does not arrive.
- Database migration fails.
- Company API keys are not tenant-isolated.
- Backup restore rehearsal has not been completed.

## Immediate rollback

1. Stop new payroll uploads.
2. Roll Render back to the prior known-good commit.
3. Restore to a rehearsed backup only if migration/data changes require it.
4. Verify `/ready`, admin login, and one authorized API read.
5. Reopen traffic after the rollback is verified.
