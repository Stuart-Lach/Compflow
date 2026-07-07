# Production Runbook

## Deployment

1. Merge verified changes to `main`.
2. Configure Render from the root `render.yaml`.
3. Set:
   - `DATABASE_URL`
   - `CORS_ORIGINS`
   - `API_KEY_BINDINGS`
   - `ADMIN_USERNAME`
   - `ADMIN_PASSWORD_HASH`
   - `ADMIN_SESSION_SECRET`
   - `ADMIN_COOKIE_SECURE=true`
4. Render runs `alembic upgrade head` as the pre-deploy command.
5. `/ready` must return HTTP 200 before traffic is accepted.
6. `/admin` must require login and must only be shared with administrators.

`API_KEY_BINDINGS` is a JSON object mapping each company to one or more keys:

```json
{"COMP001":["active-key","rotation-key"]}
```

## Key rotation

1. Add a second key for the company.
2. Deploy and confirm the new key works.
3. Move clients to the new key.
4. Remove the old key and deploy again.

Keys must never be committed or written to logs.

## Administrator console

The desktop operations console is served from `/admin`. It provides maintenance,
monitoring, readiness checks, alerts, and controlled admin actions for the
backend used by app clients.

Administrator access is separate from company API keys:

- company API keys are for payroll integrations
- administrator login is for human operators only
- administrator sessions are signed and stored in secure HTTP-only cookies

Generate the administrator password hash from an installed checkout:

```powershell
python -m app.admin.security
```

Store only the generated hash in `ADMIN_PASSWORD_HASH`; never store the
plaintext administrator password. Use a random 32+ character value for
`ADMIN_SESSION_SECRET`, and keep `ADMIN_COOKIE_SECURE=true` in production.

If an administrator leaves the team:

1. Change the administrator password.
2. Generate and set a new `ADMIN_PASSWORD_HASH`.
3. Rotate `ADMIN_SESSION_SECRET` to invalidate old dashboard sessions.
4. Redeploy and verify `/admin` login.

## Backups

Use Supabase-managed backups as the primary recovery mechanism. Before releases
that change the database, also create an independent logical backup:

```powershell
.\scripts\backup_postgres.ps1 `
  -DatabaseUrl $env:DATABASE_URL `
  -OutputDirectory C:\secure-backups\compflow
```

Store the `.dump` and `.sha256` files outside the application host with access
restricted to authorized operators.

## Restore rehearsal

Never test restoration against production. Create an empty temporary PostgreSQL
database, then run:

```powershell
.\scripts\verify_postgres_restore.ps1 `
  -BackupPath C:\secure-backups\compflow\compflow_YYYYMMDD_HHMMSS.dump `
  -RestoreDatabaseUrl $env:RESTORE_DATABASE_URL
```

Record the date, operator, backup hash, restore duration, and result.

## Rollback

1. Stop new payroll uploads.
2. Roll Render back to the prior known-good commit.
3. If the migration was data-destructive, restore the rehearsed backup to a new
   database and point Render at that database.
4. Verify `/ready`, one authorized read, and one anonymized payroll run.
5. Re-enable traffic.

## Incident response

1. Rotate all affected company API keys.
2. Preserve audit logs and request IDs.
3. Disable the affected tenant or service if containment requires it.
4. Determine whether personal information was exposed.
5. Follow the organization's POPIA incident and Information Regulator
   notification procedure.

## Data handling

- Do not log uploaded payroll rows or API keys.
- Limit database access to named operators.
- Define and enforce retention periods for raw uploads, results, and audit logs.
- Use anonymized payroll data for staging and support investigations.
