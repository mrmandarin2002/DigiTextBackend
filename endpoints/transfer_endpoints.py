from flask import Blueprint, request
from flask_praetorian import auth_required, current_user

from database import School, school_dbs, db, User, guard

transfer = Blueprint("transfer", "transfer")