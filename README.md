# ASCE – Automobile Service Cost Estimator

A web app that estimates car repair costs in Bangladesh for the Toyota Axio, Premio, Allion,
Corolla and Noah. Describe the problem in Bangla, Banglish or English; an AI agent asks up to
three questions, picks the repair jobs, and the app prices them from our parts and labour data
as a minimum / likely / maximum cost in taka.

**Stack:** Flask, Flask-SQLAlchemy (SQLite), Flask-Migrate, Flask-JWT-Extended ·
Nuxt 4 (Vue 3, SSR) · LangChain + Google Gemini

## Team

| Member | Parts |
|---|---|
| Aranya | Project setup, AI cost estimate, integration and demo data |
| Jannat | Authentication, estimate history |
| Tanima | Vehicle management, price data |

## Features

- **Accounts:** register, log in, log out, protected pages
- **My cars:** add, edit and delete cars (5 Toyota models, 1995 to this year, 0–999,999 km)
- **Price data:** 20 repair jobs, 23 parts, labour rates for three garage types, imported
  from a Bikroy listings CSV and a garage price sheet
- **AI estimate:** Gemini picks jobs from our catalogue only; every taka figure comes from the
  database. Safety warnings for brakes and suspension, and "not enough data" when a part has
  no prices. If the AI is unavailable, you can choose the jobs by hand.
- **History:** list, view and delete past estimates, filter by car and date, sort by cost
- **Job card design:** every estimate reads like a garage job card, with a price range bar,
  a parts vs labour split, safety alerts and a "Got a quote?" check against the range

## Running it locally

You need Python 3.11+ and Node 22.21+ (or 24.11+).

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Fill in SECRET_KEY and JWT_SECRET_KEY. Generate each with:
python -c "import secrets; print(secrets.token_hex(32))"
# Optional: GOOGLE_API_KEY for the AI estimate.

flask --app wsgi db upgrade
python scripts/import_prices.py     # load jobs, parts, labour rates and prices
python scripts/seed_demo.py         # optional demo account, cars and estimates
flask --app wsgi run
```

The API runs on http://127.0.0.1:5000. The app will not start without the two secrets, and no
secret or password is stored in the code. `seed_demo.py` uses `DEMO_PASSWORD` if set,
otherwise it generates a password and prints it once.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. Requests to `/api/**` are proxied to Flask (set `API_BASE` to
change where), so the browser only talks to one origin.

### Tests

```bash
cd backend
pytest
```

The AI tests use a fake model, so they need no API key or network.

## API

| Endpoint | Does |
|---|---|
| `POST /api/auth/register` | Create an account and log in |
| `POST /api/auth/login` | Log in, set the JWT cookie |
| `POST /api/auth/logout` | Clear the cookie |
| `GET /api/auth/me` | The logged-in user |
| `GET /api/vehicles` | List my cars |
| `POST /api/vehicles` | Add a car |
| `GET /api/vehicles/<id>` | One car |
| `PUT /api/vehicles/<id>` | Edit a car |
| `DELETE /api/vehicles/<id>` | Delete a car |
| `GET /api/vehicles/options` | Models, engine sizes and year range for the form |
| `GET /api/estimates/highlights` | Public: starting prices and sample estimates for the landing page |
| `GET /api/estimates/jobs?q=` | Job catalogue, with suggestions for a problem text |
| `POST /api/estimates` | Run the AI agent (or price hand-picked jobs) and save |
| `GET /api/estimates` | List my estimates (`page`, `per_page`, `vehicle_id`, `days`, `sort=newest\|cost`) |
| `GET /api/estimates/<id>` | One estimate with items |
| `DELETE /api/estimates/<id>` | Delete an estimate |

`POST /api/estimates` takes `vehicle_id`, `problem_text`, `garage_tier`
(`local`, `workshop` or `dealer`) and `answers` (the questions answered so far). It returns
`status: "question"` with the next question, `"done"` with the saved estimate, `"no_match"`,
or HTTP 503 with `"ai_unavailable"`. Send `job_codes` instead to skip the AI.

## How an estimate is calculated

1. The agent returns job codes (for example `BRAKE_PADS_F`). Codes not in the catalogue are
   dropped.
2. For every part in those jobs, all prices for that car model are looked up.
   Minimum = cheapest, maximum = most expensive, likely = median, times the quantity.
   A part used by two chosen jobs is counted once.
3. Labour = standard hours × the hourly rate for the garage type (min, middle and max).
4. Confidence: **high** with 5+ prices per part including a garage-verified one, **medium**
   with 2+, **low** with 1, **not enough data** when a part has none (it is left out of the
   total and the user is told).

## Security

- Passwords are hashed with scrypt (Werkzeug) and never returned by the API.
- The JWT is stored in an HTTP-only, SameSite=Lax cookie, so page scripts cannot read it.
- Every POST, PUT and DELETE must send the `X-CSRF-TOKEN` header, copied from the
  `csrf_access_token` cookie. `useApi.ts` does this automatically.
- Login gives the same error for a wrong password and an unknown email.
- Login is limited to 5 tries a minute, registration to 10 an hour and estimates to 30 an hour.
- Users only ever see their own cars and estimates; other ids return 404.

## Design

The UI follows the ASCE "garage job card" design: warm paper background (`#F6F4EF`), ink text
(`#16181D`) and a signal yellow (`#F2B705`) for actions and highlights. Headings use Archivo,
body text Hind Siliguri (good Bangla support) and prices JetBrains Mono. Colour tokens live in
`frontend/app/assets/css/main.css`.

## Price data

`backend/data/mapping.json` lists the 5 car models, 23 parts, 20 jobs and labour rates, plus
the spellings used in listings (for example "Corolla Axio", "Brand new Japan", "mobil filter").

The files `backend/data/sample_bikroy_listings.csv` and `sample_garage_prices.csv` are
**sample data** in the same format as our scraper output and garage sheet. They are there so
the app works out of the box. Replace them with real data and run
`python scripts/import_prices.py --bikroy <file> --garage <file>`. Rows without a price,
for other models or unknown parts, and duplicates are skipped.


