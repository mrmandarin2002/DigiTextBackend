from flask import Blueprint, request
from flask_praetorian import auth_required, current_user

from database import School, school_dbs, db, User, guard

meta = Blueprint("meta", "meta")

@meta.route("/schools")
@auth_required
def get_schools():
    if "admin" in current_user().role:
        schools = School.query.all()
        return {dict(id=school.id, name=school.name, code=school.code) for school in schools}


@meta.route("/schools", methods=["POST"])
@auth_required
def add_school():
    if "admin" in current_user().role:
        school = School(request.json["name"], request.json["code"])
        db.session.commit()
        school_dbs[current_user().school_code].create_all()
        return {"id": school.id}


@meta.route("/schools", methods=["DELETE"])
@auth_required
def remove_school():
    if "admin" in current_user().role:
        school = School.query.get_or_404(request.json["school_id"])
        db.session.delete(school)
        db.session.commit()


@meta.route("/users")
@auth_required
def get_users():
    if "admin" in current_user().role:
        users = User.query.filter_by(school_code = current_user().school_code)
        return {"users" : [dict(id=user.id, username=user.username, role=user.role, school_code=user.school_code) for user in users]}


@meta.route("/users", methods=["POST"])
@auth_required
def add_user():
    if "admin" in current_user().role:
        if User.query.filter_by(username = request.json["username"]).count() == 0:
            print(request.json["username"])
            user = User(username = request.json["username"], password = guard.hash_password(request.json["password"]), role = request.json["role"], school_code = current_user().school_code)
            db.session.add(user)
            db.session.commit()
            return {"status" : True}
        else:
            print("NAH")
            return {"status" : False}

# user will be removed based on school and username
@meta.route("/users", methods=["DELETE"])
@auth_required
def remove_user():
    if "admin" in current_user().role:
        user = User.query.filter_by(username = request.json["username"]).first()
        db.session.delete(user)
        db.session.commit()
        return {"status" : True}


