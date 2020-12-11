import json

from flask import Blueprint, request
from google.cloud import datastore
from json2html import json2html

import errors as ERR

from constants import ICEBERGS, ANIMALS
from helpers import animal_output, status_fail, status_success,\
    valid_alphanum, valid_int

bp = Blueprint("animals", __name__, url_prefix="/animals")
client = datastore.Client()


@bp.route('', methods=["POST", "GET"])
def animals_valid():
    # Create an Animal
    if request.method == "POST":
        # Check media type
        if "application/json" not in request.content_type:
            # Failure 415 Unsupported Media Type
            return status_fail(415, ERR.WRONG_MEDIA_RECEIVED)
        if "application/json" not in request.accept_mimetypes:
            # Failure 406 Not Acceptable
            return status_fail(406, ERR.WRONG_MEDIA_REQUESTED)

        # Check if request is missing any of the required attributes
        content = request.get_json()
        if ("name" not in content.keys()
                or "species" not in content.keys()
                or "height" not in content.keys()):
            # Failure 400 Bad Request
            return status_fail(400, ERR.MISSING_ATTRIBUTE)

        # Validate request
        if not valid_alphanum(content["name"], 50):
            # Failure 400 Bad Request
            return status_fail(400, ERR.INVALID_NAME)
        if not valid_alphanum(content["species"], 50):
            # Failure 400 Bad Request
            return status_fail(400, ERR.INVALID_SPECIES)
        if not valid_int(content["height"], 25):
            # Failure 400 Bad Request
            return status_fail(400, ERR.INVALID_HEIGHT)

        # Ensure that the name of an Animal is unique across all Animals
        query = client.query(kind=ANIMALS)
        results = list(query.fetch())
        for a in results:
            if a["name"] == content["name"]:
                # Failure 403 Forbidden
                return status_fail(403, ERR.NAME_EXISTS)

        # Update Animal
        animal = datastore.Entity(key=client.key(ANIMALS))
        animal.update({"name": content["name"],
                       "species": content["species"],
                       "height": content["height"],
                       "home": None})
        client.put(animal)

        # Success 201 Created
        output = animal_output(animal, client)
        return status_success(201, output=json.dumps(output),
                              location=output["self"])

    # List all Animals
    elif request.method == "GET":
        query = client.query(kind=ANIMALS)
        q_limit = int(request.args.get("limit", 5))
        q_offset = int(request.args.get("offset", 0))
        iterator = query.fetch(limit=q_limit, offset=q_offset)
        results = list(next(iterator.pages))

        if iterator.next_page_token:
            next_offset = q_offset + q_limit
            next_url = (request.base_url + "?limit=" + str(q_limit) +
                                           "&offset=" + str(next_offset))
        else:
            next_url = None

        for a in results:
            a["id"] = a.id
            a["self"] = request.url_root + "animals/" + str(a.id)

        output = {"animals": results}
        if next_url:
            output["next"] = next_url
            return status_success(200, output=json.dumps(output),
                                  page=next_url)

        # Success 200 OK
        return status_success(200, output=json.dumps(output))

    else:
        # Failure 405 Method Not Allowed
        animals_invalid()


@bp.route('', methods=["PUT", "PATCH", "DELETE"])
def animals_invalid():
    # Failure 405 Method Not Allowed
    return status_fail(405, ERR.METHOD_INVALID, header="POST, GET")


