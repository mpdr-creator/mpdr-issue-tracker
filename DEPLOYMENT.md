# MorepenPDR IMS — Complete Deployment Guide
## You can do this in ~2 hours with zero coding!

---

## STEP 1 — Create Accounts (15 min)

1. **GitHub**: https://github.com → Sign Up (free)
2. **Supabase**: https://supabase.com → Sign Up (free)
3. **Streamlit Cloud**: https://share.streamlit.io → Sign in with GitHub

---

## STEP 2 — Set Up the Database in Supabase (15 min)

1. Login to Supabase → click **New Project**
2. Give it a name like `morepenpdr-ims`
3. Set a strong database password → **Save this password!**
4. Wait for project to be ready (~1 min)
5. Click **SQL Editor** in the left sidebar
6. Click **New Query**
7. Copy the ENTIRE contents of `schema.sql` and paste it
8. Click **Run** (green button)
9. You should see "Success" messages

### Get your connection details:
- Go to **Settings → Database**
- Copy the **Host** (looks like `db.abcdef.supabase.co`)
- The password is the one you set in step 3

---

## STEP 3 — Get Gmail App Password (10 min)

1. Go to your Gmail account → **Google Account Settings**
2. Click **Security**
3. Enable **2-Step Verification** if not already on
4. Search for **"App Passwords"** in the search bar
5. Select app: **Mail** → Device: **Other** → type "Streamlit"
6. Click **Generate** → copy the 16-character password shown
7. Save it — you'll need it in the next step

---

## STEP 4 — Upload to GitHub (10 min)

1. Go to https://github.com → click **New repository**
2. Name it `morepenpdr-ims` → keep it **Private** → Create
3. Click **uploading an existing file**
4. Upload these files:
   - `app.py`
   - `requirements.txt`
5. Click **Commit changes**

> ⚠️ Do NOT upload `secrets.toml` — it contains passwords!

---

## STEP 5 — Deploy on Streamlit Cloud (10 min)

1. Go to https://share.streamlit.io
2. Click **New app**
3. Select your GitHub repo `morepenpdr-ims`
4. Main file: `app.py`
5. Click **Advanced settings** → go to **Secrets** tab
6. Paste this (fill in YOUR values):

```toml
DB_HOST     = "db.YOUR_SUPABASE_HOST.supabase.co"
DB_PORT     = 5432
DB_NAME     = "postgres"
DB_USER     = "postgres"
DB_PASSWORD = "YOUR_SUPABASE_PASSWORD"
SECRET_KEY  = "any-long-random-string-here-12345"
SMTP_USER   = "yourgmail@gmail.com"
SMTP_PASS   = "xxxx xxxx xxxx xxxx"
SMTP_FROM   = "MorepenPDR IMS <yourgmail@gmail.com>"
IT_EMAIL    = "it@morepenpdr.com"
LAB_EMAIL   = "lab@morepenpdr.com"
SAFETY_EMAIL = "safety@morepenpdr.com"
HR_EMAIL    = "hr@morepenpdr.com"
FACILITIES_EMAIL = "facilities@morepenpdr.com"
```

7. Click **Save** → click **Deploy**
8. Wait 2–3 minutes → your app URL will be shown!

---

## STEP 6 — Test Your App

### Default login accounts (created by schema.sql):
All accounts use password: `Admin@123`

| Email | Role | Department |
|-------|------|------------|
| priya.sharma@morepenpdr.com | Scientist | — |
| it.admin@morepenpdr.com | Admin | IT |
| lab.admin@morepenpdr.com | Admin | Lab Maintenance |
| safety.admin@morepenpdr.com | Admin | Safety |
| management@morepenpdr.com | Management | — |

### Test flow:
1. Login as **scientist** → create a ticket (IT dept) → submit
2. Check if email arrived at the IT department inbox
3. Login as **IT admin** → find the ticket → click Manage → move to RESOLVED
4. Check if feedback email arrived at scientist's email
5. Login as **scientist** again → go to Feedback tab → rate the experience
6. Login as **management** → check analytics dashboard

---

## STEP 7 — Invite Real Users

Share the Streamlit URL with your company. Anyone with a
`@morepenpdr.com` email can self-register using the Register tab.

---

## Common Issues & Fixes

### "Connection refused" database error
- Double-check `DB_HOST` in secrets — it should start with `db.`
- Make sure you're using the Supabase password, not a Gmail password

### Emails not sending
- Make sure you used the **App Password** (16 chars), not your Gmail password
- Check Gmail security settings — App Passwords require 2FA to be enabled

### "Module not found" error
- Make sure `requirements.txt` is in your GitHub repo alongside `app.py`

### App shows blank white page
- Wait 1-2 min and refresh — first load takes time
- Check the Streamlit Cloud logs for error details

---

## Security Notes

- Change all default passwords immediately after first login
- The app only allows `@morepenpdr.com` emails — others are blocked
- Secrets are encrypted by Streamlit Cloud and never visible to users
- Keep your GitHub repo **private**
