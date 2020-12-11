from constants import ANIMALS, CLIENT_ID, ICEBERGS
from flask import jsonify, make_response, request
from google.auth.transport import requests
from google.oauth2 import id_token


def animal_output(animal, client):
    if animal["home"] is not None:
        iceberg_key = client.key(ICEBERGS, int(animal["home"]))
        animal_home = client.get(key=iceberg_key)
        home_id = str(animal["home"])
        home_info = {"id": home_id,
                     "name": animal_home["name"],
                     "self": (request.url_root + "icebergs/" + home_id)}
    else:
        home_info = animal["home"]
    return {"id": str(animal.id),
            "name": animal["name"],
            "species": animal["species"],
            "height": animal["height"],
            "home": home_info,
            "self": request.url_root + "animals/" + str(animal.id)}


def iceberg_output(iceberg, client):
    inhabitants = []
    if iceberg["inhabitants"] is not None:
        for animal_key in iceberg["inhabitants"]:
            this_key = client.key(ANIMALS, int(animal_key))
            this_animal = client.get(key=this_key)
            animal_id = str(this_animal.id)
            result = {"id": animal_id,
                      "name": this_animal["name"],
                      "self": (request.url_root + "animals/" + animal_id)}
            inhabitants.append(result)
    return {"id": str(iceberg.id),
            "name": iceberg["name"],
            "area": iceberg["area"],
            "shape": iceberg["shape"],
            "inhabitants": inhabitants,
            "public": iceberg["public"],
            "founder": iceberg["founder"],
            "self": request.url_root + "icebergs/" + str(iceberg.id)}


def status_fail(code, msg, header=None):
    response = make_response(jsonify(Error=msg))

    if header is not None:
        response.headers["Allow"] = header

    response.mimetype = "application/json"
    response.status_code = code
    return response


def status_success(code, output=None, mime="application/json",
                   location=None, page=None):
    response = make_response() if output is None else make_response(output)

    if location is not None:
        response.headers.set("Location", location)
    if page is not None:
        response.headers.set("Next", page)

    response.headers.set("Content-Type", mime)
    response.mimetype = mime
    response.status_code = code
    return response


def valid_alphanum(val: str, range: int) -> bool:
    return (len(val) <= range) and (val.replace(' ', '').isalnum())


def valid_int(val, range: int) -> bool:
    return (type(val) is int) and (val <= range)


def valid_public(val) -> bool:
    return isinstance(val, bool)


def valid_shape(val: str) -> bool:
    shapes = ["tabular", "dome", "pinnacle", "wedge", "dry-dock", "blocky"]
    return val.lower() in shapes


def verify_jwt() -> str:
    try:
        # 7:: because jwt begins with "Bearer\n"
        jwt = str(request.headers["Authorization"])[7::]
        req = requests.Request()
        id_info = id_token.verify_oauth2_token(jwt, req, CLIENT_ID)
        return str(id_info["sub"])
    except (KeyError, ValueError):
        return "Error"
