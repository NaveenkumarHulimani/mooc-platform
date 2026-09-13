# Online Coding MOOC Platform — Local Demo

A local demo of the MOOC platform, structured as a **course catalog**: Python, Java, C and
JavaScript are each a separate course with its own Easy/Medium/Hard practice levels, its own
final exam, and its own certificate. Register/login, pick a course, solve problems in an in-browser Monaco editor
with real sandboxed execution + auto-evaluation via a self-hosted Piston instance, unlock the
course's final exam once all three levels are solved, and download a PDF certificate after
passing. There's also an admin backend (Flask-Admin) at `/admin` for managing courses, problems,
users, submissions, exam attempts, and certificates.

Visual design and the courses→levels→exam→certificate structure are modeled after a reference
prototype the user pointed at (`codepath-mooc-platform`) — dark IDE-slate theme with an amber
accent, Space Grotesk headings, JetBrains Mono labels — while keeping our own real backend,
Monaco editor, and actual code execution instead of that reference's static MCQ quizzes.

**Not included yet**: MySQL (still SQLite), mid-exam page-refresh resume mid-question-editing
(the exam attempt itself resumes fine — see "How the exam works" below), more than 8 problems per
course (small pool means exam retries can repeat questions once exhausted).

## Prerequisite: a running Piston container (required for ANY code execution — practice or exam)

