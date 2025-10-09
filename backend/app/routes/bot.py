import logging
from typing import Any, Dict, Literal

from app.dependencies import check_creating_bot_allowed
from app.repositories.custom_bot import find_bot_by_id
from app.repositories.knowledge_base import get_knowledge_base_info
from app.routes.schemas.bot import (
    ActiveModelsOutput,
    Agent,
    BedrockGuardrailsOutput,
    BedrockKnowledgeBaseOutput,
    BotInput,
    BotMetaOutput,
    BotModifyInput,
    BotOutput,
    BotPresignedUrlOutput,
    BotStarredInput,
    BotSummaryOutput,
    BotSwitchVisibilityInput,
    ConversationQuickStarter,
    FirecrawlConfig,
    GenerationParams,
    Knowledge,
    PlainTool,
)
from app.routes.schemas.bot_kb import (
    SqlKnowledgeBaseInput,
    SqlKnowledgeBaseOutput,
    KnowledgeBaseStatusOutput,
    SqlQueryInput,
    SqlQueryOutput,
    AuroraVectorKnowledgeBaseInput,
    AuroraVectorKnowledgeBaseOutput,
    AuroraVectorQueryInput,
    AuroraVectorQueryOutput,
)
from app.routes.schemas.conversation import type_model_name
from app.usecases.bot import (
    create_new_bot,
    fetch_all_bots,
    fetch_all_pinned_bots,
    fetch_available_agent_tools,
    fetch_bot_summary,
    issue_presigned_url,
    modify_bot_visibility,
    modify_owned_bot,
    modify_star_status,
    remove_bot_by_id,
    remove_bot_from_recently_used,
    remove_uploaded_file,
)
from app.user import User
from fastapi import APIRouter, Depends, Request, HTTPException

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter(tags=["bot"])


@router.post("/bot", response_model=BotOutput)
def post_bot(
    request: Request,
    bot_input: BotInput,
    create_bot_check=Depends(check_creating_bot_allowed),
):
    """Create new private owned bot."""
    current_user: User = request.state.current_user

    return create_new_bot(current_user, bot_input)


@router.patch("/bot/{bot_id}")
def patch_bot(request: Request, bot_id: str, modify_input: BotModifyInput):
    """Modify owned bot title, instruction and description."""
    current_user: User = request.state.current_user

    return modify_owned_bot(current_user, bot_id, modify_input)


@router.patch("/bot/{bot_id}/starred")
def patch_bot_star_status(
    request: Request, bot_id: str, starred_input: BotStarredInput
):
    """Modify owned bot star status."""
    current_user: User = request.state.current_user
    return modify_star_status(current_user, bot_id, starred=starred_input.starred)


@router.patch("/bot/{bot_id}/visibility")
def patch_bot_shared_status(
    request: Request, bot_id: str, visibility_input: BotSwitchVisibilityInput
):
    """Switch bot visibility"""
    current_user: User = request.state.current_user
    modify_bot_visibility(current_user, bot_id, visibility_input)


@router.get("/bot", response_model=list[BotMetaOutput])
def get_all_bots(
    request: Request,
    kind: Literal["private", "mixed"] = "private",
    starred: bool = False,
    limit: int | None = None,
):
    """Get all bots. The order is descending by `last_used_time`.
    - If `kind` is `private`, only private bots will be returned.
        - If `mixed` must give either `starred` or `limit`.
    - If `starred` is True, only starred bots will be returned.
        - When kind is `private`, this will be ignored.
    - If `limit` is specified, only the first n bots will be returned.
        - Cannot specify both `starred` and `limit`.
    """
    current_user: User = request.state.current_user

    bots = fetch_all_bots(current_user, limit, starred, kind)
    return bots


@router.get("/bot/pinned", response_model=list[BotMetaOutput])
def get_all_pinned_bots(request: Request):
    """Get all pinned bots. Currently, only pinned public bots are supported."""
    current_user: User = request.state.current_user

    bots = fetch_all_pinned_bots(current_user)
    return bots


@router.get("/bot/private/{bot_id}", response_model=BotOutput)
def get_private_bot(request: Request, bot_id: str):
    """Get private bot by id."""
    current_user: User = request.state.current_user

    bot = find_bot_by_id(bot_id)
    if not bot.is_owned_by_user(current_user):
        raise PermissionError("The bot is not owned by the user.")

    return bot.to_output()


@router.get("/bot/summary/{bot_id}", response_model=BotSummaryOutput)
def get_bot_summary(request: Request, bot_id: str):
    """Get bot summary by id."""
    current_user: User = request.state.current_user

    return fetch_bot_summary(current_user, bot_id)


