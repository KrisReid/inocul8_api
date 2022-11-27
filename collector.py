from flask import Flask, request, make_response, jsonify
import requests
from bs4 import BeautifulSoup
import data

def collector():
    for country in data.countries:
        get_data(country.get("endpoint"))

def get_data(country):
    response = requests.get(f"https://www.fitfortravel.nhs.uk/destinations/{country}")

    page = response.text
    soup = BeautifulSoup(page, "html.parser")

    vax_list = []

    vaccination = soup.find(id="maincontent")
    maincontent = vaccination.select("ul")
    unordered_list = maincontent[4].text
    split_list = unordered_list.splitlines()

    for item in split_list:
        vax_list.append(item.strip())
    vax_list = list(filter(None, vax_list))

    new_country = Country(
        id=str(uuid.uuid4()),
        name=country_name[1],
        advised=vax_list[2],
        consideration=vax_list[4],
        selectively_advised=vax_list[6],
        yellow_fever_cert_required=True if vax_list[
                                               7] == "No yellow fever vaccination certificate required for this country." else False,
        yellow_fever_information=vax_list[7],
        general_information=vax_list[0],
    )

    db.session.add(new_country)
    db.session.commit()
    return jsonify(response={"success": "Successfully added the new country."})