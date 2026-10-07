# Hotel-back

REST API for a hotel booking platform: hotels, rooms, bookings, payments and owner statistics.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00)
![Stripe](https://img.shields.io/badge/Stripe-635BFF?logo=stripe&logoColor=white)
![AWS S3](https://img.shields.io/badge/AWS%20S3-569A31?logo=amazons3&logoColor=white)

## Overview

Hotel-back is the main backend of the Hotel project. It serves both the Android client and the owner web panel.

| Repository | Role |
| --- | --- |
| [Hotel-back](https://github.com/XXXDoriXXX/Hotel-back) | This API (production backend) |
| [Hotel-front-web](https://github.com/XXXDoriXXX/Hotel-front-web) | Web panel for hotel owners, [live demo](https://hotel-front-web.vercel.app) |
| [HotelMobileApp](https://github.com/XXXDoriXXX/HotelMobileApp) | Android app for guests |
| [HotelFastApi](https://github.com/XXXDoriXXX/HotelFastApi) | Earlier prototype of this API (legacy) |

```
Android app  ─┐
              ├──> Hotel-back (FastAPI) ──> PostgreSQL
Web panel    ─┘          ├──> Stripe (payments, Connect, webhooks)
                         └──> AWS S3 (images)
```

## Features

- Registration and login for clients and owners, JWT bearer tokens
- Profile management with avatar upload
- Hotels: CRUD, images, amenities, search, trending, popular and best-deals lists, ratings
- Rooms: CRUD, images, amenities, booked dates
- Bookings: Stripe checkout, cash bookings with owner confirmation, refunds, archiving
- Stripe Connect onboarding for owners and a webhook endpoint
- Favorite hotels
- Employees per hotel with salary history
- Owner statistics (full hotel stats and summary)
- Background jobs (APScheduler): completes finished bookings every 12 hours and cancels stale card bookings every 10 minutes
- Interactive API docs at `/docs` and `/redoc`

## Tech stack

FastAPI, SQLAlchemy, Alembic, PostgreSQL (psycopg2), python-jose and passlib/bcrypt for auth, Stripe, boto3 (S3), APScheduler, Pillow, Uvicorn.

## Getting started

Requirements: Python 3.12 and a running PostgreSQL database.

```bash
git clone https://github.com/XXXDoriXXX/Hotel-back.git
cd Hotel-back
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root (see the table below), then run:

```bash
alembic upgrade head
uvicorn main:app --reload
```

The API is available at `http://localhost:8000`, docs at `http://localhost:8000/docs`.

`main.py` also calls `Base.metadata.create_all` on start, so tables are created automatically. Alembic migrations are in `alembic/versions`. `alembic.ini` contains a placeholder `sqlalchemy.url` that you must point to your own database before using Alembic.

The repository includes a `Procfile` (`web: uvicorn main:app --host 0.0.0.0 --port $PORT`) for platforms such as Railway or Heroku.

### Tests

Tests live in `tests/` and use pytest with a SQLite test database. They also need `pytest`, `pytest-asyncio` and `sqlalchemy_utils`, which are not listed in `requirements.txt`.

```bash
pip install pytest pytest-asyncio sqlalchemy_utils
pytest
```

## Environment variables

| Variable | Required | Description |
| --- | --- | --- |
| `DATABASE_URL` | yes | SQLAlchemy URL, for example `postgresql://user:password@localhost:5432/hotel_db` |
| `JWT_SECRET` | yes | Secret used to sign JWT tokens, the app will not start without it |
| `STRIPE_SECRET_KEY` | yes | Stripe secret API key |
| `STRIPE_WEBHOOK_SECRET` | yes | Signing secret of the Stripe webhook endpoint |
| `STRIPE_DOMAIN` | no | Frontend URL used for Stripe redirects, default `http://localhost:5173` |
| `S3_BUCKET` | yes | S3 bucket for hotel, room and avatar images |
| `S3_REGION` | yes | AWS region of the bucket |
| `AWS_ACCESS_KEY_ID` | yes | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | yes | AWS secret key |

## Main endpoints

| Prefix | Purpose |
| --- | --- |
| `/auth` | register (client, owner), login, current user |
| `/profile` | read and update profile, change avatar |
| `/hotels` | hotels, images, search, stats, ratings |
| `/rooms` | rooms, images, amenities, booked dates |
| `/amenities` | hotel and room amenities |
| `/bookings` | checkout, cash confirmation, refunds, history |
| `/payments`, `/stripe` | Stripe Connect and webhook |
| `/favorites` | favorite hotels |
| `/employees` | staff and salary history |

## Notes

CORS origins are set in `main.py`; add your frontend URL there when deploying it elsewhere.

## Author

[XXXDoriXXX](https://github.com/XXXDoriXXX)
