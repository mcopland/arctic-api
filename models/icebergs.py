import json

from flask import Blueprint, request
from google.cloud import datastore
from json2html import json2html

import errors as ERR

from constants import ANIMALS, ICEBERGS
from helpers import iceberg_output, status_fail, status_success,\
    valid_alphanum, valid_int, valid_public, valid_shape, verify_jwt

bp = Blueprint("icebergs", __name__, url_prefix="/icebergs")
client = datastore.Client()


@bp.route('', methods=["POST", "GET"])
def icebergs_valid():
    # Create an Iceberg
    if request.method == "POST":
        # Verify user
        user = verify_jwt()
        if user == "Error":
            return status_fail(401, ERR.UNAUTHORIZED)

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
                or "area" not in content.keys()
                or "shape" not in content.keys()
                or "public" not in content.keys()):
            # Failure 400 Bad Request
            return status_fail(400, ERR.MISSING_ATTRIBUTE)

        # Validate request
        if not valid_alphanum(content["name"], 50):
            # Failure 400 Bad Request
            return status_fail(400, ERR.INVALID_NAME)
        if not valid_int(content["area"], 8000):
            # Failure 400 Bad Request
            return status_fail(400, ERR.INVALID_AREA)
        if not valid_shape(content["shape"]):
            # Failure 400 Bad Request
            return status_fail(400, ERR.INVALID_SHAPE)
        if not valid_public(content["public"]):
            # Failure 400 Bad Request
            return status_fail(400, ERR.INVALID_PUBLIC)

        # Ensure that the name of an Iceberg is unique across all Icebergs
        query = client.query(kind=ICEBERGS)
        results = list(query.fetch())
        for i in results:
            if i["name"] == content["name"]:
                # Failure 403 Forbidden
                return status_fail(403, ERR.NAME_EXISTS)

        # Update Iceberg
        iceberg = datastore.Entity(key=client.key(ICEBERGS))
        iceberg.update({"name": content["name"],
                        "area": content["area"],
                        "shape": content["shape"],
                        "inhabitants": None,
                        "public": content["public"],
                        "founder": user})
        client.put(iceberg)

        # Success 201 Created
        output = iceberg_output(iceberg, client)
        return status_success(201, output=json.dumps(output),
                              location=output["self"])

    # List all Icebergs
    elif request.method == "GET":
        if "application/json" not in request.accept_mimetypes:
            # Failure 406 Not Acceptable
            return status_fail(406, ERR.WRONG_MEDIA_REQUESTED)

        # Display Icebergs with pagination
        query = client.query(kind=ICEBERGS)
        user = verify_jwt()

        if user == "Error":
            # Return all public Icebergs
            query = query.add_filter("public", '=', True)
        else:
            # Return all Icebergs whose founder matches the user
            query = query.add_filter("founder", '=', user)

        # Set limit, offset, and iterator
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

        for i in results:
            i["id"] = i.id
            i["self"] = request.url_root + "icebergs/" + str(i.id)

        output = {"icebergs": results}
        if next_url:
            output["next"] = next_url
            return status_success(200, output=json.dumps(output),
                                  page=next_url)

        # Success 200 OK
        return status_success(200, output=json.dumps(output))

    else:
        # Failure 405 Method Not Allowed
        icebergs_invalid()


@bp.route('', methods=["PUT", "PATCH", "DELETE"])
def icebergs_invalid():
    # Failure 405 Method Not Allowed
    return status_fail(405, ERR.METHOD_INVALID, header="POST, GET")


