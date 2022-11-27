from flask import Flask, request, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy
import uuid
import os

import collector

collector.collector()

app = Flask(__name__)

DEV_USER = os.environ.get('DEV_CLOUD_SQL_USERNAME')
DEV_PASSWORD = os.environ.get('DEV_CLOUD_SQL_PASSWORD')
DEV_DATABASE = os.environ.get('DEV_CLOUD_SQL_DATABASE_NAME')
DEV_CONNECTION_NAME = os.environ.get('DEV_CLOUD_SQL_CONNECTION_NAME')

DEV_SQLALCHEMY_DATABASE_URI = (
    'mysql+pymysql://{user}:{password}@localhost/{database}'
    '?unix_socket=/cloudsql/{connection_name}').format(
        user=DEV_USER, password=DEV_PASSWORD,
        database=DEV_DATABASE, connection_name=DEV_CONNECTION_NAME)


if os.environ.get ('GAE_INSTANCE'):
    app.config['SQLALCHEMY_DATABASE_URI'] = DEV_SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///vaccinations.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# User ORM for SQLAlchemy
class Country(db.Model):
    id = db.Column(db.String(500), primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    advised = db.Column(db.String(250), nullable=False)
    consideration = db.Column(db.String(250), nullable=False)
    selectively_advised = db.Column(db.String(250), nullable=False)
    yellow_fever_cert_required = db.Column(db.Boolean, nullable=False)
    yellow_fever_information = db.Column(db.String(500), nullable=False)
    general_information = db.Column(db.String(500), nullable=False)

    def to_dict(self):
        # Use Dictionary Comprehension
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


@app.route("/countries", methods=["GET"])
def get_all_countries():
    all_countries = db.session.query(Country).all()
    return jsonify(countries=[country.to_dict() for country in all_countries])

@app.route("/search", methods=["GET"])
def get_by_country():
    query_country = request.args.get("ctry")
    country = db.session.query(Country).filter_by(name=query_country).first()
    if country:
        return jsonify(country=country.to_dict())
    else:
        return jsonify(error={"Not Found": "Sorry, we don't have a that country."})

@app.route("/add", methods=["POST"])
def add_country():
    new_country = Country(
        id=str(uuid.uuid4()),
        name=request.form.get("name"),
        advised=request.form.get("advised"),
        consideration=request.form.get("consideration"),
        selectively_advised=request.form.get("selectively_advised"),
        yellow_fever_cert_required=bool(request.form.get("yellow_fever_cert_required")),
        yellow_fever_information=request.form.get("yellow_fever_information"),
        general_information=request.form.get("general_information")
    )

    db.session.add(new_country)
    db.session.commit()
    return jsonify(response={"success": "Successfully added the new country."})

if __name__ == "__main__":
    app.run()
