from typing import List
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas.prediction import PredictionResponse
from app.routes.deps import get_current_user
from app.services import prediction_service

router = APIRouter(prefix="/predictions", tags=["Predictions"])

@router.post("/", response_model=PredictionResponse)
def upload_and_predict(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a plant image and get AI disease diagnosis."""
    return prediction_service.process_and_predict(db, current_user, file)

@router.get("/history", response_model=List[PredictionResponse])
def get_prediction_history(
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """View personal past predictions."""
    return prediction_service.get_user_predictions(db, current_user, limit, offset)

@router.delete("/{prediction_id}", response_model=dict)
def delete_prediction_record(
    prediction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a prediction from history."""
    return prediction_service.delete_prediction(db, current_user, prediction_id)