@bp.route("/<animal_id>", methods=["GET", "PUT", "PATCH", "DELETE"])
def animalid_valid(animal_id):
    animal_key = client.key(ANIMALS, int(animal_id))
    animal = client.get(key=animal_key)

    # No Animal with this animal_id exists
    if animal is None:
        # Failure 404 Not Found
        return status_fail(404, ERR.NO_ANIMAL)

    # Get an Animal
    if request.method == "GET":
        if "application/json" in request.accept_mimetypes:
            # Success 200 OK
            output = animal_output(animal, client)
            return status_success(200, output=json.dumps(output))
        elif "text/html" in request.accept_mimetypes:
            # Success 200 OK
            output = animal_output(animal, client)
            conversion = json2html.convert(json=json.dumps(output))
            return status_success(200, output=conversion, mime="text/html")
        else:
            # Failure 406 Not Acceptable
            return status_fail(406, ERR.WRONG_MEDIA_REQUESTED)

    # Edit an Animal
    elif request.method == "PUT":
        # Check media type
        if "application/json" not in request.content_type:
            # Failure 415 Unsupported Media Type
            return status_fail(415, ERR.WRONG_MEDIA_RECEIVED)
        if "application/json" not in request.accept_mimetypes:
            # Failure 406 Not Acceptable
            return status_fail(406, ERR.WRONG_MEDIA_REQUESTED)

        # Check if request is missing any of the required attributes
        content = request.get_json()
        if ("name" not in content.keys()
                or "species" not in content.keys()
                or "height" not in content.keys()):
            # Failure 400 Bad Request
            return status_fail(400, ERR.MISSING_ATTRIBUTE)

        # Validate request
        if not valid_alphanum(content["name"], 50):
            # Failure 400 Bad Request
            return status_fail(400, ERR.INVALID_NAME)
        if not valid_alphanum(content["species"], 50):
            # Failure 400 Bad Request
            return status_fail(400, ERR.INVALID_SPECIES)
        if not valid_int(content["height"], 25):
            # Failure 400 Bad Request
            return status_fail(400, ERR.INVALID_HEIGHT)

        # Ensure that the name of an Animal is unique across all Animals
        query = client.query(kind=ANIMALS)
        results = list(query.fetch())
        for a in results:
            if a["name"] == content["name"]:
                # Failure 403 Forbidden
                return status_fail(403, ERR.NAME_EXISTS)

        # Update Animal
        animal = datastore.Entity(key=client.key(ANIMALS))
        animal.update({"name": content["name"],
                       "species": content["species"],
                       "height": content["height"]})
        client.put(animal)

        # Success 303 See Other
        output = animal_output(animal, client)
        return status_success(303, output=json.dumps(output),
                              location=output["self"])

    # Edit an Animal
    elif request.method == "PATCH":
        # Check media type
        if "application/json" not in request.content_type:
            # Failure 415 Unsupported Media Type
            return status_fail(415, ERR.WRONG_MEDIA_RECEIVED)
        if "application/json" not in request.accept_mimetypes:
            # Failure 406 Not Acceptable
            return status_fail(406, ERR.WRONG_MEDIA_REQUESTED)

        # Check if request contains any of the object attributes
        content = request.get_json()
        if "name" in content.keys():
            # Validate name
            if not valid_alphanum(content["name"], 50):
                # Failure 400 Bad Request
                return status_fail(400, ERR.INVALID_NAME)
            # Ensure that the name of an Animals is unique across all Animals
            query = client.query(kind=ANIMALS)
            results = list(query.fetch())
            for a in results:
                if a["name"] == content["name"]:
                    # Failure 403 Forbidden
                    return status_fail(403, ERR.NAME_EXISTS)
            animal.update({"name": content["name"]})
        if "species" in content.keys():
            # Validate species
            if not valid_alphanum(content["species"], 50):
                # Failure 400 Bad Request
                return status_fail(400, ERR.INVALID_SPECIES)
            animal.update({"species": content["species"]})
        if "height" in content.keys():
            # Validate height
            if not valid_int(content["height"], 25):
                # Failure 400 Bad Request
                return status_fail(400, ERR.INVALID_HEIGHT)
            animal.update({"height": content["height"]})
        client.put(animal)

        # Success 303 See Other
        output = animal_output(animal, client)
        return status_success(303, output=json.dumps(output),
                              location=output["self"])

    # Delete an Animal
    elif request.method == "DELETE":
        iceberg_id = animal["home"]
        iceberg_key = client.key(ICEBERGS, int(iceberg_id))
        iceberg = client.get(key=iceberg_key)

        if iceberg:
            if str(animal_id) in iceberg["inhabitants"]:
                iceberg["inhabitants"].remove(str(animal_id))
                client.put(iceberg)

        # Success 204 No Content
        client.delete(animal_key)
        return status_success(204)

    else:
        # Failure 405 Method Not Allowed
        animalid_invalid()


@bp.route("/<animal_id>", methods=["POST"])
def animalid_invalid(animal_id):
    # Failure 405 Method Not Allowed
    return status_fail(405, ERR.METHOD_INVALID,
                       header="GET, PUT, PATCH, DELETE")
