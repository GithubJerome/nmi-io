# pylint: disable=unused-variable, too-many-instance-attributes, broad-except, unidiomatic-typecheck, attribute-defined-outside-init, unnecessary-pass
"""PostgreSQL Queries"""
from configparser import ConfigParser
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from library.config_parser import config_section_parser
from library.log import Log

class PostgreSQL():
    """Class for PostgreSQL"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for PostgreSQL class"""
        # INIT CONFIG
        self.config = ConfigParser()
        # CONFIG FILE
        self.config.read("config/config.cfg")
        self.log = Log()

        # SET CONFIG VALUES
        self.host = config_section_parser(self.config, "POSTGRES")['host']
        self.user = config_section_parser(self.config, "POSTGRES")['username']
        self.password = config_section_parser(self.config, "POSTGRES")['password']
        self.dbname = config_section_parser(self.config, "POSTGRES")['db_name']
        self.port = config_section_parser(self.config, "POSTGRES")['port']

    def connection(self, db_name=False):
        """Connection"""
        # CONNECT TO DATABASE
        try:
            if db_name:
                conn = psycopg2.connect(host=self.host,
                                        port=self.port,
                                        user=self.user,
                                        password=self.password)
            else:
                conn = psycopg2.connect(host=self.host,
                                        port=self.port,
                                        database=self.dbname,
                                        user=self.user,
                                        password=self.password)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        except Exception as err:
            print("Error: ", err)
            raise

        # INSTANTIATE CURSOR
        self.conn = conn
        self.cursor = conn.cursor()

    def close_connection(self):
        """Close Connection"""
        self.conn.close()

    def create_database(self, db_name):
        """Create Database"""
        # print("Create Database: ", db_name)

        try:
            self.cursor.execute('CREATE DATABASE %s' % db_name)
            self.cursor.close()
            print("Database successfully created!")

        except Exception as err:
            print("Create database error: ", err)
            pass

    def exec_query(self, query, flag=False):
        """Execute Query"""
        try:
            self.cursor.execute(query)

            if flag:
                return self.cursor.fetchone()[0]

            return 1

        except Exception as err:
            return 0

    def insert(self, table, datas, table_id=False, log=False):
        """Insert"""
        try:
            self.connection()

            col = ""
            val = ""
            count = 1
            for data in datas.keys():
                col += data
                if type(datas[data]) in [int, bool, float, dict]:
                    val += str(datas[data])
                else:
                    val += "'" + str(datas[data]) + "'"

                if len(datas) != count:
                    col += ", "
                    val += ", "

                count += 1

            str_query = "INSERT INTO " + table + " (" + col + ")"
            str_query += " VALUES (" + val + ")"

            if table_id:
                str_query += " RETURNING " + table_id

            if log:

                self.log.info(str_query)

            id_created = self.exec_query(str_query, True)
            if id_created:
                self.conn.commit()
                self.close_connection()
                return id_created

            self.close_connection()
            return 0

        except Exception as err:
            self.close_connection()
            return 0

    def update(self, table, datas, conditions, log=False):
        """Update"""
        try:

            self.connection()

            str_query = "UPDATE " + table + " SET"

            count = 1
            for data in datas.keys():
                str_query += " " + data + "="

                if type(datas[data]) in [int, bool, float]:
                    str_query += str(datas[data])
                else:
                    str_query += "'" + str(datas[data]) + "'"


                if len(datas) != count:
                    str_query += ", "

                count += 1

            str_query += " WHERE "

            count = 1
            for condition in conditions:
                str_query += str(condition['col']) + " " + str(condition['con']) + " "

                if type(condition['val']) in [int, bool, float, list]:

                    if type(condition['val']) == list:
                        condition['val'] = "('" + "','".join(
                            str(x) for x in condition['val']) + "')"
                    str_query += str(condition['val'])

                else:
                    str_query += "'" + str(condition['val']) + "'"

                if len(conditions) != count:
                    str_query += " AND "

                count += 1

            if log:

                self.log.info(str_query)

            # EXECUTE QUERY
            if self.exec_query(str_query):
                self.conn.commit()
                self.close_connection()
                return 1
            self.close_connection()
            return 0

        except Exception as err:
            self.close_connection()
            return 0

    def delete(self, table, conditions, log=False):
        """Delete"""
        try:
            self.connection()

            str_query = "DELETE FROM " + table + " WHERE "

            count = 1
            for condition in conditions:
                str_query += str(condition['col']) + " " + str(condition['con']) + " "

                if type(condition['val']) in [int, bool, float, list]:

                    if type(condition['val']) == list:
                        condition['val'] = "('" + "','".join(
                            str(x) for x in condition['val']) + "')"

                    str_query += str(condition['val'])

                else:
                    str_query += "'" + str(condition['val']) + "'"

                if len(conditions) != count:
                    str_query += " AND "

                count += 1

            if log:

                self.log.info(str_query)

            # EXECUTE QUERY
            if self.exec_query(str_query):
                self.conn.commit()
                self.close_connection()
                return 1

            self.close_connection()
            return 0

        except Exception as err:
            self.close_connection()
            return 0

    # FETCH ONE RETURN JSON DATA
    def query_fetch_one(self, sql_string):
        """Query Fetch One JSON Data"""
        try:
            self.connection()

            # QUERY EXECUTE
            self.cursor.execute(sql_string)

            # GET ALL HEADERS
            row_headers = [x[0] for x in self.cursor.description]

            # FETCH ONE DATA
            result = self.cursor.fetchone()

            # CONDITION FOR THE RESULT
            if result:

                # SET RESULT TO JSON
                data = (dict(zip(row_headers, result)))

                # RETURN
                self.close_connection()
                return data

            # RETURN
            self.close_connection()
            return 0

        except Exception as err:
            self.close_connection()
            return 0

    # FETCH ONE RETURN JSON DATA
    def query_fetch_all(self, sql_string, log=False):
        """Query Fetch All JSON Data"""
        try:
            self.connection()

            # Log
            if log:

                self.log.info(sql_string)

            # QUERY EXECUTE
            self.cursor.execute(sql_string)

            # GET ALL HEADERS
            row_headers = [x[0] for x in self.cursor.description]

            # FETCH ALL DATA
            query_result = self.cursor.fetchall()

            # CONDITION FOR THE RESULT
            if query_result:

                # INIT VARIABLE
                data = []

                # LOOP DATA
                for row in query_result:
                    # SET RESULT TO JSON
                    data.append(dict(zip(row_headers, row)))

                # RETURN
                self.close_connection()
                return data

            # RETURN
            self.close_connection()
            return []

        except Exception as err:
            self.close_connection()
            return 0
