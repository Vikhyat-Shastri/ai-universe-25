# PowerShell script to set up GitHub remote and push
# Run this AFTER creating the repository on GitHub

param(
    [Parameter(Mandatory=$true)]
    [string]$RepoName,
    
    [Parameter(Mandatory=$false)]
    [string]$GitHubUsername = ""
)

if ([string]::IsNullOrWhiteSpace($GitHubUsername)) {
    Write-Host "Please enter your GitHub username: " -NoNewline
    $GitHubUsername = Read-Host
}

$remoteUrl = "https://github.com/$GitHubUsername/$RepoName.git"

Write-Host "Adding remote origin: $remoteUrl"
git remote add origin $remoteUrl

Write-Host "Pushing to GitHub..."
git push -u origin main

Write-Host "Done! Your repository is now on GitHub at: https://github.com/$GitHubUsername/$RepoName"
