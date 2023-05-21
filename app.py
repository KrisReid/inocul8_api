from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import os
import datetime
from aws_secrets import get_aws_secrets

app = Flask(__name__)

if os.environ.get("ENV") == "production":
    print("Production")
elif os.environ.get("ENV") == "development":
    secret_data = get_aws_secrets()
    DEV_SQLALCHEMY_DATABASE_URI = ('mysql+pymysql://{user}:{password}@{host}:3306/{database}').format(
        user=secret_data['username'],
        password=secret_data['password'],
        host=secret_data['host'],
        database=secret_data['dbname']
    )
    app.config['SQLALCHEMY_DATABASE_URI'] = DEV_SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
else:
    LOCAL_SQLALCHEMY_DATABASE_URI = ('mysql+pymysql://{user}:{password}@{host}:3306/{database}').format(
        user=os.environ.get('LOCAL_USER'),
        password=os.environ.get('LOCAL_PASSWORD'),
        host=os.environ.get('LOCAL_HOST'),
        database=os.environ.get('LOCAL_DATABASE')
    )
    app.config['SQLALCHEMY_DATABASE_URI'] = LOCAL_SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

for k,v in os.environ.items():
    print(k,v)

db = SQLAlchemy(app)

# User ORM for SQLAlchemy
class Countries(db.Model):
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


@app.route('/')
def home():
    # Every render_template has a logged_in variable set.
    return render_template("index.html")

@app.route("/countries", methods=["GET"])
def get_all_countries():
    all_countries = db.session.query(Countries).all()
    return jsonify([country.to_dict() for country in all_countries])


@app.route("/search", methods=["GET"])
def get_by_country():

    country_array = request.args.get("ctry").split(",")
    countries = []

    for ctry in country_array:
        country = db.session.query(Countries).filter_by(name=ctry).first()
        if country:
            object = jsonify(country.to_dict())
            countries.append(object.json)
        else:
            return jsonify(error={"Not Found": f"Sorry, {ctry} is a country we could not find. Ensure spelling is correct"})

    return jsonify(countries)


@app.route("/add", methods=["POST"])
def add_country():
    new_country = Countries(
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

def validate_date_format(date):
    try:
        if date != datetime.datetime.strptime(date, "%Y-%m").strftime('%Y-%m'):
            raise ValueError
        return True
    except ValueError:
        return False


@app.route("/validate", methods=["GET"])
def validate_country():
    query_country = request.args.get("country")
    country = db.session.query(Countries).filter_by(name=query_country).first()
    if not country:
        return jsonify(error={"Not Found": f"Sorry, we can't find {query_country} as a country."})
    selected_country = jsonify(country.to_dict())
    country_json = selected_country.json

    # Parse all the lists
    advised_list = parse_country_list(country_json['advised'])
    consideration_list = parse_country_list(country_json['consideration'])
    selectively_advised_list = parse_country_list(country_json['selectively_advised'])
    # print(selectively_advised_list)

    # do any of my vaccinations exist in any of the above lists?
    destination_list = parse_destination_list(request.args.get("vaccinations"))
    # print(destination_list)

    # Receive the travel date
    travel_date = validate_date_format(request.args.get("travel_date"))

    if not travel_date:
        return jsonify(error={"Date Error": f"Sorry, {request.args.get('travel_date')} is not an excepted date format. Please use YYYY-MM."})
    else:
        travel_date = request.args.get("travel_date")

    advised_object = create_partial_vaccination_object(destination_list, advised_list, travel_date)
    consideration_object = create_partial_vaccination_object(destination_list, consideration_list, travel_date)
    selectively_advised_object = create_partial_vaccination_object(destination_list, selectively_advised_list, travel_date)

    # Restructure the response and return to the user
    response = {
        "advised" : advised_object,
        "consideration" : consideration_object,
        "general_information" : country_json["general_information"],
        "id": country_json["id"],
        "name": country_json["name"],
        "selectively_advised": selectively_advised_object,
        "yellow_fever_cert_required": country_json["yellow_fever_cert_required"],
        "yellow_fever_information": country_json["yellow_fever_information"]
    }

    if response:
        return jsonify([response])
    else:
        return jsonify(error={"Error": "Sorry, we have experienced an issue."})


if __name__ == "__main__":
    app.run(host='0.0.0.0')
