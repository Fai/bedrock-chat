# SQL Knowledge Base User Guide

## Overview

The SQL Knowledge Base feature allows you to connect your Amazon Redshift Serverless database to Bedrock Chat, enabling natural language queries over your structured data. This guide will help you set up and use SQL-type Knowledge Bases with your custom bots.

## Prerequisites

Before creating a SQL Knowledge Base, ensure you have:

1. **Amazon Redshift Serverless Workgroup**
   - Active Redshift Serverless workgroup
   - Workgroup ARN documented
   - Database with tables/views ready for querying

2. **Database Table Requirements**
   - Table or view with at least three columns:
     - **ID column**: Unique identifier (primary key)
     - **Content column**: Main text content for semantic search
     - **Metadata column**: Additional structured data (JSON format recommended)

3. **AWS Secrets Manager Secret**
   - Secret containing Redshift database credentials
   - Secret ARN documented
   - Credentials with read access to target table/view

4. **IAM Permissions**
   - Bedrock Knowledge Base IAM role configured (handled by administrator)
   - Role has permissions for:
     - Redshift Data API access
     - Secrets Manager read access

## Step-by-Step Setup

### Step 1: Prepare Your Redshift Database

1. **Create or identify a table/view** with your data:

```sql
-- Example table structure
CREATE TABLE product_catalog (
    id VARCHAR(50) PRIMARY KEY,
    content TEXT,
    metadata JSON
);

-- Example data
INSERT INTO product_catalog VALUES
(
    'PROD-001',
    'Premium Wireless Headphones - Noise cancelling, 30-hour battery life, comfortable over-ear design',
    '{"category": "Electronics", "price": 299.99, "stock": 45, "rating": 4.5}'
);
```

2. **Verify data access**:

```sql
SELECT id, content, metadata
FROM product_catalog
LIMIT 10;
```

### Step 2: Create AWS Secrets Manager Secret

1. Navigate to AWS Secrets Manager in the AWS Console
2. Create a new secret with Redshift credentials:

```json
{
  "username": "your_redshift_user",
  "password": "your_password",
  "host": "your-workgroup.123456789012.us-east-1.redshift-serverless.amazonaws.com",
  "port": 5439,
  "dbname": "your_database"
}
```

3. Note the Secret ARN (e.g., `arn:aws:secretsmanager:us-east-1:123456789012:secret:my-redshift-creds-AbCdEf`)

### Step 3: Gather Required Information

You'll need the following information:

| Field | Example | Where to Find |
|-------|---------|---------------|
| Workgroup Name | `my-redshift-workgroup` | Redshift Console > Serverless dashboard |
| Workgroup ARN | `arn:aws:redshift-serverless:us-east-1:123456789012:workgroup/my-workgroup` | Redshift Console > Workgroup details |
| Database Name | `my_database` | Your database name |
| Table Name | `product_catalog` | Your table/view name |
| Secret ARN | `arn:aws:secretsmanager:us-east-1:123456789012:secret:my-creds` | Secrets Manager Console |
| ID Column | `id` | Your table's primary key column |
| Content Column | `content` | Your table's main text column |
| Metadata Column | `metadata` | Your table's metadata column |

### Step 4: Create Custom Bot with SQL Knowledge Base

1. **Navigate to Bot Creation**
   - Log in to Bedrock Chat
   - Click "Create New Bot"

2. **Configure Bot Basic Information**
   - Enter bot name: e.g., "Product Catalog Assistant"
   - Add description: e.g., "Query our product catalog using natural language"
   - Add instructions for the bot's behavior

3. **Select Knowledge Base Type**
   - Choose "SQL Knowledge Base" (instead of "Vector")
   - This enables the Redshift connection form

4. **Configure Redshift Connection**
   - Fill in all the information gathered in Step 3:
     - Workgroup Name
     - Workgroup ARN
     - Database Name
     - Table/View Name
     - Secret ARN

5. **Configure Field Mapping**
   - Map your table columns to Bedrock KB fields:
     - **ID Column**: Your primary key column (e.g., `id`)
     - **Content Column**: Your main text column (e.g., `content`)
     - **Metadata Column**: Your metadata column (e.g., `metadata`)

6. **Configure Search Parameters** (optional)
   - Max Results: Number of results to return (default: 10)
   - Search Type: Hybrid (default) or Semantic

7. **Create Bot**
   - Click "Create Bot"
   - Wait for Knowledge Base creation and ingestion
   - Status will update from "Creating" → "Ingesting Data" → "Ready"

### Step 5: Monitor Knowledge Base Status

After creating the bot:

1. **Check Status Badge**
   - Creating: KB is being provisioned
   - Ingesting Data: Data is being indexed
   - Ready: KB is ready for queries
   - Failed: Check error message and retry

2. **Ingestion typically takes**:
   - Small tables (< 1,000 rows): 2-5 minutes
   - Medium tables (1,000-10,000 rows): 5-15 minutes
   - Large tables (> 10,000 rows): 15-60 minutes

## Using Your SQL Knowledge Base Bot

### Querying with Natural Language

Once your bot is ready, you can query your database using natural language:

**Example Queries:**

```
User: "Show me all products in the Electronics category with a rating above 4.0"

Bot: Based on your product catalog, I found 12 electronics products with ratings above 4.0:
1. Premium Wireless Headphones - Rating: 4.5, Price: $299.99
2. Smart Watch Pro - Rating: 4.7, Price: $399.99
...

[SQL Query Used: SELECT * FROM product_catalog WHERE metadata->>'category' = 'Electronics' AND (metadata->>'rating')::float > 4.0]
```

