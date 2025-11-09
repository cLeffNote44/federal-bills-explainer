from fastapi import APIRouter, HTTPException, Header, Depends
from sqlalchemy.orm import Session
from fbx_core.db.session import SessionLocal
from fbx_core.providers.congress_gov import CongressGovProvider
from fbx_core.services.ingestion import IngestionService
from fbx_core.utils.settings import Settings

router = APIRouter()
settings = Settings()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/ingest")
def trigger_ingestion(authorization: str = Header(...), db: Session = Depends(get_db)):
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    if token != settings.admin_token:
        raise HTTPException(status_code=403, detail="Forbidden")
    # When running inside Docker, fixtures are packaged at this absolute path
    provider = CongressGovProvider(fixtures_dir="/app/apps/ingestion/fixtures")
    service = IngestionService(provider, db)
    count = service.run()
    return {"message": f"Ingested {count} bills"}
