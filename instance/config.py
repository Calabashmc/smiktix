import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Useful path variables
app_dir = os.path.abspath(os.path.dirname(__file__))


def get_db_password():
    """Read database password from environment variable or secrets file"""
    # Try environment variable first (useful for dev/staging/CI)
    password = os.getenv('DB_PASSWORD')
    if password:
        return password

    # Fall back to reading from a secrets file
    password_file = os.path.join('secrets', 'db_password')
    try:
        with open(password_file, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        raise RuntimeError(
            f"Database password not found. Set the DB_PASSWORD environment variable "
            f"or create the file {password_file}."
        )


class BaseConfig:
    # Set the CSRF token expiration time to 7 days (7 * 24 * 60 * 60 seconds)
    WTF_CSRF_TIME_LIMIT = 7 * 24 * 60 * 60

    SECRET_KEY = os.getenv('SECRET_KEY')

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # flask-security-too.readthedocs.io/en/stable/quickstart.html
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # Explicitly disable all two-factor authentication
    SECURITY_TWO_FACTOR = False
    SECURITY_TWO_FACTOR_ENABLED_METHODS = []
    SECURITY_TWO_FACTOR_REQUIRED = False


    # Add these fake entries to get around error of them being needed even though I am not using 2FA yet.
    SECURITY_TOTP_SECRETS = {"1": "base32secret3232"}
    SECURITY_TOTP_ISSUER = "smiktix"

    SECURITY_REGISTERABLE = True
    SECURITY_CONFIRMABLE = False
    SECURITY_RECOVERABLE = True
    # Unified signin configuration
    SECURITY_UNIFIED_SIGNIN = False

    SECURITY_USER_IDENTITY_ATTRIBUTES = [
        {"email": {"mapper": str.lower, "case_insensitive": True}},
        {"username": {"mapper": str.lower, "case_insensitive": True}}
    ]
    SECURITY_US_ENABLED_METHODS = ['email', 'username']
    SECURITY_US_SIGNIN_TEMPLATE = "security/us_signin.html"
    SECURITY_US_MFA_REQUIRED = False
    SECURITY_US_SIGNIN_REPLACES_LOGIN = False

    SECURITY_LOGIN_USER_TEMPLATE = "security/login_user.html"
    SECURITY_CHANGEABLE = True
    SECURITY_CHANGE_URL = "/profile/change/"
    SECURITY_PASSWORD_SALT = 'EjQtCZbWnJDiTMIDNgamsWvPnQBZyf7Z5'
    SECURITY_PASSWORD_HASH = "bcrypt"

    # Flask-Mailing configurations
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'localhost')
    MAIL_PORT = os.getenv('MAIL_PORT', 25)
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_SENDER = os.getenv('MAIL_SENDER')
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS')
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    MAIL_FROM_NAME = os.getenv('MAIL_FROM_NAME', 'SM4SB System')
    TEMPLATE_FOLDER = Path(__file__).resolve().parent.parent / 'app' / 'templates' / 'email'
    SEND_FILE_MAX_AGE_DEFAULT = 0

    # Session and security settings
    SESSION_COOKIE_SAMESITE = "None"
    SESSION_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = "https"

    # Pagination default
    ROWS_PER_PAGE = 10

    # Prevent jsonify from alphabetically ordering and screwing up the order I need
    JSON_SORT_KEYS = False

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TESTING = True
    BOOTSTRAP_SERVE_LOCAL = True
    SQLALCHEMY_ECHO = False
    DB_PASSWORD = get_db_password()
    SQLALCHEMY_DATABASE_URI = f'postgresql://postgres:{DB_PASSWORD}@localhost/sm4sb'


class TestingConfig(BaseConfig):
    DEBUG = True
    DB_PASSWORD = get_db_password()
    SQLALCHEMY_DATABASE_URI = f'postgresql://postgres:{DB_PASSWORD}@localhost/sm4sb'


class ProductionConfig(BaseConfig):
    DEBUG = False
    MAIL_SUPPRESS_SEND = False
    SQLALCHEMY_DATABASE_URI = (
            os.environ.get('DATABASE_URL')
            or f"postgresql://{os.environ.get('DB_USER', 'postgres')}:{get_db_password()}@{os.environ.get('DB_HOST', 'postgres')}/{os.environ.get('DB_NAME', 'sm4sb')}"
    )
    SECRET_KEY = os.environ.get('SECRET_KEY') or BaseConfig.SECRET_KEY


app_config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}
