# Hotel-back

![Python](https://img.shields.io/badge/language-Python-blue.svg)
![Backend](https://img.shields.io/badge/type-Backend-yellow.svg)
![FastAPI](https://img.shields.io/badge/framework-FastAPI-009688.svg)
![PostgreSQL](https://img.shields.io/badge/database-PostgreSQL-blue.svg)
![Status](https://img.shields.io/badge/status-active-brightgreen.svg)

## Description

**Hotel-back** is the backend service for the HotelMobileApp project.  
Built with **FastAPI** and **PostgreSQL**, it provides a robust, secure, and scalable RESTful API for hotel management, user authentication, reservations, payments, and administration.

This backend is the core of the hotel management system, seamlessly integrating with the mobile client and delivering all essential business logic and data persistence.

---

## Key Features

- 🏨 **Hotel & Room Management**  
  CRUD operations for hotels, rooms, and amenities.

- 👤 **User Authentication & Authorization**  
  Secure registration, JWT-based login, and role-based access for guests and administrators.

- 📅 **Booking System**  
  Real-time room availability, booking creation, modification, and cancellation.

- 💵 **Payment Integration**  
  Support for processing payments and managing transaction history.

- 📝 **Reviews & Ratings**  
  Endpoints for submitting and managing user reviews and hotel ratings.

- 📊 **Analytics & Admin Tools**  
  Statistical endpoints for occupancy, revenue, and customer insights.

- 📦 **RESTful API**  
  Well-structured, documented endpoints for easy integration with mobile and web clients.

---

## API Documentation

Interactive API docs available via **Swagger UI** at:
```
/docs
```
or **ReDoc** at:
```
/redoc
```

---

## Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL
- pip
- (Optional) Virtual environment tool (venv, poetry, etc.)

### Installation

1. **Clone the repository:**
    ```bash
    git clone https://github.com/XXXDoriXXX/Hotel-back.git
    cd Hotel-back
    ```

2. **Set up a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Configure environment variables:**  
   Create a `.env` file or set environment variables for:
   - `DATABASE_URL` (e.g., `postgresql+asyncpg://user:password@localhost/dbname`)
   - `SECRET_KEY`
   - `ALGORITHM`
   - Others as required

5. **Apply database migrations:**  
   (Assuming Alembic is used)
    ```bash
    alembic upgrade head
    ```

6. **Run the development server:**
    ```bash
    uvicorn app.main:app --reload
    ```

---

## Technologies & Frameworks

- **Language:** Python
- **Framework:** FastAPI
- **Database:** PostgreSQL (async with SQLAlchemy or Tortoise ORM)
- **Authentication:** JWT (PyJWT/FastAPI Security)
- **API Docs:** Swagger (OpenAPI)
- **Testing:** pytest

---

## Project Structure (Example)

```
hotel-back/
│
├── app/
│   ├── main.py
│   ├── models/
│   ├── schemas/
│   ├── api/
│   ├── core/
│   ├── db/
│   └── ...
├── alembic/
├── requirements.txt
├── .env
└── README.md
```

---

## Contribution

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature-name`).
3. Make your changes and commit (`git commit -am 'Add some feature'`).
4. Push to your branch.
5. Open a pull request.

---

## Contact & Support

- Author: [XXXDoriXXX](https://github.com/XXXDoriXXX)
- For questions and suggestions, please use [Issues](https://github.com/XXXDoriXXX/Hotel-back/issues)



