A Service Management application for small business. Provides everything a smaller organisation needs to establish best practice service support, including:
- Incident and Service Request management linked to Service Level Agreements
- Problem Management to group similar requests for resolution
- Change Enablement to manage all IT Changes in a controlled manner.
- Knowledge Management to produce and display in a User Portal for User self help
- Idea voting for your employees to make improvement suggestions that can be voted on (Continual Service Improvement opportunities)
- CMDB (Configuration Management Database) to document your infrastructures configuration and understand the upstream and downstream configuration items for each CI. Useful for understanding Change impacts, troubleshooting, and keeping track of IT assets.

- It has an administration interface to set defaults and change aspects of tickets that are blocked for normal users.
- Provides a simple Portal for Users to receive notifications, view Knowledge Articles, track logged tickets, and view the IT Service Catalogue.

There is much still to do and improvements to make so tread with care.  

Postgresql is used as the database. Before use seed the lookup tables with the provided script "init_db_and_seed_tables.py" 

I'd like to just offer a docker container in the future.
Note I am could not get flask-security-too unified sign in to work so login is with email address and password. Modify the seed.py to suit your requirements:

 User: {
            "data": [
                {"username": "admin", "password": "password", "roles": [
                    "admin", "team member", "manager", "approver", "CAB Member", "Tester", "Product Owner",
                    "Release/Deploy"]},
                {"username": "user", "password": "password", "roles": ["team member"]},
            ],
            "unique_fields": ["username"]
        }
 
You will need to set up email and postresql options in config.py to suit your environment.