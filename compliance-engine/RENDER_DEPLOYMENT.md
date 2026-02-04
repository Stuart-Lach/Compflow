# Deployment Guide - Render

## Overview

This guide covers deploying the compliance-engine API to Render.com with optional PostgreSQL database.

## Prerequisites

- GitHub/GitLab repository with the code
- Render account (free tier available)
- Optional: Vercel frontend domain for CORS configuration

## Deployment Options

### Option A: Deploy with render.yaml (Recommended)

1. **Push code to Git repository**
   ```bash
   git add .
   git commit -m "Add Render deployment configuration"
   git push origin main
   ```

2. **Connect to Render**
   - Go to https://render.com/dashboard
   - Click "New +" → "Blueprint"
   - Connect your repository
   - Render will detect `render.yaml` and configure automatically

3. **Update environment variables**
   - In Render dashboard, go to your service
   - Navigate to "Environment" tab
   - Update `CORS_ORIGINS` with your Vercel domain:
     ```
     https://your-app.vercel.app,http://localhost:3000
     ```

4. **Deploy**
   - Render will automatically deploy
   - Access your API at: `https://your-service.onrender.com`

### Option B: Manual Deploy (Web Service)

1. **Create Web Service**
   - Go to Render dashboard
   - Click "New +" → "Web Service"
   - Connect your repository
   - Configure:
     - **Name**: compliance-engine-api
     - **Environment**: Python 3
     - **Build Command**: `pip install -e .`
     - **Start Command**: `uvicorn src.app.main:app --host 0.0.0.0 --port $PORT`

2. **Add Environment Variables**
   ```
   APP_ENV=production
   DEBUG=false
   CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000
   DATABASE_URL=sqlite+aiosqlite:///./compliance_engine.db
   LOG_LEVEL=INFO
   ```

3. **Deploy**
   - Click "Create Web Service"
   - Render will build and deploy automatically

## Database Setup

### SQLite (Demo/Development)

SQLite works out of the box but **data is not persistent** on Render's free tier (ephemeral filesystem).

```bash
DATABASE_URL=sqlite+aiosqlite:///./compliance_engine.db
```

### PostgreSQL on Render (Recommended)

1. **Create PostgreSQL Database**
   - In Render dashboard: "New +" → "PostgreSQL"
   - Name: compliance-engine-db
   - Plan: Free or Starter
   - Create database

2. **Connect to Web Service**
   - In your web service, add environment variable:
   - Key: `DATABASE_URL`
   - Value: Select your database from dropdown
   - Render will automatically use the connection string

3. **Update Requirements** (if needed)
   - Uncomment in `requirements.txt`:
     ```
     asyncpg>=0.29.0
     ```
   - Redeploy

### Supabase PostgreSQL (Alternative)

1. **Get Supabase Connection String**
   - Create project at https://supabase.com
   - Go to Settings → Database
   - Copy "Connection pooling" string
   - Convert from `postgres://` to `postgresql+asyncpg://`

2. **Add to Render**
   - Environment variable: `DATABASE_URL`
   - Value: `postgresql+asyncpg://user:pass@host:port/db`
   - Mark as "Secret"

## CORS Configuration

Update `CORS_ORIGINS` environment variable with your frontend domains:

```bash
# Single domain
CORS_ORIGINS=https://your-app.vercel.app

# Multiple domains
CORS_ORIGINS=https://your-app.vercel.app,https://staging.vercel.app,http://localhost:3000
```

## Health Checks

Render automatically uses the health check endpoint defined in `render.yaml`:

- **Endpoint**: `/health`
- **Expected**: 200 status code
- **Response**: `{"status": "healthy", ...}`

## Monitoring

### Logs

View logs in Render dashboard:
- Service → "Logs" tab
- Real-time streaming
- Filter by severity

### Manual Health Check

```bash
curl https://your-service.onrender.com/health
curl https://your-service.onrender.com/api/v1/health
```

## Testing Deployment

### Local Testing with Production Settings

1. **Copy environment file**
   ```bash
   cp .env.example .env
   ```

2. **Update .env for production**
   ```env
   APP_ENV=production
   DEBUG=false
   PORT=8000
   DATABASE_URL=sqlite+aiosqlite:///./compliance_engine.db
   CORS_ORIGINS=http://localhost:3000
   ```

3. **Install dependencies**
   ```bash
   pip install -e .
   ```

4. **Start server**
   ```bash
   uvicorn src.app.main:app --host 0.0.0.0 --port 8000
   ```

5. **Run smoke tests**
   ```bash
   # Linux/Mac
   chmod +x scripts/smoke_test.sh
   ./scripts/smoke_test.sh

   # Windows PowerShell
   .\scripts\smoke_test.ps1
   ```

### Test Deployed API

```bash
# Health check
curl https://your-service.onrender.com/health

# API documentation
open https://your-service.onrender.com/docs

# Upload CSV test (with actual file)
curl -X POST https://your-service.onrender.com/api/v1/runs \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/samples/payroll_input_sample_v1.csv"
```

## Connecting Frontend (Vercel)

Update your Vercel frontend environment variables:

```env
# .env.production
NEXT_PUBLIC_API_URL=https://your-service.onrender.com
```

Frontend code:
```javascript
const API_URL = process.env.NEXT_PUBLIC_API_URL;

// Upload CSV
const formData = new FormData();
formData.append('file', file);

const response = await fetch(`${API_URL}/api/v1/runs`, {
  method: 'POST',
  body: formData,
});
```

## Troubleshooting

### Build Fails

**Error**: `ModuleNotFoundError`
- **Fix**: Check `requirements.txt` or `pyproject.toml` has all dependencies
- **Fix**: Ensure build command is `pip install -e .`

**Error**: `ImportError: app`
- **Fix**: Verify start command uses correct module path: `src.app.main:app`

### Database Connection Fails

**PostgreSQL**:
- Verify `DATABASE_URL` starts with `postgresql+asyncpg://`
- Check `asyncpg` is in requirements.txt
- Ensure database is in same region as web service

**SQLite**:
- Remember: ephemeral on Render free tier (data lost on restart)
- Upgrade to persistent disk or use Postgres

### CORS Errors

**Frontend can't reach API**:
- Verify `CORS_ORIGINS` includes your Vercel domain
- Check domain has `https://` prefix
- Restart web service after changing environment variables

### Application Won't Start

Check Render logs for:
- Port binding: Render sets `$PORT` automatically
- Database initialization: Check if tables are created
- Environment variables: Verify all required vars are set

## Performance Tips

1. **Use PostgreSQL** for production (persistent + better performance)
2. **Upgrade Render plan** for faster CPU and more memory
3. **Enable disk persistence** if using SQLite
4. **Set up autoscaling** for high traffic
5. **Add caching** for ruleset lookups (future enhancement)

## Security Checklist

- [ ] Set `DEBUG=false` in production
- [ ] Configure specific CORS origins (not wildcard)
- [ ] Use environment variables for secrets
- [ ] Mark `DATABASE_URL` as secret in Render
- [ ] Enable HTTPS (automatic on Render)
- [ ] Review Render security best practices

## Next Steps

1. ✅ Deploy to Render
2. ✅ Test health endpoint
3. ✅ Connect frontend
4. ✅ Test end-to-end flow
5. 🔜 Set up monitoring/alerts
6. 🔜 Configure custom domain
7. 🔜 Add authentication (V2)

## Support

- **Render Docs**: https://render.com/docs
- **FastAPI Deployment**: https://fastapi.tiangolo.com/deployment/
- **SQLAlchemy Async**: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
