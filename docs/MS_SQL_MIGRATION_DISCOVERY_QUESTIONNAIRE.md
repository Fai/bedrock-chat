# MS SQL Database Migration - Customer Discovery Questionnaire

## Purpose
This questionnaire will help us assess the scope, complexity, and requirements for migrating your MS SQL Server database to AWS and integrating it with Bedrock Chat for AI-powered querying.

---

## Section 1: Database Information

### 1.1 Database Version & Edition
- [ ] MS SQL Server Version: ________________ (e.g., 2019, 2022)
- [ ] Edition:
  - [ ] Express
  - [ ] Standard
  - [ ] Enterprise
  - [ ] Azure SQL Database
- [ ] Service Pack/Cumulative Update Level: ________________

### 1.2 Database Size & Complexity
- [ ] Total Database Size: ________ GB/TB
- [ ] Number of Databases: ________
- [ ] Number of Tables: ________
- [ ] Largest Table Size: ________ GB
- [ ] Largest Table Row Count: ________
- [ ] Number of Views: ________
- [ ] Number of Stored Procedures: ________
- [ ] Number of Functions (Scalar/Table-valued): ________
- [ ] Number of Triggers: ________

### 1.3 Data Types Usage
Please indicate if your database uses any of the following:
- [ ] XML columns
- [ ] JSON data (via varchar/nvarchar)
- [ ] FILESTREAM/FILETABLE
- [ ] CLR assemblies
- [ ] Full-Text Search indexes
- [ ] Spatial data types (geography/geometry)
- [ ] HierarchyID
- [ ] Large Objects (LOB):
  - [ ] varbinary(max)
  - [ ] varchar(max)
  - [ ] nvarchar(max)
  - [ ] text/ntext (deprecated)

### 1.4 Character Sets & Collation
- [ ] Database Collation: ________________
- [ ] Mixed collations across columns?
  - [ ] Yes
  - [ ] No
- [ ] Special character requirements (Arabic, Chinese, etc.): ________________

---

## Section 2: Network & Connectivity

### 2.1 Current Infrastructure
- [ ] MS SQL Server Location:
  - [ ] On-premises data center
  - [ ] Co-location facility
  - [ ] Cloud (specify): ________________

- [ ] Server IP Address/Hostname: ________________
- [ ] MS SQL Port (default 1433): ________
- [ ] Firewall in place?
  - [ ] Yes
  - [ ] No

### 2.2 Network Connectivity Options
Which connectivity method is preferred for migration?

- [ ] **Site-to-Site VPN**
  - Customer VPN device model: ________________
  - Supports IPSec? [ ] Yes [ ] No
  - Available bandwidth: ________ Mbps
  - Estimated cost: Free with AWS (data transfer charges apply)

- [ ] **AWS Direct Connect**
  - Existing DX connection? [ ] Yes [ ] No
  - Connection speed: [ ] 1 Gbps [ ] 10 Gbps [ ] 100 Gbps
  - Estimated setup time: 2-4 weeks
  - Estimated cost: $0.30/hour (1 Gbps port) + data transfer

- [ ] **Public Internet (with TLS encryption)**
  - Available bandwidth: ________ Mbps
  - Static IP available? [ ] Yes [ ] No
  - Note: Requires strong firewall rules and encryption

- [ ] **AWS Snowball (for very large databases)**
  - For databases >10 TB with limited bandwidth
  - Estimated cost: $300/job + shipping
  - Estimated time: 1-2 weeks for device delivery

### 2.3 Network Bandwidth Assessment
- [ ] Available bandwidth during business hours: ________ Mbps
- [ ] Available bandwidth during off-hours: ________ Mbps
- [ ] Network latency to AWS region (if known): ________ ms
- [ ] Is network QoS configured? [ ] Yes [ ] No

**Estimated Migration Time** (based on 1 Gbps connection):
- 100 GB database: ~15-30 minutes
- 500 GB database: ~1-2 hours
- 1 TB database: ~2-4 hours
- 5 TB database: ~10-20 hours
- 10 TB database: ~20-40 hours

---

## Section 3: Security & Compliance

### 3.1 Data Classification
Does your database contain:
- [ ] Personally Identifiable Information (PII)
- [ ] Payment Card Information (PCI)
- [ ] Protected Health Information (PHI/HIPAA)
- [ ] Financial data requiring SOX compliance
- [ ] Government classified data
- [ ] Export-controlled data (ITAR/EAR)
- [ ] None of the above

### 3.2 Encryption Requirements
- [ ] Data must be encrypted at rest?
  - [ ] Yes (AWS KMS will be used)
  - [ ] No

- [ ] Data must be encrypted in transit?
  - [ ] Yes (TLS 1.2+ enforced)
  - [ ] No

- [ ] Column-level encryption currently in use?
  - [ ] Yes (please specify columns): ________________
  - [ ] No

### 3.3 Access Control
- [ ] Current authentication method:
  - [ ] SQL Server Authentication
  - [ ] Windows Authentication
  - [ ] Azure AD Authentication
  - [ ] Mixed Mode

- [ ] Number of database users: ________
- [ ] Row-level security (RLS) in use? [ ] Yes [ ] No
- [ ] Dynamic data masking in use? [ ] Yes [ ] No

### 3.4 Compliance & Audit
- [ ] Audit logging required? [ ] Yes [ ] No
- [ ] Data retention policy: ________ days/months/years
- [ ] Geographic data residency requirements: ________________
- [ ] Compliance frameworks (select all that apply):
  - [ ] GDPR
  - [ ] HIPAA
  - [ ] PCI DSS
  - [ ] SOC 2
  - [ ] ISO 27001
  - [ ] None

