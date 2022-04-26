# pylint: disable=no-self-use, too-many-arguments, too-many-branches, too-many-public-methods, bare-except, unidiomatic-typecheck, no-member, anomalous-backslash-in-string
"""Common"""
import json
import time
import math
import random
import calendar
import syslog
from datetime import datetime, timedelta
import re
import simplejson
import dateutil.relativedelta

from flask import jsonify
from library.postgresql_queries import PostgreSQL
from library.log import Log

class Common():
    """Class for Common"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for Common class"""
        self.log = Log()
        self.epoch_default = 26763
        # INITIALIZE DATABASE INFO
        self.postgres = PostgreSQL()

    # RETURN DATA
    def return_data(self, data, userid=None):
        """Return Data"""
        if userid:

            data = self.update_translate(data, userid)

        # RETURN
        return jsonify(
            data
        )

    # REMOVE KEY
    def remove_key(self, data, item):
        """Remove Key"""

        # CHECK DATA
        if item in data:

            # REMOVE DATA
            del data[item]

        # RETURN
        return data

    def get_user_info(self, columns, table, user_id, token):
        """Return User Information"""
        # CHECK IF COLUMN EXIST,RETURN 0 IF NOT
        if not columns:
            return 0

        # INITIALIZE
        cols = ''
        count = 1

        # LOOP COLUMNS
        for data in columns:

            # CHECK IF COUNT EQUAL COLUMN LENGHT
            if len(columns) == count:

                # ADD DATA
                cols += data

            else:

                # ADD DATA
                cols += data + ", "

            # INCREASE COUNT
            count += 1

        # CREATE SQL QUERY
        sql_str = "SELECT " + cols + " FROM " + table + " WHERE "
        sql_str += " token = '" + token + "'"
        sql_str += " AND account_id = '" + user_id + "'"
        sql_str += " AND status = 'true'"

        # CALL FUNCTION QUERY ONE
        ret = self.postgres.query_fetch_one(sql_str)

        # RETURN
        return ret

    def get_account_status(self, account_id):
        """ GET ACCOUNT STATUS """

        # CREATE SQL QUERY
        sql_str = "SELECT status FROM account WHERE"
        sql_str += " id='{0}'".format(account_id)

        # CALL FUNCTION QUERY ONE
        res = self.postgres.query_fetch_one(sql_str)

        if res:

            return res['status']

        return 0

    def update_token_data(self, account_id, request_info):
        """ UPDATE TOKEN DATA """

        data = {}
        data['update_on'] = time.time()
        data['status'] = True

        conditions = []

        conditions.append({
            "col": "account_id",
            "con": "=",
            "val": account_id
            })

        conditions.append({
            "col": "remote_addr",
            "con": "=",
            "val": request_info.remote_addr
            })

        conditions.append({
            "col": "platform",
            "con": "=",
            "val": request_info.user_agent.platform
            })

        conditions.append({
            "col": "browser",
            "con": "=",
            "val": request_info.user_agent.browser
            })

        conditions.append({
            "col": "version",
            "con": "=",
            "val": request_info.user_agent.version
            })

        self.postgres.update('account_token', data, conditions)

        return 1

    def validate_token(self, token, user_id, request_info):
        """Validate Token"""

        # CHECK ACCOUNT STATUS
        status = self.get_account_status(user_id)

        p_status = "status: {0}".format(status)
        syslog.syslog(p_status)

        if not status:

            return 0

        # SET COLUMN FOR RETURN
        columns = ['account_id', 'update_on']

        # CHECK IF TOKEN EXISTS
        user_data = self.get_user_info(columns, "account_token", user_id, token)

        p_user_data = "user_data: {0}".format(user_data)
        syslog.syslog(p_user_data)

        self.postgres = PostgreSQL()

        # CHECK IF COLUMN EXIST,RETURN 0 IF NOT
        if user_data:

            dt1 = datetime.fromtimestamp(user_data['update_on'])
            dt2 = datetime.fromtimestamp(time.time())
            dateutil.relativedelta.relativedelta(dt2, dt1)

            rd1 = dateutil.relativedelta.relativedelta(dt2, dt1)
            # print(rd1.years, rd1.months, rd1.days, rd1.hours, rd1.minutes, rd1.seconds)

            if rd1.years or rd1.months or rd1.days or rd1.hours:

                return 0

            if rd1.minutes > 30:

                return 0

        else:

            return 0

        self.update_token_data(user_id, request_info)
        # RETURN
        return 1

    # COUNT DATA
    def count_data(self, datas, column, item):
        """Return Data Count"""

        # INITIALIZE
        count = 0

        # LOOP DATAS
        for data in datas:

            # CHECK OF DATA
            if data[column] == item:

                # INCREASE COUNT
                count += 1

        # RETURN
        return count

    def set_return(self, datas):
        """Set Return"""
        ret_data = {}
        ret_data['data'] = []
        for data in datas:
            ret_data['data'].append(data['value'])

        return ret_data

    def check_request_json(self, query_json, important_keys):
        """Check Request Json"""
        query_json = simplejson.loads(simplejson.dumps(query_json))

        for imp_key in important_keys.keys():

            if imp_key not in query_json:
                return 0

            if type(query_json.get(imp_key)):

                if type(query_json[imp_key]) != type(important_keys[imp_key]):

                    return 0

            else:

                return 0

        return 1

    def limits(self, rows, limit, page):
        """Limits"""
        skip = int((page - 1) * limit)

        limit = skip + limit

        return rows[skip:limit]

    def param_filter(self, temp_datas, params, checklist):
        """Parameter Filter"""
        if not params:

            return temp_datas

        param_datas = []
        param_datas = temp_datas

        output = []

        i = 0

        for param in params:
            key = checklist[i]

            i += 1

            for data in param_datas:

                if self.filter_checker(str(param), str(data[key])):

                    output.append(data)

        return output

    def filter_checker(self, pattern, value):
        """Check Filter"""
        if '*' in pattern:
            pattern = pattern.replace('.', r'\.')
            if pattern == "*":
                pattern = "."

            if not pattern[0] == "*" and pattern != ".":
                pattern = "^" + str(pattern)

            if pattern[-1] == "*":
                pattern = pattern[:-1] + '+'

            if not pattern[-1] == "+" and pattern != ".":
                pattern = str(pattern) + '$'

            if pattern[0] == "*":
                pattern = '.?' + pattern[1:]

            pattern = pattern.replace('*', '.+')

            # print("pattern: ", pattern)

            try:

                if not re.findall(pattern, value, re.IGNORECASE):

                    return 0

            except:

                return 0

        else:

            if not value == pattern:

                return 0

        return 1

    def isfloat(self, data):
        """Check if float"""
        try:
            if data == "infinity":
                return False

            float(data)
        except ValueError:
            return False
        else:
            return True

    def isint(self, data):
        """Check if Integer"""
        try:
            if data == "infinity":
                return False

            tmp_data1 = float(data)
            tmp_data2 = int(tmp_data1)
        except ValueError:
            return False
        else:
            return tmp_data1 == tmp_data2

    def file_replace(self, filename):
        """ File Naming """

        file_name = filename.split(".")[0]

        if "_" in file_name:

            suffix = file_name.split("_")[-1]

            if suffix.isdigit():
                new_name = filename.replace(suffix, str(int(suffix) + 1))
            else:
                new_name = filename.replace(suffix, str(suffix+"_1"))
        else:
            new_name = filename.replace(file_name, str(file_name+"_1"))

        return new_name

    def format_filter(self, datas):
        """ Return Filter in Format """

        tmp = []

        for data in datas:

            tmp.append({
                "label": data,
                "value": data
            })

        return tmp

    def data_filter(self, datas, key):
        """Filter Data"""
        temp_data = []

        if datas and key:

            key = "{0}s".format(key)

            data_list = []
            for data in datas[key]:

                data_list.append(data)

            for data in data_list:
                if data in [True, False]:
                    data = "{0}".format(data)

                if key == "statuss":

                    if data == "True":
                        data = "Enabled"

                    if data == "False":
                        data = "Disabled"

                temp_data.append({
                    "label": data,
                    "value": data
                    })


        return  temp_data

    def days_update(self, timestamp, count=0, add=False):
        """Days Update"""
        try:

            named_tuple = time.localtime(int(timestamp))

            # GET YEAR MONTH DAY
            year = int(time.strftime("%Y", named_tuple))
            month = int(time.strftime("%m", named_tuple))
            day = int(time.strftime("%d", named_tuple))

            # Date in tuple
            date_tuple = (year, month, day, 0, 0, 0, 0, 0, 0)

            local_time = time.mktime(date_tuple)
            orig = datetime.fromtimestamp(local_time)

            if add:

                new = orig + timedelta(days=count)

            else:

                new = orig - timedelta(days=count)

            return new.timestamp()

        except:

            return 0

    def check_progress(self, data):
        """ RETURN PROGRESS """

        assert data, "Data is a must."

        answer = [dta['answer'] for dta in data]
        total = len(answer)
        not_answer = [None, '', []]
        total_answer = len([ans for ans in answer if ans not in not_answer])

        average = self.format_progress((total_answer / total) * 100)

        return average

    def format_progress(self, progress):
        """ Format Progress """

        progress = round(progress, 2)
        if progress.is_integer():
            return int(progress)

        return progress

    def validate_user(self, userid, user_role):
        """ VALIDATE USER TYPE """

        sql1 = "SELECT role_id FROM account_role WHERE"
        sql1 += " account_id='{0}'".format(userid)

        sql_str = "SELECT role_name FROM role WHERE"
        sql_str += " role_id IN ({0})".format(sql1)

        role = self.postgres.query_fetch_one(sql_str)
        role_name = role['role_name']

        if role_name == user_role:

            return 1

        return 0

    def check_answer(self, question_id, answer, userid=None):
        """Return Answer"""

        # DATA
        sql_str = "SELECT e.*, cq.* FROM course_question cq"
        sql_str += " LEFT JOIN exercise e ON cq.exercise_id = e.exercise_id"
        sql_str += " WHERE course_question_id = '{0}'".format(question_id)
        result = self.postgres.query_fetch_one(sql_str)

        data = {}

        if result:

            if result['question_type'] == 'FITBT':

                question = result['question']['question'].replace("<ans>", "")

                if question == answer:

                    if result['moving_allowed'] is False:
                        data['message'] = "You cannot skip this question"
                        data['isCorrect'] = False

                    else:
                        data['message'] = "No answer given"
                        data['isCorrect'] = False

                    if userid:
                        data['message'] = self.translate(userid, data['message'])

                    return data

            if result['question_type'] == 'FITBD':

                question = result['question']['question'].replace("<ans>", "")

                if question == answer:
                    data['message'] = "No answer given"
                    data['isCorrect'] = False

                    if userid:
                        data['message'] = self.translate(userid, data['message'])

                    return data

            if answer in [None,'', str( [""]), str([]), str(['']), [], ['']]:
                if result['moving_allowed'] is False:
                    data['message'] = "You cannot skip this question"
                    data['isCorrect'] = False
                else:
                    data['message'] = "No answer given"
                    data['isCorrect'] = False

                if userid:
                    data['message'] = self.translate(userid, data['message'])

                return data

            # FITBD
            if result['question_type'] in ['FITBD']:

                correct_answer = result['correct_answer']['answer']

                if answer in correct_answer:
                    data['message'] = result['correct']
                    data['isCorrect'] = True
                else:
                    data['message'] = result['incorrect']
                    data['isCorrect'] = False

                if userid:
                    data['message'] = self.translate(userid, data['message'])

                return data

            if result['question_type'] in ['MULRE', 'MATCH']:

                correct_answer = result['correct_answer']['answer']

                if len(correct_answer) != len(answer):
                    data['message'] = result['incorrect']
                    data['isCorrect'] = False

                    if userid:
                        data['message'] = self.translate(userid, data['message'])

                    return data

                # MATCH
                if result['question_type'] == 'MATCH':
                    if answer == correct_answer:
                        data['message'] = result['correct']
                        data['isCorrect'] = True
                    else:
                        data['message'] = result['incorrect']
                        data['isCorrect'] = False

                    if userid:
                        data['message'] = self.translate(userid, data['message'])

                    return data

                # MULRE
                if result['shuffle_answers'] is False:
                    if answer == correct_answer:
                        data['message'] = result['correct']
                        data['isCorrect'] = True
                    else:
                        data['message'] = result['incorrect']
                        data['isCorrect'] = False

                else:
                    score = 0
                    for ans in answer:
                        if ans in correct_answer:
                            score += 1

                    if score == len(correct_answer):
                        data['message'] = result['correct']
                        data['isCorrect'] = True
                    else:
                        data['message'] = result['incorrect']
                        data['isCorrect'] = False

                if userid:
                    data['message'] = self.translate(userid, data['message'])

                return data

            ans = {}
            ans["answer"] = answer

            if str(result['correct_answer']) == str(ans):
                data['message'] = result['correct']
                data['isCorrect'] = True
            else:
                data['message'] = result['incorrect']
                data['isCorrect'] = False

        if userid:

            data['message'] = self.translate(userid, data['message'])

        return data

    def translate(self, user_id, message):
        """ Return Translation """

        sql_str = "SELECT language FROM account WHERE"
        sql_str += " id='{0}'".format(user_id)
        language = self.postgres.query_fetch_one(sql_str)

        if language['language'] != 'en-US':

            message = "".join(re.findall(r'[a-zA-Z\ ]', message))

            sql_str = "SELECT translation FROM translations WHERE word_id=("
            sql_str += "SELECT word_id FROM words WHERE"
            sql_str += " name = '{0}') AND ".format(message)
            sql_str += "language_id=(SELECT language_id FROM language WHERE "
            sql_str += "initial='{0}')".format(language['language'])

            translate = self.postgres.query_fetch_one(sql_str)

            if translate:
                message = translate['translation']

        return message

    def translate_course(self, user_id, course_id):
        """ Return Course Translation """

        data = {}
        sql_str = "SELECT * FROM course WHERE course_id = '{0}'".format(course_id)
        result = self.postgres.query_fetch_one(sql_str)

        data['course_name'] = self.translate(user_id, result['course_name'])
        data['description'] = self.translate(user_id, result['description'])

        return data

    def trim_url(self, url):
        """ Return domain url """

        # FORMAT URL
        trim = re.compile(r"https?://(www\.)?")
        return trim.sub('', url).strip().strip('/')

    def can_access_tutorenv(self, user_id):
        """ Check access rights """

        sql_str = "SELECT * FROM account_role ac"
        sql_str += " LEFT JOIN role r ON ac.role_id = r.role_id"
        sql_str += " WHERE account_id = '{0}'".format(user_id)
        result = self.postgres.query_fetch_one(sql_str)

        roles = ['MANAGER', 'TUTOR']
        if result['role_name'].upper() in roles:
            return 1

        return 0

    def check_question(self, question_id):
        """ Validate Question ID """

        # DATA
        sql_str = "SELECT * FROM course_question"
        sql_str += " WHERE course_question_id = '{0}'".format(question_id)
        result = self.postgres.query_fetch_one(sql_str)
        if result:
            return 1

        return 0

    def allowed_file_type(self, filename):
        """ Check Allowed File Extension """

        allowed_extensions = set(['csv'])

        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

    def course_header(self):
        """ RETURN COURSE COLUMN """

        return [
            "Course ID",
            "Course Name",
            "Course Description",
            "Course Difficulty Level",
            "Course Requirements",

            "Section ID",
            "Section Name",
            "Section Description",
            "Section Difficulty Level",

            "Subsection ID",
            "Subsection Name",
            "Subsection Description",
            "Subsection Difficulty Level",

            "Exercise ID",
            "Exercise Number",
            "Exercise Question Type",
            "Exercise Tags",
            "Exercise Description",
            "Exercise Draw By Tag",
            "Exercise Editing Allowed",
            "Exercise Help",
            "Exercise Instant Feedback",
            "Exercise Moving Allowed",
            "Exercise Number to Draw",
            "Exercise Passing Criterium",
            "Exercise Save Seed",
            "Exercise Seed",
            "Exercise Shuffled",
            "Exercise Text Before Start",
            "Exercise Text After End",
            "Exercise Timed Limit",
            "Exercise Timed Type",

            "Question ID",
            "Question",
            "Question Type",
            "Question Tags",
            "Question Choices",
            "Question Shuffle Options",
            "Question Shuffle Answers",
            "Question Num Eval",
            "Question Correct Answer",
            "Question Correct",
            "Question Incorrect",
            "Question Feedback",
            "Question Description"
        ]

    def fetch_course_details(self, userid, course_id):
        """ Return Course Details """

        sql_str = "SELECT * FROM course_master WHERE"
        sql_str += " course_id='{0}'".format(course_id)
        result = self.postgres.query_fetch_all(sql_str)

        for res in result:
            res['course_name'] = self.translate(userid, res['course_name'])
            res['description'] = self.translate(userid, res['description'])

        return result

    def check_headers(self, csv_data, headers):
        """ CHECK COLUMN """

        for key in self.course_header():

            if not key in headers:

                return 0

        return 1

    def run_update(self, csv_data):
        """ CONVERT CSV TO JSON """

        json_data = {}
        json_data['status'] = 'ok'

        course_id = ""
        section_id = ""
        subsection_id = ""

        for row in csv_data:

            # COURSE
            if row['Course ID'] or row['Course Name']:

                course_id = self.iu_course(row)

                if not course_id:

                    json_data["alert"] = "Course already exist!"
                    json_data['status'] = 'Failed'

                    return json_data

                # CHECK IF COURSE IS ALREADY IN USE
                if not self.use_course(course_id):

                    json_data["alert"] = "Course is in use!"
                    json_data['status'] = 'Failed'

                    return json_data

            # SECTION
            if row['Section ID'] or row['Section Name']:

                section_id = self.iu_section(row, course_id)

                if not section_id:

                    json_data["alert"] = "Section {0} already exist!".format(row['Section Name'])
                    json_data['status'] = 'Failed'

                    return json_data

            # SUBSECTION
            if row['Subsection ID'] or row['Subsection Name']:

                subsection_id = self.iu_subsection(row, course_id, section_id)

                if not subsection_id:

                    json_data["alert"] = "Subsection {0} already exist!".format(row['Subsection Name'])
                    json_data['status'] = 'Failed'

                    return json_data

            # EXERCISE
            if row['Exercise ID'] or row['Exercise Number']:

                exercise_id = self.iu_exercise(row, course_id, section_id, subsection_id)

                if not exercise_id:

                    json_data["alert"] = "Exercise {0} already exist!".format(row['Exercise Number'])
                    json_data['status'] = 'Failed'

                    return json_data

            # QUESTION
            # if row['Question ID'] or row['Question']:

            #     question_id = self.iu_question(row, course_id, section_id, subsection_id, exercise_id)

            #     if not question_id:

            #         json_data["alert"] = "Question {0} already exist!".format(row['Question'])
            #         json_data['status'] = 'Failed'

            #         return json_data

        return json_data

    def iu_course(self, data):
        """ UPDATE COURSE """

        if data['Course ID']:

            return self.update_course(data)

        if data['Course Name']:

            sql_str = "SELECT * FROM course WHERE"
            sql_str += " course_name ='{0}'".format(data['Course Name'])

            cdata = self.postgres.query_fetch_one(sql_str)

            if cdata:

                return 0

            updated_data = {}

            data['Course Difficulty Level'] = 1

            updated_data['course_name'] = data['Course Name']
            if data['Course Description']:
                updated_data['description'] = data['Course Description']
            if data['Course Difficulty Level']:
                updated_data['difficulty_level'] = data['Course Difficulty Level']
            if data['Course Requirements']:
                updated_data['requirements'] = data['Course Requirements']
            updated_data['status'] = True
            updated_data['created_on'] = time.time()

            course_id = self.postgres.insert('course', updated_data, 'course_id')

            return course_id

    def iu_section(self, data, course_id):
        """ UPDATE SECTION """

        if not data['Section Name'] and data['Section ID']:

            conditions = []

            conditions.append({
                "col": "section_id",
                "con": "=",
                "val": data['Section ID']
                })

            self.postgres.delete('section', conditions)

        if data['Section ID']:

            updated_data = {}

            updated_data['difficulty_level'] = 1

            updated_data['section_name'] = data['Section Name']
            if data['Section Description']:
                updated_data['description'] = data['Section Description']
            if data['Section Difficulty Level']:
                updated_data['difficulty_level'] = data['Section Difficulty Level']

            # INIT CONDITION
            conditions = []

            # CONDITION FOR QUERY
            conditions.append({
                "col": "course_id",
                "con": "=",
                "val": course_id
                })

            conditions.append({
                "col": "section_id",
                "con": "=",
                "val": data['Section ID']
                })

            self.postgres.update('section', updated_data, conditions)

            return data['Section ID']

        if data['Section Name']:

            sql_str = "SELECT * FROM section WHERE"
            sql_str += " section_name ='{0}'".format(data['Section Name'])

            sdata = self.postgres.query_fetch_one(sql_str)

            if sdata:

                return 0

            updated_data = {}

            updated_data['difficulty_level'] = 1

            updated_data['course_id'] = course_id
            updated_data['section_id'] = self.sha_security.generate_token(False)
            updated_data['section_name'] = data['Section Name']
            if data['Section Description']:
                updated_data['description'] = data['Section Description']
            if data['Section Difficulty Level']:
                updated_data['difficulty_level'] = data['Section Difficulty Level']
            updated_data['status'] = True
            updated_data['created_on'] = time.time()

            section_id = self.postgres.insert('section', updated_data, 'section_id')

        return section_id

    def iu_subsection(self, data, course_id, section_id):
        """ UPDATE SUBSECTION """

        if not data['Subsection Name'] and data['Subsection ID']:

            conditions = []

            conditions.append({
                "col": "subsection_id",
                "con": "=",
                "val": data['Subsection ID']
                })

            self.postgres.delete('subsection', conditions)

        if data['Subsection ID']:

            updated_data = {}

            updated_data['difficulty_level'] = 1

            updated_data['subsection_name'] = data['Subsection Name']
            if data['Subsection Description']:
                updated_data['description'] = data['Subsection Description']
            if data['Subsection Difficulty Level']:
                updated_data['difficulty_level'] = data['Subsection Difficulty Level']

            # INIT CONDITION
            conditions = []

            # CONDITION FOR QUERY
            conditions.append({
                "col": "course_id",
                "con": "=",
                "val": course_id
                })

            conditions.append({
                "col": "section_id",
                "con": "=",
                "val": section_id
                })

            conditions.append({
                "col": "subsection_id",
                "con": "=",
                "val": data['Subsection ID']
                })

            self.postgres.update('subsection', updated_data, conditions)

            return data['Subsection ID']

        if data['Subsection Name']:

            sql_str = "SELECT * FROM subsection WHERE"
            sql_str += " subsection_name ='{0}'".format(data['Subsection Name'])

            ssdata = self.postgres.query_fetch_one(sql_str)

            if ssdata:

                return 0

            updated_data = {}

            updated_data['difficulty_level'] = 1

            updated_data['course_id'] = course_id
            updated_data['section_id'] = section_id
            updated_data['subsection_id'] = self.sha_security.generate_token(False)
            updated_data['subsection_name'] = data['Subsection Name']
            if data['Subsection Description']:
                updated_data['description'] = data['Subsection Description']
            if data['Subsection Difficulty Level']:
                updated_data['difficulty_level'] = data['Subsection Difficulty Level']
            updated_data['status'] = True
            updated_data['created_on'] = time.time()

            subsection_id = self.postgres.insert('subsection', updated_data, 'subsection_id')

            return subsection_id

    def iu_exercise(self, data, course_id, section_id, subsection_id):
        """ UPDATE COURSE """

        if not data['Exercise Number'] and data['Exercise ID']:

            conditions = []

            conditions.append({
                "col": "exercise_id",
                "con": "=",
                "val": data['Exercise ID']
                })

            self.postgres.delete('course_question', conditions)
            self.postgres.delete('exercise', conditions)

            return data['Exercise ID']

        if data['Exercise ID']:

            updated_data = {}
            updated_data['exercise_number'] = data['Exercise Number']

            # CODE FOR QUESTIONS

            if data['Exercise Question Type']:
                updated_data['question_types'] = json.dumps(data['Exercise Question Type'].replace("\'", "").replace("\"", "")[1:-1].split(", "))
            if data['Exercise Tags']:
                updated_data['tags'] = json.dumps(data['Exercise Tags'].replace("\'", "").replace("\"", "")[1:-1].split(", "))
            if data['Exercise Description']:
                updated_data['description'] = data['Exercise Description']
            if data['Exercise Draw By Tag']:
                updated_data['draw_by_tag'] = data['Exercise Draw By Tag'].upper() == 'TRUE'
            if data['Exercise Editing Allowed']:
                updated_data['editing_allowed'] = data['Exercise Editing Allowed'].upper() == 'TRUE'
            if data['Exercise Help']:
                updated_data['help'] = data['Exercise Help'].upper() == 'TRUE'
            if data['Exercise Instant Feedback']:
                updated_data['instant_feedback'] = data['Exercise Instant Feedback'].upper() == 'TRUE'
            if data['Exercise Moving Allowed']:
                updated_data['moving_allowed'] = data['Exercise Moving Allowed'].upper() == 'TRUE'
            if data['Exercise Number to Draw']:
                updated_data['number_to_draw'] = data['Exercise Number to Draw']
            if data['Exercise Passing Criterium']:
                updated_data['passing_criterium'] = data['Exercise Passing Criterium']
            if data['Exercise Save Seed']:
                updated_data['save_seed'] = data['Exercise Save Seed'].upper() == 'TRUE'
            if data['Exercise Seed']:
                updated_data['seed'] = data['Exercise Seed']
            if data['Exercise Shuffled']:
                updated_data['shuffled'] = data['Exercise Shuffled'].upper() == 'TRUE'
            if data['Exercise Text Before Start']:
                updated_data['text_before_start'] = data['Exercise Text Before Start']
            if data['Exercise Text After End']:
                updated_data['text_after_end'] = data['Exercise Text After End']
            if data['Exercise Timed Limit']:
                updated_data['timed_limit'] = data['Exercise Timed Limit']
            if data['Exercise Timed Type']:
                updated_data['timed_type'] = data['Exercise Timed Type']


            # INIT CONDITION
            conditions = []

            # CONDITION FOR QUERY
            conditions.append({
                "col": "course_id",
                "con": "=",
                "val": course_id
                })

            conditions.append({
                "col": "section_id",
                "con": "=",
                "val": section_id
                })

            conditions.append({
                "col": "subsection_id",
                "con": "=",
                "val": subsection_id
                })

            conditions.append({
                "col": "exercise_id",
                "con": "=",
                "val": data['Exercise ID']
                })

            self.postgres.update('exercise', updated_data, conditions)

            # ADD QUESTION to COURSE QUESTION
            self.add_course_question(data['Exercise ID'])

            return data['Exercise ID']

        updated_data = {}
        updated_data['draw_by_tag'] = False
        updated_data['editing_allowed'] = True
        updated_data['help'] = True
        updated_data['instant_feedback'] = True
        updated_data['moving_allowed'] = True
        updated_data['number_to_draw'] = 10
        updated_data['passing_criterium'] = 5
        updated_data['save_seed'] = True
        updated_data['seed'] = 10
        updated_data['shuffled'] = False
        updated_data['timed_limit'] = 300
        updated_data['timed_type'] = 'per_question'

        updated_data['course_id'] = course_id
        updated_data['section_id'] = section_id
        updated_data['subsection_id'] = subsection_id
        updated_data['exercise_id'] = self.sha_security.generate_token(False)
        updated_data['exercise_number'] = data['Exercise Number']
        if data['Exercise Question Type']:
            updated_data['question_types'] = json.dumps(data['Exercise Question Type'].replace("\'", "").replace("\"", "")[1:-1].split(", "))
        if data['Exercise Tags']:
            updated_data['tags'] = json.dumps(data['Exercise Tags'].replace("\'", "").replace("\"", "")[1:-1].split(", "))
        if data['Exercise Description']:
            updated_data['description'] = data['Exercise Description']
        if data['Exercise Draw By Tag']:
            updated_data['draw_by_tag'] = data['Exercise Draw By Tag'].upper() == 'TRUE'
        if data['Exercise Description']:
            updated_data['editing_allowed'] = data['Exercise Editing Allowed'].upper() == 'TRUE'
        if data['Exercise Help']:
            updated_data['help'] = data['Exercise Help'].upper() == 'TRUE'
        if data['Exercise Instant Feedback']:
            updated_data['instant_feedback'] = data['Exercise Instant Feedback'].upper() == 'TRUE'
        if data['Exercise Moving Allowed']:
            updated_data['moving_allowed'] = data['Exercise Moving Allowed'].upper() == 'TRUE'
        if data['Exercise Number to Draw']:
            updated_data['number_to_draw'] = data['Exercise Number to Draw']
        if data['Exercise Passing Criterium']:
            updated_data['passing_criterium'] = data['Exercise Passing Criterium']
        if data['Exercise Save Seed']:
            updated_data['save_seed'] = data['Exercise Save Seed'].upper() == 'TRUE'
        if data['Exercise Seed']:
            updated_data['seed'] = data['Exercise Seed']
        if data['Exercise Shuffled']:
            updated_data['shuffled'] = data['Exercise Shuffled'].upper() == 'TRUE'
        if data['Exercise Text Before Start']:
            updated_data['text_before_start'] = data['Exercise Text Before Start']
        if data['Exercise Text After End']:
            updated_data['text_after_end'] = data['Exercise Text After End']
        if data['Exercise Timed Limit']:
            updated_data['timed_limit'] = data['Exercise Timed Limit']
        if data['Exercise Timed Type']:
            updated_data['timed_type'] = data['Exercise Timed Type']
        updated_data['created_on'] = time.time()

        exercise_id = self.postgres.insert('exercise', updated_data, 'exercise_id')

        # ADD QUESTION to COURSE QUESTION
        self.add_course_question(exercise_id)

        return exercise_id

    def iu_question(self, data, course_id, section_id, subsection_id, exercise_id):
        """ UPDATE QUESTION """

        question_id = self.get_question_id(data)

        sql_str = "SELECT question_id FROM course_question WHERE"
        sql_str += " course_id='{0}'".format(course_id)
        sql_str += " AND section_id='{0}'".format(section_id)
        sql_str += " AND subsection_id='{0}'".format(subsection_id)
        sql_str += " AND exercise_id='{0}'".format(exercise_id)
        sql_str += " AND question_id='{0}'".format(question_id)

        if not self.postgres.query_fetch_one(sql_str):

            qtype = data['Question Type']

            temp = {}
            temp['question_id'] = question_id
            temp['course_question_id'] = self.sha_security.generate_token(False)
            temp['course_id'] = course_id
            temp['section_id'] = section_id
            temp['subsection_id'] = subsection_id
            temp['exercise_id'] = exercise_id
            temp['question_type'] = data['Question Type']
            temp['tags'] = json.dumps(data['Question Tags'].replace("\'", "").replace("\"", "")[1:-1].split(", "))
            temp['shuffle_options'] = ""
            temp['shuffle_answers'] = ""
            temp['feedback'] = ""
            array_choice = []

            if qtype == 'FITBT':

                ans = "".join(re.findall(r'[^\{$\}]', data['Question Correct Answer']))
                answer = {}
                answer['answer'] = data['Question'].replace("<ans>", str(ans))

                quest = {}
                quest['question'] = data['Question']

                temp['correct_answer'] = json.dumps(answer)
                temp['question'] = json.dumps(quest)

            elif qtype == 'FITBD':

                answer = {}
                answer['answer'] = data['Question']

                allans = "".join(re.findall(r'[^\{$\}]', data['Question Correct Answer'])).split(", ")

                for ans in allans:

                    correct_answer = answer['answer'].replace("[blank]", ans, 1)
                    answer['answer'] = correct_answer

                quest = {}
                quest['question'] = data['Question'].replace("[blank]", "<ans>")

                temp['correct_answer'] = json.dumps(answer)
                temp['question'] = json.dumps(quest)

            elif qtype == 'MULCH':

                choices = "".join(re.findall(r'[^\{$\}]', data['Question Choices']))
                choices = choices.split(", ")

                for choice in choices:

                    array_choice.append(choice)

                answer = {}
                answer['answer'] = data['Question Correct Answer']

                quest = {}
                quest['question'] = data['Question']

                temp['correct_answer'] = json.dumps(answer)
                temp['question'] = json.dumps(quest)

            elif qtype == 'MATCH':

                temp['shuffle_options'] = data['Question Shuffle Options']
                temp['shuffle_answers'] = data['Question Shuffle Answers']

                allans = "".join(re.findall(r'[^\{$\}]', data['Question Correct Answer'])).split(", ")
                answer = {}
                answer['answer'] = allans

                quest_data = data['Question'].replace("\"", "")
                allquest = "".join(re.findall(r'[^\{$\}]', quest_data)).split(", ")
                quest = {}
                quest['question'] = allquest

                array_choice = "".join(re.findall(r'[^\{$\}]', data['Question Choices']))
                array_choice = array_choice.split(", ")
                temp['correct_answer'] = json.dumps(answer)
                temp['question'] = json.dumps(quest)

            elif qtype == 'MULRE':

                temp['shuffle_options'] = data['Question Shuffle Options']
                temp['shuffle_answers'] = data['Question Shuffle Answers']

                allans = data['Question Correct Answer'].replace("\"", "")
                allans = "".join(re.findall(r'[^\{$\}]', allans)).split(", ")
                answer = {}
                answer['answer'] = allans

                quest = {}
                quest['question'] = data['Question']

                array_choice = data['Question Choices'].replace("\"", "")
                array_choice = "".join(re.findall(r'[^\{$\}]', array_choice))
                array_choice = array_choice.split(", ")
                temp['correct_answer'] = json.dumps(answer)
                temp['question'] = json.dumps(quest)

            if data['Question Description']:

                temp['description'] = data['Question Description']

            else:
                temp['description'] = "Lorem ipsum dolor sit amet, consectetur "
                temp['description'] += "adipiscing elit, sed do eiusmod tempor "
                temp['description'] += "incididunt ut labore et dolore magna aliqua."

            temp['choices'] = json.dumps(array_choice)
            temp['correct'] = data['Question Correct']
            temp['incorrect'] = data['Question Incorrect']
            temp['status'] = True
            temp['num_eval'] = data['Question Num Eval'].upper() == 'TRUE'
            temp['created_on'] = time.time()

            self.postgres.insert('course_question', temp, 'course_question_id')

        return question_id

    def add_course_question(self, exercise_id):
        """ Add Question for Exercise """

        sql_str = "SELECT * FROM exercise WHERE exercise_id='{0}'".format(exercise_id)
        result = self.postgres.query_fetch_one(sql_str)

        if result:

            questions = []
            if result['shuffled'] is True:

                # SELECT QUESTION BY QUESTION TYPE AND TAGS
                tags = []
                if result['draw_by_tag'] is True:
                    tags = result['tags']

                qtypes = result['question_types']
                number_to_draw = result['number_to_draw']
                questions = self.generate_random_questions(qtypes, int(number_to_draw), tags)
                # questionnaires = self.get_questions_by_condition(qtypes, tags)
                # questions = self.select_random_questions(questionnaires, number_to_draw, qtypes)

            # INSERT TO COURSE QUESTION TABLE
            for question in questions:

                qdata = self.get_question_by_id(question)

                if qdata:

                    tmp = {}
                    tmp['course_question_id'] = self.sha_security.generate_token(False)
                    tmp['course_id'] = result['course_id']
                    tmp['section_id'] = result['section_id']
                    tmp['subsection_id'] = result['subsection_id']
                    tmp['exercise_id'] = exercise_id
                    tmp['question_id'] = question
                    tmp['question'] = json.dumps(qdata['question'])
                    tmp['question_type'] = qdata['question_type']
                    tmp['tags'] = json.dumps(qdata['tags'])
                    tmp['choices'] = json.dumps(qdata['choices'])
                    tmp['num_eval'] = qdata['num_eval']
                    tmp['correct_answer'] = json.dumps(qdata['correct_answer'])
                    tmp['correct'] = qdata['correct']
                    tmp['incorrect'] = qdata['incorrect']

                    if qdata['feedback']:
                        tmp['feedback'] = qdata['feedback']

                    if qdata['shuffle_options']:
                        tmp['shuffle_options'] = qdata['shuffle_options']

                    if qdata['shuffle_answers']:
                        tmp['shuffle_answers'] = qdata['shuffle_answers']

                    tmp['description'] = qdata['description']
                    tmp['status'] = qdata['status']
                    tmp['created_on'] = time.time()

                    self.postgres.insert('course_question', tmp, 'course_question_id')


    def get_questions_by_condition(self, question_types, tags):
        """ Return Question by type and tags """

        qtype = ','.join("'{0}'".format(qtype) for qtype in question_types)
        tag = '"tags"'

        sql_str = "SELECT * FROM questions WHERE question_type IN ({0})".format(qtype)
        if tags:
            tags = ', '.join('"{0}"'.format(tag) for tag in tags)
            sql_str += " AND CAST({0} AS text) = '[{1}]'".format(tag, tags)

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

    def get_question_by_id(self, question_id):
        """ Return Question Data by ID """

        sql_str = "SELECT * FROM questions WHERE question_id = '{0}'".format(question_id)
        result = self.postgres.query_fetch_one(sql_str)

        return result

    def use_course(self, course_id):
        """ CHECK IF COURSE IN USE """

        sql_str = "SELECT * FROM student_course WHERE"
        sql_str += " course_id='{0}'".format(course_id)

        if not self.postgres.query_fetch_one(sql_str):

            return 1

        return 0

    def update_course(self, data, course_id=None):
        """ UPDATE COURSE """

        updated_data = {}
        updated_data['course_name'] = data['Course Name']
        updated_data['description'] = data['Course Description']
        updated_data['difficulty_level'] = data['Course Difficulty Level']
        updated_data['requirements'] = data['Course Requirements']

        # INIT CONDITION
        conditions = []

        # CONDITION FOR QUERY
        conditions.append({
            "col": "course_id",
            "con": "=",
            "val": data['Course ID']
            })

        self.postgres.update('course', updated_data, conditions)

        return data['Course ID']

    def get_question_id(self, row):
        """ RETURN QUESTION ID """

        if row['Question'] and row['Question ID']:

            return row['Question ID']

        sql_str = "SELECT question_id FROM questions WHERE"
        sql_str += " question='{0}'".format(row['Question'])
        sql_str += " AND question_type='{0}'".format(row['Question Type'])
        sql_str += " AND tags='{0}'".format(row['Question Tags'])
        response = self.postgres.query_fetch_one(sql_str)

        question_id = ""

        if not response:

            qtype = row['Question Type']

            question_id = self.sha_security.generate_token(False)

            temp = {}
            temp['question_id'] = question_id
            temp['question_type'] = row['Question Type']
            temp['tags'] = json.dumps(row['Question Tags'].replace("\'", "").replace("\"", "")[1:-1].split(", "))
            temp['shuffle_options'] = ""
            temp['shuffle_answers'] = ""
            temp['feedback'] = ""
            array_choice = []

            if qtype == 'FITBT':

                ans = "".join(re.findall(r'[^\{$\}]', row['Question Correct Answer']))
                answer = {}
                answer['answer'] = row['Question'].replace("<ans>", str(ans))

                quest = {}
                quest['question'] = row['Question']

                temp['correct_answer'] = json.dumps(answer)
                temp['question'] = json.dumps(quest)

            elif qtype == 'FITBD':

                answer = {}
                answer['answer'] = row['Question']

                allans = "".join(re.findall(r'[^\{$\}]', row['Question Correct Answer'])).split(", ")

                for ans in allans:

                    correct_answer = answer['answer'].replace("[blank]", ans, 1)
                    answer['answer'] = correct_answer

                quest = {}
                quest['question'] = row['Question'].replace("[blank]", "<ans>")

                temp['correct_answer'] = json.dumps(answer)
                temp['question'] = json.dumps(quest)

            elif qtype == 'MULCH':

                choices = "".join(re.findall(r'[^\{$\}]', row['Question Choices']))
                choices = choices.split(", ")

                for choice in choices:

                    array_choice.append(choice)

                answer = {}
                answer['answer'] = row['Question Correct Answer']

                quest = {}
                quest['question'] = row['Question']

                temp['correct_answer'] = json.dumps(answer)
                temp['question'] = json.dumps(quest)

            elif qtype == 'MATCH':

                temp['shuffle_options'] = row['Question Shuffle Options']
                temp['shuffle_answers'] = row['Question Shuffle Answers']

                allans = "".join(re.findall(r'[^\{$\}]', row['Question Correct Answer'])).split(", ")
                answer = {}
                answer['answer'] = allans

                quest_data = row['Question'].replace("\"", "")
                allquest = "".join(re.findall(r'[^\{$\}]', quest_data)).split(", ")
                quest = {}
                quest['question'] = allquest

                array_choice = "".join(re.findall(r'[^\{$\}]', row['Question Choices']))
                array_choice = array_choice.split(", ")
                temp['correct_answer'] = json.dumps(answer)
                temp['question'] = json.dumps(quest)

            elif qtype == 'MULRE':

                temp['shuffle_options'] = row['Question Shuffle Options']
                temp['shuffle_answers'] = row['Question Shuffle Answers']

                allans = row['Question Correct Answer'].replace("\"", "")
                allans = "".join(re.findall(r'[^\{$\}]', allans)).split(", ")
                answer = {}
                answer['answer'] = allans

                quest = {}
                quest['question'] = row['Question']

                array_choice = row['Question Choices'].replace("\"", "")
                array_choice = "".join(re.findall(r'[^\{$\}]', array_choice))
                array_choice = array_choice.split(", ")
                temp['correct_answer'] = json.dumps(answer)
                temp['question'] = json.dumps(quest)

            if row['Question Description']:

                temp['description'] = row['Question Description']

            else:
                temp['description'] = "Lorem ipsum dolor sit amet, consectetur "
                temp['description'] += "adipiscing elit, sed do eiusmod tempor "
                temp['description'] += "incididunt ut labore et dolore magna aliqua."

            temp['choices'] = json.dumps(array_choice)
            temp['correct'] = row['Question Correct']
            temp['incorrect'] = row['Question Incorrect']
            temp['num_eval'] = row['Question Num Eval'].upper() == 'TRUE'

            if row['Question Feedback']:
                temp['feedback'] = row['Question Feedback']
            temp['status'] = True
            temp['created_on'] = time.time()
            self.postgres.insert('questions', temp)

        else:

            question_id = response['question_id']

        return question_id


    def get_period(self, epoch_range, format_range):
        """ Return Start and End Time """

        start = epoch_range[0]
        end = epoch_range[-1]

        year = datetime.fromtimestamp(int(end)).strftime('%Y')
        month = datetime.fromtimestamp(int(end)).strftime('%m')
        day = datetime.fromtimestamp(int(end)).strftime('%d')

        if format_range in ['day', 'days']:
            end = datetime(int(year), int(month), int(day), 23, 59, 59).timestamp()

        elif format_range in ['weeks', 'week']:
            end = self.week_end_date(end)

        elif format_range in ['year', 'years']:
            month_end = calendar.monthrange(int(year), int(month))[1]
            end = datetime(int(year), 12, int(month_end), 23, 59, 59).timestamp()

        else:
            month_end = calendar.monthrange(int(year), int(month))[1]
            end = datetime(int(year), int(month), int(month_end), 23, 59, 59).timestamp()

        tmp = {}
        tmp['start'] = int(start)
        tmp['end'] = int(end)

        return tmp

    def epoch_range(self, epoch_format, number):
        """ Return Epoch Timestamp Coverage """

        if epoch_format in ['years', 'year']:
            epoch_format = "years"

        if epoch_format in ['months', 'month']:
            epoch_format = "months"

        if epoch_format in ['weeks', 'week']:
            epoch_format = "weeks"

        if epoch_format in ['days', 'day']:
            epoch_format = "days"

        year = datetime.now().strftime("%Y")
        month = datetime.now().strftime("%m")
        day = datetime.now().strftime("%d")

        is_default = False
        if not epoch_format and not number:
            start = datetime(int(year), 1, 1, 0, 0)
            end = datetime(int(year), int(month), 1, 0, 0)
            number = dateutil.relativedelta.relativedelta(end, start).months
            epoch_format = "months"
            is_default = True

        epoch = []

        if epoch_format == "months":
            day = 1

        if epoch_format == "years":
            day = 1
            month = 1

        base_start = datetime(int(year), int(month), int(day), 0, 0)

        if number and int(number):
            for num in range(int(number)):
                kwargs = {}
                kwargs[epoch_format] = int(num + 1)

                start = base_start - dateutil.relativedelta.relativedelta(**kwargs)
                epoch_start = round(start.timestamp())
                epoch.append(epoch_start)

            if is_default:
                epoch.append(round(base_start.timestamp()))
            else:
                epoch.append(round(base_start.timestamp()))
                epoch.sort()
                epoch.remove(epoch[0])

            epoch.sort()

        return epoch

    def week_end_date(self, epoch):
        """ Return end of week date """

        timestamp = epoch
        one_day = 86400
        end_week_date = (timestamp + (one_day * 7)) - 1
        return end_week_date

    def week_start_end(self, epoch):
        """ Return week start and end """

        date = datetime.fromtimestamp(int(epoch)).strftime('%Y-%m-%d')

        date = datetime.strptime(date, '%Y-%m-%d')

        week_start = date - timedelta(days=date.weekday())  # Monday
        week_end = week_start + timedelta(days=6)  # Sunday

        data = {}
        data['week_start'] = week_start.timestamp()
        data['week_end'] = week_end.timestamp()
        return data

    def epoch_week_number(self, epoch):
        """ Return Week Number """

        return datetime.fromtimestamp(int(epoch)).strftime("%V")

    def yearend_month_date(self, epoch_date):
        """ Return Month Year End Date in Epoch"""

        year = datetime.fromtimestamp(int(epoch_date)).strftime('%Y')
        epoch_year = datetime(int(year), 12, 1, 0, 0).strftime('%s')
        return epoch_year

    def month_end(self, epoch_date):
        """ Return Month End """

        year = datetime.fromtimestamp(int(epoch_date)).strftime('%Y')
        month = datetime.fromtimestamp(int(epoch_date)).strftime('%m')
        day = calendar.monthrange(int(year), int(month))[1]

        month_end = int(datetime(int(year), int(month), int(day), 0, 0).timestamp())
        return month_end

    def get_epoch_weekday(self, epoch_date):
        """ Return day of epoch date """

        return datetime.fromtimestamp(epoch_date).strftime("%A")

    def get_epoch_month(self, epoch_date):
        """ Return Epoch Date Month """

        return datetime.fromtimestamp(int(epoch_date)).strftime('%b')

    def get_epoch_year(self, epoch_date):
        """ Return Epoch Year """

        return datetime.fromtimestamp(int(epoch_date)).strftime('%Y')

    def day_end(self, epoch_date):
        """ Return Day End"""

        # END
        year = datetime.fromtimestamp(int(epoch_date)).strftime("%Y")
        month = datetime.fromtimestamp(int(epoch_date)).strftime("%m")
        day = datetime.fromtimestamp(int(epoch_date)).strftime("%d")
        end = int(datetime(int(year), int(month), int(day), 23, 59, 59).timestamp())
        return end

    def generate_random_questions(self, question_types, number_to_draw, tags):
        """ Generate Random Question """

        questions = []
        limit = math.floor(number_to_draw / len(question_types))
        for qtype in question_types:

            questions += self.get_random_questions(qtype, limit, tags)

        if len(questions) != number_to_draw:

            draw_again = number_to_draw - len(questions)
            question_type = random.choice(question_types)
            questions += self.get_random_questions(question_type, draw_again, tags)

        return questions
        
    def get_random_questions(self, question_type, number_to_draw, tags):
        """ Return Question by Type and Tags """

        if question_type.upper() == "MATCH":
            # GENERATE FITBT MATCHING TYPE QUESTIONS
            questions = self.create_match_question(tags, number_to_draw)

        else:
            questionnaires = self.get_questions(question_type, tags, number_to_draw)
            questions = [question['question_id'] for question in questionnaires]

        return questions

    def get_questions(self, question_type, tags, limit):
        """ Return Questions """

        tag = '"tags"'

        sql_str = "SELECT * FROM questions WHERE question_type='{0}'".format(question_type)
        if tags:
            tags = ', '.join('"{0}"'.format(tag) for tag in tags)
            sql_str += " AND CAST({0} AS text) = '[{1}]'".format(tag, tags)

        results = self.postgres.query_fetch_all(sql_str)

        if results:
            # questions = [result['question_id'] for result in results]
            random.shuffle(results)
            results = results[:limit]
        return results

    def create_match_question(self, tags, number_to_draw):
        """ Create Matching Type Questions """

        data = []
        match_qlimit = 5
        for _ in range(number_to_draw):
            questions = self.get_questions("FITBT", tags, match_qlimit)

            if questions:
                match_questions = []
                correct_answer = []
                for question in questions:

                    quest = question['question']['question'].replace("<ans>", "")
                    if "rest" in question['question']['question']:
                        quest = question['question']['question'].replace("<ans> rest <ans>", "")

                    answer = question['correct_answer']['answer'].replace(quest, "")
                    if "rest" in answer:
                        answer = answer.replace("rest", "/")
                        answer = answer.replace(" ", "")

                    match_questions.append(quest.rstrip())
                    correct_answer.append(answer)

                choices = correct_answer
                random.shuffle(choices)

                tmp_question = {}
                tmp_question['question'] = match_questions

                tmp_correct_answer = {}
                tmp_correct_answer['answer'] = correct_answer

                temp = {}
                temp['question_id'] = self.sha_security.generate_token(False)
                temp['question'] = json.dumps(tmp_question)
                temp['question_type'] = "MATCH"
                temp['tags'] = json.dumps(tags)
                temp['choices'] = json.dumps(choices)
                temp['shuffle_options'] = True
                temp['shuffle_answers'] = False
                temp['num_eval'] = True
                temp['correct_answer'] = json.dumps(tmp_correct_answer)
                temp['correct'] = questions[0]['correct']
                temp['incorrect'] = questions[0]['incorrect']
                temp['feedback'] = questions[0]['feedback']
                temp['description'] = questions[0]['description']
                temp['status'] = True
                temp['created_on'] = time.time()

                question_id = self.postgres.insert('questions', temp, 'question_id')
                data.append(question_id)

        return data

    def get_translation(self, message, language):
        """ Return Translation """

        sql_str = "SELECT translation FROM translations WHERE word_id=("
        sql_str += "SELECT word_id FROM words WHERE"
        sql_str += " name = '{0}') AND ".format(message)
        sql_str += "language_id=(SELECT language_id FROM language WHERE "
        sql_str += "initial='{0}')".format(language)

        return self.postgres.query_fetch_one(sql_str)

    def update_translate(self, data, userid):
        """ Update Translation """

        sql_str = "SELECT language FROM account WHERE"
        sql_str += " id='{0}'".format(userid)
        language = self.postgres.query_fetch_one(sql_str)

        if language['language'] != 'en-US':
            keys = ['rows', 'data', 'course']
            for key in keys:

                if key in data.keys():

                    if type(data[key]) == list:
                        for row in data[key]:

                            # COURSE NAME
                            if 'course_name' in row.keys():
                                row['course_name'] = self.translate_key(language,
                                                                        row['course_name'])

                            # DESCRIPTION
                            if 'description' in row.keys():
                                row['description'] = self.translate_key(language,
                                                                        row['description'])

                            if 'notification_name' in row.keys():
                                row['notification_name'] = self.translate_key(language,
                                                                              row['notification_name'])
                    else:
                        if 'course_name' in data[key].keys():
                            if type(data[key]['course_name']) == str:

                                data[key]['course_name'] = self.translate_key(language,
                                                                              data[key]['course_name'])

                        if 'description' in data[key].keys():
                            if type(data[key]['description']) == str:

                                data[key]['description'] = self.translate_key(language,
                                                                              data[key]['description'])

                # else:

                #     if 'course_name' in data[key].keys():
                #         if type(data[key]['course_name']) == str:

                #             data[key]['course_name'] = self.translate_key(language,
                #                                                         data[key]['course_name'])
                #     else:
                #         for row in data[key]:
                #             if 'course_name' in row.keys():
                #                 row['course_name'] = self.translate_key(language,
                #                                                         row['çourse_name'])
    
                    # # DESCRIPTION
                    # if 'description' in data[key].keys():

                    #     if type(data[key]['description']) == str:
 
                    #         data[key]['description'] = self.translate_key(language,
                    #                                                       data[key]['course_name'])
                    #     else:
                    #         for row in data[key]:
                    #             if 'course_name' in row.keys():
                    #                 row['course_name'] = self.translate_key(language, row['description'])

        return data

    def translate_key(self, language, original):
        """ Translate Key """

        message = "".join(re.findall(r'[a-zA-Z\ \.\,]', original))
        translate = self.get_translation(message, language['language'])

        if translate:
            return translate['translation']

        return original

    def get_account_details(self, user_id):
        """ Return Account Details """

        sql_str = "SELECT * FROM account WHERE id='{0}'".format(user_id)
        result = self.postgres.query_fetch_one(sql_str)
        return result
