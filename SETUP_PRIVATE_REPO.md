# Setting Up Private Repository Distribution

This guide explains how to securely distribute Find Better from a private GitHub repository.

## Step 1: Make Repository Private

1. Go to: https://github.com/moranlevy420/birmanet/settings
2. Scroll to **Danger Zone**
3. Click **Change visibility** → **Make private**
4. Confirm by typing the repository name

## Step 2: Add Collaborators (Optional)

If you want others to view the source code:

1. Go to: https://github.com/moranlevy420/birmanet/settings/access
2. Click **Add people**
3. Enter their GitHub username or email

## Step 3: Create a GitHub Personal Access Token

You'll need this to create releases and for users to download updates.

1. Go to: https://github.com/settings/tokens
2. Click **Generate new token (classic)**
3. Settings:
   - **Name:** `FindBetter Distribution`
   - **Expiration:** 90 days (or longer)
   - **Scopes:** Check `repo` (full control of private repositories)
4. Click **Generate token**
5. **COPY THE TOKEN** - you won't see it again!

### Save your token locally:

```bash
echo "ghp_xxxxxxxxxxxx" > .github_token
```

The `.github_token` file is in `.gitignore` and won't be committed.

## Step 4: Create a Release

When you have new code to distribute:

```bash
# Run tests first
python -m pytest tests/

# Commit and push changes
git add -A
git commit -m "Your message"
git push origin main

# Create a release (e.g., v2.3.0)
python scripts/create_release.py v2.3.0
```

This will:
1. Create a zip file with all necessary files
2. Create a GitHub release with the version tag
3. Upload the zip as a downloadable asset

## Step 5: Distribute to Users

### Option A: Send Zip Directly (Simpler)

1. Download the zip from the GitHub release
2. Send it to the user via email/chat
3. They extract and run `INSTALL_WINDOWS.bat`

### Option B: Users Download with Token (Self-service)

Users need a Personal Access Token with `repo` scope.

1. Create a token for them (or have them create one)
2. They run `UPDATE_WINDOWS.bat`
3. First time: paste the token when prompted
4. The token is saved locally for future updates

## How Updates Work for Users

Once set up with a token:

1. Double-click `UPDATE_WINDOWS.bat`
2. Script automatically:
   - Authenticates with GitHub
   - Downloads latest release
   - Extracts files
   - Runs database migrations
   - Sets up/resets admin accounts
3. Done! Run `run_app.bat` to start

## Security Notes

- **Tokens expire** - set appropriate expiration (30-90 days recommended)
- **Tokens are stored locally** in `.github_token` (not committed)
- **Users can't see source code** unless added as collaborators
- **Each user should have their own token** for tracking/revocation

## Troubleshooting

### "Token verification failed"
- Token may have expired - generate a new one
- Token may not have `repo` scope - regenerate with correct scope

### "Repository not found"
- Repo may be private and token doesn't have access
- Check token has `repo` scope

### "No zip file found in release"
- Release was created but zip upload failed
- Re-run `python scripts/create_release.py <version>`

