# 🛠️ Core Django Project

This is a Django-based web application project configured for REST APIs, JWT authentication, GraphQL support, email services, cloud storage (via MinIO/S3), and a Redis-backed caching system.

---

## 📁 Project Structure

```
core/
├── core/               # Django settings and main URL config
├── users/              # Custom user app
├── product/            # Product-related models and logic
├── business/           # Business logic and models
├── templates/          # HTML templates
├── static/             # Static files (CSS/JS/images)
├── media/              # Media uploads
├── public/static/      # Collected static files for deployment
└── logs/               # Application logs
```

---

## 🚀 Features

- 🔐 JWT Authentication (`rest_framework_simplejwt`)
- 🌐 GraphQL API via `graphene-django`
- 📦 Cloud Storage with MinIO / AWS S3 support
- 📮 SMTP Email Support
- 🧠 Object-Level Permissions via `django-guardian`
- ⚙️ Custom User Model
- 🔍 Swagger/OpenAPI Docs (`drf_yasg`)
- 🔄 Redis Caching
- 🌍 CORS Enabled
- ⏳ Session Expiry Configurable
- 🔐 Secure Environment with `.env` support via `python-decouple`

---

## 📦 Installed Applications

### Core Django Apps
- `django.contrib.admin`
- `django.contrib.auth`
- `django.contrib.sessions`
- `django.contrib.staticfiles`
- etc.

### Project Apps
- `users`
- `product`
- `business`

### Third-Party Libraries
- `djangorestframework`
- `corsheaders`
- `drf_yasg`
- `simplejwt` with token blacklist
- `django_extensions`
- `simple_history`
- `graphene_django`
- `django_cleanup`
- `storages`

---

## 🔧 Environment Variables (`.env`)

Make sure to set the following variables in a `.env` file:

```env
SECRET_KEY=your_secret_key
DEBUG=True
DB_ENGINE=django.db.backends.postgresql
DB_NAME=your_db
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

EMAIL_HOST=smtp.yourprovider.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=you@example.com
EMAIL_HOST_PASSWORD=your_password
DEFAULT_FROM_EMAIL=you@example.com
SERVER_EMAIL=server@example.com

DEFAULT_FILE_STORAGE=storages.backends.s3boto3.S3Boto3Storage
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_STORAGE_BUCKET_NAME=bucket-name
AWS_S3_ENDPOINT_URL=http://localhost:9000
AWS_S3_SECURE_URLS=True
AWS_DEFAULT_ACL=False

TIME_ZONE=Asia/Kolkata
MEDIA_URL=/media/
MEDIA_ROOT=media/
REDIS_CACHE_URL=redis://localhost:6379/1

CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

SESSION_EXPIRY_TIME=3600

RAZORPAY_KEY_ID=your_razorpay_key
RAZORPAY_KEY_SECRET=your_razorpay_secret
```

---

## 🧪 Running the Project

```bash
# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Apply static
python manage.py collectstatic

# Run development server
python manage.py runserver
```

---

## 📜 API Documentation

- Swagger UI available at: `/swagger/`
- GraphQL endpoint available at: `/graphql/`

---

## 📬 Email Configuration

The project supports SMTP-based email sending, defined in `settings.py`. Configure the `.env` file as shown above to enable.

---

## 📦 Storage Configuration (MinIO / AWS S3)

The app supports MinIO or S3-compatible file storage using `django-storages`. Required credentials and URLs must be added to `.env`.

---

## 🔐 JWT Authentication

This project uses **Simple JWT** with the following lifetime settings:

- Access token: `1 day`
- Refresh token: `7 days`

---

## 🧠 Logging

Logs are written to:
```
logs/app.log
```
Log format includes timestamp, path, line number, thread, and message level.

---

## 🧵 Customizations

- Custom User model: `users.CustomUser`
- JWT Auth integrated with custom class: `core.custom_auth.CustomJWTAuthentication`
- Custom Swagger Schema: `base.models.CustomAutoSchema`
- Redis caching for improved performance

---

## ✅ Deployment Notes

- Set `DEBUG=False` in production.
- Restrict `ALLOWED_HOSTS`.
- Configure proper email & storage backends.
- Use HTTPS and secure secrets in production.