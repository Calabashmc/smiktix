from flask import current_app

def log_exception(message, e=None):
    """
    Log an exception with a message. For use in development so I don't need print statements after exceptions
    :param message: Message to log
    :param e: an Exception object
    """
    if current_app.debug:
        print(f"DEBUG: {message} - {e}")
    current_app.logger.exception(message)