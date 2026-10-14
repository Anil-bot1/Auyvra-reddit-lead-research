# Auyvra Lead Research Dashboard

A modern, professional web application designed for **Auyvra**, an AI automation agency specializing in AI voice agents, AI receptionists, 24/7 intelligent chatbots, lead generation, customer enquiry handling, automated appointment booking, follow-up automation, and business workflow automation.

The dashboard empowers Auyvra to discover businesses discussing operational friction online, qualify high-intent opportunities, transparently score them from 0 to 100, generate consultative reply drafts, and synchronize qualified prospects into a dedicated Google Spreadsheet (**`Auyvra Daily Leads`**).

---

## 🚀 Key Highlights & Capabilities

* **Modern Dark SaaS Interface**: Built with a deep charcoal/navy aesthetic (`#0B0F19`, `#111827`, `#1E293B`), subtle blue and teal accents (`#38BDF8`, `#2DD4BF`), and clear status indicators (🟢 Qualified, 🟡 Awaiting Review, 🔴 Disqualified, 🔵 Contacted).
* **Transparent 0–100 Scoring Engine**: Objective scoring based on Problem Clarity (25 pts), Auyvra Service Alignment (30 pts), Commercial Intent (25 pts), and Actionability (20 pts). Every score provides an auditable breakdown and supports manual score/status override.
* **Consultative Reply Generator**: Generates natural, helpful, problem-first reply drafts tailored to the business owner's challenge. Strictly avoids aggressive sales pitches, generic spam, or false claims. **All drafts require human review and approval; never auto-posts or auto-contacts**.
* **Daily Research Target Tracker**: Tracks daily review progress toward the agency target of reviewing ~20 relevant discussions/day and shortlisting up to 5 high-converting prospects.
* **Pluggable Data Ingestion Layer**:
  * **Manual Research Mode (Active)**: Manual URL and problem entry, freeform notes parser, and batch CSV import with row-by-row validation and URL deduplication.
  * **Reddit API Layer (Strictly Disabled)**: Commercial API approval is pending. Kept safely disabled behind `REDDIT_INTEGRATION_ENABLED=false`. Zero scraping, zero unofficial endpoints, zero fake leads.
* **Dedicated Google Sheets Synchronization**: Connects safely to **`Auyvra Daily Leads`**, automatically creates or selects daily worksheets named by Asia/Kolkata date (e.g., `Leads_2026-10-14`), prevents duplicate rows, and falls back gracefully when unconfigured.
* **09:00 AM Asia/Kolkata Daily Digest**: Formats a daily summary of new opportunities, top verticals, top countries, and shortlisted leads. Includes ready-to-deploy Google Apps Script for reliable time-driven execution that doesn't rely on Render's free tier staying awake.
* **Completely Isolated**: Operates independently with its own local database (`auyvra_leads.db`). Does not modify or interfere with any existing Supabase databases or deployed applications.

---

## 🛠️ Technology Stack

| Layer | Technology | Rationale |
| :--- | :--- | :--- |
| **Backend** | Python 3.12 + FastAPI | Ultra-fast startup (<1s), high concurrency, strict Pydantic v2 data validation, OpenAPI docs. |
| **Database** | SQLite + SQLAlchemy 2.0 | Lightweight, zero-config, ACID-compliant local storage; no external database fees. |
| **Frontend** | HTML5, Tailwind CSS, Lucide Icons, Chart.js | Clean dark SaaS interface, zero frontend build overhead, responsive across desktop and mobile. |
| **Google Sync** | `gspread` + `google-auth` | Safe Google Sheets API client with service-account credential authentication. |
| **Testing** | `pytest` + `starlette.testclient` | Comprehensive unit and integration test suite covering scoring, API routes, CSV parsing, and fallback modes. |
| **Deployment** | Render (Free Web Service) | Uses standard `requirements.txt`, `Procfile`, and `render.yaml`. |

---

## 📋 Project Structure

