from sqlalchemy.exc import IntegrityError

# Define constants for error types
UNIQUE_CONSTRAINT_VIOLATION = 'UNIQUE constraint violation'
NOT_NULL_CONSTRAINT_VIOLATION = 'NOT NULL constraint violation'
FOREIGN_KEY_CONSTRAINT_VIOLATION = 'FOREIGN KEY constraint violation'
CHECK_CONSTRAINT_VIOLATION = 'CHECK constraint violation'
UNKNOWN_INTEGRITY_ERROR = 'Unknown integrity error'

# Define constants for SQLite error messages
SQLITE_UNIQUE_CONSTRAINT_ERROR_MESSAGE = 'UNIQUE constraint failed'
SQLITE_NOT_NULL_CONSTRAINT_ERROR_MESSAGE = 'NOT NULL constraint failed'
SQLITE_FOREIGN_KEY_CONSTRAINT_ERROR_MESSAGE = 'FOREIGN KEY constraint failed'
SQLITE_CHECK_CONSTRAINT_ERROR_MESSAGE = 'CHECK constraint failed'

def classify_integrity_error(error: IntegrityError) -> str:
    """
    Classify the cause of an IntegrityError.

    Args:
        error (IntegrityError): The IntegrityError instance to classify.

    Returns:
        str: A string describing the cause of the IntegrityError.
    
    Note:
        - The current implementation primarily supports error messages from SQLite3.
    """
    error_message = str(error.orig)

    if SQLITE_UNIQUE_CONSTRAINT_ERROR_MESSAGE in error_message:
        return UNIQUE_CONSTRAINT_VIOLATION
    elif SQLITE_NOT_NULL_CONSTRAINT_ERROR_MESSAGE in error_message:
        return NOT_NULL_CONSTRAINT_VIOLATION
    elif SQLITE_FOREIGN_KEY_CONSTRAINT_ERROR_MESSAGE in error_message:
        return FOREIGN_KEY_CONSTRAINT_VIOLATION
    elif SQLITE_CHECK_CONSTRAINT_ERROR_MESSAGE in error_message:
        return CHECK_CONSTRAINT_VIOLATION
    else:
        return UNKNOWN_INTEGRITY_ERROR


def gen_integrity_error_message(model: str, error: IntegrityError) -> str:
    """
    Generate an error message for an IntegrityError.

    Args:
        model (str): The model name.
        error (IntegrityError): The IntegrityError instance.

    Returns:
        str: A string describing the cause of the IntegrityError.
    """
    error_type = classify_integrity_error(error)
    if error_type == UNIQUE_CONSTRAINT_VIOLATION:
        return f"{model} already exists."
    elif error_type == NOT_NULL_CONSTRAINT_VIOLATION:
        return f"{model} is missing a requirement field."
    elif error_type == FOREIGN_KEY_CONSTRAINT_VIOLATION:
        return f"{model} has an invalid foreign key."
    elif error_type == CHECK_CONSTRAINT_VIOLATION:
        return f"{model} failed a check constraint."
    else: 
        return f"{model} has an unknown integrity error."