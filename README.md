# Hotel-back

![Python](https://img.shields.io/badge/language-Python-blue.svg)
![Backend](https://img.shields.io/badge/type-Backend-yellow.svg)
![Status](https://img.shields.io/badge/status-active-brightgreen.svg)

## Description

**Hotel-back** is the backend service for the HotelMobileApp project. Built with Python, it provides a robust, secure, and scalable API for managing hotel data, user authentication, reservations, payments, and administrative operations.

This backend is intended to serve as the core of the hotel management system, enabling seamless integration with the mobile client and providing essential business logic and data persistence.

---

## Key Features

- 🏨 **Hotel Management**  
  CRUD operations for hotels, rooms, and amenities.

- 👤 **User Authentication & Authorization**  
  Secure registration, login, and role-based access control for guests and administrators.

- 📅 **Booking System**  
  Real-time room availability checks, booking creation, modification, and cancellation.

- 💵 **Payment Integration**  
  Support for processing payments and managing transaction history.

- 📝 **Reviews & Ratings**  
  Endpoint for submitting and managing user reviews and hotel ratings.

- 📊 **Analytics & Admin Tools**  
  Statistical endpoints for occupancy, revenue, and customer insights.

- 📦 **RESTful API**  
  Well-structured, documented endpoints for easy integration with mobile and web clients.

---

## API Documentation

Full API documentation is available via Swagger/OpenAPI at:  
`/docs` or `/swagger` endpoint (depending on framework configuration).

---

## Getting Started

### Prerequisites

- Python 3.8+
- pip
- (Optional) Virtual environment tool (venv, poetry, etc.)
- Database (e.g., PostgreSQL, MySQL, or SQLite for development)

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
   Adjust `.env` file or environment variables for database and secret keys.

5. **Apply database migrations:**
    ```bash
    # Example for Django:
    python manage.py migrate
    # Or for Flask with Alembic, etc.
    ```

6. **Run the development server:**
    ```bash
    # Example for Django:
    python manage.py runserver

    # Example for Flask:
    flask run
    ```

---

## Technologies & Frameworks

- **Language:** Python
- **Framework:** FastAPI
- **Database:** PostgreSQL 
- **Authentication:** JWT 
- **API Docs:**  OpenAPI
- **Testing:** pytest / unittest

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
