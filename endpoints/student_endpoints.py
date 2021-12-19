from flask import Blueprint
from flask_praetorian import auth_required, current_user
from flask_praetorian import Praetorian
import time

from database import *
import general_queries
from roles import staff_roles

students = Blueprint("students", "students")

@students.route("/students")
@auth_required
def get_students():
    if current_user().role in staff_roles:
        students = schools.school(current_user()).students.query.all()
        return {"students": [dict(number=student.number, name=student.name) for student in students]}


# written specifically for website *************************CLEAN THIS SHIT*******************************
# FUCK THIS FUCK THIS FUCK THIS
# security is fucked so I'm making a dictionary with all the placeholders and shit
# it's digusting so its best if we can figure out a different way of doing this fucking garbage jesus
# I don't think ya'll realise how much pain writing this function has caused me
@students.route("/students/getall/<student_number>")
@auth_required
def get_all_student(student_number):
    if current_user().role in staff_roles:
        t1 = time.time()
        student = schools.school(current_user()).students.query.get_or_404(student_number)

        withdraw_transactions = schools.school(current_user()).transactions.query.filter_by(destin_student_number = student_number).all()
        student_transactions = []
        for transaction in withdraw_transactions:
            transaction_type = "Withdraw"
            abstract_textbook_id = schools.school(current_user()).textbooks.query.filter_by(number = transaction.textbook_number).first().abstract_textbook_id
            textbookInfo = schools.school(current_user()).abstract_textbooks.query.filter_by(abstract_id = abstract_textbook_id).first()
            student_transactions.append(dict(id = len(student_transactions) + 1, cost = transaction.transaction_cost, type = transaction_type, date = transaction.date, textbookInfo = dict(condition = transaction.textbook_condition, cost = textbookInfo.cost, title = textbookInfo.title)))

        return_transactions = schools.school(current_user()).transactions.query.filter_by(origin_student_number = student_number).all()
        for transaction in return_transactions:
            transaction_type = "Return"
            abstract_textbook_id = schools.school(current_user()).textbooks.query.filter_by(number = transaction.textbook_number).first().abstract_textbook_id
            textbookInfo = schools.school(current_user()).abstract_textbooks.query.filter_by(abstract_id = abstract_textbook_id).first()
            student_transactions.append(dict(id = len(student_transactions) + 1, cost = transaction.transaction_cost, type = transaction_type, date = transaction.date, textbookInfo = dict(condition = transaction.textbook_condition, cost = textbookInfo.cost, title = textbookInfo.title)))

        # get the students' withdrawn textbooks
        withdrawn_set = set()
        for transaction in withdraw_transactions:
            if schools.school(current_user()).transactions.query.filter_by(textbook_number = transaction.textbook_number).all()[-1].destin_student_number == int(student_number):
                withdrawn_set.add(transaction.textbook_number)

        withdrawn = [general_queries.get_textbook(t_num) for t_num in withdrawn_set]
        withdrawn_ids = [textbook["abstract_textbook_id"] for textbook in withdrawn]
        courses = general_queries.get_student_courses(student_number)
        needed_textbooks = []

        #this is beyond fucking cancer
        for course in courses["course_enrollments"]:
            for textbook in course["course_textbooks"]:
                textbook_id = textbook["abstract_textbook_id"]
                if textbook_id not in withdrawn_ids:
                    withdrawn_ids.append(textbook_id)
                    needed_textbooks.append(textbook)
                
                for placeholder in schools.school(current_user()).placeholders.query.filter_by(placeholder_id = int(textbook_id)).all():
                    if placeholder.abstract_textbook_id in withdrawn_ids and textbook in needed_textbooks:
                        needed_textbooks.remove(textbook)

        print("GET ALL STUDENT RUNTIME: ", time.time() - t1)

        return dict(transactions = student_transactions, number=student.number, name=student.name, neededTextbooks = needed_textbooks, withdrawnTextbooks = withdrawn, courses = courses["course_enrollments"])


# gets a list of students with their respective student ids
@students.route("/students/getlist")
@auth_required
def get_student_list():
    if current_user().role in staff_roles:
        return { "students" : [{"number" : student.number, "name" : student.name} for student in schools.school(current_user()).students.query.all()]}
