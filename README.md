# Attendance Tracker

A Flask-based martial arts attendance management system with student profiles, belt tracking, and monthly attendance summaries.

## Features

- **Student List with Belt Color Icons**: Visual belt level indicators with clickable rows
- **Student Profiles**: Detailed student information with 12-month attendance history
- **Teacher/Student Role Management**: Separate dashboards for teachers and students
- **Monthly Attendance Tracking**: Present, absent, and late status tracking
- **Responsive Design**: Bootstrap-based UI that works on all devices

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- Git (for version control)

### Local Development Setup

1. **Clone or navigate to the project directory**
   ```bash
   cd attendance-tracker
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application**
   - **Option 1**: Use the batch file (Windows)
     ```bash
     start_local_server.bat
     ```
   - **Option 2**: Run directly
     ```bash
     python app.py
     ```

6. **Access the application**
   - Local: http://127.0.0.1:5000/
   - Network: http://[your-ip]:5000/

## Version Control Guidelines

### Git Workflow

1. **Before making changes**
   ```bash
   git status  # Check current status
   git pull    # Get latest changes (if using remote)
   ```

2. **Make your changes**
   - Edit files as needed
   - Test your changes locally

3. **Commit your changes**
   ```bash
   git add .                    # Stage all changes
   git commit -m "Description"  # Commit with descriptive message
   ```

4. **Push to remote (if using GitHub/GitLab)**
   ```bash
   git push origin main
   ```

### Commit Message Guidelines

Use descriptive commit messages:
- ✅ `"Add student profile page with attendance summary"`
- ✅ `"Fix belt color display in student list"`
- ✅ `"Update requirements.txt for new dependencies"`
- ❌ `"fix stuff"`
- ❌ `"update"`

### Branch Strategy (Optional)

For larger projects, consider using branches:
```bash
git checkout -b feature/new-feature    # Create feature branch
git checkout -b bugfix/fix-issue       # Create bugfix branch
git checkout main                      # Return to main branch
git merge feature/new-feature          # Merge feature branch
```

## Project Structure

```
attendance-tracker/
├── app.py                    # Main Flask application
├── requirements.txt          # Python dependencies
├── start_local_server.bat    # Windows startup script
├── .gitignore               # Git ignore rules
├── README.md                # This file
├── instance/                # Instance-specific files (ignored by Git)
└── venv/                    # Virtual environment (ignored by Git)
```

## Database

The application uses SQLite for local development and PostgreSQL for production (Heroku).

### Local Database
- File: `instance/app.db` (created automatically)
- Tables: `user`, `attendance`

### Production Database
- Platform: Heroku Postgres
- Environment variable: `DATABASE_URL`

## Deployment

### Heroku Deployment
1. Create a Heroku app
2. Add PostgreSQL addon
3. Set environment variables
4. Deploy using Git:
   ```bash
   git remote add heroku https://git.heroku.com/your-app-name.git
   git push heroku main
   ```

## Troubleshooting

### Common Issues

1. **Port already in use**
   - Change port in `app.py`: `app.run(port=5001)`

2. **Database errors**
   - Delete `instance/app.db` and restart the application

3. **Import errors**
   - Ensure virtual environment is activated
   - Run `pip install -r requirements.txt`

4. **Git issues**
   - Check `.gitignore` file
   - Use `git status` to see what's tracked

## Contributing

1. Make changes in a feature branch
2. Test thoroughly
3. Commit with descriptive messages
4. Create a pull request (if using GitHub/GitLab)

## License

This project is for educational and personal use. 