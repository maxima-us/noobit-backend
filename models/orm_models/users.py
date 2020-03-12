from fastapi_users.db import TortoiseBaseUserModel
# from fastapi_users import BaseUser, FastAPIUsers
# from fastapi_users.authentication import JWTAuthentication

class User(TortoiseBaseUserModel):
    pass


# This probably needs to be put in the routing/views directory? 

# SECRET = ""
# auth = JWTAuthentication(secret=SECRET, lifetime_seconds=3600)
# user_db = TortoiseUserDatabase(User)
# fastapi_users = FastAPIUsers(user_db, auth, User, SECRET)