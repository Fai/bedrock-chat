"""SQL Knowledge Base routes for schema management."""

import logging
from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.repositories.models.custom_bot import BotModel
from app.repositories.custom_bot import find_bot_by_id
from app.user import User
from app.sql_kb_schema_sync import sync_sql_kb_schema
from pydantic import BaseModel
import os

router = APIRouter(tags=["sql-kb"])
logger = logging.getLogger(__name__)


class SyncSchemaRequest(BaseModel):
    """Request to sync SQL KB schema."""
    bot_id: str


class SyncSchemaResponse(BaseModel):
    """Response from schema sync."""
    success: bool
    message: str
    tables_synced: int


@router.post("/sql-kb/sync-schema", response_model=SyncSchemaResponse)
def sync_sql_kb_schema_endpoint(
    request: SyncSchemaRequest,
    user: User = Depends(get_current_user),
) -> SyncSchemaResponse:
    """
    Manually trigger schema sync for a SQL Knowledge Base.

    This endpoint queries the Redshift database to get the current table schema
    and updates the Bedrock Knowledge Base configuration with that schema.

    Returns:
        Success status and number of tables synced
    """
    try:
        # Get bot to verify ownership and get KB ID
        bot = find_bot_by_id(request.bot_id, user.id)

        if not bot.bedrock_knowledge_base:
            return SyncSchemaResponse(
                success=False,
                message="Bot does not have a knowledge base configured",
                tables_synced=0
            )

        # Check if it's a SQL KB
        kb_type = getattr(bot.bedrock_knowledge_base, 'knowledge_base_type', 'VECTOR')
        if kb_type != 'SQL':
            return SyncSchemaResponse(
                success=False,
                message="Bot knowledge base is not a SQL type",
                tables_synced=0
            )

        # Get KB configuration
        knowledge_base_id = (
            bot.bedrock_knowledge_base.exist_knowledge_base_id
            if bot.bedrock_knowledge_base.exist_knowledge_base_id
            else bot.bedrock_knowledge_base.knowledge_base_id
        )

        if not knowledge_base_id:
            return SyncSchemaResponse(
                success=False,
                message="Knowledge base ID not found",
                tables_synced=0
            )

        # Get SQL KB configuration details
        from app.repositories.knowledge_base import get_knowledge_base_info
        kb_info = get_knowledge_base_info(knowledge_base_id=knowledge_base_id)

        sql_config = kb_info.knowledge_base.knowledge_base_configuration.sql_knowledge_base_configuration
        redshift_config = sql_config.redshift_configuration

        # Extract connection details
        query_engine = redshift_config.query_engine_configuration
        serverless_config = query_engine.serverless_configuration
        workgroup_arn = serverless_config.workgroup_arn

        # Parse workgroup name from ARN
        workgroup_name = workgroup_arn.split('/')[-1]

        # Get database name
        storage_config = redshift_config.storage_configurations[0]
        database = storage_config.redshift_configuration.database_name

        logger.info(f"Syncing schema for KB {knowledge_base_id}, workgroup={workgroup_name}, db={database}")

        # Perform schema sync
        from app.sql_kb_schema_sync import get_redshift_schema, update_kb_schema

        region = os.environ.get("BEDROCK_REGION", "us-east-1")

        # Get schema from Redshift
        tables_schema = get_redshift_schema(
            workgroup_name=workgroup_name,
            database=database,
            schema="public",
            region=region
        )

        if not tables_schema:
            return SyncSchemaResponse(
                success=False,
                message="No tables found in database schema",
                tables_synced=0
            )

        # Update KB configuration
        update_kb_schema(
            knowledge_base_id=knowledge_base_id,
            tables_schema=tables_schema,
            region=region
        )

        logger.info(f"Successfully synced {len(tables_schema)} tables for KB {knowledge_base_id}")

        return SyncSchemaResponse(
            success=True,
            message=f"Successfully synced schema with {len(tables_schema)} tables",
            tables_synced=len(tables_schema)
        )

    except Exception as e:
        logger.error(f"Error syncing SQL KB schema: {e}")
        return SyncSchemaResponse(
            success=False,
            message=f"Error: {str(e)}",
            tables_synced=0
        )
