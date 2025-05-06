from api.src.models.settings import SettingsRequest, SettingsResponse

def update_user_settings(
    settings_request: SettingsRequest
) -> SettingsResponse:
    """
    Update user settings.
    """
    response = SettingsResponse(
        success=True,
        message="Settings updated successfully",
        username=settings_request.username or "current_username",
        email=settings_request.email or "current_email",
        email_notifications_enabled=settings_request.email_notifications_enabled or False
    )
    # Here you would typically update the user's settings in the database
    # For now, we will just return the received settings
    return response