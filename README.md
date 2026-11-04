# Soteria Business School — Computer Science Attendance

A Flask attendance site for ND1 and ND2, configured for free Render web hosting and a Supabase PostgreSQL database. It includes separate class-rep logins, admin student import, editable timetable details, lesson attendance (Present / Absent / Late), and printable PDF reports.

## What is needed
- A GitHub account
- A Render account
- A Supabase account

The free hosting option has limits: Render Free services sleep when idle and can take a little time to wake. Supabase Free projects have usage limits and may pause after inactivity. This is suitable for a small pilot, but do not treat a free tier as a guaranteed archival system. Export/backup attendance regularly.

## Part 1 — Create the Supabase database
1. Go to https://supabase.com and create a free account.
2. Select **New project**. Name it `soteria-attendance` and set a strong database password. Save that database password privately.
3. Wait for the project to finish creating.
4. Open **Project Settings → Database** (or **Connect**) and find the PostgreSQL connection string. Choose the **Session pooler** connection if offered; otherwise use the direct connection string. It should begin with `postgresql://` or `postgres://`.
5. Copy the entire connection string. Replace any `[YOUR-PASSWORD]` placeholder with the database password you created. Do not post this string in chats or screenshots; it grants database access.
6. No manual SQL setup is needed. The app creates its tables and starter timetable automatically on first start.

## Part 2 — Upload this project to GitHub
1. Download and extract the ZIP file on your computer.
2. Go to https://github.com and create a new **Private** repository named `soteria-attendance`.
3. Open the empty repository and choose **Add file → Upload files**.
4. Upload the *contents* of the extracted folder, including `app.py`, `render.yaml`, `requirements.txt`, and the `templates` folder. Do not upload only the ZIP, and do not put everything inside an extra nested folder.
5. Commit the upload to the `main` branch.
6. Check that `app.py` and `render.yaml` are visible at the top level of the repository.

## Part 3 — Deploy on Render Free
1. Go to https://render.com and sign in using GitHub.
2. Choose **New + → Blueprint**.
3. Connect GitHub if asked, then select the `soteria-attendance` repository and branch `main`.
4. Render reads `render.yaml`. Before creating the service, supply these environment variables when prompted:
   - `ADMIN_PASSWORD`: create a strong private password for the administrator.
   - `ND1_PASSWORD`: create a different strong password for the ND1 class representative.
   - `ND2_PASSWORD`: create a different strong password for the ND2 class representative.
   - `DATABASE_URL`: paste the Supabase PostgreSQL connection string from Part 1.
   - `SECRET_KEY` should be generated automatically by Render. If it asks you to provide one, use a long random secret.
5. Create/apply the Blueprint using the **Free** instance option. Do not choose a paid instance if your goal is zero hosting cost.
6. Wait for the deployment to finish. Open the `.onrender.com` URL shown by Render.

If the Blueprint was created without the variables, open the Render service → **Environment** → **Add Environment Variable**, add the four values above, save, and redeploy. Never share the passwords or database URL with anyone.

## Part 4 — Sign in and configure
- Admin username: `admin`
- ND1 representative username: `nd1_rep`
- ND2 representative username: `nd2_rep`

Passwords are the values you created in Render. There is no public student signup. The admin adds students and gives each class rep their own login privately.

1. Sign in as `admin`.
2. Open **Students** and add students individually, or upload a CSV file.
3. CSV must have columns `student_id,full_name`. In Excel, use **Save As → CSV UTF-8 (Comma delimited)**. Select the class (ND1 or ND2) on upload.
4. Open **Timetable** and correct any course names, codes, or lecturers marked “to confirm”.
5. Give the ND1 and ND2 representatives their respective usernames and passwords privately.
6. Each representative signs in, selects a lesson/date, marks each student Present, Absent, or Late, and saves.
7. Admin opens **Reports**, selects the class and optional course code, then downloads/prints the PDF. The PDF includes lecturer and school administrator signature spaces.

## Important operating notes
- Keep the database connection string and all login passwords private.
- Use strong, unique passwords. Change them in Render → service → Environment when needed, then redeploy.
- Export/backup your attendance data from Supabase regularly. Free services have limits and are not a substitute for a formal school records backup policy.
- Render Free sleeps when idle. The first visit after inactivity may take a little time to load.
- The supplied timetable was transcribed from photos and contains entries marked “to confirm”. Admin should verify all timetable details before use.
- This is a starter project, not a security-audited student information system. Before storing sensitive official records, have the school/IT administrator review access controls, privacy, backups, and applicable data-protection requirements.

## Local development
Set `DATABASE_URL` to a PostgreSQL connection string, set `SECRET_KEY`, `ADMIN_PASSWORD`, `ND1_PASSWORD`, and `ND2_PASSWORD`, then run:

```bash
pip install -r requirements.txt
python app.py
```
