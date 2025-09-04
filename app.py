from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from data_models import db
from data_manager import DataManager

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Link database and app
db.init_app(app)

print("TEST")

with app.app_context():
    db.create_all()

manager = DataManager(db)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)