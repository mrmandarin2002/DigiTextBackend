import openpyxl
from pathlib import Path
import time

def get_new_data():

    start_time = time.time() #to time performance of code

    xlsx_file = Path('', 'sphsdata2021.xlsx')
    wb_obj = openpyxl.load_workbook(xlsx_file)

    enroll_ws = wb_obj["Enrollment"]
    courses_ws = wb_obj["Courses"]
    teachers_ws = wb_obj["Teachers"]

    #dictionaries for data for easy lookup
    teacher_dict = {}
    course_dict = {}
    students_num_dict = {}
    students_set = set()

    #iterators for the excel worksheets
    iterenroll = enroll_ws.values
    itercourses = courses_ws.values
    iterteachers = teachers_ws.values

    #skips first row
    next(iterenroll) 
    next(itercourses)
    next(iterteachers)

    #get course info
    # 0 --> course name
    # 1 --> course id
    # 2 --> teacher id
    courses = [(row[0], row[1], "N/A") for row in itercourses if row[0][0] != '*']
    for course in courses:
        course_dict[str(course[1])] = course[0]

    #get teacher info
    # 0 --> teacher name
    # 1 --> teacher id
    teachers = [(row[1] + ' ' + row[0], row[2]) for row in iterteachers]
    for teacher in teachers:
        teacher_dict[teacher[1]] = teacher[0]

    # 0 --> student_number
    # 1 --> course_number
    course_enrollments = []

    #get enrollment info
    #col 0 --> student number
    #col 1 --> grade
    #col 2 --> Last Name
    #col 3 --> First Name
    #col 4 --> course number
    #col 5 --> section number
    #col 6 --> teacher id
    for row in iterenroll:
        student_name = row[2] + ' ' + row[3]
        if student_name not in students_set:
            students_set.add(student_name)
            students_num_dict[student_name] = int(row[0])
        full_course = str(row[4]) + '.' + str(row[5])
        if full_course not in course_dict:
            course_name = course_dict[str(row[4])]
            course_dict[full_course] = course_name
            courses.append((course_name, full_course, row[6]))
        course_enrollments.append((int(row[0]), full_course))

    courses = [course for course in courses if course[2] != 'N/A']
    ''' 
    # print shit
    for student in list(students_set):
        print(student, students_num_dict[student])
    '''

    print("RUNTIME: ", time.time() - start_time)

    return {"students_dict" : students_num_dict, "students" : list(students_set), "teachers" : teachers, "course_enrollments" : course_enrollments, "course_dict" : course_dict, "courses" : courses}