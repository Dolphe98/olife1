# Olife (olife1.com) — Django

Fresh Django rebuild of the Olife blog (ported from the React/`Olife1withreact` site).

**Do not use** the old broken `olife_with_python` folder.

## Local run

```powershell
cd "C:\Users\AURO\OneDrive\Documents\Olphe_Company\olife1"
.\venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py seed_content
python manage.py runserver
```

Open http://127.0.0.1:8000/

## Pages

- `/` Home
- `/fragments/` Fragments gallery
- `/blog/` Blog index
- `/blog/<id>/` Blog post
- `/about/` About
- `/contact/` Contact + WhatsApp + newsletter
- `/privacy/` Data privacy
- `/copyright/` Copyright notice

## Railway

Push this folder to GitHub, create a Railway service from the repo, set:

- `SECRET_KEY` (random string)
- `DEBUG=False`
- `ALLOWED_HOSTS` (your Railway domain and later `olife1.com`)
- `CSRF_TRUSTED_ORIGINS` (e.g. `https://olife1.com,https://your-app.up.railway.app`)
- Optional Postgres: Railway Postgres plugin sets `DATABASE_URL`

Then point `olife1.com` DNS from Hostinger to Railway and cancel the old WordPress hosting.