```text
Auyvra lead research/
├── .env.example              # Safe environment variable template with placeholders
├── .gitignore                # Protects credentials, SQLite DBs, virtual environments, and caches
├── Procfile                  # Web process definition for Render
├── render.yaml               # Infrastructure-as-code Blueprint for Render free web service
├── requirements.txt          # Python dependencies
├── README.md                 # Full project documentation & operator manual
├── config.py                 # Application settings with Pydantic
├── database.py               # SQLAlchemy database session setup
├── models.py                 # ORM models (Lead, DailyResearchStat, ActivityLog)
├── schemas.py                # Pydantic validation schemas
├── scoring.py                # Transparent 0–100 scoring engine & keyword classifiers
├── response_generator.py     # Consultative, advice-first reply draft engine
├── main.py                   # FastAPI application entrypoint & REST API
├── sources/
│   ├── base.py               # Abstract BaseLeadSource interface
│   ├── manual.py             # ManualLeadSource (URL, text parser, CSV batch import)
│   └── reddit.py             # RedditApiLeadSource (safely disabled pending commercial authorization)
├── services/
│   ├── lead_service.py       # Queries, filtering, deduplication, KPI metrics
│   ├── sheets_service.py     # Google Sheets "Auyvra Daily Leads" daily tab sync
│   └── report_service.py     # 09:00 AM Asia/Kolkata digest generator & Apps Script code
├── static/
│   ├── css/custom.css        # Dark SaaS aesthetic, custom scrollbars, badges, glow borders
│   └── js/dashboard.js       # Client controller, Chart.js visualizers, modals, and toasts
├── templates/
│   └── dashboard.html        # Main dashboard template
└── tests/
    ├── test_scoring.py       # Unit tests for scoring, services, and industry detection
    └── test_leads_api.py     # Integration tests for API, CSV ingestion, deduplication, and reports
```

---

## 💻 Local Setup & Development

### 1. Prerequisites
* Python 3.10+ (Tested on Python 3.12)
* Git

### 2. Clone / Open Directory
```bash
cd "c:\Users\aniln\Documents\Antigravity_workspace\Auyvra lead research"
```

### 3. Initialize Python Virtual Environment
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Setup Local Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(By default, all settings in `.env.example` allow the dashboard to run 100% locally with zero external credentials needed).*

