import os
import time
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="DermAssist API", description="Lightweight skin image analysis placeholder API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        # Try to import database module
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response


# --- Lightweight placeholder image analysis endpoint ---
@app.post("/analyze")
async def analyze_skin_image(file: UploadFile = File(...)):
    """
    Accepts an uploaded skin image and returns a fast, meaningful placeholder analysis.
    Designed so a real ML model can replace the dummy predictor without changing the frontend.
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")

    start = time.time()

    # Read bytes (no heavy processing here to keep it snappy)
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    # Simple, deterministic pseudo-analysis based on byte patterns
    total = sum(content[:4096])  # sample first 4KB for speed
    size_kb = len(content) / 1024.0

    # Map hash bucket to a condition
    conditions = [
        {
            "name": "Acne Vulgaris",
            "desc": "Common inflammatory condition with comedones, papules, or pustules.",
            "tips": [
                "Use a gentle, non-comedogenic cleanser twice daily",
                "Apply a 2.5%-5% benzoyl peroxide or salicylic acid product",
                "Avoid picking and use clean pillowcases",
            ],
        },
        {
            "name": "Eczema (Atopic Dermatitis)",
            "desc": "Itchy, dry, and inflamed patches that may flare periodically.",
            "tips": [
                "Moisturize with fragrance-free cream after bathing",
                "Use lukewarm showers and gentle cleansers",
                "Consider OTC hydrocortisone for short-term flares",
            ],
        },
        {
            "name": "Psoriasis",
            "desc": "Well-demarcated, scaly plaques often on elbows, knees, or scalp.",
            "tips": [
                "Keep skin moisturized; avoid harsh scrubbing",
                "Sun exposure in moderation may help",
                "Discuss topical steroids or vitamin D analogs with a clinician",
            ],
        },
        {
            "name": "Benign Nevus (Mole)",
            "desc": "Uniformly pigmented lesion with symmetric borders.",
            "tips": [
                "Monitor for ABCDE changes (Asymmetry, Border, Color, Diameter, Evolving)",
                "Use daily SPF 30+",
                "Seek evaluation if rapid change or symptoms occur",
            ],
        },
        {
            "name": "Contact Dermatitis",
            "desc": "Localized redness or rash triggered by irritants or allergens.",
            "tips": [
                "Identify and avoid suspected triggers",
                "Cool compresses; fragrance-free emollients",
                "Short course OTC hydrocortisone for itch",
            ],
        },
    ]

    idx = (total % len(conditions))
    selected = conditions[idx]

    # Confidence heuristic: more bytes and more variance -> higher confidence (placeholder)
    variance = 0.0
    sample = content[:8192]
    if len(sample) > 0:
        mean = sum(sample) / len(sample)
        variance = sum((b - mean) ** 2 for b in sample) / len(sample)
    base_conf = min(0.98, 0.55 + (variance % 2000) / 5000 + min(size_kb / 2048.0, 0.2))

    latency_ms = int((time.time() - start) * 1000)

    return {
        "condition": selected["name"],
        "confidence": round(base_conf * 100, 1),
        "description": selected["desc"],
        "suggestions": selected["tips"],
        "latency_ms": latency_ms,
        "filename": file.filename,
        "size_kb": round(size_kb, 1),
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
