# Production Runbook

## Deployment

1. Merge verified changes to `main`.
2. Configure Render from the root `render.yaml`.
3. Set:
   - `DATABASE_URL`
   - `CORS_ORIGINS`
   - `API_KEY_BINDINGS`
4. Render runs `alembic upgrade head` as the pre-deploy command.
5. `/ready` must return HTTP 200 before traffic is accepted.

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
