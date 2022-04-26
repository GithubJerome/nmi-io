# pylint: disable=too-many-locals, no-member
""" AWS S3 """
from configparser import ConfigParser
import boto3
from library.postgresql_queries import PostgreSQL
from library.common import Common
from library.config_parser import config_section_parser

class AwsS3(Common):
    """Class for AwsS3"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for S3 class"""
        self.postgres = PostgreSQL()

        # INIT CONFIG
        self.config = ConfigParser()

        # CONFIG FILE
        self.config.read("config/config.cfg")

        super(AwsS3, self).__init__()

    def get_url(self, key):
        """ Return S3 URL """

        assert key, "Key is required."
        # AWS ACCESS
        aws_access_key_id = config_section_parser(self.config, "AWS")['aws_access_key_id']
        aws_secret_access_key = config_section_parser(self.config,
                                                      "AWS")['aws_secret_access_key']
        region_name = config_section_parser(self.config, "AWS")['region_name']

        # CONNECT TO S3
        s3_client = boto3.client('s3',
                                 aws_access_key_id=aws_access_key_id,
                                 aws_secret_access_key=aws_secret_access_key,
                                 region_name=region_name)

        s3_params = {
            'Bucket': config_section_parser(self.config, "AWS")['bucket'],
            'Key': key
        }

        expiration = config_section_parser(self.config, "AWS")['image_expires']
        url = s3_client.generate_presigned_url('get_object',
                                               Params=s3_params,
                                               ExpiresIn=expiration,
                                               HttpMethod='GET')

        return url

    def save_file(self, key_file, body_request):
        """ Save File to S3 Bucket """

        # AWS ACCESS
        aws_access_key_id = config_section_parser(self.config, "AWS")['aws_access_key_id']
        aws_secret_access_key = config_section_parser(self.config,
                                                      "AWS")['aws_secret_access_key']
        region_name = config_section_parser(self.config, "AWS")['region_name']

        # CONNECT TO S3
        s3_resource = boto3.resource('s3',
                                     aws_access_key_id=aws_access_key_id,
                                     aws_secret_access_key=aws_secret_access_key,
                                     region_name=region_name)
        # SAVE TO S3
        save_to_bucket = s3_resource.Bucket('nmi.fileserver').put_object(
            Key=key_file,
            Body=body_request)

        if save_to_bucket:
            return 1
        return 0

    def get_instruction_image(self, image_id):
        """ Return Instruction Image URL"""

        assert image_id, "Instruction Image ID is required."

        # DATA
        sql_str = "SELECT * FROM instruction_image"
        sql_str += " WHERE image_id='{0}'".format(image_id)
        sql_str += " AND status = 'active'"

        img = self.postgres.query_fetch_one(sql_str)

        image_url = ""
        if img:
            filename = img['image_name']
            ext = filename.split(".")[-1]

            # IMAGE FILE NAME
            image_name = str(img['image_id']) + "." + ext
            key_file = 'Instruction/' + "NMI_" + image_name

            image_url = self.get_url(key_file)

        return image_url
