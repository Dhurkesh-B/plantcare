import os
import shutil
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
from app.models import Prediction, User
from app.utils.ai_model import predict_disease

# Ensure uploads directory exists
UPLOAD_DIR = "static/uploads/predictions"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def process_and_predict(db: Session, current_user: User, file: UploadFile):
    # Validate image type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File provided is not an image.")

    try:
        # Read file bytes for AI model
        file_bytes = file.file.read()
        
        # Run AI prediction
        ai_result = predict_disease(file_bytes)
        if "error" in ai_result:
            raise HTTPException(status_code=500, detail=f"AI Prediction failed: {ai_result['error']}")
            
        label = ai_result["label"]
        confidence = float(ai_result["confidence"])
        
        # Save file locally
        file.file.seek(0) # Reset file pointer
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{current_user.id}_{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Optional: In a real app we'd construct a full URL, but storing relative path is fine here.
        # e.g., image_url = f"/static/uploads/predictions/{filename}"
        
        # Save to database
        db_prediction = Prediction(
            user_id=current_user.id,
            image_path=file_path,
            predicted_label=label,
            confidence=confidence
        )
        db.add(db_prediction)
        db.commit()
        db.refresh(db_prediction)
        
        return db_prediction
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_user_predictions(db: Session, current_user: User, limit: int = 10, offset: int = 0):
    return db.query(Prediction)\
             .filter(Prediction.user_id == current_user.id)\
             .order_by(Prediction.created_at.desc())\
             .offset(offset).limit(limit).all()

def delete_prediction(db: Session, current_user: User, prediction_id: int):
    pred = db.query(Prediction).filter(Prediction.id == prediction_id, Prediction.user_id == current_user.id).first()
    if not pred:
        raise HTTPException(status_code=404, detail="Prediction not found or unauthorized")
        
    # Delete image file
    if os.path.exists(pred.image_path):
        os.remove(pred.image_path)
        
    db.delete(pred)
    db.commit()
    return {"message": "Prediction deleted successfully"}
