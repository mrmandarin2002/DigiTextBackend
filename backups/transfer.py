import sqlite3
from datetime import datetime

def get_students(conn):
    # create a cursor object
    cur = conn.cursor()
    # execute an sql command string
    cur.execute("SELECT * FROM Students WHERE 1")
    # return the results of the query
    result = cur.fetchall()
    cur.close()
    return result

def get_textbooks(conn):
    # create a cursor object
    cur = conn.cursor()
    # execute an sql command string
    cur.execute("SELECT * FROM Textbooks WHERE 1")
    # return the results of the query
    result = cur.fetchall()
    cur.close()
    return result

def get_courses(conn):
    # create a cursor object
    cur = conn.cursor()
    # execute an sql command string
    cur.execute("SELECT * FROM Courses WHERE 1")
    # return the result of the query
    result = cur.fetchall()
    cur.close()
    return result

def insert_student(conn, student_number, student_name):
    # create a cursor object
    cur = conn.cursor()
    # createa an sql command string
    sql_cmd = "INSERT INTO students(number, name) VALUES(?,?)"
    # execute sql command string
    cur.execute(sql_cmd, (int(student_number), student_name))
    # close cursor and commit changes
    cur.close()
    conn.commit()

def insert_teacher(conn, teacher_name, teacher_id):
    # create a cursor object
    cur = conn.cursor()
    # createa an sql command string
    sql_cmd = "INSERT INTO teachers(id, name) VALUES(?,?)"
    # execute sql command string
    cur.execute(sql_cmd, (int(teacher_id), teacher_name))
    # close cursor and commit changes
    cur.close()
    conn.commit()

def insert_course(conn, course_number, course_name, teacher_id):
    # create a cursor object
    cur = conn.cursor()
    # create an sql command string
    sql_cmd = "INSERT INTO courses(number, name, teacher_id) VALUES(?,?,?)"
    # execute sql command string
    cur.execute(sql_cmd, (course_number, course_name, int(teacher_id)))

def insert_course_enrollment(conn, student_number, course_number):
    # create cursor object
    cur = conn.cursor()
    # create an sql command string
    sql_cmd = "INSERT INTO course_enrollments(student_number, course_number) VALUES(?,?)"
    # execute sql command string
    cur.execute(sql_cmd, (int(student_number), str(course)))
    # close cursor and commit changes
    cur.close()
    conn.commit()

def insert_abstract_textbook(conn, title, cost):
    # create cursor object
    cur = conn.cursor()
    # create an sql command string
    sql_cmd = "INSERT INTO abstract_textbooks(title, cost) VALUES(?,?)"
    # execute sql command string
    cur.execute(sql_cmd, (title, float(cost)))
    # close cursor and commit changes
    cur.close()
    conn.commit()
    # return id of inserted abstract textbook
    return cur.lastrowid

def insert_textbook(conn, number, abstract_textbook_id):
    # create cursor object
    cur = conn.cursor()
    # create an sql command string
    sql_cmd = "INSERT INTO textbooks(number, abstract_textbook_id) VALUES(?,?)"
    # execute sql command string
    cur.execute(sql_cmd, (int(number), abstract_textbook_id))
    # close cursor and commit changes
    cur.close()
    conn.commit()
    # return id of inserted textbook
    return cur.lastrowid

def insert_textbook_assignment(conn, abstract_textbook_id, course_number):
    # create cursor object
    cur = conn.cursor()
    # create an sql command string
    sql_cmd = "INSERT INTO textbook_assignments(abstract_textbook_id, course_number) VALUES(?,?)"
    # execute sql command string
    cur.execute(sql_cmd, (int(abstract_textbook_id), course_number))
    # close cursor and commit changes
    cur.close()
    conn.commit()

def insert_transaction(conn, condition, student_number, textbook_number):
    # create cursor object
    cur = conn.cursor()
    # create an sql command string
    sql_cmd = "INSERT INTO transactions(textbook_condition, student_number, textbook_number) VALUES(?,?,?)"
    cur.execute(sql_cmd, (int(condition), int(student_number), int(textbook_number)))
    # close cursor and commit changes
    cur.close()
    conn.commit()


if __name__ == "__main__":

    old_conn = sqlite3.connect("server.db")
    new_conn = sqlite3.connect("data.db")

    # transfer student information
    print("Transfering student information...")
    for student in get_students(old_conn):
        _1, student_number, student_name, _2, courses = student
        print(student_name)
        courses = courses.split("|")
        if courses[0] == "":
            courses = []
        try:
            insert_student(new_conn, student_number, student_name)
        except sqlite3.IntegrityError:
            print(student)
        for course in courses:
            insert_course_enrollment(new_conn, student_number, course)

    # count duplicates
    nums = []
    duplicated = []
    count = 0
    for textbook in get_textbooks(old_conn):
        if textbook[1] in nums:
            duplicated.append(textbook[1])
            count += 1
        else:
            try:
                nums.append(int(textbook[1]))
            except:
                print(textbook)

    # i = 70000000
    # barcode_nums = []
    # while len(barcode_nums) < 10000:
    #     if i not in nums:
    #         barcode_nums.append(str(i))
    #         print(len(barcode_nums))
    #     i += 1
    # open("barcodes.txt", "w").write("\n".join(barcode_nums))
    # # print(count)

    textbooks = []
    for num in duplicated:
        cur = old_conn.cursor()
        cur.execute("SELECT * FROM Textbooks WHERE TextbookNumber='{}'".format(num))
        result = cur.fetchall()
        for textbook in result:
            textbooks.append(", ".join(list(map(str, textbook))))
        cur.close()
    open("discarded.txt", "w").write("\n".join(textbooks))

    # transfer textbook data
    abstract_textbooks = {}
    discarded = []
    for textbook in get_textbooks(old_conn):
        _1, number, title, cost, condition, student_number = textbook
        print(number)
        # insert abstract textbook if needed
        if title not in abstract_textbooks:
            abstract_textbook_id = insert_abstract_textbook(new_conn, title, cost)
            abstract_textbooks[title] = abstract_textbook_id
        try:
            # insert textbook
            textbook_id = insert_textbook(new_conn, number, abstract_textbooks[title])
            # insert transaction to school
            insert_transaction(new_conn, condition, 0, number)
            # if the textbook is currently with a student, create transaction accordingly
            if student_number:
                insert_transaction(new_conn, condition, student_number, textbook_id)
        except:
            discarded.append(textbook)
    open("discarded_textbooks.txt", "w").write("\n".join([",".join(list(map(str, i))) for i in discarded]))

    # insert teacher data
    teachers = [i.split("|") for i in open("teachers.txt").read().split("\n")]
    for teacher in teachers:
        last_name, first_name, teacher_id = teacher
        insert_teacher(new_conn, first_name + " " + last_name, teacher_id)

    # insert course data
    courses = [i.split(",") for i in open("courses.txt").read().split("\n")]
    course_names = {i.split(",")[1]: i.split(",")[0] for i in open("course_names.txt").read().split("\n")}
    for course in courses:
        course_num, section_num, teacher_id = course
        insert_course(new_conn, course_num+"."+section_num, course_names[course_num], teacher_id)

    # insert textbook assignments
    for course in get_courses(old_conn):
        course = _, course_num, course_name, teacher_name, textbooks = course
        textbooks = textbooks.split("|")
        if textbooks[0] != "":
            for textbook in textbooks:
                insert_textbook_assignment(new_conn, abstract_textbooks[textbook], course_num)

    old_conn.close()
    new_conn.close()