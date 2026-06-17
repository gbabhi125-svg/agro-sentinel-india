import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

# Import Flask app
from backend.app import app

if __name__ == "__main__":
    app.run()