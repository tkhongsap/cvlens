# CVLens-Agent 📄

**Privacy-first resume screening from your Outlook inbox**

CVLens-Agent is a desktop-only application that streamlines early-stage hiring by automatically collecting resumes from your Outlook folders, parsing them, scoring candidates against your job requirements, and presenting an interactive dashboard for quick decision-making.

## 🌟 Features

- **📧 Email Integration**: Connects to your Outlook account via Microsoft Graph API
- **📁 Folder-Scoped Access**: Only accesses the specific folder you select
- **📄 Document Parsing**: Extracts text from PDF, DOC, and DOCX files (with OCR support)
- **🎯 Smart Scoring**: Scores candidates based on skills, education, and experience
- **🔒 Privacy-First**: All processing happens locally, data is AES-encrypted
- **📊 Interactive Dashboard**: Review, filter, and make decisions on candidates
- **💾 Export Functionality**: Export candidate data to CSV
- **🧹 Data Purge**: One-click removal of all stored data

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Microsoft 365 account with Outlook
- Azure AD app registration (for OAuth)
- Tesseract OCR (optional, for scanned PDFs)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/cvlens-agent.git
   cd cvlens-agent
   ```

2. **Set up environment variables**
   ```bash
   cp env.example .env
   ```
   
   Edit `.env` and add your configuration:
   ```env
   CLIENT_ID=your_azure_app_client_id
   TENANT_ID=your_azure_tenant_id
   AES_KEY=your_32_byte_aes_encryption_key_base64_encoded
   ```

3. **Run the application**
   
   **Windows:**
   ```cmd
   run_local.bat
   ```
   
   **Linux/Mac:**
   ```bash
   chmod +x run_local.sh
   ./run_local.sh
   ```

## 🔧 Configuration

### Azure AD App Setup

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to Azure Active Directory > App registrations
3. Create a new registration:
   - Name: CVLens-Agent
   - Supported account types: Single tenant
   - Redirect URI: Not required for device code flow
4. Note down the Application (client) ID and Directory (tenant) ID
5. Under API permissions, add:
   - Microsoft Graph > Delegated permissions > Mail.Read

### Job Profile Configuration

Edit `job_profile.yml` to define your hiring criteria:

```yaml
job_title: "Senior Software Engineer"
weights:
  skills: 60
  education: 20
  experience: 20

skills:
  required:
    - python
    - javascript
  preferred:
    - docker
    - kubernetes
```

### Optional: Tesseract OCR

For parsing scanned PDFs, install Tesseract:

**Windows:**
Download from: https://github.com/UB-Mannheim/tesseract/wiki

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

**Mac:**
```bash
brew install tesseract
```

## 📖 Usage Guide

### 1. Authentication

- Click "Authenticate with Microsoft" in the sidebar
- A device code will be displayed in the console
- Visit https://microsoft.com/devicelogin
- Enter the code and sign in with your Microsoft account

### 2. Folder Selection

- Once authenticated, select your recruitment email folder
- Optionally enable "Include subfolders"
- Click "Save Folder Selection"

### 3. Syncing Resumes

- Click "Sync Emails" to start the pipeline
- The app will:
  - Fetch emails with attachments
  - Download and parse resumes
  - Score candidates against your job profile

### 4. Reviewing Candidates

- View candidates sorted by match score
- Click on any candidate to see details
- Use action buttons:
  - ✅ Interested: Mark for interview
  - ❌ Pass: Reject candidate
  - ↩️ Reset: Return to new status
- Add notes for each candidate
- Download original resume files

### 5. Exporting Data

- Click "Export CSV" to download candidate data
- Includes all candidate information and scores

## 🛡️ Privacy & Security

- **Local Processing**: All data processing happens on your machine
- **AES Encryption**: Sensitive data is encrypted in the SQLite database
- **Folder Scoped**: Only accesses the email folder you explicitly select
- **No Cloud Storage**: Resume data never leaves your computer
- **Data Purge**: Complete data removal with one click

## 🐛 Troubleshooting

### Common Issues

**Authentication fails:**
- Ensure your Azure AD app has Mail.Read permissions
- Check that CLIENT_ID and TENANT_ID are correct
- Try clearing the token cache in `data/.token/`

**No resumes found:**
- Verify the selected folder contains emails with attachments
- Check that attachments are PDF, DOC, or DOCX files
- Ensure files are under 25MB (configurable limit)

**OCR not working:**
- Install Tesseract and add to PATH
- Or set TESSERACT_CMD in .env file

**Database errors:**
- Ensure AES_KEY is a valid base64-encoded 32-byte key
- Try deleting `data/db/cvlens.db` and restarting

### Logs

Check `logs/cvlens.log` for detailed error messages.

## 📁 Project Structure

```
cvlens-agent/
├── app.py              # Main Streamlit application
├── src/
│   ├── auth/          # Authentication modules
│   ├── services/      # Core services (ingest, parse, score)
│   ├── models/        # Database models
│   └── config.py      # Configuration management
├── data/              # Local data storage
│   ├── cache/         # Downloaded attachments
│   ├── db/            # SQLite database
│   └── .token/        # OAuth tokens
├── logs/              # Application logs
├── job_profile.yml    # Scoring criteria
└── settings.json      # Application settings
```

## 🤝 Contributing

This is a local-only application designed for individual use. Feel free to fork and customize for your needs.

## 📄 License

MIT License - See LICENSE file for details

## ⚠️ Disclaimer

This application is designed for personal use in screening resumes. Ensure compliance with your organization's data protection policies and local privacy laws when handling candidate information.
