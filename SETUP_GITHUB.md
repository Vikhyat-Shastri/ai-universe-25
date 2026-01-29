# Setting up GitHub Repository

## Step 1: Create Repository on GitHub

1. Go to https://github.com/new
2. Repository name: `ai-universe-25` (or your preferred name)
3. Description: "AI Universe 25 / Grokipedia - Multi-agent collaborative wiki with MCP governance and PSI metrics"
4. Choose **Public** or **Private**
5. **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

## Step 2: Connect and Push

After creating the repository, run one of these commands (replace `YOUR_USERNAME` with your GitHub username):

### Option A: Using the helper script
```powershell
.\setup_github.ps1 -RepoName "ai-universe-25" -GitHubUsername "YOUR_USERNAME"
```

### Option B: Manual commands
```powershell
git remote add origin https://github.com/YOUR_USERNAME/ai-universe-25.git
git push -u origin main
```

### Option C: Using SSH (if you have SSH keys set up)
```powershell
git remote add origin git@github.com:YOUR_USERNAME/ai-universe-25.git
git push -u origin main
```

## Troubleshooting

If you get authentication errors:
- For HTTPS: GitHub may prompt for username/password. Use a **Personal Access Token** instead of password
- Create token at: https://github.com/settings/tokens (with `repo` scope)
- For SSH: Ensure your SSH key is added to GitHub
