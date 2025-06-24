# Deployment Guide for Attendance Tracker

## Option 1: Deploy to Heroku (Recommended)

### Prerequisites
1. Install Git: https://git-scm.com/
2. Install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli
3. Create a Heroku account: https://signup.heroku.com/

### Step-by-Step Deployment

1. **Login to Heroku**
   ```bash
   heroku login
   ```

2. **Create a new Heroku app**
   ```bash
   heroku create your-attendance-tracker
   ```

3. **Add PostgreSQL database**
   ```bash
   heroku addons:create heroku-postgresql:mini
   ```

4. **Set environment variables**
   ```bash
   heroku config:set SECRET_KEY="your-super-secret-key-here"
   ```

5. **Deploy the app**
   ```bash
   git add .
   git commit -m "Initial deployment"
   git push heroku main
   ```

6. **Run database migrations**
   ```bash
   heroku run python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
   ```

7. **Open the app**
   ```bash
   heroku open
   ```

### Access from Your Phone

Once deployed, you can access the app from your phone by:
1. Opening your phone's browser
2. Going to: `https://your-attendance-tracker.herokuapp.com`
3. Logging in with your teacher credentials

## Option 2: Local Network Access (Alternative)

If you prefer to keep it on your local network:

### 1. Find Your Router's External IP
- Go to https://whatismyipaddress.com/
- Note your external IP address

### 2. Configure Port Forwarding
1. Access your router's admin panel (usually 192.168.1.1)
2. Find "Port Forwarding" settings
3. Add a rule:
   - External Port: 5000
   - Internal IP: Your computer's IP
   - Internal Port: 5000
   - Protocol: TCP

### 3. Configure Firewall
1. Open Windows Firewall
2. Allow Python/Flask through the firewall
3. Allow port 5000

### 4. Access from Phone
- Use: `http://YOUR_EXTERNAL_IP:5000`
- Example: `http://203.45.67.89:5000`

## Security Considerations

### For Heroku Deployment:
- ✅ HTTPS automatically enabled
- ✅ Database is secure and backed up
- ✅ No need to expose your home network
- ✅ Can set up authentication for additional security

### For Local Network:
- ❌ Exposes your home network
- ❌ Requires static IP or dynamic DNS
- ❌ Less secure than cloud deployment
- ⚠️ Consider VPN for additional security

## Recommended: Heroku Deployment

I recommend the Heroku deployment because:
1. **Security**: Your home network stays private
2. **Reliability**: 99.9% uptime guarantee
3. **Ease of use**: No router configuration needed
4. **Scalability**: Can handle multiple users
5. **Backup**: Database automatically backed up

## Next Steps

1. Choose your deployment method
2. Follow the step-by-step guide
3. Test access from your phone
4. Set up any additional security measures

Would you like me to help you with any specific part of the deployment process? 