@router.delete("/bot/{bot_id}")
def delete_bot(request: Request, bot_id: str):
    """Delete bot by id. This can be used for both owned and shared bots.
    If the bot is shared, just remove the alias.
    """
    current_user: User = request.state.current_user
    remove_bot_by_id(current_user, bot_id)


@router.get("/bot/{bot_id}/presigned-url", response_model=BotPresignedUrlOutput)
def get_bot_presigned_url(
    request: Request, bot_id: str, filename: str, contentType: str
):
    """Get presigned url for bot"""
    current_user: User = request.state.current_user
    url = issue_presigned_url(current_user, bot_id, filename, contentType)
    return BotPresignedUrlOutput(url=url)


@router.delete("/bot/{bot_id}/uploaded-file")
def delete_bot_uploaded_file(request: Request, bot_id: str, filename: str):
    """Delete uploaded file for bot"""
    current_user: User = request.state.current_user
    remove_uploaded_file(current_user, bot_id, filename)


@router.delete("/bot/{bot_id}/recently-used")
def remove_bot_from_recent_history(request: Request, bot_id: str):
    """Remove bot from recently used bots history by removing LastUsedTime attribute."""
    current_user: User = request.state.current_user
    remove_bot_from_recently_used(current_user, bot_id)
    return {"message": f"Bot {bot_id} removed from recently used bots history"}


@router.get("/bot/{bot_id}/agent/available-tools", response_model=list[PlainTool])
def get_bot_available_tools(request: Request, bot_id: str):
    """Get available tools for bot"""
    tools = fetch_available_agent_tools()
    return [
        PlainTool(tool_type="plain", name=tool.name, description=tool.description)
        for tool in tools
    ]


# SQL Knowledge Base Endpoints
@router.post("/bot/{bot_id}/knowledge-base/sql", response_model=SqlKnowledgeBaseOutput)
def create_sql_knowledge_base_endpoint(
    request: Request,
    bot_id: str,
    sql_kb_input: SqlKnowledgeBaseInput,
):
    """Create SQL Knowledge Base for bot with Redshift data source."""
    from app.repositories.sql_knowledge_base import create_sql_knowledge_base
    from app.repositories.models.custom_bot_kb import SqlDatabaseConfigModel

    current_user: User = request.state.current_user

    # Verify bot ownership
    bot = find_bot_by_id(bot_id)
    if not bot.is_owned_by_user(current_user):
        raise PermissionError("The bot is not owned by the user.")

    # Convert schema to model
    sql_config = SqlDatabaseConfigModel(
        workgroup_name=sql_kb_input.database_config.workgroup_name,
        workgroup_arn=sql_kb_input.database_config.workgroup_arn,
        database_name=sql_kb_input.database_config.database_name,
        table_name=sql_kb_input.database_config.table_name,
        field_mapping=sql_kb_input.database_config.field_mapping,
        secret_arn=sql_kb_input.database_config.secret_arn,
        embedding_model_arn=sql_kb_input.embedding_model_arn,
    )

    # Create SQL Knowledge Base
    kb_id, data_source_id = create_sql_knowledge_base(
        bot_id=bot_id,
        sql_config=sql_config,
        kb_name=f"sql-kb-{bot_id}",
    )

    logger.info(f"Created SQL KB {kb_id} for bot {bot_id}")

    # Return output
    return SqlKnowledgeBaseOutput(
        knowledge_base_type="SQL",
        database_config=sql_kb_input.database_config,
        search_params=sql_kb_input.search_params,
        embedding_model_arn=sql_kb_input.embedding_model_arn,
        knowledge_base_id=kb_id,
        data_source_ids=[data_source_id] if data_source_id else [],
        status="CREATING",
    )


@router.get(
    "/bot/{bot_id}/knowledge-base/status", response_model=KnowledgeBaseStatusOutput
)
def get_knowledge_base_status(request: Request, bot_id: str, knowledge_base_id: str):
    """Get ingestion job status for SQL Knowledge Base."""
    from app.repositories.sql_knowledge_base import get_ingestion_job_status

    current_user: User = request.state.current_user

    # Verify bot ownership
    bot = find_bot_by_id(bot_id)
    if not bot.is_owned_by_user(current_user):
        raise PermissionError("The bot is not owned by the user.")

    # Get data source ID from bot knowledge base configuration
    # Note: In a full implementation, this should be stored in DynamoDB with the bot
    # For now, we'll need to list data sources to get the ID
    from app.utils import get_bedrock_agent_client

    client = get_bedrock_agent_client()
    data_sources = client.list_data_sources(knowledgeBaseId=knowledge_base_id)
    data_source_id = None
    if data_sources.get("dataSourceSummaries"):
        data_source_id = data_sources["dataSourceSummaries"][0]["dataSourceId"]

    if not data_source_id:
        return KnowledgeBaseStatusOutput(
            knowledge_base_id=knowledge_base_id,
            status="ACTIVE",
            ingestion_job_id=None,
            ingestion_job_status=None,
        )

    # Get ingestion status
    status_info = get_ingestion_job_status(knowledge_base_id, data_source_id)

    return KnowledgeBaseStatusOutput(
        knowledge_base_id=knowledge_base_id,
        status=status_info.get("status", "UNKNOWN"),
        ingestion_job_id=status_info.get("ingestion_job_id"),
        ingestion_job_status=status_info.get("ingestion_job_status"),
        error_message=status_info.get("error"),
    )


