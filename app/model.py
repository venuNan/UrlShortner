from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class URL(db.Model):
    url_id: str = db.Column( db.String(10), primary_key=True, nullable=False)
    url: str    = db.Column(db.String(2048), nullable=False)
    passkey: str = db.Column(db.String(2048), nullable=False)
    count: int  = db.Column(db.Integer, default=0)
    