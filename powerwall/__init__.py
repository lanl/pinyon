__author__ = 'Logan Ward'

import extract
import mongoengine as mge

mongodb_settings = dict(
    name='powerwall',
    user='powerwall_user',
    pswd='powerwall_user',
    host='127.0.0.1',
    port=27018
)
"""Settings for MongoDB server"""

def connect_to_mongo():
    """Connect to the MongoDB supporting powerwall"""
    mge.connect(mongodb_settings['name'],
        host=mongodb_settings['host'],
        port=mongodb_settings['port'],
        username=mongodb_settings['user'],
        password=mongodb_settings['pswd']
    )
