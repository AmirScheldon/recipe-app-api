# 🧑‍🍳 Recipe API

A full-featured backend API for managing recipes, including support for user accounts, tagging, image uploads, and advanced filtering. Built with **Django**, **Django REST Framework**, and **Docker**, with **GitHub Actions** for continuous integration and unit testing.

---

## 🚀 Features

- ✅ **Dockerized setup** for easy local development and deployment
- 🔐 **User authentication** (Token-based) and account management
- 🍽️ **Create and manage recipes** with:
  - Ingredients
  - Tags
- 📅 **Image upload support** for ingredients
- 🔍 **Filtering** recipes by tags, ingredients, etc.
- 📦 **CI/CD with GitHub Actions**
- 🧪 **Extensive unit tests** for robustness

---

## 📸 Integration with Images

You can upload and associate images with individual ingredients. The API handles image uploads, stores them, and serves the URLs for front-end use.

---

## ⚙️ Tech Stack

- Python
- Django & Django REST Framework
- Docker & Docker Compose
- PostgreSQL
- GitHub Actions (CI/CD)

---

## 🚧 Setup Instructions

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-username/recipe-api.git
   cd recipe-api
   ```

2. **Run with Docker**

   ```bash
   docker-compose up --build
   ```

   Or if you just want to start it without rebuilding:

   ```bash
   docker-compose up
   ```

3. **Run tests**

   ```bash
   docker-compose run app sh -c "python manage.py test"
   ```
