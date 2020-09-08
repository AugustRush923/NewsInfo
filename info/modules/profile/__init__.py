from flask import Blueprint

profile_blu = Blueprint("profile", __name__, url_prefix="/profile")

from . import views