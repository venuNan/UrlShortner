import os
import hashlib
from flask import Flask, redirect, request,jsonify
from redis import StrictRedis
from sqlalchemy.exc import IntegrityError
from .model import db, URL

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///urls.db'
redis = StrictRedis(host="localhost", port=6379, db=0)
db.init_app(app)

@app.route("/shorten", methods = ["POST"])
def shorten():
    data = request.get_json()
    url = data.get("url")
    passkey = data.get("passkey")
    if url and passkey:
        shortened_url = hashlib.shake_128(url.encode()).hexdigest(5)
        entry = URL(url_id=shortened_url, url=url, passkey=passkey)
        try:
            db.session.add(entry)
            db.session.commit()
            return jsonify({"Message": "Successful", "URL_ID":shortened_url}), 201
        except IntegrityError:
            db.session.rollback()
            return jsonify({"Error": "Short URL already exists"}), 409
        except Exception:
            return jsonify({"Error": f"Internal server Error"}), 500
    else:
        return jsonify({"Error": "Missing required data"}), 400
   

@app.route("/url/<string:short_url>", methods=["GET"])
def redirect(short_url:str):
    try:
        main_url = redis.get(short_url)
        if not main_url:
            smt = db.select(URL).where(URL.url_id == short_url)
            url = db.session.execute(smt).first()
            if url:
                redis.set(short_url, url[0].url, ex=1800)
                return jsonify({"Message":"Successfull", "URL":url[0].url}), 200
            else:
                return jsonify({"Error": "URL doesnt exist"}), 404
        else:
            smt = db.update(URL).where(URL.url_id == short_url).values(count = URL.count+1)
            db.session.execute(smt)
            db.session.commit()
            return jsonify({"Message":"Successfull", "URL":main_url.decode()}), 200
    except Exception:
        return jsonify({"Error": "Internal Server Error"}), 500

@app.route("/delete", methods=["DELETE"])
def delete():
    data = request.get_json()
    short_url: str = data.get("short_url")
    passkey: str = data.get("passkey")
    if short_url and passkey:
        try:
            smt = db.delete(URL).where(URL.passkey == passkey, URL.url_id == short_url)
            result = db.session.execute(smt)
            db.session.commit()
            if result.rowcount > 0:
                if key:=redis.get(short_url):
                    redis.delete(short_url)
                return jsonify({"Message": f"{key.decode()} deleted successfully"}), 200
            else:
                if key:=redis.get(short_url):
                    redis.delete(short_url)
                return jsonify({"Message": "URL doesnt exist."}), 404
            
        except Exception:
            return jsonify({"Error": "Internal Server Error"}), 500
    else:
        return jsonify({"Error": "Missing Required Fields"}), 401


with app.app_context():
    db.create_all()