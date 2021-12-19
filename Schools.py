class School_db:
    
    def __init__(self, students, teachers, courses, course_enrollments,
                 abstract_textbooks, textbooks, textbook_assignments,
                 transactions, placeholders):
        self.students = students
        self.teachers = teachers
        self.courses = courses
        self.course_enrollments = course_enrollments
        self.abstract_textbooks = abstract_textbooks
        self.textbooks = textbooks
        self.textbook_assignments = textbook_assignments
        self.transactions = transactions
        self.placeholders = placeholders


class Schools:

    def __init__(self):
        self.school_databases = {}

    def add_school(self, school_code, students, teachers, courses, course_enrollments,
                   abstract_textbooks, textbooks, textbook_assignments, transactions, placeholders):
        self.school_databases[school_code] = School_db(students, teachers, courses,
                                                       course_enrollments, abstract_textbooks,
                                                       textbooks, textbook_assignments, transactions, placeholders)

    def __getitem__(self, key):
        return self.school_databases[key]

    def school(self, user):
        return self[user.school_code]

    def session(self, user):
        return self.school_sessions[user.school_code]
