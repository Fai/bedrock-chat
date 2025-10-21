import os
from fastapi import APIRouter

from app.usecases.global_config import get_global_available_models

router = APIRouter(tags=["config"])


@router.get("/config/global")
def get_global_config():
    """Get global configuration including available models and bedrock region."""
    global_models = get_global_available_models()
    bedrock_region = os.environ.get("BEDROCK_REGION", "us-east-1")
    return {
        "globalAvailableModels": global_models,
        "bedrockRegion": bedrock_region
    }
