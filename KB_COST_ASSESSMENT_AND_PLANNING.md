# Knowledge Base Cost Assessment & Implementation Planning

**Project**: BrChat v3.x - KB Services Cost Management
**Date**: 2025-10-08
**Status**: Planning Phase
**Author**: Development Team

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current Infrastructure Cost Analysis](#current-infrastructure-cost-analysis)
3. [New KB Services Cost Breakdown](#new-kb-services-cost-breakdown)
4. [Cost Calculator Implementation Plan](#cost-calculator-implementation-plan)
5. [Cost Monitoring & Optimization Strategy](#cost-monitoring--optimization-strategy)
6. [Implementation Roadmap](#implementation-roadmap)

---

## Executive Summary

### Current State

BrChat v3.x currently uses **OpenSearch Serverless** for Knowledge Base (RAG) storage with the following cost structure:
- **Base Cost**: ~$700/month (4 OCU minimum for collection + indexing pipeline)
- **Scaling**: Additional OCU capacity based on workload
- **Standby Replicas**: Optional (disabled in dev, enabled in prod for HA)

### New KB Services Being Added

| KB Type | Storage Backend | Typical Monthly Cost | Use Case |
|---------|----------------|----------------------|----------|
| **S3 Vectors** (Preview) | S3 Vectors | $0.13 - $5 | Cost-sensitive, <500 token chunks |
| **Redshift SQL KB** (Implemented) | Redshift Serverless | $260 - $500 | Large datasets, analytics queries |
| **Aurora Vector KB** (Planned v4.0) | Aurora PostgreSQL | $44 - $100 | Frequent queries, relational data |

### Cost Impact Analysis

**Monthly Cost Range by Deployment Size**:

| Deployment | Current (OpenSearch) | With New KBs | Potential Savings |
|------------|---------------------|--------------|-------------------|
| **Small** (1-5 bots, 100 queries/day) | $700 | $44 - $260 | **62-94%** |
| **Medium** (5-20 bots, 1000 queries/day) | $1,200 | $100 - $500 | **58-92%** |
| **Large** (20+ bots, 5000+ queries/day) | $2,000+ | $500 - $1,000 | **50-75%** |

**Key Insight**: New KB options provide **50-94% cost savings** for most workloads while maintaining or improving performance.

---

## Current Infrastructure Cost Analysis

### 1. Core Services (Always Running)

#### 1.1 Compute & API

| Service | Component | Configuration | Monthly Cost | Notes |
|---------|-----------|---------------|--------------|-------|
| **Lambda** | Backend API Handler | 1 GB RAM, arm64 | ~$20-50 | SnapStart enabled (prod) |
| **Lambda** | WebSocket Handler | 1 GB RAM, arm64 | ~$15-30 | Streaming responses |
| **Lambda** | Embedding State Machine | 3 GB RAM, x86 | ~$5-15 | KB ingestion pipeline |
| **Lambda** | Bot Store Sync | 512 MB RAM | ~$2-5 | DynamoDB → OpenSearch |
| **API Gateway** | HTTP API | REST endpoints | ~$5-10 | Pay per request |
| **API Gateway** | WebSocket API | Streaming | ~$5-10 | Connection + message charges |
| **CloudFront** | CDN Distribution | S3 origin | ~$5-20 | Data transfer charges |

**Subtotal**: **$57 - $140/month**

#### 1.2 Database & Storage

| Service | Component | Configuration | Monthly Cost | Notes |
|---------|-----------|---------------|--------------|-------|
| **DynamoDB** | Conversation Table | On-demand, streams | ~$20-50 | Per request pricing |
| **DynamoDB** | Bot Table | On-demand, streams, PITR | ~$15-40 | Global indexes |
| **DynamoDB** | WebSocket Session Table | On-demand, TTL | ~$2-5 | Temporary storage |
| **S3** | Document Bucket | Standard class | ~$5-20 | Per GB/month |
| **S3** | Large Message Bucket | Standard class | ~$2-10 | >300KB messages |
| **S3** | Source Code Bucket | Standard class | ~$1-5 | CodeBuild artifacts |
| **S3** | Access Logs Bucket | Standard class | ~$1-5 | CloudFront/ALB logs |

**Subtotal**: **$46 - $135/month**

#### 1.3 Authentication & Security

| Service | Component | Configuration | Monthly Cost | Notes |
|---------|-----------|---------------|--------------|-------|
| **Cognito** | User Pool | MAU pricing | ~$5-50 | First 50K MAU free |
| **WAF** | CloudFront WebACL | Rules + requests | ~$5-15 | IP allowlist rules |
| **WAF** | Cognito WebACL | Rules + requests | ~$5-15 | Optional |
| **WAF** | Published API WebACL | Rules + requests | ~$5-15 | API publication |
| **Secrets Manager** | Secrets (IAM, RDS) | Per secret/month | ~$1-5 | $0.40/secret |
| **KMS** | Customer Managed Keys | Per key + requests | ~$1-5 | Encryption |

**Subtotal**: **$22 - $105/month**

---

### 2. Knowledge Base Services (Current: OpenSearch Serverless)

#### 2.1 OpenSearch Serverless (RAG)

| Component | Configuration | Monthly Cost | Formula |
|-----------|---------------|--------------|---------|
| **Collection** | 4 OCU minimum | $700.80 | 4 OCU × $0.24/hour × 730 hours |
| **Standby Replicas** | Optional (prod) | +$700.80 | Doubles cost for HA |
| **Indexing Pipeline** | OSIS pipeline | $175.20 | 1 OCU × $0.24/hour × 730 hours |
| **Scaling** | Auto (peak load) | Variable | Additional OCU charged hourly |

**Scenarios**:
- **Dev** (no replicas): **$876/month** (4 OCU collection + 1 OCU pipeline)
- **Prod** (with replicas): **$1,577/month** (8 OCU collection + 1 OCU pipeline)

#### 2.2 Bot Store (Optional Feature)

| Component | Configuration | Monthly Cost | Formula |
|-----------|---------------|--------------|---------|
| **OpenSearch Collection** | 4 OCU minimum | $700.80 | Same as RAG collection |
| **Standby Replicas** | Optional (prod) | +$700.80 | Doubles cost |
| **OSIS Pipeline** | Bot/Conversation sync | $175.20 | 1 OCU × $0.24/hour × 730 hours |

**Scenarios**:
- **Dev** (no replicas): **$876/month**
- **Prod** (with replicas): **$1,577/month**

**Total with Bot Store Enabled**:
- **Dev**: $876 (RAG) + $876 (Bot Store) = **$1,752/month**
- **Prod**: $1,577 (RAG) + $1,577 (Bot Store) = **$3,154/month**

---

### 3. CodeBuild (Dynamic KB Stack Creation)

| Component | Configuration | Monthly Cost | Notes |
|-----------|---------------|--------------|-------|
| **Custom Bot KB Build** | general1.small (on-demand) | ~$5-20 | Per KB creation (15-30 min builds) |
| **API Publish Build** | general1.small (on-demand) | ~$2-10 | Per API publication |

**Formula**: $0.005/minute × build minutes
- Small bot (5 min): $0.025
- Large bot (30 min): $0.15

**Typical**: 10-50 KB creations/month = **$5-20/month**

---

### 4. Usage Analytics (Optional Feature)

| Service | Component | Configuration | Monthly Cost | Notes |
|---------|-----------|---------------|--------------|-------|
| **Athena** | Query processing | Per TB scanned | ~$5-20 | $5/TB scanned |
| **Glue** | Data Catalog | Per object/month | ~$1-5 | $1/100K objects |
| **S3** | Query results | Standard class | ~$1-5 | Result storage |

**Subtotal**: **$7 - $30/month** (if enabled)

---

### Current Infrastructure Total Cost

| Scenario | Monthly Cost | Annual Cost | Notes |
|----------|--------------|-------------|-------|
| **Minimal** (no Bot Store, dev settings) | $1,007 - $1,286 | $12,084 - $15,432 | Core + RAG only |
| **Dev** (Bot Store, no replicas) | $1,883 - $2,162 | $22,596 - $25,944 | Full features, cost-optimized |
| **Prod** (Bot Store, replicas, analytics) | $3,423 - $3,784 | $41,076 - $45,408 | Full HA + all features |

**Breakdown (Prod)**:
- Core Services: $125 - $380/month
- OpenSearch RAG (with replicas): $1,577/month
- Bot Store (with replicas): $1,577/month
- CodeBuild: $10 - $30/month
- Analytics: $7 - $30/month
- Bedrock API calls: $100 - $500/month (variable)

---

## New KB Services Cost Breakdown

### 1. S3 Vectors Knowledge Base (Preview)

#### Cost Components

| Component | Pricing | Monthly Cost (1M vectors, 1024-dim) | Notes |
|-----------|---------|-------------------------------------|-------|
| **Vector Storage** | $0.00013 per 1M vectors | $0.13 | 99% cheaper than OpenSearch |
| **Vector Bucket** | Standard S3 pricing | ~$0.023/GB | Minimal (vectors only) |
| **Query Requests** | $0.0004 per 1K requests | $0.012 (30K queries) | Sub-second latency |
| **Embedding Generation** | Titan V2: $0.0001/1K tokens | $10 (100M tokens) | During ingestion |
| **Data Transfer** | Standard S3 egress | Variable | Same-region = free |

**Total Monthly Cost Example**:
- **1M vectors, 1024-dim**: **$0.13/month** (storage only)
- **100 queries/day** (3K/month): $0.13 + $0.0012 = **$0.13/month**
- **1000 queries/day** (30K/month): $0.13 + $0.012 = **$0.14/month**

**vs OpenSearch Serverless**: **99.98% cost reduction** ($0.14 vs $700/month)

#### Scaling Characteristics

| Vectors | Storage Cost | Query Cost (100/day) | Total Monthly |
|---------|--------------|----------------------|---------------|
| 1M | $0.13 | $0.0012 | $0.13 |
| 10M | $1.30 | $0.012 | $1.31 |
| 100M | $13.00 | $0.12 | $13.12 |
| 1B | $130.00 | $1.20 | $131.20 |

**Key Constraint**: **500 token chunk limit** (critical for document size planning)

---

### 2. Redshift Serverless SQL KB (Implemented)

#### Cost Components

| Component | Pricing | Monthly Cost | Configuration |
|-----------|---------|--------------|---------------|
| **Base Capacity** | $0.36/RPU-hour | $2,102.40 | 8 RPU minimum × 730 hours |
| **Auto-Pause Savings** | Automatic after 60 min idle | Variable | Can reduce cost by 50-80% |
| **Storage** | $45/TB/month | $4.50 (100 GB) | Managed storage |
| **Data Scanned** | Included | $0 | No additional query charges |
| **Cross-AZ Data Transfer** | $0.01/GB | ~$1-5 | Usually minimal |

**Scenarios**:

**Infrequent Use** (4 hours/day active, 20 hours paused):
- Active: 4 hours × 30 days × 8 RPU × $0.36 = $345.60
- Storage: $4.50
- **Total**: ~**$350/month**

**Moderate Use** (12 hours/day active, 12 hours paused):
- Active: 12 hours × 30 days × 8 RPU × $0.36 = $1,036.80
- Storage: $4.50
- **Total**: ~**$1,041/month**

**Heavy Use** (24/7 active, no auto-pause):
- Active: 730 hours × 8 RPU × $0.36 = $2,102.40
- Storage: $4.50
- **Total**: ~**$2,107/month**

#### Scaling & RPU Usage

| Workload | RPU Capacity | Cost/Hour | Use Case |
|----------|--------------|-----------|----------|
| Light | 8 RPU (minimum) | $2.88 | Small datasets, simple queries |
| Medium | 32 RPU | $11.52 | Medium datasets, complex queries |
| Heavy | 128 RPU | $46.08 | Large datasets, concurrent users |
| Maximum | 512 RPU | $184.32 | Massive scale |

**Auto-Scaling**: Redshift automatically scales RPU based on workload (pay for what you use)

---

### 3. Aurora PostgreSQL Vector KB (Planned v4.0)

#### Aurora Serverless v2 Cost Components

| Component | Pricing | Monthly Cost (0.5-1 ACU) | Configuration |
|-----------|---------|-------------------------|---------------|
| **Base Capacity** | $0.12/ACU-hour | $43.80 | 0.5 ACU × 730 hours |
| **Peak Scaling** | $0.12/ACU-hour | Variable | Auto-scales to 4 ACU max |
| **Storage** | $0.10/GB/month | $1.00 (10 GB) | Database size |
| **I/O Requests** | $0.20 per 1M requests | $0.02 (100K I/O) | Included in Serverless v2 |
| **Backup Storage** | $0.021/GB/month | $0.21 (10 GB) | Automated backups |
| **Snapshot Export** | S3 pricing | Optional | Data export costs |

**Scenarios**:

**Light Workload** (0.5 ACU constant):
- Compute: 0.5 ACU × 730 hours × $0.12 = $43.80
- Storage: $1.00 (10 GB)
- I/O: $0.02
- Backup: $0.21
- **Total**: ~**$45/month**

**Moderate Workload** (0.5 ACU base, scales to 1 ACU for 4 hours/day):
- Base: 0.5 ACU × 730 hours × $0.12 = $43.80
- Peak: 0.5 ACU × 120 hours × $0.12 = $7.20
- Storage: $5.00 (50 GB)
- I/O: $0.20 (1M requests)
- Backup: $1.05 (50 GB)
- **Total**: ~**$57/month**

**Heavy Workload** (1 ACU constant, occasional spikes to 2 ACU):
- Base: 1 ACU × 730 hours × $0.12 = $87.60
- Peak: 1 ACU × 100 hours × $0.12 = $12.00
- Storage: $10.00 (100 GB)
- I/O: $2.00 (10M requests)
- Backup: $2.10 (100 GB)
- **Total**: ~**$114/month**

#### Aurora Provisioned (Alternative)

| Instance Type | vCPU | RAM | Cost/Hour | Monthly Cost | Use Case |
|---------------|------|-----|-----------|--------------|----------|
| **db.t4g.medium** | 2 | 4 GB | $0.087 | $63.51 | Dev/test |
| **db.r6g.large** | 2 | 16 GB | $0.240 | $175.20 | Production |
| **db.r6g.xlarge** | 4 | 32 GB | $0.480 | $350.40 | High performance |

**+ Storage** ($0.10/GB) + I/O ($0.20/1M) + Backup ($0.021/GB)

---

### Cost Comparison Matrix

#### Scenario: 10M Vectors, 1000 Queries/Day, 100 GB Data

| KB Type | Storage Backend | Monthly Cost | Query Latency | Best For |
|---------|----------------|--------------|---------------|----------|
| **Current** | OpenSearch Serverless | $876 (dev) / $1,577 (prod) | <50ms | Production RAG, hybrid search |
| **S3 Vectors** | S3 Vectors (Preview) | $13.14 | <1s | Cost-sensitive, simple RAG |
| **Redshift** | Redshift Serverless | $350 (auto-pause) / $2,107 (24/7) | 1-5s | Analytics, large datasets |
| **Aurora** | Aurora Serverless v2 | $57 (light) / $114 (heavy) | <100ms | Frequent queries, relational data |

---

## Cost Calculator Implementation Plan

### 1. Cost Estimation API

#### 1.1 Backend Cost Calculator Module

**File**: `backend/app/services/cost_calculator.py` (NEW)

```python
"""
KB Cost Calculator Service

Provides real-time cost estimates for different Knowledge Base types
based on user inputs (vectors, queries, data size).
"""

from enum import Enum
from typing import Dict, Optional
from pydantic import BaseModel


class KBType(str, Enum):
    OPENSEARCH = "opensearch_serverless"
    S3_VECTORS = "s3_vectors"
    REDSHIFT = "redshift_serverless"
    AURORA = "aurora_serverless_v2"


class CostEstimateInput(BaseModel):
    kb_type: KBType
    num_vectors: int  # Number of vectors to store
    vector_dimensions: int  # 256, 512, 1024, etc.
    queries_per_day: int  # Query volume
    data_size_gb: Optional[int] = None  # For Redshift/Aurora
    auto_pause_hours: Optional[int] = None  # For Redshift (hours paused/day)
    enable_replicas: bool = False  # For OpenSearch (HA)


class CostBreakdown(BaseModel):
    storage_cost: float
    compute_cost: float
    io_cost: float
    backup_cost: float
    total_monthly_cost: float
    total_annual_cost: float
    cost_per_query: float
    notes: list[str]


def estimate_opensearch_cost(input: CostEstimateInput) -> CostBreakdown:
    """
    Calculate OpenSearch Serverless cost

    Pricing:
    - 4 OCU minimum for collection ($0.24/OCU-hour)
    - Standby replicas double the cost
    - 1 OCU for indexing pipeline ($0.24/OCU-hour)
    """
    hours_per_month = 730
    ocu_hourly_rate = 0.24

    # Base collection (4 OCU minimum)
    collection_ocu = 4
    if input.enable_replicas:
        collection_ocu *= 2  # Standby replicas

    # Indexing pipeline
    pipeline_ocu = 1

    total_ocu = collection_ocu + pipeline_ocu
    compute_cost = total_ocu * ocu_hourly_rate * hours_per_month

    # Storage included in OCU pricing
    storage_cost = 0.0
    io_cost = 0.0
    backup_cost = 0.0

    total_monthly = compute_cost
    total_annual = total_monthly * 12
    cost_per_query = total_monthly / (input.queries_per_day * 30) if input.queries_per_day > 0 else 0

    notes = [
        f"{total_ocu} OCU total ({collection_ocu} collection + {pipeline_ocu} pipeline)",
        "4 OCU minimum enforced",
        "Storage and I/O included in OCU pricing",
    ]

    if input.enable_replicas:
        notes.append("Standby replicas enabled (2x cost) for high availability")

    return CostBreakdown(
        storage_cost=storage_cost,
        compute_cost=compute_cost,
        io_cost=io_cost,
        backup_cost=backup_cost,
        total_monthly_cost=total_monthly,
        total_annual_cost=total_annual,
        cost_per_query=cost_per_query,
        notes=notes
    )


def estimate_s3_vectors_cost(input: CostEstimateInput) -> CostBreakdown:
    """
    Calculate S3 Vectors cost (Preview feature)

    Pricing:
    - $0.00013 per 1M vectors per month
    - $0.0004 per 1K query requests
    - Standard S3 storage for vector bucket
    """
    # Vector storage
    vectors_in_millions = input.num_vectors / 1_000_000
    storage_cost = vectors_in_millions * 0.00013

    # Query cost
    queries_per_month = input.queries_per_day * 30
    query_cost = (queries_per_month / 1000) * 0.0004

    # S3 bucket storage (minimal - just vector metadata)
    # Estimate ~100 bytes per vector for metadata
    storage_gb = (input.num_vectors * 100) / (1024**3)
    s3_storage_cost = storage_gb * 0.023  # Standard S3 pricing

    compute_cost = query_cost
    io_cost = 0.0
    backup_cost = 0.0
    total_storage = storage_cost + s3_storage_cost

    total_monthly = total_storage + compute_cost
    total_annual = total_monthly * 12
    cost_per_query = compute_cost / queries_per_month if queries_per_month > 0 else 0

    notes = [
        "Preview feature - not production-ready",
        "500 token chunk limit enforced",
        "Semantic search only (no hybrid search)",
        "Available in 5 regions only",
        f"{vectors_in_millions:.2f}M vectors stored",
        f"{storage_gb:.4f} GB S3 storage",
    ]

    return CostBreakdown(
        storage_cost=total_storage,
        compute_cost=compute_cost,
        io_cost=io_cost,
        backup_cost=backup_cost,
        total_monthly_cost=total_monthly,
        total_annual_cost=total_annual,
        cost_per_query=cost_per_query,
        notes=notes
    )


def estimate_redshift_cost(input: CostEstimateInput) -> CostBreakdown:
    """
    Calculate Redshift Serverless cost

    Pricing:
    - $0.36 per RPU-hour (8 RPU minimum)
    - $45/TB/month for managed storage
    - Auto-pause after 60 minutes of inactivity
    """
    hours_per_month = 730
    rpu_hourly_rate = 0.36
    base_rpu = 8
    storage_rate_per_gb = 0.045  # $45/TB

    # Calculate active hours based on auto-pause
    if input.auto_pause_hours:
        active_hours_per_day = 24 - input.auto_pause_hours
        active_hours_per_month = active_hours_per_day * 30
    else:
        active_hours_per_month = hours_per_month  # 24/7

    # Compute cost
    compute_cost = base_rpu * rpu_hourly_rate * active_hours_per_month

    # Storage cost
    data_size_gb = input.data_size_gb or 100  # Default 100 GB
    storage_cost = data_size_gb * storage_rate_per_gb

    io_cost = 0.0  # Included
    backup_cost = 0.0  # Managed backups included

    total_monthly = compute_cost + storage_cost
    total_annual = total_monthly * 12
    cost_per_query = total_monthly / (input.queries_per_day * 30) if input.queries_per_day > 0 else 0

    notes = [
        f"{base_rpu} RPU minimum capacity",
        f"{active_hours_per_month:.0f} active hours/month",
        f"{data_size_gb} GB managed storage",
    ]

    if input.auto_pause_hours:
        savings_percent = (input.auto_pause_hours / 24) * 100
        notes.append(f"Auto-pause enabled: ~{savings_percent:.0f}% cost reduction")
    else:
        notes.append("24/7 active (no auto-pause)")

    notes.append("Cold start: 30-60 seconds after auto-pause")

    return CostBreakdown(
        storage_cost=storage_cost,
        compute_cost=compute_cost,
        io_cost=io_cost,
        backup_cost=backup_cost,
        total_monthly_cost=total_monthly,
        total_annual_cost=total_annual,
        cost_per_query=cost_per_query,
        notes=notes
    )


def estimate_aurora_cost(input: CostEstimateInput) -> CostBreakdown:
    """
    Calculate Aurora Serverless v2 cost

    Pricing:
    - $0.12 per ACU-hour (0.5 ACU minimum)
    - $0.10/GB/month for storage
    - $0.20 per 1M I/O requests (included in Serverless v2)
    - $0.021/GB/month for backup storage
    """
    hours_per_month = 730
    acu_hourly_rate = 0.12
    base_acu = 0.5  # Minimum
    storage_rate_per_gb = 0.10
    io_rate_per_million = 0.20
    backup_rate_per_gb = 0.021

    # Compute cost (base capacity)
    compute_cost = base_acu * acu_hourly_rate * hours_per_month

    # Storage cost
    data_size_gb = input.data_size_gb or 10  # Default 10 GB
    storage_cost = data_size_gb * storage_rate_per_gb

    # I/O cost (estimate based on query volume)
    # Assume 10 I/O operations per query
    io_operations = input.queries_per_day * 30 * 10
    io_cost = (io_operations / 1_000_000) * io_rate_per_million

    # Backup cost (7-day retention)
    backup_cost = data_size_gb * backup_rate_per_gb

    total_monthly = compute_cost + storage_cost + io_cost + backup_cost
    total_annual = total_monthly * 12
    cost_per_query = total_monthly / (input.queries_per_day * 30) if input.queries_per_day > 0 else 0

    notes = [
        f"{base_acu} ACU minimum capacity",
        f"{data_size_gb} GB database storage",
        f"{io_operations:,.0f} I/O operations/month",
        "Auto-scales up to 4 ACU based on load",
        "Sub-100ms query latency",
        "pgvector 0.5.0+ with HNSW indexing",
    ]

    return CostBreakdown(
        storage_cost=storage_cost,
        compute_cost=compute_cost,
        io_cost=io_cost,
        backup_cost=backup_cost,
        total_monthly_cost=total_monthly,
        total_annual_cost=total_annual,
        cost_per_query=cost_per_query,
        notes=notes
    )


def calculate_cost(input: CostEstimateInput) -> CostBreakdown:
    """
    Main entry point for cost calculation
    """
    if input.kb_type == KBType.OPENSEARCH:
        return estimate_opensearch_cost(input)
    elif input.kb_type == KBType.S3_VECTORS:
        return estimate_s3_vectors_cost(input)
    elif input.kb_type == KBType.REDSHIFT:
        return estimate_redshift_cost(input)
    elif input.kb_type == KBType.AURORA:
        return estimate_aurora_cost(input)
    else:
        raise ValueError(f"Unknown KB type: {input.kb_type}")


def compare_all_kb_types(
    num_vectors: int,
    vector_dimensions: int,
    queries_per_day: int,
    data_size_gb: Optional[int] = None,
) -> Dict[str, CostBreakdown]:
    """
    Compare costs across all KB types for given parameters

    Returns:
        Dictionary mapping KB type to cost breakdown
    """
    results = {}

    # OpenSearch (dev - no replicas)
    results["opensearch_dev"] = calculate_cost(CostEstimateInput(
        kb_type=KBType.OPENSEARCH,
        num_vectors=num_vectors,
        vector_dimensions=vector_dimensions,
        queries_per_day=queries_per_day,
        enable_replicas=False
    ))

    # OpenSearch (prod - with replicas)
    results["opensearch_prod"] = calculate_cost(CostEstimateInput(
        kb_type=KBType.OPENSEARCH,
        num_vectors=num_vectors,
        vector_dimensions=vector_dimensions,
        queries_per_day=queries_per_day,
        enable_replicas=True
    ))

    # S3 Vectors
    results["s3_vectors"] = calculate_cost(CostEstimateInput(
        kb_type=KBType.S3_VECTORS,
        num_vectors=num_vectors,
        vector_dimensions=vector_dimensions,
        queries_per_day=queries_per_day
    ))

    # Redshift (with auto-pause)
    results["redshift_autopause"] = calculate_cost(CostEstimateInput(
        kb_type=KBType.REDSHIFT,
        num_vectors=num_vectors,
        vector_dimensions=vector_dimensions,
        queries_per_day=queries_per_day,
        data_size_gb=data_size_gb,
        auto_pause_hours=20  # 4 hours active/day
    ))

    # Redshift (24/7)
    results["redshift_247"] = calculate_cost(CostEstimateInput(
        kb_type=KBType.REDSHIFT,
        num_vectors=num_vectors,
        vector_dimensions=vector_dimensions,
        queries_per_day=queries_per_day,
        data_size_gb=data_size_gb,
        auto_pause_hours=0
    ))

    # Aurora
    results["aurora"] = calculate_cost(CostEstimateInput(
        kb_type=KBType.AURORA,
        num_vectors=num_vectors,
        vector_dimensions=vector_dimensions,
        queries_per_day=queries_per_day,
        data_size_gb=data_size_gb
    ))

    return results
```

#### 1.2 API Endpoint

**File**: `backend/app/routes/cost.py` (NEW)

```python
from fastapi import APIRouter
from app.services.cost_calculator import (
    calculate_cost,
    compare_all_kb_types,
    CostEstimateInput,
    CostBreakdown
)

router = APIRouter(prefix="/cost", tags=["cost"])


@router.post("/estimate", response_model=CostBreakdown)
def estimate_kb_cost(input: CostEstimateInput):
    """
    Estimate monthly cost for a specific KB type
    """
    return calculate_cost(input)


@router.post("/compare")
def compare_kb_costs(
    num_vectors: int,
    vector_dimensions: int,
    queries_per_day: int,
    data_size_gb: int | None = None
):
    """
    Compare costs across all KB types
    """
    return compare_all_kb_types(
        num_vectors=num_vectors,
        vector_dimensions=vector_dimensions,
        queries_per_day=queries_per_day,
        data_size_gb=data_size_gb
    )
```

---

### 2. Frontend Cost Calculator UI

#### 2.1 Cost Calculator Component

**File**: `frontend/src/features/knowledgeBase/components/CostCalculator.tsx` (NEW)

```typescript
import React, { useState, useMemo } from 'react';
import { Button, Input, Select, Card, Alert } from '@/components/ui';
import { useCostEstimate } from '@/hooks/useCostEstimate';

interface CostCalculatorProps {
  onSelectKBType?: (kbType: string, cost: number) => void;
}

export const CostCalculator: React.FC<CostCalculatorProps> = ({ onSelectKBType }) => {
  const [numVectors, setNumVectors] = useState(1000000); // 1M
  const [dimensions, setDimensions] = useState(1024);
  const [queriesPerDay, setQueriesPerDay] = useState(100);
  const [dataSizeGB, setDataSizeGB] = useState(100);

  const { data: comparison, isLoading, error } = useCostEstimate({
    num_vectors: numVectors,
    vector_dimensions: dimensions,
    queries_per_day: queriesPerDay,
    data_size_gb: dataSizeGB,
  });

  const formatCost = (cost: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(cost);
  };

  const getSavingsPercent = (baseCost: number, newCost: number) => {
    return ((baseCost - newCost) / baseCost * 100).toFixed(0);
  };

  return (
    <div className="space-y-6">
      {/* Input Section */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Cost Estimation Parameters</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              Number of Vectors
            </label>
            <Input
              type="number"
              value={numVectors}
              onChange={(e) => setNumVectors(parseInt(e.target.value))}
              min={1000}
              step={1000}
            />
            <span className="text-xs text-gray-500">
              {(numVectors / 1_000_000).toFixed(2)}M vectors
            </span>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Vector Dimensions
            </label>
            <Select
              value={dimensions}
              onChange={(e) => setDimensions(parseInt(e.target.value))}
            >
              <option value={256}>256 (Titan V2 small)</option>
              <option value={512}>512 (Titan V2 medium)</option>
              <option value={1024}>1024 (Titan V2 full, Cohere)</option>
              <option value={1536}>1536 (Titan V1)</option>
            </Select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Queries Per Day
            </label>
            <Input
              type="number"
              value={queriesPerDay}
              onChange={(e) => setQueriesPerDay(parseInt(e.target.value))}
              min={1}
              step={10}
            />
            <span className="text-xs text-gray-500">
              {(queriesPerDay * 30).toLocaleString()} queries/month
            </span>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Data Size (GB) - for SQL KBs
            </label>
            <Input
              type="number"
              value={dataSizeGB}
              onChange={(e) => setDataSizeGB(parseInt(e.target.value))}
              min={1}
              step={10}
            />
          </div>
        </div>
      </Card>

      {/* Results Section */}
      {isLoading && <div>Calculating costs...</div>}
      {error && <Alert variant="error">{error.message}</Alert>}

      {comparison && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* OpenSearch Serverless */}
          <CostCard
            title="OpenSearch Serverless (Current)"
            subtitle="Production with replicas"
            cost={comparison.opensearch_prod.total_monthly_cost}
            breakdown={comparison.opensearch_prod}
            isRecommended={false}
            onSelect={() => onSelectKBType?.('opensearch', comparison.opensearch_prod.total_monthly_cost)}
          />

          {/* S3 Vectors */}
          <CostCard
            title="S3 Vectors (Preview)"
            subtitle="99% cost savings"
            cost={comparison.s3_vectors.total_monthly_cost}
            breakdown={comparison.s3_vectors}
            isRecommended={comparison.s3_vectors.total_monthly_cost < 5}
            badge="Cheapest"
            badgeColor="green"
            savingsPercent={getSavingsPercent(
              comparison.opensearch_prod.total_monthly_cost,
              comparison.s3_vectors.total_monthly_cost
            )}
            onSelect={() => onSelectKBType?.('s3_vectors', comparison.s3_vectors.total_monthly_cost)}
          />

          {/* Aurora PostgreSQL */}
          <CostCard
            title="Aurora PostgreSQL"
            subtitle="Best performance/cost"
            cost={comparison.aurora.total_monthly_cost}
            breakdown={comparison.aurora}
            isRecommended={true}
            badge="Recommended"
            badgeColor="blue"
            savingsPercent={getSavingsPercent(
              comparison.opensearch_prod.total_monthly_cost,
              comparison.aurora.total_monthly_cost
            )}
            onSelect={() => onSelectKBType?.('aurora', comparison.aurora.total_monthly_cost)}
          />

          {/* Redshift Auto-Pause */}
          <CostCard
            title="Redshift Serverless"
            subtitle="With auto-pause"
            cost={comparison.redshift_autopause.total_monthly_cost}
            breakdown={comparison.redshift_autopause}
            isRecommended={false}
            savingsPercent={getSavingsPercent(
              comparison.opensearch_prod.total_monthly_cost,
              comparison.redshift_autopause.total_monthly_cost
            )}
            onSelect={() => onSelectKBType?.('redshift', comparison.redshift_autopause.total_monthly_cost)}
          />
        </div>
      )}
    </div>
  );
};

interface CostCardProps {
  title: string;
  subtitle: string;
  cost: number;
  breakdown: any;
  isRecommended?: boolean;
  badge?: string;
  badgeColor?: 'blue' | 'green' | 'yellow';
  savingsPercent?: string;
  onSelect?: () => void;
}

const CostCard: React.FC<CostCardProps> = ({
  title,
  subtitle,
  cost,
  breakdown,
  isRecommended,
  badge,
  badgeColor = 'blue',
  savingsPercent,
  onSelect,
}) => {
  const formatCost = (cost: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(cost);
  };

  return (
    <Card className={`p-6 ${isRecommended ? 'border-blue-500 border-2' : ''}`}>
      <div className="flex justify-between items-start mb-4">
        <div>
          <h4 className="font-semibold text-lg">{title}</h4>
          <p className="text-sm text-gray-500">{subtitle}</p>
        </div>
        {badge && (
          <span className={`px-2 py-1 text-xs font-semibold rounded bg-${badgeColor}-100 text-${badgeColor}-800`}>
            {badge}
          </span>
        )}
      </div>

      <div className="mb-4">
        <div className="text-3xl font-bold">{formatCost(cost)}</div>
        <div className="text-sm text-gray-500">/month</div>
        {savingsPercent && (
          <div className="text-sm text-green-600 font-medium mt-1">
            {savingsPercent}% savings
          </div>
        )}
      </div>

      <div className="space-y-2 mb-4 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-600">Storage:</span>
          <span className="font-medium">{formatCost(breakdown.storage_cost)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Compute:</span>
          <span className="font-medium">{formatCost(breakdown.compute_cost)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Cost per query:</span>
          <span className="font-medium">{formatCost(breakdown.cost_per_query)}</span>
        </div>
      </div>

      <div className="text-xs text-gray-500 mb-4">
        <ul className="list-disc list-inside space-y-1">
          {breakdown.notes.slice(0, 3).map((note: string, idx: number) => (
            <li key={idx}>{note}</li>
          ))}
        </ul>
      </div>

      {onSelect && (
        <Button onClick={onSelect} variant="primary" className="w-full">
          Select This Option
        </Button>
      )}
    </Card>
  );
};
```

---

### 3. Cost Monitoring Dashboard

#### 3.1 AWS Cost Explorer Integration

**Backend Service**: `backend/app/services/cost_monitoring.py` (NEW)

```python
"""
Cost Monitoring Service

Integrates with AWS Cost Explorer to track actual KB costs.
"""

import boto3
from datetime import datetime, timedelta
from typing import Dict, List

cost_explorer = boto3.client('ce')

def get_kb_costs_by_service(
    start_date: datetime,
    end_date: datetime,
    env_name: str
) -> Dict[str, float]:
    """
    Get KB costs broken down by service

    Returns:
        Dictionary mapping service name to cost
    """
    response = cost_explorer.get_cost_and_usage(
        TimePeriod={
            'Start': start_date.strftime('%Y-%m-%d'),
            'End': end_date.strftime('%Y-%m-%d')
        },
        Granularity='MONTHLY',
        Filter={
            'And': [
                {
                    'Tags': {
                        'Key': 'CDKEnvironment',
                        'Values': [env_name]
                    }
                },
                {
                    'Dimensions': {
                        'Key': 'SERVICE',
                        'Values': [
                            'Amazon OpenSearch Service',
                            'Amazon Redshift',
                            'Amazon RDS',
                            'Amazon S3',
                            'AWS Lambda',
                        ]
                    }
                }
            ]
        },
        Metrics=['UnblendedCost'],
        GroupBy=[
            {
                'Type': 'DIMENSION',
                'Key': 'SERVICE'
            }
        ]
    )

    costs = {}
    for result in response['ResultsByTime']:
        for group in result['Groups']:
            service = group['Keys'][0]
            cost = float(group['Metrics']['UnblendedCost']['Amount'])
            costs[service] = costs.get(service, 0) + cost

    return costs


def get_kb_cost_forecast(days: int = 30) -> float:
    """
    Get cost forecast for next N days
    """
    today = datetime.now()
    future = today + timedelta(days=days)

    response = cost_explorer.get_cost_forecast(
        TimePeriod={
            'Start': today.strftime('%Y-%m-%d'),
            'End': future.strftime('%Y-%m-%d')
        },
        Metric='UNBLENDED_COST',
        Granularity='MONTHLY'
    )

    return float(response['Total']['Amount'])
```

---

## Cost Monitoring & Optimization Strategy

### 1. Cost Tagging Strategy

**CDK Tag Policy**:
```typescript
// Apply tags to all KB-related resources
Tags.of(kbConstruct).add('Component', 'KnowledgeBase');
Tags.of(kbConstruct).add('KBType', 'S3Vectors'); // or 'Redshift', 'Aurora'
Tags.of(kbConstruct).add('BotId', botId);
Tags.of(kbConstruct).add('Environment', envName);
Tags.of(kbConstruct).add('CostCenter', 'RAG');
```

### 2. CloudWatch Cost Alarms

```typescript
// Create alarm for monthly KB costs
const costAlarm = new cloudwatch.Alarm(this, 'KBCostAlarm', {
  metric: new cloudwatch.Metric({
    namespace: 'AWS/Billing',
    metricName: 'EstimatedCharges',
    dimensions: {
      ServiceName: 'Amazon OpenSearch Service', // or Redshift, Aurora
    },
    statistic: 'Maximum',
    period: cdk.Duration.hours(6),
  }),
  threshold: 1000, // $1000/month threshold
  evaluationPeriods: 1,
  comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
  alarmDescription: 'Alert when KB costs exceed $1000/month',
});
```

### 3. Cost Optimization Recommendations

**Automated Recommendations**:
1. **Detect under-utilized OpenSearch collections** → Suggest S3 Vectors
2. **Detect 24/7 Redshift clusters** → Suggest Aurora for frequent queries
3. **Detect replica-enabled dev environments** → Suggest disabling replicas
4. **Monitor OCU scaling patterns** → Suggest right-sizing

---

## Implementation Roadmap

### Phase 1: Cost Calculator Backend (Week 1)
- [ ] Create `cost_calculator.py` service module
- [ ] Implement cost estimation functions for all 4 KB types
- [ ] Add API endpoints (`/cost/estimate`, `/cost/compare`)
- [ ] Write unit tests for cost calculations
- [ ] Validate pricing against AWS docs

### Phase 2: Cost Calculator Frontend (Week 2)
- [ ] Create `CostCalculator.tsx` component
- [ ] Design interactive cost comparison UI
- [ ] Add cost calculator to KB creation flow
- [ ] Add help text explaining cost factors
- [ ] Test responsive design

### Phase 3: Cost Monitoring Integration (Week 3)
- [ ] Implement AWS Cost Explorer integration
- [ ] Create cost monitoring dashboard
- [ ] Add CloudWatch cost alarms
- [ ] Implement cost anomaly detection
- [ ] Create cost reports (weekly/monthly emails)

### Phase 4: Cost Optimization Engine (Week 4)
- [ ] Implement automated cost analysis
- [ ] Generate optimization recommendations
- [ ] Create migration tools (OpenSearch → Aurora/S3)
- [ ] Add cost forecasting
- [ ] Implement budget alerts

### Phase 5: Documentation & Training (Week 5)
- [ ] Create cost management user guide
- [ ] Document cost optimization best practices
- [ ] Create video tutorials
- [ ] Add inline help and tooltips
- [ ] Conduct user training sessions

---

## Success Metrics

### Cost Reduction Targets
- [ ] 50-70% cost reduction for typical workloads
- [ ] 90%+ cost reduction for low-volume workloads (S3 Vectors)
- [ ] < 5% cost increase for high-performance workloads

### User Experience Metrics
- [ ] Cost calculator usage: >80% of new KB creations
- [ ] Cost-related support tickets: <5% of total
- [ ] User satisfaction with cost transparency: >4.5/5

### Technical Metrics
- [ ] Cost estimation accuracy: ±10% of actual costs
- [ ] API response time: <200ms for cost calculations
- [ ] Cost monitoring data lag: <24 hours

---

## References

- [AWS Pricing Calculator](https://calculator.aws/)
- [OpenSearch Serverless Pricing](https://aws.amazon.com/opensearch-service/pricing/)
- [S3 Vectors Pricing](https://aws.amazon.com/s3/pricing/)
- [Redshift Serverless Pricing](https://aws.amazon.com/redshift/pricing/)
- [Aurora Pricing](https://aws.amazon.com/rds/aurora/pricing/)
- [AWS Cost Explorer Documentation](https://docs.aws.amazon.com/cost-management/latest/userguide/ce-what-is.html)

---

**Plan Prepared By**: Development Team
**Next Steps**: Phase 1 implementation (Cost Calculator Backend)
