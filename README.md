# Attendance Tracker

A web-based attendance tracking application built with Flask.

## Development Setup

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- Windows:
```bash
.\venv\Scripts\activate
```
- Unix/MacOS:
```bash
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
flask db upgrade
```

5. Run the development server:
```bash
python run.py
```

The application will be available at http://localhost:5000

## Production Deployment

For production deployment, it's recommended to:

1. Use a production WSGI server like Gunicorn or uWSGI
2. Set up HTTPS using a reverse proxy like Nginx or Apache
3. Use proper SSL certificates from a trusted certificate authority
4. Set appropriate security headers and configurations

Example Nginx configuration for HTTPS:
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Features

- User authentication with role-based access control
- Teacher and student roles
- Attendance tracking and management
- SQLite database for data storage
- QR code generation for students
- QR code scanning for attendance
- Student and teacher dashboards
- Attendance history tracking
- Export attendance data

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- Windows:
```bash
venv\Scripts\activate
```
- Unix/MacOS:
```bash
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

5. Run the application:
```bash
flask run
```

## Project Structure

```
attendance-tracker/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── static/
│   └── templates/
├── instance/
├── migrations/
├── .env
├── .gitignore
├── config.py
├── requirements.txt
└── run.py
```

## Environment Variables

Create a `.env` file in the root directory with the following variables:
```
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
``` 