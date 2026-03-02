from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    """
    Custom exception handler that formats all DRF errors into a standardized
    JSON structure for the frontend.
    """
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    if response is not None:
        # Create a standard error format
        custom_response_data = {
            "status": "error",
            "code": response.status_code,
            "message": "An error occurred processing your request.",
            "errors": response.data
        }

        # Handle specific DRF error structures to make message more readable
        if isinstance(response.data, dict):
            if "detail" in response.data:
                custom_response_data["message"] = response.data["detail"]
                custom_response_data["errors"] = None
            else:
                # Likely a validation error (field: [errors])
                custom_response_data["message"] = "Validation failed. Please check your input."
        
        response.data = custom_response_data

    return response