from database import *
from flask_praetorian import auth_required, current_user
from roles import staff_roles

def get_textbook(textbook_number):
    textbook = schools.school(current_user()).textbooks.query.get_or_404(textbook_number)
    # get textbook attributes from abstract class
    t_info = schools.school(current_user()).abstract_textbooks.query.get_or_404(textbook.abstract_textbook_id)
    # get who currently owns the textbook
    
    transactions = schools.school(current_user()).transactions.query.filter_by(textbook_number = textbook_number).all()
    cur_transaction = transactions[-1]
    cur_owner = cur_transaction.destin_student_number
    cur_owner_name = schools.school(current_user()).students.query.filter_by(number = cur_owner).first().name
    cur_condition = cur_transaction.textbook_condition
    placeholders = [placeholder.placeholder_id for placeholder in schools.school(current_user()).placeholders.query.filter_by(abstract_textbook_id = textbook.abstract_textbook_id).all()]
    return dict(placeholders = placeholders, number=textbook.number, abstract_textbook_id=textbook.abstract_textbook_id, cost = t_info.cost, title = t_info.title, owner = dict(name = cur_owner_name, id = cur_transaction.destin_student_number), condition = cur_condition)

#fuck list comprehensions so much clearer the normal way jesus fucking christ
#returns a student's courses and the textbooks associated with the course
def get_student_courses(student_number):
    if current_user().role in staff_roles:
        course_enrollments = schools.school(current_user()).course_enrollments.query.filter_by(student_number=student_number).all()
        courses = []
        for course in course_enrollments:
            textbook_assignments = schools.school(current_user()).textbook_assignments.query.filter_by(course_number=course.course_number).all()
            course_textbooks = []
            for assignment in textbook_assignments:
                textbook_info = schools.school(current_user()).abstract_textbooks.query.filter_by(abstract_id=assignment.abstract_textbook_id).first()
                course_textbooks.append(dict(abstract_textbook_id=int(assignment.abstract_textbook_id), title = textbook_info.title, cost = textbook_info.cost))
            courseInfo = schools.school(current_user()).courses.query.filter_by(number = course.course_number).first()
            teacherInfo = schools.school(current_user()).teachers.query.filter_by(id = courseInfo.teacher_id).first()
            course_dict = dict(id = course.id, teacher = teacherInfo.name, name = courseInfo.name, student_number = course.student_number, course_number = course.course_number, course_textbooks = course_textbooks)
            courses.append(course_dict)
        return {"course_enrollments": courses}    

def get_transaction_info(school_db, transaction):
    try:
        textbook_info = school_db.abstract_textbooks.query.filter_by(abstract_id = school_db.textbooks.query.filter_by(number = transaction.textbook_number).first().abstract_textbook_id).first()
        to_name = school_db.students.query.filter_by(number = transaction.destin_student_number).first().name
        from_name = "N/A"
        if transaction.origin_student_number != -1:
            from_name = school_db.students.query.filter_by(number = transaction.origin_student_number).first().name

        transaction_type = "WITHDRAW"

        if transaction.destin_student_number == 0 and transaction.origin_student_number == -1:
            transaction_type = "ADD"
        elif transaction.destin_student_number == 0:
            transaction_type = "RETURN"

        return {"transaction_type" : transaction_type, "textbook_info" : {"title" : textbook_info.title, "cost" : textbook_info.cost},"date" : transaction.date, "textbook_condition" : transaction.textbook_condition, "transaction_cost" : transaction.transaction_cost, "from" : from_name,"to" : to_name}
    except Exception as e:
        print(e)
        return {}