from typing import Optional
from pydantic import BaseModel, model_validator

class SettingsRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    email_notifications_enabled: Optional[bool] = None
    
class SettingsResponse(BaseModel):
    success: bool
    message: str
    username: str
    email: str
    email_notifications_enabled: bool