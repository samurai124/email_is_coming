# Job Application Auto-Mailer (CLI)

An automated, AI-personalized cold outreach CLI application that sends job application emails with your resume attached directly to hiring teams, with built-in anti-spam safeguards, duplicate protection, and dry-run preview capabilities.

---

## 📁 Project Structure

```text
job_application_mailer/
├── data/
│   ├── companies.csv       <- List of target companies & contacts
│   ├── sent_log.csv        <- Automatically tracked delivery history (prevents duplicates)
│   └── resumes/
│       └── resume.pdf      <- Your resume PDF to attach
├── templates/
│   └── default_template.txt<- Fallback customizable email template
├── .env                    <- Your credentials and personal profile
├── .env.example            <- Example configuration reference
├── ai_generator.py         <- Gemini API integration & template engine
├── csv_manager.py          <- CSV parsing, email validation & logging
├── email_sender.py         <- SMTP client, MIME multipart builder & attachment handler
├── config.py               <- Settings & environment loader
├── main.py                 <- Interactive CLI terminal interface
└── README.md
```

---

## 🚀 Quick Start (In 3 Steps)

### Step 1: Configure Your Profile & Email in `.env`
Open `.env` in any text editor and fill in your details:
```ini
SENDER_NAME="Your Full Name"
SENDER_EMAIL="your_email@gmail.com"
SENDER_PHONE="+1 (555) 012-3456"
SENDER_LINKEDIN="https://linkedin.com/in/yourprofile"
CANDIDATE_SUMMARY="Full-Stack Developer with experience in Python, React, and cloud architectures."

# Gmail Settings:
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_PASSWORD="xxxx xxxx xxxx xxxx"   # Use a 16-character App Password (see below)

# AI Personalization (Google Gemini):
GEMINI_API_KEY="your-gemini-api-key"
```

#### 🔑 How to get a Gmail App Password (1 minute):
1. Go to your [Google Account Security Settings](https://myaccount.google.com/security).
2. Enable **2-Step Verification** (if not already enabled).
3. Search for or click on **App passwords** (or visit [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)).
4. Enter an app name (e.g. `JobMailer`) and click **Create**.
5. Copy the generated 16-character code (e.g. `abcd efgh ijkl mnop`) and paste it into `SENDER_PASSWORD` in your `.env`.

#### 🤖 How to get a Free Gemini API Key:
1. Visit [Google AI Studio](https://aistudio.google.com/).
2. Click **Get API key** and generate a new key.
3. Paste the key into `GEMINI_API_KEY` in `.env`.
*(Note: If you don't provide an API key, the app will automatically fall back to the professional template in `templates/default_template.txt`).*

---

### Step 2: Add Your Resume & Target Companies

1. **Add your resume**:
   - Place your PDF file inside `data/resumes/` and make sure it matches `RESUME_FILENAME` in `.env` (default is `resume.pdf`).
2. **Add companies to `data/companies.csv`**:
   The CSV supports the following columns:
   ```csv
   company_name,email,contact_name,role,company_notes
   Stripe,jobs@stripe.com,Recruiting Team,Backend Engineer,Leading payment APIs and developer tools
   Datadog,talent@datadoghq.com,Jane Doe,Software Engineer,Cloud observability and monitoring platforms
   ```

---

### Step 3: Run the Application

Navigate to the project folder in your terminal and run:

```powershell
python main.py
```

This opens the interactive menu:
```text
===============================================================
       JOB APPLICATION AUTO-MAILER (CLI)
       AI-Powered Cold Outreach with Resume Attachment
===============================================================

Select an action:
  1. Test Connection & Resume Setup
  2. Inspect CSV & View Pending Companies
  3. Preview AI-Generated Email (Dry-Run)
  4. Send Emails (Live Batch)
  5. Exit
```

---

## ⚡ Direct Command-Line Flags

You can also run specific tasks directly without entering the interactive menu:

- **Check status & pending companies:**
  ```powershell
  python main.py --status
  ```
- **Test your email SMTP connection & credentials:**
  ```powershell
  python main.py --test
  ```
- **Preview personalized emails without sending (Dry-Run):**
  ```powershell
  python main.py --preview 2
  ```
- **Send emails to pending companies:**
  ```powershell
  python main.py --send
  ```

---

## 🛡️ Anti-Spam & Safety Features

- **Duplicate Prevention**: Every sent email is recorded in `data/sent_log.csv`. Running the script repeatedly will **never** send duplicate emails to the same address.
- **Human-Like Cooldown / Jitter**: A randomized delay (20–45 seconds) is executed between each email to prevent personal email accounts from being flagged by spam filters.
- **Daily Quota Cap**: Configured to process a safe maximum batch size (`DAILY_MAX_EMAILS=40`) per run.
- **Explicit Confirmation**: The tool always prompts for confirmation before sending live emails.
