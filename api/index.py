import sys
import os

# Add project root directory to sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from wsgi import app

# Expose WSGI application object for Vercel Serverless Functions
app = app

if __name__ == "__main__":
    app.run()
