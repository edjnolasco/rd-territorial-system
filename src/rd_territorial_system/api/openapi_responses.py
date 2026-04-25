from rd_territorial_system.api.schemas import ApiErrorResponse

VALIDATION_ERROR_RESPONSE = {
    "model": ApiErrorResponse,
    "description": "Invalid request input.",
}

NOT_FOUND_RESPONSE = {
    "model": ApiErrorResponse,
    "description": "Requested territorial entity was not found.",
}

AMBIGUOUS_RESPONSE = {
    "model": ApiErrorResponse,
    "description": "The request matched multiple territorial entities.",
}

INTERNAL_ERROR_RESPONSE = {
    "model": ApiErrorResponse,
    "description": "Unexpected internal server error.",
}


COMMON_ERROR_RESPONSES = {
    422: VALIDATION_ERROR_RESPONSE,
    500: INTERNAL_ERROR_RESPONSE,
}

STRICT_RESOLVE_ERROR_RESPONSES = {
    404: NOT_FOUND_RESPONSE,
    409: AMBIGUOUS_RESPONSE,
    422: VALIDATION_ERROR_RESPONSE,
    500: INTERNAL_ERROR_RESPONSE,
}