@bp.route("/<iceberg_id>", methods=["GET", "PUT", "PATCH", "DELETE"])
def icebergid_valid(iceberg_id):
    iceberg_key = client.key(ICEBERGS, int(iceberg_id))
    iceberg = client.get(key=iceberg_key)

    # No Iceberg with this iceberg_id exists
    if iceberg is None:
        # Failure 404 Not Found
        return status_fail(404, ERR.NO_ICEBERG)

    # Verify user
    user = verify_jwt()
    if user == "Error":
        return status_fail(401, ERR.UNAUTHORIZED)

    # Get an Iceberg
    if request.method == "GET":
        if iceberg["founder"] != user and iceberg["public"] is False:
            return status_fail(403, ERR.NO_PERMISSION)

        if "application/json" in request.accept_mimetypes:
            # Success 200 OK
            output = iceberg_output(iceberg, client)
            return status_success(200, output=json.dumps(output))
        elif "text/html" in request.accept_mimetypes:
            # Success 200 OK
            output = iceberg_output(iceberg, client)
            conversion = json2html.convert(json=json.dumps(output))
            return status_success(200, output=conversion, mime="text/html")
        else:
            # Failure 406 Not Acceptable
            return status_fail(406, ERR.WRONG_MEDIA_REQUESTED)

    # Edit an Iceberg
    elif request.method == "PUT":
        if iceberg["founder"] != user:
            return status_fail(403, ERR.NO_PERMISSION)

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
                or "area" not in content.keys()
                or "shape" not in content.keys()
                or "public" not in content.keys()):
            # Failure 400 Bad Request
            return status_fail(400, ERR.MISSING_ATTRIBUTE)

        # Validate request
        if not valid_alphanum(content["name"], 50):
            # Failure 400 Bad Request
            return status_fail(400, ERR.INVALID_NAME)
        if not valid_int(content["area"], 8000):
            # Failure 400 Bad Request
            return status_fail(400, ERR.INVALID_AREA)
        if not valid_shape(content["shape"]):
            # Failure 400 Bad Request
            return status_fail(400, ERR.INVALID_SHAPE)
        if not valid_public(content["public"]):
            # Failure 400 Bad Request
            return status_fail(400, ERR.INVALID_PUBLIC)

        # Ensure that the name of an Iceberg is unique across all Icebergs
        query = client.query(kind=ICEBERGS)
        results = list(query.fetch())
        for i in results:
            if i["name"] == content["name"]:
                # Failure 403 Forbidden
                return status_fail(403, ERR.NAME_EXISTS)

        # Update Iceberg
        iceberg.update({"name": content["name"],
                        "area": content["area"],
                        "shape": content["shape"],
                        "public": content["public"]})
        client.put(iceberg)

        # Success 303 See Other
        output = iceberg_output(iceberg, client)
        return status_success(303, output=json.dumps(output),
                              location=output["self"])

    # Edit an Iceberg
    elif request.method == "PATCH":
        if iceberg["founder"] != user:
            return status_fail(403, ERR.NO_PERMISSION)

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
            # Ensure that the name of an Iceberg is unique across all Icebergs
            query = client.query(kind=ICEBERGS)
            results = list(query.fetch())
            for i in results:
                if i["name"] == content["name"]:
                    # Failure 403 Forbidden
                    return status_fail(403, ERR.NAME_EXISTS)
            iceberg.update({"name": content["name"]})
        if "area" in content.keys():
            # Validate area
            if not valid_int(content["area"], 8000):
                # Failure 400 Bad Request
                return status_fail(400, ERR.INVALID_AREA)
            iceberg.update({"area": content["area"]})
        if "shape" in content.keys():
            # Validate shape
            if not valid_shape(content["shape"]):
                # Failure 400 Bad Request
                return status_fail(400, ERR.INVALID_SHAPE)
            iceberg.update({"shape": content["shape"]})
        if "public" in content.keys():
            # Validate public
            if not valid_public(content["public"]):
                # Failure 400 Bad Request
                return status_fail(400, ERR.INVALID_PUBLIC)
            iceberg.update({"public": content["public"]})
        client.put(iceberg)

        # Success 303 See Other
        output = iceberg_output(iceberg, client)
        return status_success(303, output=json.dumps(output),
                              location=output["self"])

    # Delete an Iceberg
    elif request.method == "DELETE":
        # JWT is valid but iceberg_id is founded by someone else
        if iceberg["founder"] != user:
            return status_fail(403, ERR.NO_PERMISSION)

        # Remove Animals from Iceberg if applicable
        query = client.query(kind=ANIMALS)
        results = list(query.fetch())
        for a in results:
            if a["home"] == iceberg_id:
                a.update({"home": None})
                client.put(a)

        # Success 204 No Content
        client.delete(iceberg_key)
        return status_success(204)

    else:
        # Failure 405 Method Not Allowed
        icebergid_invalid()


@bp.route("/<iceberg_id>", methods=["POST"])
def icebergid_invalid(iceberg_id):
    # Failure 405 Method Not Allowed
    return status_fail(405, ERR.METHOD_INVALID,
                       header="GET, PUT, PATCH, DELETE")


@bp.route("/<iceberg_id>/animals/<animal_id>", methods=["PUT", "DELETE"])
def icebergid_animals_animalid_valid(iceberg_id, animal_id):
    iceberg_key = client.key(ICEBERGS, int(iceberg_id))
    animal_key = client.key(ANIMALS, int(animal_id))
    iceberg = client.get(key=iceberg_key)
    animal = client.get(key=animal_key)

    # Check if Iceberg and Animal exist
    if iceberg is None:
        if animal is None:
            return status_fail(404, ERR.NEITHER_EXISTS)
        return status_fail(404, ERR.NO_ICEBERG)
    if animal is None:
        return status_fail(404, ERR.NO_ANIMAL)

    # Verify user
    user = verify_jwt()
    if user == "Error":
        return status_fail(401, ERR.UNAUTHORIZED)

    # Put an Animal on an Iceberg
    if request.method == "PUT":
        # Check media type
        if "application/json" not in request.content_type:
            # Failure 415 Unsupported Media Type
            return status_fail(415, ERR.WRONG_MEDIA_RECEIVED)

        if animal["home"] is None:
            animal.update({"home": str(iceberg.id)})
        else:
            return status_fail(400, ERR.ANIMAL_ASSIGNED)

        # Add Animal to Iceberg
        if iceberg["inhabitants"] is None:
            iceberg["inhabitants"] = [str(animal.id)]
        else:
            iceberg["inhabitants"].append(str(animal.id))

        client.put(iceberg)
        client.put(animal)

        # Success 303 See Other
        output = iceberg_output(iceberg, client)
        return status_success(303, output=json.dumps(output),
                              location=output["self"])

    # Remove an Animal from an Iceberg
    elif request.method == "DELETE":
        if iceberg["inhabitants"] is None:
            return status_fail(404, ERR.NO_ANIMAL_HERE)

        if "inhabitants" in iceberg.keys():
            if str(animal_id) in iceberg["inhabitants"]:
                iceberg["inhabitants"].remove(str(animal_id))
                if len(iceberg["inhabitants"]) == 0:
                    iceberg["inhabitants"] = None
                animal["home"] = None
                client.put(iceberg)
                client.put(animal)
            else:
                return status_fail(404, ERR.NO_ANIMAL_HERE)

        # Success 204 No Content
        return status_success(204)

    else:
        # Failure 405 Method Not Allowed
        icebergid_animals_animalid_invalid()


@bp.route("/<iceberg_id>/animals/<animal_id>",
          methods=["POST", "GET", "PATCH"])
def icebergid_animals_animalid_invalid():
    # Failure 405 Method Not Allowed
    return status_fail(405, ERR.METHOD_INVALID, header="PUT, DELETE")
