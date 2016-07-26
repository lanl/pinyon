Instructions for setting up MongoDB, heavily borrowing from instructions supplied for MDCS at https://github.com/usnistgov/MDCS/blob/stable/docs/MongoDB%20Configuration

This document provides explanations about the configuration of MongoDB.
Please use the configuration file provided with the MDCS (mdcs/conf/mongodb.conf), to be sure to have the minimum required security for your database.
You can find more information about MongoDB security: http://docs.mongodb.org/manual/administration/security-checklist/

Required: Edit the file conf/mongodb.conf and replace the value of dbPath by the path on your system (path/to/mdcs/data/db). By default, this is given as a relative path from the root directory of pinyon

Required: Please follow these instructions to set up authentication for your database:
- Add mongodb/bin folder to your path for more convenience

- In a first command prompt, run the following command:
mongod --config ./conf/mongodb.conf

- Edit the make_admin_accnt.txt script to define admin account settings

<mongo_admin_user> : choose a username for the administrator of mongodb
<mongo_admin_password> : choose a password for the administrator of mongodb
<mongo_mgi_user> : choose a username for the user of mgi database
<mongo_mgi_password> : choose a password for the user of mgi database

mongo --port 27018 < make_admin_accnt.txt

- Edit the make_user_accnt.txt to create the first user account for this server

mongo --port 27018 -u "<mongo_admin_user>" -p "<mongo_admin_password>" --authenticationDatabase admin < make_user_account.txt
- Edit the file path/to/mdcs/mgi/settings.py, and set the following parameters to the values you chose earlier:
MONGO_MGI_USER = "<mongo_mgi_user>"
MONGO_MGI_PASSWORD = "<mongo_mgi_password>"