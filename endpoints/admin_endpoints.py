from flask import Blueprint, send_file, request
from flask_praetorian import auth_required, current_user

import time

from database import School, db, schools
from pdf_utils import textbook_barcodes, book_return_page
from PyPDF2 import PdfFileMerger

from conversions import *
from grade_difference_functions import *

admin = Blueprint("admin", "admin")

@admin.route("/getbarcodes/<n>")
@auth_required
def generate_barcodes(n):
    if "admin" in current_user().role:
        if current_user().role == "admin":
            school = School.query.filter_by(code=current_user().school_code).first()
            filename = current_user().school_code + "barcodes" + str(school.last_barcode) + '-' + str(school.last_barcode + 30 * int(n)) + ".pdf"
            textbook_barcodes(school.last_barcode, school.last_barcode + 30 * int(n), filename = filename)
            school.last_barcode = school.last_barcode + 30 * int(n)
            db.session.commit()
            return send_file("barcode_pdfs/" + filename, mimetype = "application/pdf", as_attachment=True, cache_timeout=0)
    return {"status" : False}

@admin.route("/invoice/neededtextbooks")
@auth_required
def generate_student_needed_list():
    pass

@admin.route("/invoice/<student_number>")
@auth_required
def generate_student_invoice(student_number):
    current_school = schools.school(current_user())
    student = current_school.students.query.filter_by(number=student_number).first()
    books = []
    visited_books = set()
    for transaction in current_school.transactions.query.filter_by(destin_student_number = student_number).all():
        if transaction.textbook_number not in visited_books and current_school.transactions.query.filter_by(textbook_number = transaction.textbook_number).all()[-1].destin_student_number != 0:
            textbook_info = current_school.abstract_textbooks.query.filter_by(abstract_id = current_school.textbooks.query.filter_by(number = transaction.textbook_number).first().abstract_textbook_id).first()
            visited_books.add(transaction.textbook_number)
            books.append([transaction.textbook_number, textbook_info.title, textbook_info.cost, "OUT"])

    for transaction in current_school.transactions.query.filter_by(origin_student_number = student_number).all():
        if transaction.transaction_cost != 0:
            textbook_info = current_school.abstract_textbooks.query.filter_by(abstract_id = current_school.textbooks.query.filter_by(number = transaction.textbook_number).first().abstract_textbook_id).first()
            visited_books.add(transaction.textbook_number)
            prev_condition = condition_to_word(current_school.transactions.query.filter_by(textbook_number = transaction.textbook_number).all()[-2].textbook_condition)
            books.append([transaction.textbook_number, textbook_info.title, transaction.transaction_cost, "DAMAGED", (prev_condition, condition_to_word(transaction.textbook_condition))])

    student_name = student.name.replace(' ', '_')
    book_return_page(current_user().school_code, student.name, student_number, books, filename= "student_invoices/" + current_user().school_code + "/" + student_name + ".pdf")
    return send_file("student_invoices/" + current_user().school_code + '/' + student_name+".pdf", mimetype="application/pdf", as_attachment=True , cache_timeout=0)


@admin.route("/invoice/all/<balanceLowerBound>")
@auth_required
def generate_all_invoices(balanceLowerBound):
    t0 = time.time()
    filenames = []
    current_school = schools.school(current_user())
    students = current_school.students.query.all()
    del students[0]
    prev_idx = 0 #assumes school is the first 

    for idx, student in enumerate(students):
        #sort alphabetically but by grade
        #compares student numbers to determine if there is a grade change
        if idx != 0 and (idx == len(students) - 1 or grade_difference[current_user().school_code](student.number, students[idx - 1].number)):
            print(idx)
            filenames[prev_idx:] = sorted(filenames[prev_idx:])
            prev_idx = len(filenames)
        books = []
        visited_books = set()
        student_balance = 0
        for transaction in current_school.transactions.query.filter_by(destin_student_number = student.number).all():
            if transaction.textbook_number not in visited_books and current_school.transactions.query.filter_by(textbook_number = transaction.textbook_number).all()[-1].destin_student_number != 0:
                textbook_info = current_school.abstract_textbooks.query.filter_by(abstract_id = current_school.textbooks.query.filter_by(number = transaction.textbook_number).first().abstract_textbook_id).first()
                visited_books.add(transaction.textbook_number)
                books.append([transaction.textbook_number, textbook_info.title, textbook_info.cost, "OUT"])
                student_balance += textbook_info.cost

        for transaction in current_school.transactions.query.filter_by(origin_student_number = student.number).all():
            if transaction.transaction_cost != 0:
                textbook_info = current_school.abstract_textbooks.query.filter_by(abstract_id = current_school.textbooks.query.filter_by(number = transaction.textbook_number).first().abstract_textbook_id).first()
                visited_books.add(transaction.textbook_number)
                prev_condition = condition_to_word(current_school.transactions.query.filter_by(textbook_number = transaction.textbook_number).all()[-2].textbook_condition)
                books.append([transaction.textbook_number, textbook_info.title, transaction.transaction_cost, "DAMAGED", (prev_condition, condition_to_word(transaction.textbook_condition))])
                student_balance += transaction.transaction_cost
        
        if student_balance > float(balanceLowerBound):
            student_name = student.name.replace(' ', '_')
            book_return_page(current_user().school_code, student.name, student.number, books, filename= "student_invoices/" + current_user().school_code + "/" + student_name + ".pdf")
            filenames.append("student_invoices/" + current_user().school_code + "/" + student_name + ".pdf")

    merger = PdfFileMerger()
    [merger.append(filename) for filename in filenames]
    merger.write("student_invoices/" + current_user().school_code + "/" + current_user().school_code + "_all_invoices.pdf")
    merger.close()
    print("GET ALL INVOICES RUNTIME: ", time.time() - t0)
    return send_file("student_invoices/" + current_user().school_code + "/" + current_user().school_code + "_all_invoices.pdf", mimetype="application/pdf", as_attachment=True, cache_timeout=0)
