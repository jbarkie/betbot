import bcrypt
from api.src.models.settings import SettingsRequest, SettingsResponse
from api.src.models.tables import Users
from shared.database import connect_to_db

def update_user_settings(
    settings_request: SettingsRequest
) -> SettingsResponse:
    """
    Update user settings.
    """

    session = None

    try:
        session = connect_to_db()
        user = session.query(Users).filter_by(username=settings_request.username).first()

        if not user:
            return SettingsResponse(
                success=False,
                message="User not found",
                username=settings_request.username,
                email=None,
                email_notifications_enabled=None
            )
    
        if settings_request.username:
            user.username = settings_request.username

        if settings_request.email:
            user.email = settings_request.email

        if settings_request.password:
            hashed = bcrypt.hashpw(settings_request.password.encode('utf-8'), bcrypt.gensalt())
            user.password = hashed
            
        if settings_request.email_notifications_enabled is not None:
            user.email_notifications_enabled = settings_request.email_notifications_enabled

        session.commit()

        response = SettingsResponse(
            success=True,
            message="Settings updated successfully",
            username=user.username,
            email=user.email,
            email_notifications_enabled=user.email_notifications_enabled
        )
    
        return response
    
    except Exception as e:
        if session:
            session.rollback()
        return SettingsResponse(
            success=False,
            message=f"An error occurred: {str(e)}",
            username=settings_request.username,
            email=None,
            email_notifications_enabled=None
        )
    
    finally:
        if session:
            session.close()
            
def get_user_settings(
    username: str
) -> SettingsResponse:
    """
    Get user settings.
    """
    
    session = None

    try:
        session = connect_to_db()
        user = session.query(Users).filter_by(username=username).first()

        if not user:
            return SettingsResponse(
                success=False,
                message="User not found",
                username=username,
                email=None,
                email_notifications_enabled=None
            )
        
        response = SettingsResponse(
            success=True,
            message="Settings retrieved successfully",
            username=user.username,
            email=user.email,
            email_notifications_enabled=user.email_notifications_enabled
        )
        
        return response
    
    except Exception as e:
        if session:
            session.rollback()
        return SettingsResponse(
            success=False,
            message=f"An error occurred: {str(e)}",
            username=username,
            email=None,
            email_notifications_enabled=None
        )
    
    finally:
        if session:
            session.close()