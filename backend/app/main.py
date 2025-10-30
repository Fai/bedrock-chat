import logging
import os
import traceback
import uuid
from typing import Callable

from app.dependencies import get_current_user
from app.repositories.common import (
    RecordAccessNotAllowedError,
    RecordNotFoundError,
    ResourceConflictError,
)
from app.routes.admin import router as admin_router
from app.routes.api_publication import router as api_publication_router
from app.routes.bot import router as bot_router
from app.routes.bot_store import router as bot_store_router
from app.routes.conversation import router as conversation_router
from app.routes.global_config import router as global_config_router
from app.routes.model_validation import router as model_validation_router
from app.routes.published_api import router as published_api_router
from app.routes.user import router as user_router
from app.routes.sql_kb import router as sql_kb_router
from app.user import User
from app.utils import is_running_on_lambda
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Message
import json


CORS_ALLOW_ORIGINS = os.environ.get("CORS_ALLOW_ORIGINS", "*")
PUBLISHED_API_ID = os.environ.get("PUBLISHED_API_ID", None)

is_published_api = PUBLISHED_API_ID is not None

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
    datefmt="%Y-%m-%dT%H:%M:%S"
)
logger = logging.getLogger(__name__)

if not is_published_api:
    openapi_tags = [
        {"name": "conversation", "description": "Conversation API"},
        {"name": "bot", "description": "Bot API"},
        {"name": "api_publication", "description": "API Publication API"},
        {"name": "admin", "description": "Admin API"},
        {"name": "user", "description": "User API (cognito)"},
        {"name": "bot_store", "description": "Bot Store API"},
        {"name": "config", "description": "Global Configuration API"},
    ]
    title = "Bedrock Chat"
else:
    openapi_tags = [{"name": "published_api", "description": "Published API"}]
    title = "Bedrock Chat Published API"


app = FastAPI(
    openapi_tags=openapi_tags,
    title=title,
)


if not is_published_api:
    app.include_router(conversation_router)
    app.include_router(bot_router)
    app.include_router(api_publication_router)
    app.include_router(admin_router)
    app.include_router(user_router)
    app.include_router(bot_store_router)
    app.include_router(global_config_router)
    app.include_router(model_validation_router)
    app.include_router(sql_kb_router)
else:
    app.include_router(published_api_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def error_handler_factory(status_code: int) -> Callable[[Request, Exception], Response]:
    def error_handler(request: Request, exc: Exception) -> JSONResponse:
        correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
        error_details = {
            "correlation_id": correlation_id,
            "error_type": type(exc).__name__,
            "message": str(exc),
            "path": request.url.path,
            "method": request.method
        }
        
        logger.error(json.dumps({
            **error_details,
            "traceback": "".join(traceback.format_tb(exc.__traceback__))
        }))
        
        return JSONResponse({
            "errors": [error_details["message"]],
            "correlation_id": correlation_id
        }, status_code=status_code)

    return error_handler  # type: ignore


app.add_exception_handler(RecordNotFoundError, error_handler_factory(404))
app.add_exception_handler(FileNotFoundError, error_handler_factory(404))
app.add_exception_handler(RecordAccessNotAllowedError, error_handler_factory(403))
app.add_exception_handler(ValueError, error_handler_factory(400))
app.add_exception_handler(TypeError, error_handler_factory(400))
app.add_exception_handler(AssertionError, error_handler_factory(400))
app.add_exception_handler(PermissionError, error_handler_factory(403))
app.add_exception_handler(ValidationError, error_handler_factory(422))
app.add_exception_handler(ResourceConflictError, error_handler_factory(409))
app.add_exception_handler(Exception, error_handler_factory(500))


@app.middleware("http")
async def add_correlation_id(request: Request, call_next: ASGIApp):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id
    
    response = await call_next(request)  # type: ignore
    response.headers["X-Correlation-ID"] = correlation_id
    return response


@app.middleware("http")
def add_current_user_to_request(request: Request, call_next: ASGIApp):
    if is_running_on_lambda():
        if not is_published_api:
            authorization = request.headers.get("Authorization")
            if authorization:
                token_str = authorization.split(" ")[1]
                token = HTTPAuthorizationCredentials(
                    scheme="Bearer", credentials=token_str
                )
                request.state.current_user = get_current_user(token)
        else:
            assert PUBLISHED_API_ID is not None, "PUBLISHED_API_ID is not set."
            request.state.current_user = User.from_published_api_id(PUBLISHED_API_ID)
    else:
        authorization = request.headers.get("Authorization")
        if authorization:
            token_str = authorization.split(" ")[1]
            token = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token_str)
            request.state.current_user = get_current_user(token)
        else:
            request.state.current_user = User(
                id="test_user", name="test_user", email="user@example.com", groups=[]
            )

    response = call_next(request)  # type: ignore
    return response


@app.middleware("http")
async def add_log_requests(request: Request, call_next: ASGIApp):
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
    
    logger.info(json.dumps({
        "correlation_id": correlation_id,
        "event": "request_start",
        "path": request.url.path,
        "method": request.method,
        "user_agent": request.headers.get("user-agent", ""),
        "ip": request.client.host if request.client else ""
    }))

    response = await call_next(request)  # type: ignore
    
    logger.info(json.dumps({
        "correlation_id": correlation_id,
        "event": "request_end",
        "status_code": response.status_code,
        "path": request.url.path,
        "method": request.method
    }))

    return response