### 6. Run the Application
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
Open your browser at **[http://localhost:8000](http://localhost:8000)** to view the dashboard.
API interactive documentation is available at **[http://localhost:8000/docs](http://localhost:8000/docs)**.

### 7. Run Automated Tests
```bash
pytest -v
```

---

## 📊 Transparent 0–100 Lead Scoring Engine

The dashboard scores every opportunity objectively across four critical dimensions:

$$\text{Lead Score} = \text{Clarity} (25) + \text{Relevance} (30) + \text{Evidence} (25) + \text{Feasibility} (20)$$

| Dimension | Max Points | What It Measures |
| :--- | :---: | :--- |
| **Problem Clarity** | 25 | Length and specificity of stated bottleneck, operational pain words (*missed calls, losing clients, overwhelmed, repetitive, manual*). |
| **Auyvra Service Fit** | 30 | Direct match to Auyvra offerings: AI Voice Agents, AI Receptionist, Appointment Booking, Follow-up Automation, Workflow Automation. |
| **Commercial Reality** | 25 | Evidence of an active business (*staff, patients, customers, invoices, revenue*) and high-value vertical (*Dental, Clinic, Restaurant, Real Estate, Home Services*). |
| **Outreach Feasibility** | 20 | Explicit questions/seeking recommendations (*"how do you", "recommend tool", "what software"*) and known geographic context. |

* **70–100**: 🟢 **Qualified** (High commercial intent and service alignment).
* **50–69**: 🟡 **Awaiting Review** (Moderate fit, requires manual inspection).
* **< 50**: 🔴 **Disqualified** (Consumer inquiry or low relevance).

*You can manually adjust the score and status in the Lead Inspector modal at any time.*

---

## 📝 Manual Research Mode Guide

Because Reddit commercial API approval is pending, the application operates in **Manual Research Mode**:

1. **Add Lead Manually**:
   * Click **"+ Add Lead"** on the header.
   * Enter Discussion URL, Topic, Stated Problem, Industry, and Country.
   * Click **"Add & Score Lead"**. The system auto-scores, assigns the Auyvra service, and generates a reply draft.
2. **Parse Freeform Notes**:
   * Click **"Parse Notes"**.
   * Paste any raw discussion snippet, post, or client email.
   * Click **"Analyze Text"** to preview the auto-extracted problem, matching service, and score, then click **"Save as Lead"**.
3. **Batch CSV Import**:
   * Click **"CSV Import"**.
   * Upload a CSV file with the following column headers:
     ```csv
     url,title,stated_problem,industry,country,source,author,notes
     https://reddit.com/r/smallbusiness/comments/1,Missed calls during lunch,We run a busy cafe and miss 15 calls daily,Restaurant / Catering,United States,Reddit,cafe_owner,High priority
     https://reddit.com/r/realtors/comments/2,Lead follow up ghosting,Buyer inquiries go cold after 48 hours,Real Estate,Canada,Reddit,realtor_mike,Needs follow-up sequence
     ```
   * Duplicate URLs are automatically skipped to keep your database clean.

---

## 📈 Google Sheets Sync ("Auyvra Daily Leads")

The application connects to a dedicated Google Spreadsheet named **`Auyvra Daily Leads`**.

### Credentials & Permissions Required:
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project and enable both **Google Sheets API** and **Google Drive API**.
3. Go to **APIs & Services > Credentials** and create a **Service Account**.
4. Create and download a **JSON Key** for this Service Account.
5. Create a new Google Spreadsheet named exactly **`Auyvra Daily Leads`**.
6. Share this spreadsheet with the Service Account email address (e.g., `auyvra-leads@your-project.iam.gserviceaccount.com`) with **Editor** permissions.
7. Configure your credentials in `.env`:
   * Local: Set `GOOGLE_SERVICE_ACCOUNT_FILE="path/to/credentials.json"`
   * Render: Set `GOOGLE_SERVICE_ACCOUNT_JSON='{"type": "service_account", ...}'` (as a single-line string).

### Daily Tab Organization:
* The system detects or creates a daily worksheet named with Asia/Kolkata date: `Leads_YYYY-MM-DD` (e.g. `Leads_2026-10-14`).
* Inserts a consistent 16-column header row and appends only new records (matching by Discussion URL to avoid duplicates).
* If Google credentials are not configured, the app runs locally and displays a clear setup message without crashing.

---

## ⏰ 09:00 AM Asia/Kolkata Daily Digest Report

To avoid relying on a free Render web service staying awake 24/7, the 9:00 AM daily report is delivered using a **Google Apps Script Time-Driven Trigger** directly attached to your spreadsheet.

> [!NOTE]
> Google Apps Script time-driven triggers execute within a standard time window (e.g., between 8:00 AM – 9:00 AM or 9:00 AM – 10:00 AM) rather than at the exact second.

### Setup Steps:
1. Open your **`Auyvra Daily Leads`** Google Spreadsheet.
2. Click **Extensions > Apps Script**.
3. In the dashboard, click the **Mail icon** or open the **Report Modal**, then click **"Copy Apps Script Code"**.
4. Paste the script into `Code.gs`.
5. Set `RECIPIENT_EMAIL = "lingamanil55@gmail.com"`.
6. Click **Triggers** (clock icon on the left navigation) > **Add Trigger**:
   * Function: `sendDailyLeadDigest`
   * Event Source: `Time-driven`
   * Type: `Day timer`
   * Time of day: `8am to 9am` or `9am to 10am`
7. Click **Save** and grant permissions to send emails via your Google account.
8. To test formatting anytime, click **"Daily Report"** in the dashboard and view the rendered preview.

---

## 🔒 Reddit API Commercial Restriction Notice

* Commercial API access for Reddit is currently pending approval.
* The application **strictly adheres to Reddit terms**:
  * ❌ No web scraping.
  * ❌ No unofficial API endpoints or bypasses.
  * ❌ No fabricated or simulated scan results.
* The Reddit API module (`sources/reddit.py`) is locked behind `REDDIT_INTEGRATION_ENABLED=false`.
* When commercial API authorization is officially granted, you can set `REDDIT_INTEGRATION_ENABLED=true` and input your OAuth client credentials in `.env` without changing the dashboard UI.

---

## ☁️ Deployment on Render

This application is ready to deploy directly to Render on the **Free Web Service** tier:

1. Push your repository to GitHub (`Auyvra-reddit-lead-research`).
2. Log in to [Render](https://render.com/) and click **New > Blueprint** (or **New > Web Service**).
3. Connect your repository. Render will automatically detect `render.yaml`.
4. Configure the following environment variables in Render:
   * `APP_NAME`: `Auyvra Lead Research Dashboard`
   * `APP_ENV`: `production`
   * `DEBUG`: `false`
   * `SECRET_KEY`: `(generate a secure 32-character random string)`
   * `TIMEZONE`: `Asia/Kolkata`
   * `REDDIT_INTEGRATION_ENABLED`: `false`
   * `GOOGLE_SHEET_NAME`: `Auyvra Daily Leads`
   * `GOOGLE_SERVICE_ACCOUNT_JSON`: `(paste your single-line service account JSON)`
   * `ALERT_EMAIL_RECIPIENT`: `lingamanil55@gmail.com`
   * `DASHBOARD_PUBLIC_URL`: `https://your-app-name.onrender.com`
5. Click **Deploy**. The application will build and be live in ~2 minutes.

---

## 🛡️ Security & Privacy Checklist

* ✅ **Zero Private Credentials in Frontend**: No service account keys, tokens, or secrets are exposed in JavaScript or HTML.
* ✅ **Strict `.gitignore`**: All `.env`, `*.json` keys, SQLite databases, and caches are excluded from Git commits.
* ✅ **No Auto-Outreach**: Personalized replies are strictly drafts for manual operator review and approval.
* ✅ **Separation of Concerns**: Uses an isolated SQLite database; does not modify your existing Supabase database or environment.
