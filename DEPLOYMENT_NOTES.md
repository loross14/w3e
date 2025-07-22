# 🚀 Deployment Configuration Guide

## Critical Deployment Flow

This application has a **React frontend** and **FastAPI backend** that must be properly coordinated during deployment.

### The Problem We Solved

The deployed frontend was unable to connect to the backend because the static files weren't being served correctly. This happened because:

1. The frontend builds to a `dist/` directory in the project root
2. The backend runs from the `server/` directory 
3. The backend looks for frontend files at `./dist` (relative to `server/`)
4. **Without proper copying, the backend can't find the frontend files**

### Current Working Configuration

**In `.replit`:**
```toml
[deployment]
build = ["sh", "-c", "npm run build && cp -r dist server/dist"]
run = ["sh", "-c", "cd server && python3 -m pip install --break-system-packages -r requirements.txt && python3 main.py"]
```

**What this does:**
1. `npm run build` - Creates `dist/` with built React app
2. `cp -r dist server/dist` - **CRITICAL**: Copies files to `server/dist/`
3. Backend starts in `server/` directory
4. Backend finds files at `./dist` and serves them

### How to Verify Deployment Works

#### Check Build Process
1. Build command should show: `"Build completed successfully"`
2. Verify `server/dist/index.html` exists after build

#### Check Backend Logs
Look for these SUCCESS messages:
- `✅ [STATIC FILES] Found valid frontend build at: ./dist`
- `✅ [STATIC FILES] Mounted frontend from: ./dist` 
- `✅ [ROOT] Successfully serving React app from: ./dist/index.html`

#### Check for FAILURE messages:
- `❌ [STATIC FILES] CRITICAL: No valid frontend build found!`
- `❌ [ROOT] DEPLOYMENT ERROR: Frontend build not found!`

### Troubleshooting Deployment Issues

#### Frontend Shows API JSON Instead of React App
**Symptoms:** Visiting the deployed URL shows `{"message": "Crypto Fund API", ...}`

**Cause:** Frontend files not copied to correct location

**Fix:** 
1. Check build command includes: `cp -r dist server/dist`
2. Verify `npm run build` completed successfully
3. Redeploy with correct configuration

#### Backend Can't Connect to Database  
**Symptoms:** Backend logs show database connection errors

**Fix:**
1. Ensure PostgreSQL database is created in Replit
2. Check `DATABASE_URL` environment variable is set
3. Wait 30-60 seconds for database to initialize

#### Environment Variables Missing
**Symptoms:** Backend crashes with missing variable errors

**Fix:**
1. Set `ALCHEMY_API_KEY` in Replit Secrets
2. Database URL should be automatically set when PostgreSQL is added

### Development vs Deployment Differences

| Aspect | Development | Deployment |
|--------|-------------|------------|
| Frontend Location | `../dist` (relative to server/) | `./dist` (copied to server/) |
| Build Process | Manual `npm run build` | Automatic during deployment |
| File Serving | Backend finds files at `../dist` | Backend finds files at `./dist` |
| Port | Multiple ports (5000, 8000) | Single port (80) |

### Critical Files

**Never modify these without understanding the deployment flow:**
- `.replit` - Contains deployment configuration
- `server/main.py` - Static file serving logic around lines 100-150
- `package.json` - Frontend build configuration

### Emergency Deployment Fix

If deployment breaks:

1. **Check the build logs** for errors in `npm run build`
2. **Verify the copy command** succeeds: `cp -r dist server/dist`  
3. **Look for backend static file messages** in server logs
4. **Test locally** with the same build process
5. **Redeploy** after confirming local build works

---

## Deployment Checklist

Before deploying, ensure:

1. **Environment Variables**: All required environment variables are set in Replit Secrets
2. **Database**: PostgreSQL database is created and accessible
3. **Frontend Build**: Run `npm run build` to create production build
4. **Backend Dependencies**: All Python dependencies are in requirements.txt
5. **Static Files**: Frontend build files are copied to server/dist/
6. **Port Configuration**: Backend uses port 80 in production

## Common Issues and Solutions

### ETH Price Shows as $0
- **Cause**: ETH uses special zero address `0x0000000000000000000000000000000000000000`
- **Solution**: ETH price fetching has special handling in `EthereumPriceFetcher.fetch_prices()`
- **Prevention**: Do not treat ETH like a regular ERC-20 token

### Frontend Connection Timeout
- **Cause**: Backend not responding or wrong port configuration
- **Solution**: Ensure backend runs on port 80 in production, frontend uses same origin

**Remember:** The deployment must build the frontend AND copy files to the right location for the backend to serve them. Both steps are critical.