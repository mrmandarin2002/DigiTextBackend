from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_praetorian import Praetorian

import os

from summermigration import *

from datetime import datetime

from Schools import Schools

# Flask app and database initialization
app = Flask(__name__)
CORS(app, origins='*', 
     headers=['Content-Type', 'Authorization'], 
     expose_headers= ['Authorization', 'Content-Disposition'])
app.config["CORS_HEADERS"] = "Content-Type"
app.config["SECRET_KEY"] = "thisshouldbereplacedwithsomethingwithbetterentropybutthisisgoodfornow"

# configure main database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///meta.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['JWT_ACCESS_LIFESPAN'] = {'minutes' : 360}
app.config['JWT_REFRESH_LIFEPSAN'] = {'minutes' : 720}


db = SQLAlchemy(app)

class School(db.Model):
    __tablename__ = "schools"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    code = db.Column(db.String, unique=True)
    last_barcode = db.Column(db.Integer)
    textbooks_worth = db.Column(db.Integer)
    money_owed = db.Column(db.Float)

    def __init__(self, name, code):
        self.name = name
        self.code = code
        self.last_barcode = 1000000


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String)
    password = db.Column(db.String)
    role = db.Column(db.String)
    school_code = db.Column(db.Integer, db.ForeignKey("schools.code"))

    def set_password(self, password):
        self.password = guard.hash_password(password)

    def check_password(self, password):
        return guard.hash_password(password) == self.password

    @property
    def identity(self):
        return self.id

    @property
    def rolenames(self):
        return [self.role]

    @classmethod
    def lookup(cls, username):
        return cls.query.filter_by(username=username).one_or_none()

    @classmethod
    def identify(cls, id):
        return cls.query.get(id)

guard = Praetorian()
guard.init_app(app, User)

db.create_all()

# configure school-specific databases
app.config["SQLALCHEMY_BINDS"] = {school.code: "sqlite:///schools/{}.db".format(school.code) for school in School.query.all()}

# DATABASE CODE
school_dbs = {}
schools = Schools()

