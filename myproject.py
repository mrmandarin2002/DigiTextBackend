from flask import request
from flask import make_response
from flask_sqlalchemy import SQLAlchemy
from flask import render_template
from datetime import datetime
from flask_praetorian import Praetorian
from flask_praetorian import auth_required
from flask_praetorian import roles_required
from flask_praetorian import current_user
from sqlalchemy import func
from flask_cors import CORS, cross_origin

from condition_drop_functions import *
from conversions import *

import time #to test speed of code

from database import *
from sqlalchemy import func

# import blueprints
from endpoints.meta_endpoints import meta
from endpoints.admin_endpoints import admin
from endpoints.transaction_endpoints import transactions
from endpoints.textbook_endpoints import textbooks
from endpoints.teacher_endpoints import teachers
from endpoints.student_endpoints import students


# API CODE
@app.route("/login", methods=["POST"])
def login():
    try:
        user = guard.authenticate(request.json["username"], request.json["password"])
        token = guard.encode_jwt_token(user)
        print("ACCESS TOKEN:", token)
        return {"access_token": token, "school_code": user.school_code, "role": user.role}
    except:
        print("LOGIN FAILED")
        return {"access_token" : "FAILED"}

app.register_blueprint(meta)
app.register_blueprint(admin)
app.register_blueprint(transactions)
app.register_blueprint(textbooks)
app.register_blueprint(teachers)
app.register_blueprint(students)


if __name__ == "__main__":
    #migrate()
    app.run(host = "0.0.0.0", debug = True)
