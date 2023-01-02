import json
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import uuid
import os

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
    return jsonify([country.to_dict() for country in all_countries])
    # return jsonify(countries=[country.to_dict() for country in all_countries])


@app.route("/search", methods=["GET"])
def get_by_country():

    country_array = request.args.get("ctry").split(",")
    countries = []

    for ctry in country_array:
        country = db.session.query(Country).filter_by(name=ctry).first()
        if country:
            object = jsonify(country.to_dict())
            countries.append(object.json)
        else:
            return jsonify(error={"Not Found": f"Sorry, {ctry} is a country we could not find. Ensure spelling is correct"})

    return jsonify(countries)


@app.route("/add", methods=["POST"])
def add_country():
    new_country = Country(
        id=request.form.get("id"),
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


def parse_country_list(text):
    final_list = []
    remove_fullstop = text[:-1]
    list = remove_fullstop.split(";")

    for item in list:
        k = item.strip()
        final_list.append(k)

    return final_list

def parse_destination_list(text):
    final_list = []
    for vaccination in text.split(","):
        b = vaccination.split(":")
        final_list.append(b)
    return final_list


def create_partial_vaccination_object(destination_list, severity_list, travel_date):
    object = {}
    # Calculate if the vaccination is covered
    for vaccination in severity_list:
        for destination in destination_list:
            if vaccination in destination[0]:
                if destination[1] >= travel_date:
                    object.update({f"{vaccination}": "valid"})
                else:
                    # don't update the object if it already has been set to valid
                    if vaccination not in object.keys():
                        object.update({f"{vaccination}": "invalid"})
            else:
                # don't update the object if it already has been set to valid
                if vaccination not in object.keys():
                    object.update({f"{vaccination}": "invalid"})

    return object


@app.route("/validate", methods=["GET"])
def validate_country():
    query_country = request.args.get("country")
    country = db.session.query(Country).filter_by(name=query_country).first()
    selected_country = jsonify(country.to_dict())
    country_json = selected_country.json

    print(country_json)

    # Parse all the lists
    advised_list = parse_country_list(country_json['advised'])
    consideration_list = parse_country_list(country_json['consideration'])
    selectively_advised_list = parse_country_list(country_json['selectively_advised'])
    # print(selectively_advised_list)

    # do any of my vaccinations exist in any of the above lists?
    destination_list = parse_destination_list(request.args.get("vaccinations"))
    # print(destination_list)

    # Receive the travel date
    travel_date = request.args.get("travel_date")

    advised_object = create_partial_vaccination_object(destination_list, advised_list, travel_date)
    consideration_object = create_partial_vaccination_object(destination_list, consideration_list, travel_date)
    selectively_advised_object = create_partial_vaccination_object(destination_list, selectively_advised_list, travel_date)

    print("----ADVISED OBJECT ----")
    print(advised_object)
    print("----CONSIDERATION OBJECT ----")
    print(consideration_object)
    print("----SELECTIVELY ADVISED OBJECT ----")
    print(selectively_advised_object)


    # Restructure the response and return to the user


    if country:
        return jsonify(country.to_dict())
    else:
        return jsonify(error={"Not Found": "Sorry, we don't have that country."})


if __name__ == "__main__":
    app.run()


# // EXAMPLE REQUEST
# {
#     "country": "United Kingdom",
#     "travel_date": "2022-05",
#     "vaccinations": {
#         "tetanus": "2023-01",
#         "Hepititus A" : "2025-10"
#     }
# }
#
# // EXAMPLE RESPONSE
# {
#         "advised": {
#             "Poliomyelitis" : "Invalid"
#         },
#         "consideration": {
#             "Tetanus": "Valid"
#         },
#         "general_information": "Confirm primary courses and boosters are up to date as recommended for life in Britain - including for example, seasonal flu vaccine (if indicated), MMR, vaccines required for occupational risk of exposure, lifestyle risks and underlying medical conditions.",
#         "id": "669f3f50-9237-4dfa-bc6e-41f849f35083",
#         "name": "United Kingdom",
#         "selectively_advised": {
#             "Hepatitis A": "Valid",
#             "Hepatitis B": "Invalid"
#         },
#         "yellow_fever_cert_required": false,
#         "yellow_fever_information": "No yellow fever vaccination certificate required for this country."
#     }