for school_code in app.config["SQLALCHEMY_BINDS"]:

    school_db = SQLAlchemy(app)

    class Student(school_db.Model): # table containing current students
        __bind_key__ = school_code
        __tablename__ = "students"
        number = school_db.Column(school_db.Integer, primary_key=True)
        name = school_db.Column(school_db.String)

        def __init__(self, number, name):
            self.number = number
            self.name = name


    class Teacher(school_db.Model): # table containing teacher information
        __bind_key__ = school_code
        __tablename__ = "teachers"
        id = school_db.Column(school_db.Integer, primary_key=True)
        name = school_db.Column(school_db.String)

        def __init__(self, id, name):
            self.id = id
            self.name = name


    class Course(school_db.Model): # table containing course information
        __bind_key__ = school_code
        __tablename__ = "courses"
        number = school_db.Column(school_db.String, primary_key=True)
        name = school_db.Column(school_db.String)
        teacher_id = school_db.Column(school_db.Integer, school_db.ForeignKey("teachers.id"))
        # teacher = db.relation("Teacher", backref=db.backref("teachers", uselist=False))

        def __init__(self, number, name, teacher_id):
            self.number = number
            self.name = name
            self.teacher_id = teacher_id


    class CourseEnrollment(school_db.Model): # junction table containing relationships between students and courses
        __bind_key__ = school_code
        __tablename__ = "course_enrollments"
        id = school_db.Column(school_db.Integer, primary_key=True)
        student_number = school_db.Column(school_db.Integer, school_db.ForeignKey("students.number"))
        course_number = school_db.Column(school_db.String, school_db.ForeignKey("courses.number"))

        def __init__(self, student_number, course_number):
            self.student_number = student_number
            self.course_number = course_number


    class AbstractTextbook(school_db.Model):
        __bind_key__ = school_code
        __tablename__ = "abstract_textbooks"
        id = school_db.Column(school_db.Integer, primary_key=True)
        abstract_id = school_db.Column(school_db.Integer)
        title = school_db.Column(school_db.String)
        cost = school_db.Column(school_db.Float)
        amount = school_db.Column(school_db.Integer)
        needed = school_db.Column(school_db.Integer)

        def __init__(self, title, cost, abstract_id, amount, needed):
            self.title = title
            self.cost = cost
            self.abstract_id = abstract_id
            self.amount = amount
            self.needed = needed


    class Textbook(school_db.Model): # table containing textbook information
        __bind_key__ = school_code
        __tablename__ = "textbooks"
        number = school_db.Column(school_db.Integer, primary_key=True)
        abstract_textbook_id = school_db.Column(school_db.Integer, school_db.ForeignKey("abstract_textbooks.id"))

        def __init__(self, number, abstract_textbook_id):
            self.number = number
            self.abstract_textbook_id = abstract_textbook_id


    class TextbookAssignment(school_db.Model): # junction table containing relationships between textbooks and courses
        __bind_key__ = school_code
        __tablename__ = "textbook_assignments"
        id = school_db.Column(school_db.Integer, primary_key=True)
        abstract_textbook_id = school_db.Column(school_db.String, school_db.ForeignKey("textbooks.abstract_textbook_id"))
        course_number = school_db.Column(school_db.String, school_db.ForeignKey("courses.number"))

        def __init__(self, abstract_textbook_id, course_number):
            self.abstract_textbook_id = abstract_textbook_id
            self.course_number = course_number


    class Transaction(school_db.Model):
        __bind_key__ = school_code
        __tablename__ = "transactions"
        id = school_db.Column(school_db.Integer, primary_key=True)
        date = school_db.Column(school_db.DateTime)
        textbook_condition = school_db.Column(school_db.Integer)
        origin_student_number = school_db.Column(school_db.Integer, school_db.ForeignKey("students.number"))
        destin_student_number = school_db.Column(school_db.Integer, school_db.ForeignKey("students.number"))
        textbook_number = school_db.Column(school_db.Integer, school_db.ForeignKey("textbooks.number"))
        transaction_cost = school_db.Column(school_db.Float)

        def __init__(self, textbook_condition, origin_student_number, destin_student_number, textbook_number, transaction_cost = 0):
            self.date = datetime.utcnow()
            self.textbook_condition = textbook_condition
            self.origin_student_number = origin_student_number
            self.destin_student_number = destin_student_number
            self.textbook_number = textbook_number
            self.transaction_cost = transaction_cost

    class Placeholder(school_db.Model):
        __bind_key__ = school_code
        __tablename__ = "placeholders"
        placeholder_id = school_db.Column(school_db.Integer, school_db.ForeignKey("abstract_textbooks.abstract_id"))
        abstract_textbook_id = school_db.Column(school_db.Integer, school_db.ForeignKey("abstract_textbooks.abstract_id"), primary_key = True)

        def __init__(self, placeholder_id, abstract_textbook_id):
            self.placeholder_id = placeholder_id
            self.abstract_textbook_id = abstract_textbook_id

    schools.add_school(school_code, Student, Teacher, Course, CourseEnrollment,
                      AbstractTextbook, Textbook, TextbookAssignment, Transaction, Placeholder)

    school_dbs[school_code] = school_db

    if not os.path.isfile("schools/{}.db".format(school_code)):
        school_db.create_all()



# where we can add and modify shit from specific dbs

sphs_db = school_dbs["sphs"]
sphs = schools.school_databases["sphs"]

