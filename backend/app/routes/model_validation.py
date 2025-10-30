from fastapi import APIRouter, Depends
from app.dependencies import check_admin
from app.model_validation import get_model_validation_report
from app.config import BEDROCK_REGION

router = APIRouter(prefix="/model-validation", tags=["model-validation"])

@router.get("/report")
def get_validation_report(admin_user=Depends(check_admin)):
    """Get model availability validation report for the current region."""
    return {
        "region": BEDROCK_REGION,
        "models": get_model_validation_report(BEDROCK_REGION)
    }
