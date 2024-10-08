from api.src.models.tables import Users
from shared.database import connect_to_db
import bcrypt

def register_user(username: str, first_name: str, last_name: str, email: str, password: str):
    session = connect_to_db()
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user = Users(username=username, first_name=first_name, last_name=last_name, email=email, password=hashed)
    session.add(user)
    session.commit()
    session.close()
    return user