# temporary solution until a better one can be implemented
def migrate():
    
    #adds new students
    data = get_new_data()
    for student in data["students"]:
        if not sphs.students.query.filter_by(number = data["students_dict"][student]).count():
            new_student = sphs.students(number = data["students_dict"][student], name = student)
            sphs_db.session.add(new_student)
    
    #deletes all previous teachers
    teachers = sphs.teachers.query.all()
    for teacher in teachers:
        sphs_db.session.delete(teacher)

    #adds current teachers
    for teacher in data["teachers"]:
        new_teacher = sphs.teachers(id = int(teacher[1]), name = teacher[0])
        sphs_db.session.add(new_teacher)

    #deletes all textbook assignments
    textbook_assignments = sphs.textbook_assignments.query.all()
    for assignment in textbook_assignments:
        sphs_db.session.delete(assignment)

    #deletes all course enrollments
    course_enrollments = sphs.course_enrollments.query.all()
    for enrollment in course_enrollments:
        sphs_db.session.delete(enrollment)
    
    #adds new course enrollments
    for enrollment in data["course_enrollments"]:
        new_enrollment = sphs.course_enrollments(student_number = int(enrollment[0]), course_number = str(enrollment[1]))
        sphs_db.session.add(new_enrollment)

    courses = sphs.courses.query.all()
    for course in courses:
        sphs_db.session.delete(course)
    
    for course in data["courses"]:
        new_course = sphs.courses(number = str(course[1]), name = course[0], teacher_id = int(course[2]))
        sphs_db.session.add(new_course)

    abstract_textbooks = sphs.abstract_textbooks.query.all()
    for textbook in abstract_textbooks:
        textbook.needed = 0
        textbook.amount = 0
    sphs_db.session.commit()

    # # remove destroyed textbooks
    # textbooks = sphs.textbooks.query.all()
    # for textbook in textbooks:
    #     textbook_transactions = sphs.transactions.query.filter_by(textbook_number = textbook.number).all()
    #     #if textbook is destroyed
    #     if textbook_transactions[-1].textbook_condition == 4:
    #         #clear the transactions
    #         for transaction in textbook_transactions:
    #             sphs_db.session.delete(transaction)
    #         sphs_db.session.delete(textbook)
    #     #if textbook is not returned by a student --> set it to lost
    #     elif textbook_transactions[-1].destin_student_number != 0:
    #         transaction = textbook_transactions[-1]
    #         transaction.textbook_condition = 5

    # recount all the statistics 

    for textbook in sphs.textbooks.query.all():
        textbook_transactions = sphs.transactions.query.filter_by(textbook_number = textbook.number).all()
        if textbook_transactions[-1].textbook_condition != 5:
            abstract_textbook = sphs.abstract_textbooks.query.filter_by(abstract_id = textbook.abstract_textbook_id).first()
            abstract_textbook.amount = abstract_textbook.amount + 1

    total_worth = 0
    for abstract_textbook in sphs.abstract_textbooks.query.all():
        total_worth += abstract_textbook.amount * abstract_textbook.cost

    current_school = School.query.filter_by(code = "sphs").first()
    current_school.textbooks_worth = total_worth
    current_school.money_owed = 0

    db.session.commit()
    sphs_db.session.commit()

# textbook = sphs.textbooks.query.filter_by(number = 9000000).first()
# sphs_db.session.delete(textbook)
# textbook = sphs.textbooks.query.filter_by(number = 9000003).first()
# sphs_db.session.delete(textbook)

# sphs_db.session.commit()

# for abstract_textbook in sphs.abstract_textbooks.query.all():
#     print(abstract_textbook.abstract_id)
#     needed_textbooks = 0
#     for assignment in sphs.textbook_assignments.query.filter_by(abstract_textbook_id = abstract_textbook.abstract_id).all():
#         needed_textbooks += sphs.course_enrollments.query.filter_by(course_number = assignment.course_number).count()
#     abstract_textbook.needed = needed_textbooks

# sphs_db.session.commit()

# transactions = sphs.transactions.query.all()
# for transaction in transactions:
#     transaction.transaction_cost = 0

# sphs_db.session.commit()

 # cost of textbooks
# textbooks = sphs.textbooks.query.all()
# print("# of textbooks:", len(textbooks))
# total_value = 0
# for cnt, textbook in enumerate(textbooks):
#     abstract_id = textbook.abstract_textbook_id
#     total_value += sphs.abstract_textbooks.query.filter_by(abstract_id = abstract_id).first().cost

# print("Total Textbook Value:", total_value)


# transactions = sphs.transactions.query.all()
# temp_dict = {}

# for idx, transaction in enumerate(transactions):
#     print(idx)
#     if(transaction.origin_student_number == None):
#         prev_student = 0
#         if transaction.textbook_number in temp_dict:
#             transaction.origin_student_number = 0
#         else:
#             temp_dict[transaction.textbook_number] = 1
#             transaction.origin_student_number = -1

# sphs_db.session.commit()

# abstract_textbooks = sphs.abstract_textbooks.query.all()

# for abstract_textbook in abstract_textbooks:
#     abstract_textbook.amount = sphs.textbooks.query.filter_by(abstract_textbook_id = abstract_textbook.abstract_id).count()
#     sphs_db.session.commit()

# user = User.query.filter_by(username = "sphsteacher").first()
# db.session.delete(user)
# db.session.commit()

# def add_user_temp(username, password, role, school_code):
#     user = User(username = username, password = guard.hash_password(password), school_code =school_code, role = role)
#     db.session.add(user)
#     db.session.commit()

#add_user_temp("sphsteacher", "gocrusaders2020", "teacher", "sphs")

