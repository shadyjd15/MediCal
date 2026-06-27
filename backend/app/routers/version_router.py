import os
from fastapi import APIRouter
from .. import schemas

router = APIRouter(prefix="/api/version", tags=["version"])

APP_VERSION = os.getenv("APP_VERSION", "1.1.0")
GITHUB_REPO = os.getenv("GITHUB_REPO", "")  # e.g. "yourname/medical"


@router.get("", response_model=schemas.VersionInfo)
def get_version():
    return schemas.VersionInfo(version=APP_VERSION, repo=GITHUB_REPO or None)
