from flask import Blueprint, request
from flask_praetorian import auth_required, current_user
import time

from database import schools, school_dbs, School, db
from roles import staff_roles
import general_queries

textbooks = Blueprint("textbooks", "textbooks")

#returns a dictionary with a list of textbooks of a given course
@textbooks.route("/courses/prerequisites/<course_number>")
@auth_required
def get_course_prerequisites(course_number):
    textbook_assignments = schools.school(current_user()).textbook_assignments.query.filter_by(course_number=course_number).all()
    textbook_list = []
    for assignment in textbook_assignments:
        textbook_info = schools.school(current_user()).abstract_textbooks.query.filter_by(abstract_id=assignment.abstract_textbook_id).first()
        textbook_list.append(dict(abstract_textbook_id=assignment.abstract_textbook_id, title = textbook_info.title, cost = textbook_info.cost))
    return {"textbook_requisites": textbook_list}


@textbooks.route("/abstract_textbooks")
@auth_required
def get_abstract_textbooks():
    t1 = time.time()
    test = [dict(needed = abstract_textbook.needed, id=abstract_textbook.abstract_id, amount = abstract_textbook.amount,title=abstract_textbook.title, cost=abstract_textbook.cost) for abstract_textbook in schools.school(current_user()).abstract_textbooks.query.all()]
    print("GET ABSTRACT RUNTIME:", time.time() - t1)
    return {"abstract_textbooks": test}


# function to be completed
@textbooks.route("/abstract_textbooks/<abstract_id>", methods = ['DELETE'])
@auth_required
def delete_abstract_textbook(abstract_id):
    if current_user().role == "admin":
        school = School.query.filter_by(code = current_user().school_code).first()
        abstract_textbook = schools.school(current_user()).abstract_textbooks.query.filter_by(abstract_id = abstract_id).first()

        for textbook in schools.school(current_user()).textbooks.query.filter_by(abstract_textbook_id = abstract_id).all():
            for transaction in schools.school(current_user()).transactions.query.filter_by(textbook_number = textbook.number).all():
                school.money_owed = school.money_owed - transaction.transaction_cost
                school_dbs[current_user().school_code].session.delete(transaction)
            school.textbooks_worth = school.textbooks_worth - abstract_textbook.cost
            school_dbs[current_user().school_code].session.delete(textbook)

        for assignment in schools.school(current_user()).textbook_assignments.query.filter_by(abstract_textbook_id = abstract_id).all():
            school_dbs[current_user().school_code].session.delete(assignment)

        school_dbs[current_user().school_code].session.delete(abstract_textbook)

        school_dbs[current_user().school_code].session.commit()
        db.session.commit()

        return {"status" : True}


@textbooks.route("/textbooks")
@auth_required
def get_textbooks():
    textbooks = schools.school(current_user()).textbooks.query.all()
    return {"textbooks": [dict(number=textbook.number, abstract_textbook_id=textbook.abstract_textbook_id) for textbook in textbooks]}


# returns dict of textbook_info
# { number, abstract_textbook_id, cost, title, owner, condition }
@textbooks.route("/textbooks/<textbook_number>")
@auth_required
def get_textbook(textbook_number):
    textbook_transactions = []
    textbook = general_queries.get_textbook(textbook_number)
    for transaction in schools.school(current_user()).transactions.query.filter_by(textbook_number = textbook_number).all():
        if transaction.origin_student_number == -1: #first added to school
            textbook_transactions.append(dict(id = len(textbook_transactions), type = "ADD", condition = transaction.textbook_condition, cost = 0, date = transaction.date, origin = "N/A", destin = "SCHOOL"))
        elif transaction.origin_student_number == 0: #withdraw
            textbook_transactions.append(dict(id = len(textbook_transactions), type = "WITHDRAW", condition = transaction.textbook_condition, cost = 0, date = transaction.date, origin = "SCHOOL", destin = schools.school(current_user()).students.query.filter_by(number = transaction.destin_student_number).first().name))
        else:
            textbook_transactions.append(dict(id = len(textbook_transactions), type = "RETURN", condition = transaction.textbook_condition, cost = transaction.transaction_cost, date = transaction.date, origin = schools.school(current_user()).students.query.filter_by(number = transaction.origin_student_number).first().name, destin = "SCHOOL"))
    textbook["transactions"] = textbook_transactions
    return textbook

