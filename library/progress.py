# pylint: disable=too-many-locals, no-member
""" Progress """

import time

from library.postgresql_queries import PostgreSQL
from library.common import Common
from library.sha_security import ShaSecurity

class Progress(Common):
    """Class for Progress"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for Progress class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()
        super(Progress, self).__init__()

    def update_score_progress(self, user_id, exercise_id, key):
        """ UPDATE SCORE AND PROGRESS """

        exercise_table = "{0}_exercise".format(key)
        sql_str = "SELECT * FROM {0}".format(exercise_table)
        sql_str += " WHERE exercise_id='{0}'".format(exercise_id)
        sql_str += " AND account_id='{0}' AND status is True".format(user_id)
        result = self.postgres.query_fetch_one(sql_str)

        if result:

            # QUESTIONS
            column_id = "{0}_exercise_id".format(key)

            sql_str = "SELECT * FROM {0}_exercise_questions".format(key)
            sql_str += " WHERE {0} = '{1}'".format(column_id, result[column_id])
            questions = self.postgres.query_fetch_all(sql_str)

            score = 0
            for question in questions:
                ans = self.check_answer(question['course_question_id'], question['answer'])

                if ans['isCorrect'] is True:
                    score += 1

            # UPDATE PROGRESS
            progress = self.check_progress(questions)

            # PERCENT SCORE
            total = len(questions)
            percent_score = self.format_progress((score / total) * 100)

            # UPDATE SCORE
            tmp = {}
            tmp['score'] = score
            tmp['progress'] = progress
            tmp['percent_score'] = percent_score
            if key.upper() == "STUDENT":
                tmp['end_on'] = time.time()

            tmp['update_on'] = time.time()
            conditions = []

            conditions.append({
                "col": "exercise_id",
                "con": "=",
                "val": exercise_id
            })

            conditions.append({
                "col": column_id,
                "con": "=",
                "val": result[column_id]
            })

            data = self.remove_key(tmp, "exercise_id")

            self.postgres.update(exercise_table, data, conditions)

    def update_subsection_progress(self, user_id, exercise_id, key):
        """ Update Course Progress """

        exercise_table = "{0}_exercise".format(key)
        subsection_table = "{0}_subsection".format(key)
        exercise_questions_table = "{0}_exercise_questions".format(key)
        key_subsection_id = "{0}_subsection_id".format(key)
        key_exercise_id = "{0}_exercise_id".format(key)

        sql_str = "SELECT * FROM exercise e LEFT JOIN {0}".format(subsection_table)
        sql_str += " sub ON e.subsection_id = sub.subsection_id"
        sql_str += " WHERE e.exercise_id='{0}'".format(exercise_id)
        subsection = self.postgres.query_fetch_one(sql_str)

        student_subsection_id = subsection[key_subsection_id]
        subsection_id = subsection['subsection_id']
        course_id = subsection['course_id']

        sql_str = "SELECT answer, percent_score FROM {0}".format(exercise_questions_table)
        sql_str += " WHERE {0} IN (SELECT {0}".format(key_exercise_id)
        sql_str += " FROM {0} WHERE status is True AND".format(exercise_table)
        sql_str += " account_id='{0}' AND".format(user_id)
        sql_str += "  exercise_id IN (SELECT exercise_id FROM exercise WHERE "
        sql_str += "  subsection_id='{0}' AND status is True))".format(subsection_id)
        student_exercise = self.postgres.query_fetch_all(sql_str)

        answer = [dta['answer'] for dta in student_exercise]
        total = len(answer)
        not_answer = [None, '', []]
        total_answer = len([ans for ans in answer if ans not in not_answer])
        # print("Total: {0} Answer: {1}".format(total, total_answer))
        progress = 0
        if total_answer:
            progress = self.format_progress((total_answer / total) * 100)

        # PERCENT SCORE
        percent_score = [dta['percent_score'] for dta in student_exercise]
        total = len(percent_score)
        percent_100 = len([dta['percent_score'] for dta in student_exercise \
                           if dta['percent_score'] is not None and \
                           int(dta['percent_score']) == 100])

        percent_score = self.format_progress((percent_100 / total) * 100)

        # UPDATE PROGRESS
        conditions = []

        conditions.append({
            "col": key_subsection_id,
            "con": "=",
            "val": student_subsection_id
        })

        conditions.append({
            "col": "course_id",
            "con": "=",
            "val": course_id
        })

        data = {}
        data['progress'] = progress
        data['percent_score'] = percent_score
        data['update_on'] = time.time()

        self.postgres.update(subsection_table, data, conditions)

    def update_section_progress(self, user_id, exercise_id, key):
        """ Update Course Progress """

        section_table = "{0}_section".format(key)
        key_section_id = "{0}_section_id".format(key)
        exercise_question_table = "{0}_exercise_questions".format(key)
        key_exercise_id = "{0}_exercise_id".format(key)
        exercise_table = "{0}_exercise".format(key)

        sql_str = "SELECT * FROM exercise e"
        sql_str += " LEFT JOIN {0} ss ON e.section_id = ss.section_id".format(section_table)
        sql_str += " WHERE e.exercise_id='{0}'".format(exercise_id)
        section = self.postgres.query_fetch_one(sql_str)

        section_id = section['section_id']
        course_id = section['course_id']
        student_section_id = section[key_section_id]

        sql_str = "SELECT answer, percent_score FROM {0}".format(exercise_question_table)
        sql_str += " WHERE {0} IN (SELECT {0}".format(key_exercise_id)
        sql_str += " FROM {0} WHERE status is True AND".format(exercise_table)
        sql_str += " account_id='{0}' AND".format(user_id)
        sql_str += " exercise_id IN (SELECT exercise_id FROM exercise WHERE "
        sql_str += " section_id='{0}' AND status is True))".format(section_id)
        student_exercise = self.postgres.query_fetch_all(sql_str)

        answer = [dta['answer'] for dta in student_exercise]
        total = len(answer)
        not_answer = [None, '', []]
        total_answer = len([ans for ans in answer if ans not in not_answer])

        progress = 0
        if total_answer:
            progress = self.format_progress((total_answer / total) * 100)

        # PERCENT SCORE
        percent_100 = len([dta['percent_score'] for dta in student_exercise \
                           if dta['percent_score'] is not None and \
                           int(dta['percent_score']) == 100])

        percent_score = self.format_progress((percent_100 / total) * 100)

        # UPDATE PROGRESS
        conditions = []

        conditions.append({
            "col": key_section_id,
            "con": "=",
            "val": student_section_id
        })

        conditions.append({
            "col": "course_id",
            "con": "=",
            "val": course_id
        })

        data = {}
        data['progress'] = progress
        data['percent_score'] = percent_score
        data['update_on'] = time.time()

        self.postgres.update(section_table, data, conditions)


    def update_course_progress(self, user_id, exercise_id, key):
        """ Update Course Progress """

        exercise_table = "{0}_exercise".format(key)
        exercise_question_table = "{0}_exercise_questions".format(key)
        key_exercise_id = "{0}_exercise_id".format(key)
        course_table = "{0}_course".format(key)

        sql_str = "SELECT * FROM {0} WHERE".format(exercise_table)
        sql_str += " exercise_id='{0}' AND status=true".format(exercise_id)
        sql_str += " AND account_id='{0}'".format(user_id)
        student_course = self.postgres.query_fetch_one(sql_str)
        course_id = student_course['course_id']

        sql_str = "SELECT answer, percent_score FROM {0}".format(exercise_question_table)
        sql_str += " WHERE {0} IN (SELECT {0}".format(key_exercise_id)
        sql_str += " FROM {0} WHERE status is True AND".format(exercise_table)
        sql_str += "  account_id='{0}' AND status is True)".format(user_id)
        student_exercise = self.postgres.query_fetch_all(sql_str)

        answer = [dta['answer'] for dta in student_exercise]
        total = len(answer)

        not_answer = [None, '', []]
        total_answer = len([ans for ans in answer if ans not in not_answer])

        progress = self.format_progress((total_answer / total) * 100)

        # PERCENT SCORE
        percent_score = [dta['percent_score'] for dta in student_exercise]
        total = len(percent_score)
        percent_100 = len([dta['percent_score'] for dta in student_exercise \
                           if dta['percent_score'] is not None and \
                           int(dta['percent_score']) == 100])

        percent_score = self.format_progress((percent_100 / total) * 100)

        # UPDATE PROGRESS
        conditions = []

        conditions.append({
            "col": "account_id",
            "con": "=",
            "val": user_id
        })

        conditions.append({
            "col": "course_id",
            "con": "=",
            "val": course_id
        })

        data = {}
        data['progress'] = progress
        data['percent_score'] = percent_score
        data['update_on'] = time.time()

        self.postgres.update(course_table, data, conditions)

        if key == 'student':

            self.all_progress(user_id)
            self.group_progress(user_id)

    def all_progress(self, user_id):
        """ UPDATE ALL PROGRESS """

        sql_str = "SELECT progress FROM student_course WHERE"
        sql_str += " account_id='{0}' AND status='t'".format(user_id)
        progress = self.postgres.query_fetch_all(sql_str)

        total_prog = 0
        total_course = len(progress) * 100
        for pgrss in progress:

            total_prog = total_prog + float(pgrss['progress'])

        average = self.format_progress((total_prog/total_course) * 100)

        # UPDATE PROGRESS
        conditions = []

        conditions.append({
            "col": "id",
            "con": "=",
            "val": user_id
        })

        data = {}
        data['progress'] = average
        data['update_on'] = time.time()

        self.postgres.update('account', data, conditions)

        return 1

    def group_progress(self, user_id):
        """ UPDATE GROUP PROGRESS """

        sql_str = "SELECT user_group_id FROM user_group_students WHERE"
        sql_str += " student_id='{0}'".format(user_id)

        user_group = self.postgres.query_fetch_all(sql_str)

        # UPDATE GROUP
        for sgroup in user_group:

            user_group_id = sgroup['user_group_id']

            # GET ALL USER PROGRESS IN A GROUP
            sql_str = "SELECT progress FROM account WHERE id IN ("
            sql_str += "SELECT student_id FROM user_group_students WHERE"
            sql_str += " user_group_id='{0}')".format(user_group_id)
            progress = self.postgres.query_fetch_all(sql_str)

            total_prog = 0
            total_student = len(progress) * 100

            for pgrss in progress:

                total_prog = total_prog + float(pgrss['progress'])

            # GET AVERAGE PROGRESS
            average = self.format_progress((total_prog/total_student) * 100)

            # UPDATE PROGRESS
            conditions = []

            conditions.append({
                "col": "user_group_id",
                "con": "=",
                "val": user_group_id
            })

            # GET LEAST PERFORMER
            sql_str = "SELECT id, ROUND(cast(progress as numeric),2) AS progress"
            sql_str += " FROM account WHERE id IN (SELECT student_id FROM"
            sql_str += " user_group_students WHERE"
            sql_str += " user_group_id='{0}')".format(user_group_id)
            sql_str += " ORDER BY progress ASC"
            student = self.postgres.query_fetch_one(sql_str)

            # UPDATE GROUP PROGRESS
            data = {}
            data['least_performer'] = student['id']
            data['progress'] = average
            data['update_on'] = time.time()

            self.postgres.update('user_group', data, conditions)

        return 1
