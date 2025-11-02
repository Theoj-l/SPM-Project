from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class TeamBase(BaseModel):
    name: str
    description: Optional[str] = None

class TeamCreate(TeamBase):
    pass

class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class TeamMemberAdd(BaseModel):
    member_user_id: str
    role: str = "member"

class TeamOut(TeamBase):
    id: str
    manager_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TeamMemberOut(BaseModel):
    id: str
    team_id: str
    user_id: str
    role: str  # "member" or "manager"
    joined_at: datetime
    
    class Config:
        from_attributes = True
