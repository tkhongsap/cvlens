# CVLens-Agent Quick Start Guide 🚀

Get CVLens-Agent up and running in 5 minutes!

## Prerequisites Checklist

- [ ] Python 3.8+ installed
- [ ] Microsoft 365 account with Outlook access
- [ ] Git installed (to clone the repository)

## Step 1: Clone and Setup (2 minutes)

```bash
# Clone the repository
git clone https://github.com/yourusername/cvlens-agent.git
cd cvlens-agent

# Copy environment template
cp env.example .env
```

## Step 2: Azure AD App Registration (3 minutes)

1. Go to https://portal.azure.com
2. Search for "App registrations" and click it
3. Click "New registration"
4. Fill in:
   - Name: `CVLens-Agent`
   - Account types: `Single tenant`
   - Leave Redirect URI empty
5. Click "Register"
6. Copy these values:
   - **Application (client) ID** → Save this
   - **Directory (tenant) ID** → Save this
7. Go to "API permissions" → "Add permission"
8. Select "Microsoft Graph" → "Delegated permissions"
9. Search and add: `Mail.Read`
10. Click "Grant admin consent" (if you have admin rights)

## Step 3: Configure Environment (1 minute)

1. Generate an AES key:
   ```bash
   python generate_aes_key.py
   ```

2. Edit `.env` file and add:
   ```
   CLIENT_ID=<your-application-id>
   TENANT_ID=<your-directory-id>
   AES_KEY=<generated-aes-key>
   ```

## Step 4: Run the Application (1 minute)

**Windows:**
```cmd
run_local.bat
```

**Mac/Linux:**
```bash
chmod +x run_local.sh
./run_local.sh
```

## Step 5: First Time Setup

1. **Browser opens** at http://localhost:8501
2. Click **"Authenticate with Microsoft"** in sidebar
3. **Check console** for device code
4. Go to https://microsoft.com/devicelogin
5. Enter the code and sign in
6. Return to CVLens-Agent
7. Select your recruitment email folder
8. Click **"Sync Emails"** to start!

## Troubleshooting

**"Module not found" errors:**
- The run script should install dependencies automatically
- If not, run: `pip install -r requirements.txt`

**Authentication fails:**
- Double-check CLIENT_ID and TENANT_ID in .env
- Ensure Mail.Read permission is granted
- Try clearing `data/.token/` folder

**No emails found:**
- Check the selected folder has emails with attachments
- Verify attachments are PDF/DOC/DOCX files

## Next Steps

- Edit `job_profile.yml` to match your hiring criteria
- Review the full README.md for detailed features
- Check TASKS.md for upcoming features

---

Need help? Check the logs in `logs/cvlens.log` for detailed error messages. 