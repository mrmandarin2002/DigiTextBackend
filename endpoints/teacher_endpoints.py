from flask import Blueprint
from flask_praetorian import auth_required, current_user
import time

from database import schools
from roles import staff_roles

teachers = Blueprint("teachers", "teachers")

# returns list of teachers with relevant course and textbook info
# too slow, currently runs in about 0.6 seconds.... 
@teachers.route("/teachers")
@auth_required
def get_teachers():
    if current_user().role in staff_roles:
        t1 = time.time()
        teachers = schools.school(current_user()).teachers.query.all()
        teacher_list = []
        for teacher in teachers:
            teacher_courses = schools.school(current_user()).courses.query.filter_by(teacher_id = teacher.id).all()
            if teacher_courses:
                teacher_courses_list = [{"name" : course.name, "course_number" : course.number, "teacher" : teacher.name, "textbooks" : [{"id" : textbook.abstract_textbook_id} for textbook in schools.school(current_user()).textbook_assignments.query.filter_by(course_number = course.number).all()]} for course in teacher_courses]
                teacher_list.append(dict(id=teacher.id, name=teacher.name, courses = teacher_courses_list))
        print("GET TEACHER RUNTIME:", time.time() - t1)
        return {"teachers": teacher_list}
