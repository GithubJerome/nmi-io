# pylint: disable=too-many-arguments, no-self-use, too-many-locals
""" Questions """
import random
import json
import time
import math

from library.postgresql_queries import PostgreSQL
from library.common import Common
from library.sha_security import ShaSecurity

class Questions(Common):
    """Class for Questions"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for Questions class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()
        super(Questions, self).__init__()

    def generate_questions(self, user_id, course_id, exercise_id, key):
        """ Generate Questionnaires based on settings """

        sql_str = "SELECT * FROM exercise WHERE exercise_id = '{0}'".format(exercise_id)
        sql_str += " AND course_id = '{0}'".format(course_id)
        result = self.postgres.query_fetch_one(sql_str)

        if result:

            # shuffle = result['shuffled']
            # question_types = result['question_types']
            # tags = result['tags']
            # cast = '"tags"'

            # qtype = ""
            # if question_types:
            #     qtype = ','.join("'{0}'".format(qtype) for qtype in question_types)

            sql_str = "SELECT * FROM course_question"
            sql_str += " WHERE course_id = '{0}'".format(course_id)
            sql_str += " AND exercise_id='{0}'".format(result['exercise_id'])

            # if shuffle is True:
            #     if question_types:
            #         sql_str += " AND question_type IN ({0})".format(qtype)

            #     if tags not in [None, [], str(['']), str([""]), ['']]:
            #         sql_str += " AND CAST({0} AS text) = '{1}'".format(cast, json.dumps(tags))

            questions = self.postgres.query_fetch_all(sql_str)

            number_to_draw = 10 # BY DEFAULT
            if result['number_to_draw']:
                number_to_draw = result['number_to_draw']

            # questions = self.select_questions(questions, number_to_draw, question_types, shuffle)
            questions = [question['course_question_id'] for question in questions]

            questions = questions[:number_to_draw]
            result['questions'] = questions

            self.add_student_exercise(user_id, course_id, key, result)
        return result

    def select_questions(self, questions, number_to_draw, question_type, shuffle):
        """ Return Questions by type """

        questionnaires = []

        if not question_type:
            question_type = ['FITBT', 'MULRE', 'MATCH', 'MULCH']
        limit = math.floor(number_to_draw / len(question_type))

        for qtype in question_type:
            qlist = [question['course_question_id'] for question in questions \
                     if question['question_type'] == qtype]

            if shuffle is True:
                # SHUFFLE QUESTIONS
                random.shuffle(qlist)

            qlist = qlist[:limit]
            questionnaires += qlist

        if len(questionnaires) != number_to_draw:

            draw_again = number_to_draw - len(questionnaires)
            qlist = [question['course_question_id'] for question in questions \
                     if question['question_type'] in question_type \
                     and question['course_question_id'] not in questionnaires]

            if shuffle is True:
                # SHUFFLE QUESTIONS
                random.shuffle(qlist)

            qlist = qlist[:draw_again]
            questionnaires += qlist

        return questionnaires

    def regenerate_questions(self, exercise_id, user_id, key):
        """ Generate Seed Questionnaires based on settings """

        sql_str = "SELECT * FROM exercise WHERE exercise_id = '{0}'".format(exercise_id)
        result = self.postgres.query_fetch_one(sql_str)
        shuffle = result['shuffled']
        question_types = result['question_types']
        tags = result['tags']
        cast = '"tags"'

        exercise_table = "{0}_exercise".format(key)
        questions_table = "{0}_exercise_questions".format(key)
        key_id = "{0}_exercise_id".format(key)

        sql_str = "SELECT * FROM {0} se  LEFT JOIN {1}".format(exercise_table, questions_table)
        sql_str += " seq ON se.{0} = seq.{0}".format(key_id)
        sql_str += " WHERE se.status is True AND se.exercise_id = '{0}'".format(exercise_id)
        result = self.postgres.query_fetch_all(sql_str)

        answered = [res['course_question_id'] for res in result if res['answer'] is not None]
        total_answered = len(answered)
        total = len(result)
        number_to_draw = total - total_answered

        qtype = ""
        if question_types:
            qtype = ','.join("'{0}'".format(qtype) for qtype in question_types)

        sql_str = "SELECT * FROM course_question"
        sql_str += " WHERE exercise_id='{0}'".format(result[0]['exercise_id'])
        if question_types:
            sql_str += " AND question_type IN ({0})".format(qtype)

        if answered:
            answered_questions = ','.join("'{0}'".format(ans) for ans in answered)
            sql_str += " AND course_question_id NOT IN ({0})".format(answered_questions)

        if tags:
            tags = ', '.join('"{0}"'.format(tag) for tag in tags)
            sql_str += " AND CAST({0} AS text) = '[{1}]'".format(cast, tags)

        questions = self.postgres.query_fetch_all(sql_str)
        questions = self.select_questions(questions, number_to_draw, question_types, shuffle)

        # DELETE ITEMS TO SHUFFLE NEW QUESTION(S)
        no_answer = [res['course_question_id'] for res in result if res['answer'] is None]
        self.delete_item_sequence(key, result[0][key_id], no_answer)

        # ADD STUDENT EXERCISE QUESTIONS
        next_item = self.get_next_sequence(result[0][key_id], key)
        if self.add_student_questions(result[0][key_id], key, questions,
                                      next_item, user_id):
            return 1
        return 0

    def delete_item_sequence(self, key, student_exercise_id, items):
        """ DELETE ITEMS TO BE SHUFFLED """

        key_exercise_id = "{0}_exercise_id".format(key)
        table = "{0}_exercise_questions".format(key)

        conditions = []

        conditions.append({
            "col": "course_question_id",
            "con": "in",
            "val": items
            })

        conditions.append({
            "col": key_exercise_id,
            "con": "=",
            "val": student_exercise_id
        })

        if self.postgres.delete(table, conditions):
            return 1

        return 0

    def get_next_sequence(self, student_exercise_id, key):
        """ Return next item sequence """

        table = "{0}_exercise_questions".format(key)
        key_id = "{0}_exercise_id".format(key)

        sql_str = "SELECT MAX(sequence) as sequence FROM {0}".format(table)
        sql_str += " WHERE {0}='{1}'".format(key_id, student_exercise_id)
        result = self.postgres.query_fetch_one(sql_str)

        if result['sequence'] is None:
            return 1

        return result['sequence'] + 1

    def add_student_exercise(self, user_id, course_id, key, data):
        """ Assign Exercise to Student """

        if data:

            key_exercise_id = "{0}_exercise_id".format(key)
            table = "{0}_exercise".format(key)
            # ADD EXERCISE

            temp = {}
            temp[key_exercise_id] = self.sha_security.generate_token(False)
            temp['exercise_id'] = data['exercise_id']
            temp['account_id'] = user_id
            temp['course_id'] = course_id
            temp['exercise_number'] = data['exercise_number']
            temp['status'] = True
            temp['created_on'] = time.time()

            add = self.postgres.insert(table, temp, key_exercise_id)

            # ADD QUESTIONS
            sequence = 1
            self.add_student_questions(add, key, data['questions'], sequence, user_id)

            return 1

        return 0

    def add_student_questions(self, exercise_id, key, questions, sequence, user_id):
        """ ADD STUDENT EXERCISE QUESTIONS BY SEED """

        key_exercise_id = "{0}_exercise_id".format(key)
        table = "{0}_exercise_questions".format(key)

        # ADD QUESTIONS
        for question in questions:

            tmp = {}
            tmp[key_exercise_id] = exercise_id
            tmp['account_id'] = user_id
            tmp['course_question_id'] = question
            tmp['sequence'] = sequence
            tmp['skip_times'] = 0

            self.postgres.insert(table, tmp, key_exercise_id)
            sequence += 1

        return 1

    # FOR COURSE DEVELOPMENT
    def get_question_by_id(self, question_id):
        """ Return Question Data by ID """

        sql_str = "SELECT * FROM questions WHERE question_id = '{0}'".format(question_id)
        result = self.postgres.query_fetch_one(sql_str)

        return result

    def get_questions_by_condition(self, question_types, tags):
        """ Return Question by type and tags """

        qtype = ','.join("'{0}'".format(qtype) for qtype in question_types)
        tag = '"tags"'

        sql_str = "SELECT * FROM questions WHERE question_type IN ({0})".format(qtype)
        if tags:
            tags = ', '.join('"{0}"'.format(tag) for tag in tags)
            sql_str += "AND CAST({0} AS text) = '[{1}]'".format(tag, tags)

        results = self.postgres.query_fetch_all(sql_str)

        return results

    def select_random_questions(self, questions, number_to_draw, question_type):
        """ Return Questions by type """

        questionnaires = []

        number_to_draw = int(number_to_draw)
        if not number_to_draw:
            number_to_draw = 10

        limit = math.floor(number_to_draw / len(question_type))

        for qtype in question_type:
            qlist = [question['question_id'] for question in questions \
                     if question['question_type'] == qtype]

            # SHUFFLE QUESTIONS
            random.shuffle(qlist)

            qlist = qlist[:limit]
            questionnaires += qlist

        if len(questionnaires) != number_to_draw:

            draw_again = number_to_draw - len(questionnaires)
            qlist = [question['question_id'] for question in questions \
                     if question['question_type'] in question_type \
                     and question['question_id'] not in questionnaires]

            # SHUFFLE QUESTIONS
            random.shuffle(qlist)

            qlist = qlist[:draw_again]
            questionnaires += qlist

        return questionnaires