# makes sure to also add a transaction while doing it
@textbooks.route("/textbooks/<textbook_number>", methods=["PUT"])
@auth_required
def add_textbook(textbook_number):
    if "admin" in current_user().role:
        title = request.json["title"]
        cost = request.json["cost"]
        condition = request.json["condition"]
        abstract_textbook = schools.school(current_user()).abstract_textbooks.query.filter_by(title = title).all()
        
        #if textbook exist in data abstract textbooks database
        if len(abstract_textbook) == 1:
            textbook = schools.school(current_user()).textbooks(textbook_number, abstract_textbook[0].id)
            abstract_textbook[0].amount = abstract_textbook[0].amount + 1
            school_dbs[current_user().school_code].session.add(textbook)
            school_dbs[current_user().school_code].session.commit()
        elif len(abstract_textbook) > 1:
            print("There are two identical abstract IDs... yikes")
            return {"status" : False}
        else:
            print("ADDING NEW TYPE OF TEXTBOOK!")
            # gets a new abstract_id key
            # currently loops... definitely a way to make it faster but I'm too lazy rn
            new_id = sorted([textbook.abstract_id for textbook in schools.school(current_user()).abstract_textbooks.query.all()])[-1] + 1
            #adds new type of textbook in database
            abstract_textbook = schools.school(current_user()).abstract_textbooks(title = title, cost = cost, abstract_id = new_id, amount = 1, needed = 0)
            school_dbs[current_user().school_code].session.add(abstract_textbook)
            school_dbs[current_user().school_code].session.commit()
            textbook = schools.school(current_user()).textbooks(textbook_number, new_id)
            school_dbs[current_user().school_code].session.add(textbook)
            school_dbs[current_user().school_code].session.commit()

        #add transaction
        transaction = schools.school(current_user()).transactions(textbook_condition = condition, destin_student_number = 0, origin_student_number = -1, textbook_number = textbook_number)
        
        # changes school textbook worth
        school = School.query.filter_by(code = current_user().school_code).first()
        school.textbooks_worth = school.textbooks_worth + cost

        school_dbs[current_user().school_code].session.add(transaction)
        school_dbs[current_user().school_code].session.commit()
        db.session.commit()

        return {"textbook_number": textbook_number}


# replaces the info of all the "bad textbooks" with the "good textbooks"
# also removes the abstract_id of the "bad_textbook"
# also change textbook assignments to make sure all the assignments are converted to the correct textbook
@textbooks.route("/textbooks/merge", methods = ["PATCH"])
@auth_required
def merge_textbooks():
    if "admin" in current_user().role:
        if request.json["good_textbook"] != request.json["bad_textbook"]:
            school = School.query.filter_by(code = current_user().school_code).first()
            abstract_textbook = schools.school(current_user()).abstract_textbooks.query.filter_by(abstract_id = request.json["good_textbook"]).first()
            bad_abstract_textbook = schools.school(current_user()).abstract_textbooks.query.filter_by(abstract_id = request.json["bad_textbook"]).first() 
            bad_textbooks = schools.school(current_user()).textbooks.query.filter_by(abstract_textbook_id = request.json["bad_textbook"]).all()
            for bad_textbook in bad_textbooks:
                bad_textbook.abstract_textbook_id = request.json["good_textbook"]
                
            school.textbooks_worth = school.textbooks_worth + (abstract_textbook.cost - bad_abstract_textbook.cost) * len(bad_textbooks)
            abstract_textbook.amount += len(bad_textbooks)

            for assignment in schools.school(current_user()).textbook_assignments.query.filter_by(abstract_textbook_id = request.json["bad_textbook"]).all():
                assignment.abstract_textbook_id = request.json["good_textbook"]

            for placeholder in schools.school(current_user()).placeholders.query.filter_by(abstract_textbook_id = request.json["bad_textbook"]).all():
                placeholder.abstract_textbook_id = request.json["good_textbook"]
            
            bad_textbook_abstract = schools.school(current_user()).abstract_textbooks.query.filter_by(abstract_id = request.json["bad_textbook"]).first()
            school_dbs[current_user().school_code].session.delete(bad_textbook_abstract)
            school_dbs[current_user().school_code].session.commit()
            db.session.commit()

            return {"merged" : {"bad_textbook" : request.json["bad_textbook"], "good_textbook" : request.json["good_textbook"]}}
        else:
            return {"status" : False}


