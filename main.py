import importlib.util
import os

# Load the app.py file directly
spec = importlib.util.spec_from_file_location("flask_app", "app.py")
flask_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flask_app)

# Get the app instance
app = flask_app.app

if __name__ == '__main__':
    app.run() 