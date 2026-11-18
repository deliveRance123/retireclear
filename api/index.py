import sys
import os

# Add root repository directory to Python path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from wsgi import app

# Vercel Serverless Function entry point
if __name__ == "__main__":
    app.run()
