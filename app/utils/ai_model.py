from transformers import pipeline
import io
from PIL import Image
from app.config import settings

# Initialize the pipeline
# device=-1 explicitly uses CPU. We load it globally so it's only loaded once on startup.
try:
    print(f"Loading AI Model: {settings.MODEL_NAME}")
    classifier = pipeline("image-classification", model=settings.MODEL_NAME, device=-1)
    print("AI Model loaded successfully!")
except Exception as e:
    print(f"Failed to load AI model: {e}")
    classifier = None

def predict_disease(image_bytes: bytes):
    if not classifier:
        return {"error": "Classifier model not loaded properly"}
        
    try:
        # Load image from bytes
        image = Image.open(io.BytesIO(image_bytes))
        
        # Ensure image is in RGB format
        if image.mode != "RGB":
            image = image.convert("RGB")
            
        # Run inference
        results = classifier(image)
        
        # The pipeline returns a list of dictionaries with 'label' and 'score'
        # We'll return the highest scoring prediction
        if results and len(results) > 0:
            best_prediction = results[0]
            return {
                "label": best_prediction["label"],
                "confidence": best_prediction["score"]
            }
        else:
            return {"error": "No prediction generated"}
    except Exception as e:
        return {"error": str(e)}
