# Deployment Guide for Render

## Prerequisites
- GitHub repository with your code
- Render account (free at render.com)

## Steps to Deploy

1. **Push your code to GitHub**
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin master
   ```

2. **Create a Render account**
   - Go to https://render.com
   - Sign up with your GitHub account

3. **Create a new Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the repository

4. **Configure the service**
   - **Name**: attendance-tracker (or your preferred name)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Free

5. **Add Environment Variables**
   - Go to Environment tab
   - Add these variables:
     - `FLASK_ENV`: `production`
     - `SECRET_KEY`: Generate a random secret key

6. **Create Database**
   - Go to "New +" → "PostgreSQL"
   - Create a new PostgreSQL database
   - Copy the Internal Database URL
   - Add it as environment variable: `DATABASE_URL`

7. **Deploy**
   - Click "Create Web Service"
   - Render will automatically deploy your app

## Database Migration
After deployment, you'll need to run database migrations:
- Go to your service's "Shell" tab
- Run: `flask db upgrade`

## Custom Domain (Optional)
- Go to your service settings
- Add your custom domain
- Update DNS records as instructed

## Monitoring
- View logs in the "Logs" tab
- Monitor performance in the "Metrics" tab 