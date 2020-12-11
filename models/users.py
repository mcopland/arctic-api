import errors as ERR
import json

from constants import ICEBERGS, USERS
from flask import Blueprint, request
from google.cloud import datastore
from helpers import status_fail, status_success, verify_jwt

bp = Blueprint("users", __name__, url_prefix="/users")
client = datastore.Client()


@bp.route('', methods=["GET"])
def users_valid():
    if request.method == "GET":

        query = client.query(kind=USERS)
        results = list(query.fetch())

        # Success 200 OK
        output = {"users": results}
        return status_success(200, output=json.dumps(output))

    else:
        # Failure 405 Method Not Allowed
        users_invalid()


@bp.route('', methods=["POST", "PUT", "PATCH", "DELETE"])
def users_invalid(user_id):
    # Failure 405 Method Not Allowed
    return status_fail(405, ERR.METHOD_INVALID, header="GET")


@bp.route("/<user_id>/icebergs", methods=["GET"])
def userid_icebergs_valid(user_id):
    if request.method == "GET":
        if "application/json" not in request.accept_mimetypes:
            # Failure 406 Not Acceptable
            return status_fail(406, ERR.WRONG_MEDIA_REQUESTED)

        # Display Icebergs with pagination
        user = verify_jwt()
        query = client.query(kind=ICEBERGS)
        query.add_filter("founder", "=", user_id)

        if user == "Error":
            # Return public Icebergs only
            query.add_filter("public", "=", True)

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
        userid_icebergs_invalid()


@bp.route("/<user_id>/icebergs", methods=["POST", "PUT", "PATCH", "DELETE"])
def userid_icebergs_invalid(user_id):
    # Failure 405 Method Not Allowed
    return status_fail(405, ERR.METHOD_INVALID, header="GET")
