# GitHub Pages Setup for AtroZ Dashboard

## Quick Start Guide

Follow these steps to deploy the AtroZ Dashboard to GitHub Pages:

## Step 1: Enable GitHub Pages

1. **Go to Repository Settings**
   - Navigate to your repository: `https://github.com/kkkkknhh/SAAAAAA`
   - Click on **Settings** tab (top right)

2. **Configure Pages**
   - Scroll down to **Pages** section (left sidebar under "Code and automation")
   - Under **Source**, select **GitHub Actions**
   - Click **Save**

![GitHub Pages Settings](https://docs.github.com/assets/cb-47267/images/help/pages/publishing-source-drop-down.png)

## Step 2: Verify Workflow Permissions

1. **Check Actions Permissions**
   - Go to **Settings** > **Actions** > **General**
   - Scroll to **Workflow permissions**
   - Select **Read and write permissions**
   - Check **Allow GitHub Actions to create and approve pull requests**
   - Click **Save**

2. **Verify Pages Permissions**
   - Go to **Settings** > **Environments**
   - If you see `github-pages` environment, click on it
   - Verify deployment branch is set correctly

## Step 3: Trigger Deployment

### Option A: Push to Main Branch

The workflow is configured to run automatically on push to `main` or `master`:

```bash
# Merge your PR or push directly to main
git checkout main
git merge copilot/setup-atroz-dashboard
git push origin main
```

### Option B: Manual Trigger

1. Go to **Actions** tab
2. Click on **Deploy AtroZ Dashboard** workflow
3. Click **Run workflow** button
4. Select branch (usually `main`)
5. Click **Run workflow**

## Step 4: Monitor Deployment

1. **Check Workflow Status**
   - Go to **Actions** tab
   - Click on the running workflow
   - Watch the progress in real-time
   - Deployment typically takes 1-2 minutes

2. **Verify Success**
   - Look for green checkmark ✅
   - Check the **Deploy to GitHub Pages** step for the URL
   - Example: `https://kkkkknhh.github.io/SAAAAAA/`

## Step 5: Access Dashboard

Once deployed, access your dashboard at:

```
https://<username>.github.io/<repository>/
```

For this repository:
```
https://kkkkknhh.github.io/SAAAAAA/
```

## Troubleshooting

### Issue: Workflow Fails with "Permission denied"

**Solution**: Enable workflow permissions (see Step 2)

### Issue: 404 Page Not Found

**Solutions**:
1. Wait 5-10 minutes after first deployment
2. Verify GitHub Pages is enabled in Settings
3. Check that workflow completed successfully
4. Try hard refresh (Ctrl+Shift+R or Cmd+Shift+R)

### Issue: Dashboard loads but no data

**Reason**: GitHub Pages only serves static files (frontend)

**Solutions**:

**Option 1: Configure External API**
Edit `src/saaaaaa/api/static/index.html`:
```javascript
window.ATROZ_API_URL = 'https://your-api-server.com';
```

**Option 2: Deploy Backend Separately**
- Deploy API server to Heroku, Railway, or other hosting
- Update `ATROZ_API_URL` to point to deployed backend
- Ensure CORS is configured to allow your GitHub Pages domain

**Option 3: Use Local Development**
For full functionality, run locally:
```bash
bash scripts/start_dashboard.sh
# Access at http://localhost:5000/
```

### Issue: CSS/JS not loading

**Solution**: Verify file paths in `index.html` are relative:
```html
<link rel="stylesheet" href="css/atroz-dashboard.css">
<script src="js/atroz-dashboard.js"></script>
```

### Issue: "Resource not found" in Actions

**Solution**: 
1. Verify `src/saaaaaa/api/static/` directory exists
2. Verify `index.html` exists in that directory
3. Re-run workflow

## Configuration Options

### Custom Domain

To use a custom domain:

1. Add a `CNAME` file to `src/saaaaaa/api/static/`:
   ```
   dashboard.yourdomain.com
   ```

2. Configure DNS at your domain provider:
   ```
   Type: CNAME
   Name: dashboard
   Value: <username>.github.io
   ```

3. Update **Settings** > **Pages** > **Custom domain**

### Base URL Configuration

If repository is not at root path, update the base URL:

In `index.html`:
```javascript
window.ATROZ_BASE_PATH = '/SAAAAAA/';
```

## Monitoring

### Check Deployment Status

```bash
# Using GitHub CLI
gh run list --workflow=deploy-dashboard.yml

# View latest run
gh run view

# Watch logs
gh run watch
```

### View Logs

1. Go to **Actions** tab
2. Click on latest workflow run
3. Click on **deploy** job
4. Expand each step to see detailed logs

## Updating the Dashboard

After making changes:

1. **Push changes**:
   ```bash
   git add src/saaaaaa/api/static/
   git commit -m "Update dashboard"
   git push origin main
   ```

2. **Workflow runs automatically**
   - No manual intervention needed
   - Changes live in 1-2 minutes

3. **Force refresh** in browser:
   - Windows/Linux: `Ctrl + Shift + R`
   - Mac: `Cmd + Shift + R`

## Security Considerations

### Public Repository

⚠️ **Warning**: GitHub Pages sites from public repositories are publicly accessible.

- Don't commit secrets or API keys
- Use environment variables for sensitive data
- Configure CORS on backend to restrict access

### Private Repository

✅ Private repositories can use GitHub Pages with:
- GitHub Pro, Team, or Enterprise
- Access restricted to repository collaborators

## Alternative: GitHub Pages with Backend

For full-stack deployment on GitHub infrastructure:

1. **Frontend**: GitHub Pages (static files)
2. **Backend**: GitHub Actions + Cloud Run/Lambda
   - Deploy API to serverless platform
   - Update frontend API URL
   - Configure CORS

See `ATROZ_DASHBOARD_DEPLOYMENT.md` for cloud deployment options.

## Getting Help

### Documentation

- Main deployment guide: `ATROZ_DASHBOARD_DEPLOYMENT.md`
- Frontend docs: `src/saaaaaa/api/static/README.md`
- GitHub Pages docs: https://docs.github.com/pages

### Common Commands

```bash
# Check workflow status
gh run list --workflow=deploy-dashboard.yml

# View latest run
gh run view

# Cancel running workflow
gh run cancel

# Re-run failed workflow
gh run rerun

# Download workflow artifacts
gh run download
```

### Support

If you encounter issues:

1. Check GitHub Actions logs
2. Review error messages
3. Consult troubleshooting section above
4. Open an issue with:
   - Error message
   - Workflow run link
   - Steps to reproduce

## Success Checklist

- [ ] GitHub Pages enabled in Settings
- [ ] Workflow permissions configured (read/write)
- [ ] Workflow completed successfully (green checkmark)
- [ ] Dashboard accessible at GitHub Pages URL
- [ ] Visual elements load correctly
- [ ] No console errors
- [ ] (Optional) Backend API configured
- [ ] (Optional) Custom domain configured

## Next Steps

Once your dashboard is deployed:

1. **Share the URL** with your team
2. **Configure backend** for full functionality
3. **Set up monitoring** (Google Analytics, etc.)
4. **Customize** the dashboard for your needs
5. **Add authentication** if needed (external service)

---

**Ready to deploy?** 🚀

Merge your PR to main branch and watch the magic happen!

```bash
git checkout main
git merge copilot/setup-atroz-dashboard
git push origin main
```

Then visit: `https://kkkkknhh.github.io/SAAAAAA/`
