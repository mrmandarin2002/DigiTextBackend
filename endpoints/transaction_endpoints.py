from flask import Blueprint, request
from flask_praetorian import auth_required, current_user
import time
from shutil import copy

import general_queries

from database import *
from condition_drop_functions import school_condition_drop
from roles import staff_roles

transactions = Blueprint("transactions", "transactions")

@transactions.route("/transactions", methods=["POST"])
@auth_required
def add_transaction():
    if current_user().role in staff_roles:
        school = School.query.filter_by(code = current_user().school_code).first()
        transaction = schools.school(current_user()).transactions(request.json["textbook_condition"], request.json["origin_student_number"], request.json["destin_student_number"], request.json["textbook_number"])
        
        prev_transactions = schools.school(current_user()).transactions.query.filter_by(textbook_number = transaction.textbook_number).all()
        # can't be return
        if len(prev_transactions) < 2 or transaction.destin_student_number != 0:
            transaction.transaction_cost = 0
        else:
            textbook_cost = schools.school(current_user()).abstract_textbooks.query.filter_by(abstract_id = schools.school(current_user()).textbooks.query.filter_by(number = transaction.textbook_number).first().abstract_textbook_id).first().cost
            transaction.transaction_cost = school_condition_drop[current_user().school_code](abs(int(prev_transactions[-1].textbook_condition) - int(transaction.textbook_condition)), textbook_cost)
            if transaction.transaction_cost != 0:
                school.money_owed = school.money_owed + transaction.transaction_cost

        school_dbs[current_user().school_code].session.add(transaction)
        school_dbs[current_user().school_code].session.commit()
        db.session.commit()
        if transaction.id % 10 == 0:
            copy(f"schools/{current_user().school_code}.db", f"backups/{current_user().school_code}_{transaction.id // 10}.db")
        return {"id": transaction.id}

# number of past transactions we want
@transactions.route("/stats/<past_transactions>")
@auth_required
def get_stats(past_transactions):
    if current_user().role in staff_roles:
        past_transactions = int(past_transactions)
        t0 = time.time()
        number_of_textbooks = schools.school(current_user()).textbooks.query.count()
        school = School.query.filter_by(code = current_user().school_code).first()
        # don't ask me how but it works lmao
        # engineering math intensifies
        to_school_num = schools.school(current_user()).transactions.query.filter_by(destin_student_number = 0).count() - number_of_textbooks
        withdrawn_num = (schools.school(current_user()).transactions.query.count() - (to_school_num + number_of_textbooks)) - to_school_num

        transactions = schools.school(current_user()).transactions.query.all()
        latest_transactions = []
        if len(transactions) >= past_transactions:
            transactions = transactions[-past_transactions:]

        latest_transactions = [general_queries.get_transaction_info(schools.school(current_user()), transaction) for transaction in transactions]

        destroyed_textbooks = schools.school(current_user()).transactions.query.filter_by(textbook_condition = 4).count()

        students_with_damaged_books = set()
        for transaction in schools.school(current_user()).transactions.query.filter(schools.school(current_user()).transactions.transaction_cost != 0).all():
            students_with_damaged_books.add(transaction.origin_student_number)

        students_owing_money = len(students_with_damaged_books)

        while {} in latest_transactions:
            latest_transactions.remove({})

        textbook_worth = school.textbooks_worth
        money_owed = school.money_owed

        print("STATS RUNTIME: ", time.time() - t0)

        return {"students_owing_money" : students_owing_money, "destroyed_textbooks" : destroyed_textbooks, "total_number" : number_of_textbooks, "total_money_owed" : money_owed, "total_textbook_worth" : textbook_worth, "total_withdrawn" : withdrawn_num, "latest_transactions" : latest_transactions}
