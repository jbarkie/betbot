from api.src.models.auth import AuthenticatedUser
from api.src.models.tables import Users
from api.src.utils import connect_to_db


def get_user_by_username(username: str) -> AuthenticatedUser:
    session = connect_to_db()
    user = session.query(Users).filter_by(username=username).first()
    if user:
        user = AuthenticatedUser(
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            hashed_password=user.password
        )
    return user