@textbooks.route("/textbooks/<textbook_number>", methods=["DELETE"])
@auth_required
def delete_textbook(textbook_number):
    if "admin" in current_user().role:
        school = School.query.filter_by(code = current_user().school_code).first()
        textbook = schools.school(current_user()).textbooks.query.get_or_404(textbook_number)
        abstract_textbook = schools.school(current_user()).abstract_textbooks.query.filter_by(abstract_id = textbook.abstract_textbook_id).first()
        abstract_textbook.amount = abstract_textbook.amount - 1
        textbook_transactions = schools.school(current_user()).transactions.query.filter_by(textbook_number = textbook_number).all()
        for transaction in textbook_transactions:
            school_dbs[current_user().school_code].session.delete(transaction)
            school.money_owed = school.money_owed - transaction.transaction_cost
        
        school.textbooks_worth = school.textbooks_worth - abstract_textbook.cost
        school_dbs[current_user().school_code].session.delete(textbook)
        school_dbs[current_user().school_code].session.commit()
        db.session.commit()
        return {"deleted_textbook" : textbook_number}


@textbooks.route("/textbook_assignments", methods=["POST"])
@auth_required
def add_textbook_assignment():
    if current_user().role in staff_roles:
        needed_textbooks = 0
        if "course_number" in request.json:
            textbook_assignment = schools.school(current_user()).textbook_assignments(request.json["abstract_textbook_id"], request.json["course_number"])
            needed_textbooks += schools.school(current_user()).course_enrollments.query.filter_by(course_number = request.json["course_number"]).count()
            school_dbs[current_user().school_code].session.add(textbook_assignment)
        else:
            teacher_id = schools.school(current_user()).teachers.query.filter_by(name = request.json["teacher_name"]).first().id
            teacher_courses = schools.school(current_user()).courses.query.filter_by(teacher_id = teacher_id).all()
            for course in teacher_courses:
                if request.json["course_name"] == course.name:
                    needed_textbooks += schools.school(current_user()).course_enrollments.query.filter_by(course_number = course.number).count()
                    textbook_assignment = schools.school(current_user()).textbook_assignments(request.json["abstract_textbook_id"], course.number)
                    school_dbs[current_user().school_code].session.add(textbook_assignment)
        abstract_textbook = schools.school(current_user()).abstract_textbooks.query.filter_by(abstract_id = request.json["abstract_textbook_id"]).first()
        abstract_textbook.needed = abstract_textbook.needed + needed_textbooks
        school_dbs[current_user().school_code].session.commit()
        return {"id": textbook_assignment.id}


@textbooks.route("/textbook_assignments", methods=["DELETE"])
@auth_required
def delete_textbook_assignment():
    if current_user().role in staff_roles:
        not_needed_textbooks = 0
        if "course_number" in request.json:
            for assignment in schools.school(current_user()).textbook_assignments.query.filter_by(abstract_textbook_id = request.json["abstract_textbook_id"]).all():
                if assignment.course_number == request.json["course_number"]:
                    not_needed_textbooks += schools.school(current_user()).course_enrollments.query.filter_by(course_number = request.json["course_number"]).count()
                    school_dbs[current_user().school_code].session.delete(assignment)
                    break
        else:
            for assignment in schools.school(current_user()).textbook_assignments.query.filter_by(abstract_textbook_id = request.json["abstract_textbook_id"]).all():
                teacher_id = schools.school(current_user()).courses.query.filter_by(number = assignment.course_number).first().teacher_id
                if request.json["teacher_name"] == schools.school(current_user()).teachers.query.filter_by(id = teacher_id).first().name:
                    not_needed_textbooks += schools.school(current_user()).course_enrollments.query.filter_by(course_number = assignment.course_number).count()
                    school_dbs[current_user().school_code].session.delete(assignment)

        abstract_textbook = schools.school(current_user()).abstract_textbooks.query.filter_by(abstract_id = request.json["abstract_textbook_id"]).first()
        abstract_textbook.needed = abstract_textbook.needed - not_needed_textbooks
        school_dbs[current_user().school_code].session.commit()
        return {"id" : request.json["abstract_textbook_id"]}