@router.post("/bot/{bot_id}/knowledge-base/query", response_model=SqlQueryOutput)
def query_knowledge_base(
    request: Request,
    bot_id: str,
    query_input: SqlQueryInput,
    knowledge_base_id: str,
):
    """Query SQL Knowledge Base with natural language."""
    from app.repositories.sql_knowledge_base import query_sql_knowledge_base

    current_user: User = request.state.current_user

    # Verify bot ownership
    bot = find_bot_by_id(bot_id)
    if not bot.is_owned_by_user(current_user):
        raise PermissionError("The bot is not owned by the user.")

    # Query the knowledge base
    result = query_sql_knowledge_base(
        knowledge_base_id=knowledge_base_id,
        query=query_input.query,
        user_id=current_user.id,
        max_results=query_input.max_results,
    )

    logger.info(f"Queried SQL KB {knowledge_base_id} for bot {bot_id}")

    return result


@router.delete("/bot/{bot_id}/knowledge-base")
def delete_knowledge_base(request: Request, bot_id: str, knowledge_base_id: str):
    """Delete SQL Knowledge Base."""
    from app.repositories.sql_knowledge_base import delete_sql_knowledge_base

    current_user: User = request.state.current_user

    # Verify bot ownership
    bot = find_bot_by_id(bot_id)
    if not bot.is_owned_by_user(current_user):
        raise PermissionError("The bot is not owned by the user.")

    # Delete the knowledge base
    success = delete_sql_knowledge_base(knowledge_base_id)

    if success:
        logger.info(f"Deleted SQL KB {knowledge_base_id} for bot {bot_id}")
        return {"success": True, "message": f"Knowledge Base {knowledge_base_id} deleted successfully"}
    else:
        logger.error(f"Failed to delete SQL KB {knowledge_base_id}")
        return {"success": False, "message": f"Failed to delete Knowledge Base {knowledge_base_id}"}


@router.get("/knowledge-base/{knowledge_base_id}")
def get_knowledge_base_details(knowledge_base_id: str):
    """Get knowledge base configuration details."""
    try:
        kb_info = get_knowledge_base_info(knowledge_base_id)
        return {
            "knowledgeBaseId": knowledge_base_id,
            "type": kb_info.knowledge_base.knowledge_base_configuration.type
        }
    except Exception as e:
        logger.error(f"Failed to get KB details for {knowledge_base_id}: {e}")
        raise HTTPException(status_code=404, detail=f"Knowledge Base {knowledge_base_id} not found")


# Aurora Vector Knowledge Base Endpoints
@router.post("/bot/{bot_id}/knowledge-base/aurora", response_model=AuroraVectorKnowledgeBaseOutput)
def create_aurora_knowledge_base_endpoint(
    request: Request,
    bot_id: str,
    aurora_kb_input: AuroraVectorKnowledgeBaseInput,
):
    """Create Aurora Vector Knowledge Base for bot with S3 data source."""
    from app.repositories.aurora_vector_kb import create_aurora_knowledge_base
    from app.repositories.models.custom_bot_kb import AuroraVectorConfigModel

    current_user: User = request.state.current_user

    # Verify bot ownership
    bot = find_bot_by_id(bot_id)
    if not bot.is_owned_by_user(current_user):
        raise PermissionError("The bot is not owned by the user.")

    # Build Aurora configuration
    aurora_config = AuroraVectorConfigModel(
        cluster_name=aurora_kb_input.aurora_config.cluster_name,
        cluster_arn=aurora_kb_input.aurora_config.cluster_arn,
        database_name=aurora_kb_input.aurora_config.database_name,
        table_name=aurora_kb_input.aurora_config.table_name,
        secret_arn=aurora_kb_input.aurora_config.secret_arn,
        embeddings_model=aurora_kb_input.aurora_config.embeddings_model,
        embedding_dimensions=aurora_kb_input.aurora_config.embedding_dimensions,
        chunking_configuration=aurora_kb_input.chunking_configuration,
        parsing_model=aurora_kb_input.parsing_model,
    )

    # Create Aurora Vector Knowledge Base
    # Note: For now, we'll use a default S3 bucket. In production, this should be configurable
    import os
    document_bucket_arn = os.getenv("DOCUMENT_BUCKET_ARN", f"arn:aws:s3:::bedrock-kb-documents-{bot_id}")
    
    kb_id, data_source_id = create_aurora_knowledge_base(
        bot_id=bot_id,
        aurora_config=aurora_config,
        kb_name=f"aurora-kb-{bot_id}",
        document_bucket_arn=document_bucket_arn,
        document_prefix=f"bot-{bot_id}/",
    )

    logger.info(f"Created Aurora Vector KB {kb_id} for bot {bot_id}")

    # Return output
    return AuroraVectorKnowledgeBaseOutput(
        knowledge_base_type="AURORA_VECTOR",
        aurora_config=aurora_kb_input.aurora_config,
        chunking_configuration=aurora_kb_input.chunking_configuration,
        search_params=aurora_kb_input.search_params,
        parsing_model=aurora_kb_input.parsing_model,
        knowledge_base_id=kb_id,
        data_source_ids=[data_source_id] if data_source_id else [],
        status="CREATING",
    )


