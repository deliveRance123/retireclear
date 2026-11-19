import sys
import os
import traceback

# Ensure project root directory is on sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Middleware to safely handle Vercel serverless function path rewrites
class VercelPathMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        matched_path = environ.get('HTTP_X_MATCHED_PATH')
        if matched_path:
            if '?' in matched_path:
                matched_path = matched_path.split('?', 1)[0]
            environ['PATH_INFO'] = matched_path
        else:
            path = environ.get('PATH_INFO', '')
            if path.startswith('/api/index.py'):
                environ['PATH_INFO'] = path[len('/api/index.py'):] or '/'
            elif path.startswith('/api/index'):
                environ['PATH_INFO'] = path[len('/api/index'):] or '/'
        return self.wsgi_app(environ, start_response)

try:
    from wsgi import app
    app.wsgi_app = VercelPathMiddleware(app.wsgi_app)
except Exception as e:
    # If app import fails on serverless cold start, surface the exact error instead of generic 500
    from flask import Flask, Response
    app = Flask(__name__)
    err_trace = traceback.format_exc()

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def catch_all(path):
        return Response(
            f"<h2>RetireClear - Serverless Function Diagnostic</h2>"
            f"<p>An error occurred during application initialization:</p>"
            f"<pre style='background:#f4f4f4;padding:15px;border-radius:5px;border:1px solid #ddd;'>{err_trace}</pre>",
            status=500,
            mimetype="text/html"
        )

if __name__ == "__main__":
    app.run()
