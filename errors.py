# 400 Bad Request
# Must be an int value within given range
INVALID_AREA = "The area (sq mi) of an Iceberg must be an int value less "\
               "than or equal to 8000"
INVALID_HEIGHT = "The height of an Animal must be an int value less "\
                 "than or equal to 25"

# Must be a string of alphanumeric characters within given range
INVALID_NAME = "The name of an Animal/Iceberg can only consist of up to 50 "\
               "alphanumeric characters"
INVALID_SPECIES = "The species of an Animal can only consist of up to 50 "\
                  "alphanumeric characters"

# Other bad requests
ANIMAL_ASSIGNED = "This Animal already has a home"
INVALID_PUBLIC = "The public attribute must be True or False"
INVALID_SHAPE = "The shape of an Iceberg can only be of the following: "\
                "tabular, dome, pinnacle, wedge, dry-dock, or blocky"
MISSING_ATTRIBUTE = "The request object is missing at least one of the "\
                    "required attributes"

# 401 Unauthorized
UNAUTHORIZED = "Proper authorization is required"

# 403 Forbidden
NAME_EXISTS = "An Animal/Iceberg with this name already exists"
NO_PERMISSION = "This user does not have permission to access this resource"

# 404 Not Found
NO_ANIMAL = "No Animal with this animal_id exists"
NO_ANIMAL_HERE = "There is no Animal with this animal_id on this Iceberg"
NO_ICEBERG = "No Iceberg with this iceberg_id exists"
NEITHER_EXISTS = "No Iceberg with this iceberg_id exists and no Animal with "\
                 "this animal_id exists"

# 405 Method Not Allowed
METHOD_INVALID = "This method is not allowed"

# 406 Not Acceptable
WRONG_MEDIA_REQUESTED = "The requested media type is not offered"

# 415 Unsupported Media Type
WRONG_MEDIA_RECEIVED = "The received media type is not supported"
