import logging
from typing import Dict, Set
from functools import lru_cache
from botocore.exceptions import ClientError
from app.utils import get_bedrock_client
from app.routes.schemas.conversation import type_model_name

logger = logging.getLogger(__name__)

# Cache for 5 minutes to avoid repeated API calls
@lru_cache(maxsize=128, typed=True)
def get_available_models(region: str) -> Set[str]:
    """Get list of available foundation models in a region."""
    try:
        client = get_bedrock_client(region)
        response = client.list_foundation_models()
        return {model['modelId'] for model in response['modelSummaries']}
    except ClientError as e:
        logger.error(f"Failed to list models in region {region}: {e}")
        return set()

def validate_model_availability(model: type_model_name, region: str) -> bool:
    """Validate if a model is available in the specified region."""
    from app.bedrock import get_model_id
    
    try:
        model_id = get_model_id(model)
        available_models = get_available_models(region)
        
        # Check if exact model ID is available
        if model_id in available_models:
            return True
            
        # For inference profiles, check base model availability
        if "inference-profile" in model_id:
            base_model = model_id.split("::")[-1].split(":")[0]
            base_available = any(base_model in available_model for available_model in available_models)
            if base_available:
                return True
                
        logger.warning(f"Model {model} (ID: {model_id}) not available in region {region}")
        return False
        
    except Exception as e:
        logger.error(f"Error validating model {model} in region {region}: {e}")
        return False

def get_model_validation_report(region: str) -> Dict[str, bool]:
    """Generate validation report for all supported models."""
    from app.bedrock import BASE_MODEL_IDS
    
    report = {}
    for model_name in BASE_MODEL_IDS.keys():
        report[model_name] = validate_model_availability(model_name, region)
    
    return report
