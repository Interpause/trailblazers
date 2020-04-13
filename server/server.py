from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.run(port=5000)