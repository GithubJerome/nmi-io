# pylint: disable=no-self-use, too-many-instance-attributes
"""Log"""
from __future__ import print_function

class Log():
    """Class for Log"""

    def __init__(self):
        """The Constructor for Log class"""
        self.pink = '\033[95m'
        self.blue = '\033[94m'
        self.green = '\033[92m'
        self.yellow = '\033[93m'
        self.red = '\033[91m'
        self.superred = '\033[31m'
        self.bold = '\033[1m'
        self.normal = '\033[2m'
        self.italic = '\033[3m'
        self.underline = '\033[4m'
        self.end_color = '\033[0m' #end colors

    def info(self, message):
        """Information log"""
        print("{0} {1} {2}".format(self.green, message, self.end_color))

    def debug(self, message):
        """Debug log"""
        print("{0} {1} {2}".format(self.normal, message, self.end_color))

    def warning(self, message):
        """Warning log"""
        print("{0} {1} {2}".format(self.yellow, message, self.end_color))

    def error(self, message):
        """Error log"""
        print("{0} {1} {2}".format(self.red, message, self.end_color))

    def critical(self, message):
        """Critical log"""
        print("{0} {1} {2}".format(self.superred, message, self.end_color))

    def low(self, message):
        """Low log"""
        print("{0} {1} {2}".format(self.blue, message, self.end_color))

    def medium(self, message):
        """Medium log"""
        print("{0} {1} {2}".format(self.pink, message, self.end_color))
