"""
Entry point for the Tran Gia Phat backend.

Local development:
    python main.py

Production (see README for full instructions), e.g. with gunicorn/waitress:
    gunicorn -w 4 -b 0.0.0.0:8000 "main:app"
"""
from app import create_app
from app.config.settings import config

app = create_app()

if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