Code execution runs through [Piston](https://github.com/engineer-man/piston), self-hosted in a
local Docker container — **not** Judge0/RapidAPI (that was the original plan, but RapidAPI's
Judge0 CE now requires a card on file even for its free-tier "Basic" plan, and Piston's public
API now requires manual maintainer approval — self-hosting sidesteps both).

**One-time setup** (requires Docker Desktop running):

```
mkdir piston-data
docker run --privileged -v "<absolute-path-to>/piston-data:/piston" -dit -p 2000:2000 --name piston_api ghcr.io/engineer-man/piston

# install the four runtimes this app uses (each takes a few minutes — Python alone is ~1GB)
curl -X POST http://localhost:2000/api/v2/packages -H "Content-Type: application/json" -d "{\"language\":\"python\",\"version\":\"3.12.0\"}"
curl -X POST http://localhost:2000/api/v2/packages -H "Content-Type: application/json" -d "{\"language\":\"java\",\"version\":\"15.0.2\"}"
curl -X POST http://localhost:2000/api/v2/packages -H "Content-Type: application/json" -d "{\"language\":\"gcc\",\"version\":\"10.2.0\"}"
curl -X POST http://localhost:2000/api/v2/packages -H "Content-Type: application/json" -d "{\"language\":\"node\",\"version\":\"20.11.1\"}"
```

Note: the package name you install (e.g. `node`, `gcc`) isn't always the same as the language
name you execute against — installing `node` registers an invokable language called
`javascript`, and installing `gcc` registers `c` (and `c++`, `d`, `fortran`). Check
`GET /api/v2/runtimes` after installing if a new language doesn't work — it lists the actual
invokable names.

On Windows Git Bash, prefix the `docker run` line with `MSYS_NO_PATHCONV=1` — otherwise Git Bash
mangles the `-v` volume path and the container fails to start (chown error on `/piston`).

**Every time you want to use the app**, the container just needs to be running:
```
docker start piston_api     # if it's stopped
docker ps                   # confirm it shows piston_api on port 2000
```
`backend/judge.py` calls `http://localhost:2000` directly — no API key, no `.env` entry needed
for code execution. If the container isn't running, submit/exam calls fail with a clear message
telling you to start it, instead of hanging.

Optional: add a `GEMINI_API_KEY` to `backend/.env` (copy from `.env.example`) to get real AI
hints on the Solve page. Without it, the "Get AI Hint" button returns a static placeholder tip.

## Run the backend

```
cd backend
python -m venv venv          # already created if you're continuing this session
venv\Scripts\activate         # Windows
pip install -r requirements.txt
python seed.py                # populates courses + problems (only needs to run once)
python app.py                 # starts Flask on http://127.0.0.1:5000
```

`seed.py` also creates one hardcoded admin account: **admin@mooc.local / admin123**. Log in with
it at **http://127.0.0.1:5000/admin/login** to manage Courses, Problems, Users, Submissions, Exam
Attempts, and Certificates through auto-generated CRUD tables (Flask-Admin). This is a separate,
session-cookie-based login from the student JWT auth used by the React app — change the password
by editing the `User` row in the admin's Users view, or change `ADMIN_PASSWORD` in `seed.py`
before first running it. This admin backend is a local-dev convenience, not hardened for
production (no rate limiting, no 2FA, no audit log).

Note: SQLite writes to `backend/instance/mooc.db` (Flask-SQLAlchemy resolves relative sqlite
URIs against an `instance/` folder, not the working directory) — that's the file to delete if
you ever need to wipe demo data and reseed from scratch.

## Run the frontend

```
cd frontend
npm install
npm run dev                   # starts Vite, usually on http://localhost:5173 (or next free port)
```

Open the printed local URL in your browser. Register a new account, then explore Courses → pick
a course → Easy/Medium/Hard practice → once all three are solved, the exam card unlocks → pass
the exam → certificate ready. Dashboard aggregates progress across all courses.

## Project structure

```
backend/
  app.py              Flask app factory + blueprint registration
  models.py           User, Course, Problem, Submission, CourseEnrollment, ExamAttempt,
                       ExamAnswer, Certificate
  auth.py             register/login (JWT)
  courses.py           GET /api/courses, GET /api/courses/<id> — level-completion logic lives
                       here (shared with exam.py and dashboard.py)
  problems.py         list/get problems, course-scoped, annotated with attempted/solved
  judge.py            Piston (localhost:2000) client + test-case evaluation
  submit.py           POST /api/submit — practice mode run/evaluate (language derived from course)
  exam.py             POST /api/exam/start, POST /api/exam/<id>/finalize — course-scoped exam,
                       gated on all-levels-done, resets levels on fail
  certificate.py      GET /api/certificate, GET /api/certificate/download — course-scoped
  certificate_pdf.py  ReportLab-based certificate PDF builder
  dashboard.py        cross-course aggregate: certs earned, levels completed, exam history
  ai.py               AI hint endpoint via Google Gemini (stub if no GEMINI_API_KEY)
  admin.py            Flask-Admin + Flask-Login setup — CRUD backend at /admin
  templates/          admin_login.html, admin_index.html (server-rendered, not part of the React app)
  seed.py             4 courses (python/java/c/javascript) × 8 problems each, idempotent per
                      course (safe to re-run after adding a new course) + hardcoded admin account
piston-data/          bind-mounted volume for the Piston container's installed language runtimes
frontend/
  src/pages/     Login, Register, Courses, CourseDetail, Practice, Solve, Exam, Certificate,
                 Dashboard
  src/api/       axios client with JWT auto-attach
  src/auth.js    localStorage session helpers
  src/index.css  dark IDE-slate + amber theme (Bootstrap 5.3 dark mode + custom tokens/components)
```

## How courses, levels, and exams work
Each course (Python/Java/C/JavaScript) has 8 problems split Easy/Medium/Hard. A level counts as complete
once every problem in that difficulty (for that course) has a PASSing submission. All three
levels done unlocks that course's final exam — 3 random questions (one per difficulty), 15
minutes, enforced server-side too (a late submission past a 10-second grace period auto-fails).
Score ≥ 60% = PASS, which issues that course's certificate.

**Failing the exam resets that course's levels** — you'll need to re-solve all three levels
before the exam unlocks again (matching the reference design's "fair second chance" policy). This
doesn't delete your past submissions — internally, a `CourseEnrollment.cycle_started_at`
timestamp is bumped forward on failure, and only submissions made after that timestamp count
toward level-completion, so your solve history is preserved for the dashboard even though the
levels show as incomplete again.

Navigating away mid-exam and coming back resumes the same attempt with the correct remaining
time (via `GET /api/exam/current`) instead of orphaning it — only your in-editor typing since the
last save is lost, not the attempt itself.

## Known limitations of this build
- SQLite, not MySQL — fine for a single-machine demo, swap `SQLALCHEMY_DATABASE_URI` in
  `app.py` when moving to a shared/deployed environment.
- Code execution depends on Docker Desktop + the `piston_api` container running locally — this
  won't work on a machine without Docker, and doesn't scale to multiple students hitting a
  shared server (that would need a real deployed Piston/Judge0 instance, not this local setup).
- Certificate PDFs use ReportLab, not WeasyPrint (the original stack doc's pick) — WeasyPrint
  needs GTK/Pango native libraries that are painful to install on Windows; ReportLab is
  pure-Python and installs cleanly.
- Only 8 problems per course; exam retries can start repeating questions once you've used them
  all across attempts within that course. Add more to `seed.py`'s `PROBLEM_TEMPLATES` list to
  widen the pool for all courses at once.
- I can't run a browser myself in this environment — the visual reskin (amber theme, progress
  track, level cards, certificate) hasn't been screenshot-verified by me, only by reading the
  code. Worth an eyeball pass against the reference design.
