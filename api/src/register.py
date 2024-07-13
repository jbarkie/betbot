from api.src.models.tables import Users
from api.src.utils import connect_to_db


def register_user(username: str, first_name: str, last_name: str, email: str, password: str):
    session = connect_to_db()
    user = Users(username=username, first_name=first_name, last_name=last_name, email=email, password=password)
    session.add(user)
    session.commit()
    session.close()
    return user