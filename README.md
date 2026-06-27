# MediCal

A self-hosted medication, prescription and health-records tracker. An admin creates user logins; each user logs visits to doctors/hospitals (with cost & vitals), records medicines prescribed (with mandatory dose + composition so alternates can be found later), tracks lab tests/imaging and vaccinations, and gets a dashboard with spending and health analytics.

**Current version: 1.1.0**

## Stack
- **Backend:** FastAPI + SQLAlchemy + PostgreSQL, JWT auth, file uploads on a Docker volume, Tesseract OCR, ReportLab PDF export.
- **Frontend:** Static HTML/CSS/vanilla JS (no build step) served by Nginx, which reverse-proxies `/api` and `/uploads` to the backend. Light/dark theme, collapsible sidebar.
- **Deployment:** Docker Compose — 3 services: `db`, `backend`, `frontend`.

## Quick start

```bash
cp .env.example .env
# edit .env — at minimum change SECRET_KEY and the default admin password
docker compose up -d --build
```

Visit **http://localhost:8080**. Log in with the admin credentials from your `.env` (default `admin` / `admin123` if unchanged — change this immediately via Settings).

## What's new in 1.1.0

- **Rebrand**: MediCal name and logo, new blue brand palette sampled from the logo, full dark mode.
- **Visit cost tracking**: log cash vs. insurance, itemized by category (reception, pharmacy, laboratory, x-ray, consultation, procedure, other).
- **Spending analytics**: dashboard shows year-to-date cash vs. insurance totals and a per-category breakdown.
- **Refill tracking**: quantity remaining + low-stock threshold per medicine, quick +/- adjusters, dashboard low-stock widget, low-stock search filter.
- **Export**: medication history, visit history, and yearly spending — each as CSV or a branded PDF — from the new **Reports** page.
- **OCR auto-fill**: scan an uploaded prescription photo (Tesseract) to suggest doctor name, hospital name, and dose — always shown for review, never auto-saved.
- **Insurance/cost on medicines**: optional per-medicine cost, payment method, and insurance-covered flag.
- **Vaccination records**: a dedicated record type with dose number, next-due tracking, and certificate upload.
- **Dark mode toggle**: in the sidebar and in Settings, persisted per-user.
- **Vitals on visits**: blood pressure, weight, heart rate captured per visit; latest reading surfaced on the dashboard.
- **Lab Tests & Imaging**: log tests requested by physicians (CBC, X-Ray, etc.), mark completed, attach result files.
- **App version + update check**: version shown bottom-left of the sidebar; if `GITHUB_REPO` is set in `.env`, it checks the GitHub Releases API and shows an "Update available" pill linking to the release.
- **Reports**: dedicated page to export/visualize visits, medicines and spending.

## How it works

1. **Admin** logs in, goes to **Manage Users**, creates accounts for patients/family members (role `user` or `admin`).
2. A **user** adds a **Doctor Visit**: doctor, hospital, dates, vitals (BP/weight/heart rate), a default payment method, itemized costs per category, and an optional prescription photo (with OCR auto-fill).
3. Within that visit, the user adds **medicines**: name, **composition** and **dose** are mandatory (so "what else has this same composition" can be searched if a brand isn't available), plus frequency, timing, manufacturer, dates, symptom tags, refill quantity/threshold, cost, payment method, insurance flag, and a photo.
4. **Lab Tests & Imaging** and **Vaccinations** are tracked as their own record types, each independently of medicines.
5. The **Dashboard** shows totals, last visit, next visit, next medicine, medicines ending soon, last vitals, low-stock medicines, and this year's spending split by cash/insurance.
6. **Search** filters by keyword, composition, doctor, hospital, symptom tag, status, stock level, and visit date range, plus a one-click "find alternates by composition" lookup.
7. **Reports** exports medicine history, visit history, and yearly spending as CSV or PDF.
8. **Settings** lets any user change their password and toggle dark mode; admins manage all accounts under **Manage Users**.

Admins can see all users' data; regular users only see their own.

## Enabling the update checker

Set in `.env`:
```
APP_VERSION=1.1.0
GITHUB_REPO=yourname/your-repo
```
The sidebar will then call `https://api.github.com/repos/<GITHUB_REPO>/releases/latest` from the browser and show an "Update available" pill if the latest tag differs from `APP_VERSION`. Tag your GitHub releases as `v1.1.0`, `v1.2.0`, etc. Bump `APP_VERSION` in `.env` (and the `VERSION` file) with each release you ship.

## Project structure
```
medtrack/
├── docker-compose.yml
├── .env.example
├── VERSION
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── database.py
│       ├── models.py
│       ├── schemas.py
│       ├── auth.py
│       └── routers/
│           ├── auth_router.py
│           ├── users_router.py
│           ├── prescriptions_router.py   # visits, cost items, vitals
│           ├── medicines_router.py       # incl. refill tracking
│           ├── tags_router.py
│           ├── dashboard_router.py       # spending, vitals, low-stock
│           ├── labtests_router.py
│           ├── vaccinations_router.py
│           ├── ocr_router.py
│           ├── export_router.py          # CSV/PDF
│           └── version_router.py
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── assets/logo.png
    ├── index.html
    ├── dashboard.html
    ├── medicines.html
    ├── visits.html
    ├── lab-tests.html
    ├── vaccinations.html
    ├── search.html
    ├── reports.html
    ├── users.html
    ├── settings.html
    ├── css/style.css
    └── js/ (api.js, sidebar.js, theme.js)
```

## Feature ideas not yet built

- Dose reminders via push/email notifications, not just dashboard display.
- Allergy & adverse-reaction log surfaced as a warning when adding a matching composition.
- Caregiver view — one login managing multiple linked patient profiles.
- Admin audit log of who changed what.
- Two-factor authentication for admins.
- Family/household grouping so costs can be rolled up across multiple users.
- Native push notifications / PWA install support for refill and appointment reminders.
- Bulk CSV import of historical medicines for onboarding.
- Pharmacy price comparison API integration alongside "find alternates by composition."

## Security notes before production use
- Change `SECRET_KEY` and the default admin password immediately.
- Put this behind HTTPS (e.g. Caddy/Traefik with Let's Encrypt) — it runs plain HTTP by default, fine for local/LAN use only.
- Tighten CORS in `backend/app/main.py` (currently `allow_origins=["*"]`) to your real domain.
- OCR text and lab/vaccination files are stored unencrypted on the upload volume — encrypt the underlying disk/volume if hosting sensitive records.
