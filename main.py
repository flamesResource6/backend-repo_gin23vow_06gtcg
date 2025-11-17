import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import db, create_document, get_documents
from schemas import Program

app = FastAPI(title="Free TV Programs API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Free TV backend is running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# Seed some demo, free and openly hosted videos (royalty-free sample clips)
SEED_PROGRAMS = [
    {
        "title": "Big Buck Bunny (Trailer)",
        "description": "Open movie by Blender Foundation - short trailer",
        "category": "Animation",
        "thumbnail_url": "https://peach.blender.org/wp-content/uploads/title_anouncement.jpg?x11217",
        "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
        "duration_seconds": 596,
        "tags": ["blender", "open movie", "animation"]
    },
    {
        "title": "Sintel (Trailer)",
        "description": "Open movie trailer by Blender Foundation",
        "category": "Fantasy",
        "thumbnail_url": "https://durian.blender.org/wp-content/uploads/2010/05/sintel_poster.jpg",
        "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.jpg",
        "duration_seconds": 300,
        "tags": ["sintel", "trailer", "fantasy"]
    },
    {
        "title": "Tears of Steel (Short)",
        "description": "Open VFX short by Blender Institute",
        "category": "Sci-Fi",
        "thumbnail_url": "https://mango.blender.org/wp-content/uploads/2013/05/ToS_poster.jpg",
        "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4",
        "duration_seconds": 734,
        "tags": ["vfx", "blender", "sci-fi"]
    }
]

class ProgramResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    category: str
    thumbnail_url: Optional[str]
    video_url: str
    duration_seconds: Optional[int]
    tags: Optional[List[str]]

@app.post("/api/programs", response_model=dict)
def create_program(program: Program):
    inserted_id = create_document("program", program)
    return {"id": inserted_id}

@app.get("/api/programs", response_model=List[ProgramResponse])
def list_programs(q: Optional[str] = Query(None, description="Search query"), category: Optional[str] = None, limit: int = 50):
    filter_query = {}
    if category:
        filter_query["category"] = category
    # Basic search by title/description if q provided
    if q:
        filter_query["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"tags": {"$regex": q, "$options": "i"}},
        ]
    docs = get_documents("program", filter_query, limit)
    # If empty, seed once in-memory result (won't persist until user adds)
    if not docs:
        docs = SEED_PROGRAMS
    # Normalize _id
    normalized = []
    for d in docs:
        item = {
            "id": str(d.get("_id", "seed")),
            "title": d.get("title"),
            "description": d.get("description"),
            "category": d.get("category", "All"),
            "thumbnail_url": d.get("thumbnail_url"),
            "video_url": d.get("video_url"),
            "duration_seconds": d.get("duration_seconds"),
            "tags": d.get("tags", []),
        }
        normalized.append(item)
    return normalized

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
