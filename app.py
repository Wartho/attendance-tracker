from flask import Flask, render_template_string
import os

app = Flask(__name__)

# Configuration
if os.environ.get('DATABASE_URL'):
    # Production database (Heroku)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)
else:
    # Development database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_secret_key')

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Attendance Tracker</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 600px; margin: 0 auto; }
            h1 { color: #333; }
            .status { padding: 20px; background: #e8f5e8; border: 1px solid #4caf50; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎉 Attendance Tracker</h1>
            <div class="status">
                <h2>✅ Successfully Deployed!</h2>
                <p>Your attendance tracker app is now running on Heroku.</p>
                <p><strong>URL:</strong> https://attendance-tracker-app-7f35b5ba0406.herokuapp.com/</p>
                <p>Next steps: Add your attendance tracking functionality.</p>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/health')
def health():
    return {'status': 'healthy', 'message': 'Attendance Tracker is running!'}

if __name__ == '__main__':
    app.run(debug=True) 