from pydantic import BaseModel
from datetime import datetime

class PredictionResponse(BaseModel):
    id: int
    user_id: str
    image_path: str
    predicted_label: str
    confidence: float
    created_at: datetime

    class Config:
        from_attributes = True
