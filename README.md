# MedTrack

A self-hosted medication & prescription tracker. An admin creates user logins; each user logs visits to doctors/hospitals, records the medicines prescribed (with mandatory dose + composition so alternates can be found later), tags symptoms, and attaches photos of medicines and prescriptions. A dashboard surfaces key stats, and a dedicated search page filters across doctor, hospital, symptom tag, composition, and date.

## Stack
- **Backend:** FastAPI + SQLAlchemy + PostgreSQL, JWT auth, file uploads stored on a Docker volume.
- **Frontend:** Static HTML/CSS/vanilla JS (no build step) served by Nginx, which also reverse-proxies `/api` and `/uploads` to the backend.
- **Deployment:** Docker Compose — 3 services: `db`, `backend`, `frontend`.

## Quick start

```bash
cp .env.example .env
# edit .env — at minimum change SECRET_KEY and the default admin password
docker compose up -d --build
```

Visit **http://localhost:8080**. Log in with the admin credentials from your `.env` (default `admin` / `admin123` if unchanged — change this immediately via Settings or by creating a new admin and deleting the seed account).

## How it works

1. **Admin** logs in, goes to **Manage Users**, creates accounts for patients/family members (role `user` or `admin`).
2. A **user** logs in and adds a **Doctor Visit** (doctor name, hospital, visit date, next visit date, optional prescription photo/scan).
3. Within that visit, the user adds **medicines**: name, **composition** and **dose** are mandatory (this enables searching "what else has this same composition" if a specific brand isn't available), plus frequency, timing, manufacturer, start/end dates, symptom tags, notes, and a medicine photo (camera capture supported on mobile).
4. The **Dashboard** shows total medicines, active count, total hospital visits, distinct doctors/hospitals, last visit date, next scheduled visit, the most recently added active medicine, and medicines ending soon.
5. **Search** filters by keyword, composition, doctor, hospital, symptom tag, status, and visit date range, and includes a one-click "find alternates by composition" lookup.
6. **Settings** lets any user change their own password; admins manage all accounts under **Manage Users**.

Admins can see all users' data; regular users only see their own.

## Project structure
```
medtrack/
├── docker-compose.yml
├── .env.example
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
│           ├── prescriptions_router.py
│           ├── medicines_router.py
│           ├── tags_router.py
│           └── dashboard_router.py
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── index.html
    ├── dashboard.html
    ├── medicines.html
    ├── visits.html
    ├── search.html
    ├── users.html
    ├── settings.html
    ├── css/style.css
    └── js/
```

## Feature ideas not yet built

- Dose reminders via push/email notifications, not just dashboard display.
- Refill tracking — quantity remaining and low-stock alerts.
- Allergy & adverse-reaction log surfaced as a warning when adding a matching composition.
- Caregiver view — one login managing multiple linked patient profiles.
- Export medication history to PDF/CSV for a new doctor.
- OCR on uploaded prescriptions to auto-fill medicine fields.
- Admin audit log of who changed what.
- Two-factor authentication for admins.
- Insurance/cost tracking per medicine or visit.
- Vaccination records as a separate record type.
- Dark mode toggle.

## Security notes before production use
- Change `SECRET_KEY` and the default admin password immediately.
- Put this behind HTTPS (e.g. Caddy/Traefik with Let's Encrypt) — it runs plain HTTP by default, fine for local/LAN use only.
- Tighten CORS in `backend/app/main.py` (currently `allow_origins=["*"]`) to your real domain.