```
User: "What's the total inventory value by category?"

Bot: Here's the inventory value breakdown by category:
- Electronics: $125,450.75
- Home & Garden: $89,320.50
- Clothing: $67,890.25
...
```

### Understanding Query Results

Your bot responses will include:

1. **Natural Language Answer**: Human-readable summary of results
2. **SQL Query** (expandable): The actual SQL query generated by Bedrock
3. **Structured Data Table**: Formatted results with columns and rows
4. **Citations**: Source data from your database

### Best Practices for Queries

✅ **DO:**
- Use natural, conversational language
- Ask specific questions about your data
- Request aggregations, filters, and summaries
- Reference column names from your table

❌ **DON'T:**
- Try to modify data (INSERT, UPDATE, DELETE) - read-only access only
- Expect real-time updates - data is indexed periodically
- Query tables not configured in the KB

## Troubleshooting

### Common Issues

#### Issue: Bot Status Shows "Failed"

**Possible Causes:**
- Invalid Redshift workgroup ARN
- Incorrect database credentials in Secrets Manager
- Network connectivity issues
- Missing IAM permissions

**Solutions:**
1. Verify all ARNs are correct (no typos)
2. Test Redshift credentials using Query Editor
3. Check Bedrock KB role has required permissions
4. Contact your administrator

#### Issue: "No results returned from query"

**Possible Causes:**
- Query doesn't match any data
- Field mapping is incorrect
- Table is empty

**Solutions:**
1. Try broader queries
2. Verify field mapping in bot settings
3. Check table has data: `SELECT COUNT(*) FROM your_table`

#### Issue: Slow Query Performance

**Possible Causes:**
- Large table without indexes
- Complex queries
- Redshift workgroup scaled down

**Solutions:**
1. Add indexes on frequently queried columns
2. Increase Redshift workgroup RPU capacity
3. Simplify queries
4. Use materialized views for complex aggregations

#### Issue: Ingestion Job Stuck

**Possible Causes:**
- Very large table
- Redshift workgroup paused

**Solutions:**
1. Wait longer (large tables can take 30-60 minutes)
2. Check Redshift workgroup is active
3. Contact administrator if stuck > 2 hours

## Security Considerations

### Data Access
- Bots respect row-level security (same as your Cognito user permissions)
- Users can only query data they have access to
- All queries are logged for audit purposes

### Credentials
- Database credentials are stored securely in AWS Secrets Manager
- Credentials are never exposed in chat responses
- Only the Bedrock KB IAM role can access credentials

### Query Limitations
- **Read-only**: Only SELECT queries are allowed
- **No DDL**: Cannot create/modify table schemas
- **No DML**: Cannot INSERT/UPDATE/DELETE data

## Advanced Configuration

### Optimizing Content for Semantic Search

The **Content Column** is used for semantic search. For best results:

```sql
-- Good: Rich, descriptive text
UPDATE product_catalog
SET content = name || ' - ' || description || '. Features: ' || features || '. Use case: ' || use_case;

-- Poor: Just IDs or codes
-- content = 'PROD-001'
```

### Using Metadata Effectively

Store structured attributes in the **Metadata Column** as JSON:

```json
{
  "category": "Electronics",
  "brand": "TechCo",
  "price": 299.99,
  "stock": 45,
  "rating": 4.5,
  "tags": ["wireless", "premium", "noise-cancelling"],
  "last_updated": "2025-01-15"
}
```

### Creating Optimized Views

For better performance and security:

```sql
-- Create a view with pre-joined data
CREATE VIEW product_catalog_view AS
SELECT
    p.id,
    p.name || ' - ' || p.description AS content,
    json_build_object(
        'category', c.name,
        'price', p.price,
        'stock', p.stock,
        'rating', r.avg_rating
    )::text AS metadata
FROM products p
LEFT JOIN categories c ON p.category_id = c.id
LEFT JOIN ratings r ON p.id = r.product_id
WHERE p.is_active = true;
```

## FAQs

**Q: Can I connect multiple tables to one Knowledge Base?**
A: Yes, create a VIEW that joins your tables, then point the KB to that view.

**Q: How often is data refreshed?**
A: Data is indexed when you create the KB. To refresh, you'll need to trigger a new ingestion job (contact administrator).

**Q: What's the maximum table size?**
A: Bedrock KB can handle tables with millions of rows, but ingestion time increases with size. For very large tables (>10M rows), consider using a filtered view.

**Q: Can I use multiple databases?**
A: One KB connects to one table/view in one database. Create multiple bots with different KBs for multiple databases.

**Q: What SQL syntax is supported?**
A: Redshift SQL syntax (PostgreSQL-compatible). Complex features like window functions and CTEs are supported.

**Q: Can I export query results?**
A: Results are displayed in the chat interface. You can copy the generated SQL query and run it in Redshift Query Editor for export.

## Getting Help

- **Technical Issues**: Contact your Bedrock Chat administrator
- **Database Questions**: Contact your data team
- **AWS Support**: For Bedrock/Redshift issues, contact AWS Support

## Next Steps

- Explore example queries with your data
- Share the bot with your team
- Create multiple bots for different use cases
- Provide feedback to improve the feature

---

**Related Documentation:**
- [SQL KB Developer Guide](./SQL_KB_DEVELOPER_GUIDE.md)
- [MS SQL Migration Guide](./MS_SQL_MIGRATION_DISCOVERY_QUESTIONNAIRE.md)
- [Bedrock Chat Administrator Guide](./ADMINISTRATOR.md)