@router.post("/bot/{bot_id}/knowledge-base/aurora/query", response_model=AuroraVectorQueryOutput)
def query_aurora_knowledge_base_endpoint(
    request: Request,
    bot_id: str,
    query_input: AuroraVectorQueryInput,
    knowledge_base_id: str,
):
    """Query Aurora Vector Knowledge Base with natural language."""
    from app.repositories.aurora_vector_kb import query_aurora_knowledge_base
    import time

    current_user: User = request.state.current_user

    # Verify bot ownership
    bot = find_bot_by_id(bot_id)
    if not bot.is_owned_by_user(current_user):
        raise PermissionError("The bot is not owned by the user.")

    # Query the knowledge base
    start_time = time.time()
    result = query_aurora_knowledge_base(
        knowledge_base_id=knowledge_base_id,
        query=query_input.query,
        max_results=query_input.max_results,
        min_similarity_score=query_input.min_similarity_score,
        metadata_filter=query_input.metadata_filter,
    )
    query_latency_ms = int((time.time() - start_time) * 1000)

    logger.info(f"Queried Aurora Vector KB {knowledge_base_id} for bot {bot_id} in {query_latency_ms}ms")

    return AuroraVectorQueryOutput(
        citations=result["citations"],
        total_results=result["total_results"],
        knowledge_base_id=knowledge_base_id,
        query_latency_ms=query_latency_ms,
    )


@router.get("/bot/{bot_id}/knowledge-base/aurora/status", response_model=KnowledgeBaseStatusOutput)
def get_aurora_knowledge_base_status(
    request: Request, 
    bot_id: str, 
    knowledge_base_id: str
):
    """Get Aurora Vector Knowledge Base status."""
    from app.repositories.aurora_vector_kb import get_aurora_knowledge_base_status

    current_user: User = request.state.current_user

    # Verify bot ownership
    bot = find_bot_by_id(bot_id)
    if not bot.is_owned_by_user(current_user):
        raise PermissionError("The bot is not owned by the user.")

    # Get KB status
    status_info = get_aurora_knowledge_base_status(knowledge_base_id)

    return KnowledgeBaseStatusOutput(
        knowledge_base_id=knowledge_base_id,
        status=status_info.get("status", "UNKNOWN"),
        ingestion_job_id=None,  # Aurora Vector doesn't use ingestion jobs
        ingestion_job_status=None,
        error_message=None,
    )


@router.delete("/bot/{bot_id}/knowledge-base/aurora")
def delete_aurora_knowledge_base_endpoint(
    request: Request, 
    bot_id: str, 
    knowledge_base_id: str
):
    """Delete Aurora Vector Knowledge Base."""
    from app.repositories.aurora_vector_kb import delete_aurora_knowledge_base

    current_user: User = request.state.current_user

    # Verify bot ownership
    bot = find_bot_by_id(bot_id)
    if not bot.is_owned_by_user(current_user):
        raise PermissionError("The bot is not owned by the user.")

    # Delete the knowledge base
    success = delete_aurora_knowledge_base(knowledge_base_id)

    if success:
        logger.info(f"Deleted Aurora Vector KB {knowledge_base_id} for bot {bot_id}")
        return {"success": True, "message": f"Aurora Vector Knowledge Base {knowledge_base_id} deleted successfully"}
    else:
        logger.error(f"Failed to delete Aurora Vector KB {knowledge_base_id}")
        return {"success": False, "message": f"Failed to delete Aurora Vector Knowledge Base {knowledge_base_id}"}
