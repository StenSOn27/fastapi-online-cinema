# 🎬 Online Cinema (Portfolio Project)

An online cinema platform built with **FastAPI**, **PostgreSQL**, and **Docker**, allowing users to browse, purchase, and watch movies online.  
It includes user management, movie catalogs, ratings, reviews, shopping carts, orders, payments, and admin functionality.

---

## 📖 Overview

**Online Cinema** is a digital platform where users can explore, purchase, and watch movies online.  
It offers personalized recommendations, advanced filtering, and a secure payment process.

### 🔹 Highlights
- User registration with email activation and JWT authentication  
- Movie catalog with genres, directors, and actors  
- Shopping cart and secure payment integration  
- Admin and moderator dashboards for management  

---

## 🚀 Features

### 👤 User Features
- Register with email verification  
- Login/logout with JWT tokens (access & refresh)  
- Password reset and change with validation  
- Browse, search, filter, and sort movies  
- Like/dislike movies and leave comments  
- Add to favorites  
- View genres and movies by genre  
- Rate movies on a 10-point scale  
- Manage cart and purchase movies  
- View order and payment history  

### 🛠 Moderator Features
- CRUD for movies, genres, stars, and directors  
- Manage user carts and orders  
- Prevent deletion of purchased movies  

### 🧑‍💼 Admin Features
- Manage all users and groups  
- Manually activate accounts  
- Full access to orders, payments, and movie catalog  

---

## 🧱 Database Structure

### 🧍 Accounts
- **User** – stores user data, hashed password, activation status, and group  
- **UserProfile** – optional details (name, avatar, gender)  
- **UserGroup** – defines roles (USER, MODERATOR, ADMIN)  
- **ActivationToken / PasswordResetToken / RefreshToken** – manage user authentication flows  

### 🎥 Movies
- **Movie** – includes UUID, title, year, duration, IMDb rating, metascore, gross, description, price, certification  
- **Genre, Star, Director, Certification** – related entities  
- Many-to-many relationships: `movie_genres`, `movie_stars`, `movie_directors`  

### 🛒 Shopping Cart
- **Cart** – one per user  
- **CartItem** – unique movie items per cart  

### 📦 Orders
- **Order** – includes multiple movies, total price, and status  
- **OrderItem** – links movies to orders, stores historical price  

### 💳 Payments
- **Payment** – tracks order payments (successful, canceled, refunded)  
- **PaymentItem** – links individual order items to payments  

---

## ⚙️ Tech Stack

| Component | Technology |
|------------|-------------|
| Backend | FastAPI |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Database | PostgreSQL |
| Queue | Celery + Celery Beat |
| Cache | Redis |
| Containerization | Docker, Docker Compose |
| Mail | Mailhog (development) |
| Payments | Stripe |

---

## 🧩 Installation

```bash
# 1️⃣ Clone the repository
git clone https://github.com/yourusername/fastapi-online-cinema.git
cd fastapi-online-cinema

# 2️⃣ Copy and edit environment file
cp .env.example .env

# 3️⃣ Start Docker containers
docker-compose up --build