---

## Section 4: Business Requirements

### 4.1 Migration Strategy
- [ ] **Preferred migration approach:**
  - [ ] **One-time migration** (historical data snapshot)
    - Lower cost, simpler implementation
    - Data frozen at migration time
    - Recommended for: Archival data, reporting databases

  - [ ] **Continuous replication** (near real-time sync)
    - Higher cost (DMS instance running 24/7)
    - Data stays synchronized with source
    - Recommended for: Active operational databases
    - Note: Source database must support Change Data Capture (CDC)

### 4.2 Downtime & Cutover
- [ ] Maximum acceptable downtime: ________ hours/minutes
- [ ] Preferred migration window:
  - [ ] Weekday off-hours (specify): ________________
  - [ ] Weekend
  - [ ] No preference

- [ ] Cutover strategy:
  - [ ] Direct cutover (source DB retired)
  - [ ] Parallel run period (both systems active)
  - [ ] Gradual migration (table by table)

### 4.3 Post-Migration Requirements
- [ ] Source database lifecycle:
  - [ ] Decommission immediately after migration
  - [ ] Keep as archive for ________ months
  - [ ] Keep operational (bidirectional sync needed)

- [ ] Data refresh frequency (if continuous replication):
  - [ ] Real-time (< 1 minute lag)
  - [ ] Near real-time (< 15 minutes)
  - [ ] Hourly
  - [ ] Daily
  - [ ] On-demand

---

## Section 5: Use Case & Query Patterns

### 5.1 Business Objective
What will users ask the AI chatbot? (examples):
- [ ] Customer order history queries
  - _Example: "Show me all orders from customer ABC in Q1 2024"_
- [ ] Product inventory lookups
  - _Example: "What's the current stock level for product XYZ?"_
- [ ] Sales analytics
  - _Example: "What were our top-selling products last month?"_
- [ ] Financial reporting
  - _Example: "Calculate total revenue by region for 2024"_
- [ ] Other: ________________________________________________

### 5.2 Query Complexity
- [ ] Simple lookups (single table, primary key)
- [ ] Moderate joins (2-3 tables)
- [ ] Complex analytics (5+ tables, aggregations, subqueries)
- [ ] Time-series analysis
- [ ] Geospatial queries

### 5.3 Expected Usage
- [ ] Number of concurrent users: ________
- [ ] Queries per day (estimated): ________
- [ ] Peak usage hours: ________________
- [ ] Average query response time expectation: ________ seconds

---

## Section 6: Technical Contacts & Credentials

### 6.1 Customer Team
- [ ] Database Administrator Name: ________________
  - Email: ________________
  - Phone: ________________

- [ ] Network Administrator Name: ________________
  - Email: ________________
  - Phone: ________________

- [ ] Security/Compliance Officer Name: ________________
  - Email: ________________
  - Phone: ________________

### 6.2 Database Access (to be provided securely)
**Note: Credentials will be stored in AWS Secrets Manager**

- [ ] Read-only SQL user account (for migration):
  - Username: ________________
  - Password: [To be provided via secure channel]
  - Required permissions:
    - `db_datareader` on all databases
    - `VIEW DEFINITION` for schema extraction
    - `VIEW DATABASE STATE` for monitoring

### 6.3 Firewall Access
- [ ] AWS IP ranges to whitelist (will be provided after VPN setup)
- [ ] Customer firewall change approval process: ________________
- [ ] Estimated time for firewall changes: ________ days

---

## Section 7: Budget & Timeline

### 7.1 Budget Constraints
- [ ] Monthly AWS budget allocation: $________
- [ ] One-time migration budget: $________
- [ ] Budget approval authority: ________________

### 7.2 Project Timeline
- [ ] Desired go-live date: ________________
- [ ] Critical business milestones: ________________
- [ ] Blackout dates (no changes allowed): ________________

---

## Section 8: Risk Assessment

### 8.1 Known Challenges
Please describe any known issues:
- [ ] Database performance issues: ________________________________________________
- [ ] Data quality problems: ________________________________________________
- [ ] Legacy code dependencies: ________________________________________________
- [ ] Vendor-specific features: ________________________________________________

### 8.2 Dependencies
- [ ] Other systems reading from this database: ________________
- [ ] Scheduled jobs/ETL processes: ________________
- [ ] External API integrations: ________________

---

## Next Steps

After completing this questionnaire:

1. **Technical Review Call** (1-2 hours)
   - Review responses with AWS solutions architect
   - Clarify technical requirements
   - Discuss migration strategy

2. **Network Connectivity Test** (1 week)
   - Set up VPN/Direct Connect
   - Validate database access
   - Perform bandwidth test

3. **Proof of Concept** (1-2 weeks)
   - Migrate sample dataset (1-2 tables)
   - Test Bedrock SQL KB integration
   - Validate query performance

4. **Formal Project Kickoff**
   - Finalize implementation timeline
   - Sign Statement of Work (SOW)
   - Begin full migration

---

## Submission Instructions

Please complete this questionnaire and return to:
- **Email**: [your-email@company.com]
- **Secure File Upload**: [link to secure portal]
- **Meeting**: Schedule technical review call

**Estimated completion time**: 30-45 minutes

---

*Last Updated: 2025-10-02*
*Version: 1.0*
