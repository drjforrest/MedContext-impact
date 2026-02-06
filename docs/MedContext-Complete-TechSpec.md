# MedContext: Complete Technical Architecture for Medical Image Verification

**Author:** Dr. Jamie Forrest  
**Date:** January 14, 2026  
**Status:** Complete Pre-Development Planning  
**Database Stack:** PostgreSQL (primary) + Neo4j (post-functional prototype)  
**Total Estimated Development Timeline:** 6 weeks (+ 2 weeks post-launch hardening)

---

## Executive Summary

MedContext is a seven-module system designed to combat medical image misinformation by:

1. **Ingesting** medical images from multiple channels
2. **Analyzing** images using MedGemma 1.5 4B for clinical understanding
3. **Tracing** image distribution across the web and closed messaging platforms
4. **Extracting** health claims associated with each image
5. **Building** provenance chains showing genealogy and consensus patterns
6. **Visualizing** distribution patterns for end users
7. **Providing** contextual authenticity assessments and recommendations

This document provides complete technical specification for a 6-week MVP development cycle.

---

## Complete Module Dependency Graph

```
User Submission
    ↓
[1] IMAGE INGESTION MODULE
    ├─ Telegram Bot Handler
    ├─ Browser Extension Handler
    ├─ Web Form Handler
    └─ PostgreSQL Storage
    ↓
[2] MEDGEMMA ANALYSIS MODULE (Parallel)
    ├─ Image Understanding
    ├─ Clinical Description
    ├─ Context Assessment
    └─ PostgreSQL Storage
    ↓
[3] REVERSE IMAGE SEARCH MODULE (Parallel)
    ├─ TinEye Integration
    ├─ Google Vision Integration
    ├─ Custom Crawlers
    └─ PostgreSQL Storage
    ↓
[4] SEMANTIC ANALYSIS MODULE
    ├─ Claim Extraction
    ├─ Claim Classification
    ├─ MedGemma Context Analysis
    ├─ Semantic Clustering
    └─ PostgreSQL Storage
    ↓
[5] PROVENANCE & BLOCKCHAIN MODULE
    ├─ Provenance Chain Building
    ├─ Consensus Pattern Detection
    ├─ Genealogical Tree Construction
    └─ PostgreSQL Storage + IPFS
    ↓
[6] CONSENSUS VISUALIZATION MODULE
    ├─ Distribution Chart Generation
    ├─ Timeline Creation
    ├─ Confidence Scoring
    └─ JSON Output
    ↓
[7] DECISION SUPPORT MODULE
    ├─ Contextual Authenticity Assessment
    ├─ Recommendation Generation
    ├─ Risk Stratification
    └─ User-Facing Output
    ↓
User Response
```

---

## Module 1: Image Ingestion Module

### Purpose

Receive medical images from multiple channels, validate, normalize, and persist to database.

### Responsibilities

- **Telegram Bot Handler:** Parse Telegram Bot API webhook events
- **Browser Extension Handler:** Receive images from Chrome/Firefox extension
- **Web Form Handler:** Simple web upload interface
- **Image Validation:** Verify format, size, and content
- **Image Normalization:** Standardize DICOM handling, compression, orientation
- **Storage:** Persist to PostgreSQL with metadata

### Edge AI Triage (Hardening)

- **Privacy-Preserving Triage:** For Telegram/mobile ingestion, explore 4-bit quantized MedGemma 1.5 4B (GGUF/CoreML) on-device to classify urgency before sending to the backend.
- **Why:** Reduce latency and protect sensitive content while still routing complex cases to the full cloud workflow.

### Database Models

```python
# image_ingestion/models.py
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, UUID
from sqlalchemy.orm import relationship
from datetime import datetime

class ImageSubmission(Base):
    __tablename__ = "image_submissions"

    id: UUID = Column(UUID, primary_key=True)
    source_channel: str = Column(String)  # 'telegram', 'extension', 'web'
    user_id: str = Column(String, index=True)
    image_hash: str = Column(String, unique=True, index=True)  # SHA256
    image_path: str = Column(String)  # IPFS path
    file_size: int = Column(Integer)
    mime_type: str = Column(String)
    image_format: str = Column(String)  # jpg, png, dicom
    width: int = Column(Integer)
    height: int = Column(Integer)
    orientation_corrected: bool = Column(Boolean, default=False)
    metadata_extracted: bool = Column(Boolean, default=False)
    submitted_at: DateTime = Column(DateTime, default=datetime.utcnow, index=True)
    created_at: DateTime = Column(DateTime, default=datetime.utcnow)
    updated_at: DateTime = Column(DateTime, onupdate=datetime.utcnow)

    submissions_context = relationship("SubmissionContext", back_populates="image")
    analyses = relationship("MedGemmaAnalysis", back_populates="image")


class SubmissionContext(Base):
    __tablename__ = "submission_contexts"

    id: UUID = Column(UUID, primary_key=True)
    image_id: UUID = Column(UUID, ForeignKey("image_submissions.id"))
    surrounding_text: str = Column(Text)
    claimed_condition: str = Column(String)
    claimed_origin: str = Column(String)
    source_url: str = Column(String, nullable=True)
    source_telegram_chat: str = Column(String, nullable=True)
    language_code: str = Column(String, default="en")
    created_at: DateTime = Column(DateTime, default=datetime.utcnow)

    image = relationship("ImageSubmission", back_populates="submissions_context")

# Schema Evolution Note:
# - Pre-migration: source_whatsapp_group column existed
# - Transition period: Both source_whatsapp_group and source_telegram_chat columns exist
# - Final state: Only source_telegram_chat column remains (source_whatsapp_group dropped)
```

### Migration Guide: WhatsApp to Telegram

**Context:** The system originally supported WhatsApp ingestion via the `source_whatsapp_group` column in the `submission_contexts` table and the `/api/v1/ingest/whatsapp` endpoint. This section documents the migration to Telegram-based ingestion using `source_telegram_chat` and `/api/v1/ingest/telegram`.

#### 1. Database Migration Strategy

**Objective:** Rename `source_whatsapp_group` to `source_telegram_chat` in the `submission_contexts` table while preserving existing data and maintaining backward compatibility during the transition period.

**Pre-Migration Checklist:**

1. **Create Full Database Backup:**

   ```bash
   # Create timestamped backup
   pg_dump -h localhost -U medcontext_user -d medcontext > \
     backup_medcontext_$(date +%Y%m%d_%H%M%S).sql

   # Verify backup integrity
   pg_restore --list backup_medcontext_*.sql
   ```

2. **Check Existing Data:**

   ```sql
   -- Count records with WhatsApp source data
   SELECT COUNT(*) FROM submission_contexts WHERE source_whatsapp_group IS NOT NULL;

   -- Sample existing data
   SELECT id, source_whatsapp_group, created_at
   FROM submission_contexts
   WHERE source_whatsapp_group IS NOT NULL
   LIMIT 10;
   ```

**Migration Steps (Alembic):**

```python
# alembic/versions/xxxx_migrate_whatsapp_to_telegram.py
"""Migrate WhatsApp source to Telegram source

Revision ID: xxxx
Revises: 8b1b3f0a7c3a
Create Date: 2026-01-31 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'xxxx'
down_revision = '8b1b3f0a7c3a'
branch_labels = None
depends_on = None

def upgrade():
    # Step 1: Add new column (nullable, no default)
    op.add_column('submission_contexts',
                  sa.Column('source_telegram_chat', sa.String(), nullable=True))

    # Step 2: Copy data from old column to new column
    op.execute("""
        UPDATE submission_contexts
        SET source_telegram_chat = source_whatsapp_group
        WHERE source_whatsapp_group IS NOT NULL
    """)

    # Step 3: Drop old column (after compatibility period)
    # COMMENTED OUT FOR COMPATIBILITY PERIOD - Uncomment after 30 days
    # op.drop_column('submission_contexts', 'source_whatsapp_group')

    # Follow-up migration: After 30-day compatibility window, run:
    # alembic/versions/xxxx_drop_whatsapp_column.py to complete the migration

def downgrade():
    # Reverse migration: restore WhatsApp column
    op.add_column('submission_contexts',
                  sa.Column('source_whatsapp_group', sa.String(), nullable=True))

    # Copy data back
    op.execute("""
        UPDATE submission_contexts
        SET source_whatsapp_group = source_telegram_chat
        WHERE source_telegram_chat IS NOT NULL
    """)

    # Drop Telegram column
    op.drop_column('submission_contexts', 'source_telegram_chat')
```

**Manual Migration (SQL - for emergency rollout):**

```sql
-- Phase 1: Add new column
ALTER TABLE submission_contexts
ADD COLUMN source_telegram_chat VARCHAR;

-- Phase 2: Migrate existing data
UPDATE submission_contexts
SET source_telegram_chat = source_whatsapp_group
WHERE source_whatsapp_group IS NOT NULL;

-- Phase 3: Verify migration
SELECT
    COUNT(*) as total_rows,
    COUNT(source_whatsapp_group) as whatsapp_count,
    COUNT(source_telegram_chat) as telegram_count,
    COUNT(CASE WHEN source_whatsapp_group = source_telegram_chat THEN 1 END) as matched_count
FROM submission_contexts;

-- Phase 4: Drop old column (WAIT 30 DAYS - see compatibility period)
-- ALTER TABLE submission_contexts DROP COLUMN source_whatsapp_group;

-- Follow-up migration: After 30-day compatibility window, run the automated
-- Alembic migration to drop the source_whatsapp_group column
```

**Column Handling Notes:**

- **Nullable:** Both columns are nullable (`nullable=True`) to support images submitted without source chat context (e.g., web uploads, browser extension)
- **No Default Value:** No default value is set; applications must explicitly provide chat identifiers when available
- **Index Consideration:** If queries frequently filter by source chat, add an index:
  ```sql
  CREATE INDEX idx_submission_contexts_telegram_chat
  ON submission_contexts(source_telegram_chat)
  WHERE source_telegram_chat IS NOT NULL;
  ```

#### 2. API Transition and Versioning Strategy

**Objective:** Transition from `/api/v1/ingest/whatsapp` to `/api/v1/ingest/telegram` while maintaining backward compatibility for 30 days.

**Transition Timeline:**

| Phase                     | Duration  | Actions                                                          |
| ------------------------- | --------- | ---------------------------------------------------------------- |
| **Phase 1: Dual Support** | Days 1-30 | Both endpoints active; WhatsApp endpoint deprecated with warning |
| **Phase 2: Hard Cutover** | Day 31+   | WhatsApp endpoint returns 410 Gone; Telegram endpoint only       |

**Implementation Approach:**

```python
# src/app/api/v1/endpoints/ingestion.py
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
import warnings
import logging

router = APIRouter(prefix="/api/v1/ingest", tags=["ingestion"])
logger = logging.getLogger(__name__)

# Configuration
WHATSAPP_ENDPOINT_CUTOFF_DATE = "2026-03-02"  # 30 days from migration
COMPATIBILITY_MODE_ENABLED = True  # Toggle for emergency rollback

@router.post("/telegram", status_code=201)
async def handle_telegram_webhook(
    request: TelegramWebhookRequest,
    db: Session = Depends(get_db)
):
    """
    Primary endpoint for Telegram Bot API webhook.

    **Replaces:** /api/v1/ingest/whatsapp (deprecated 2026-01-31)

    Stores source chat identifier in submission_contexts.source_telegram_chat.

    **Security Notes:**
    - Telegram uses cloud storage (not E2E encrypted by default)
    - Consider PHI/PII handling implications
    - Avoid storing identifiable medical data in bot messages
    - Use explicit consent, data minimization, and anonymization practices
    """
    # Parse Telegram update
    message = request.message
    chat_id = str(message.chat.id)

    # Store with new schema
    context = SubmissionContext(
        image_id=image_id,
        surrounding_text=message.caption or "",
        source_telegram_chat=chat_id,  # NEW FIELD
        language_code=message.from_user.language_code or "en"
    )
    db.add(context)
    db.commit()

    return {"status": "success", "image_id": image_id}


@router.post("/whatsapp",
             status_code=201,
             deprecated=True,
             description="⚠️ DEPRECATED: Use /api/v1/ingest/telegram instead. "
                         f"This endpoint will be removed on {WHATSAPP_ENDPOINT_CUTOFF_DATE}.")
async def handle_whatsapp_webhook_deprecated(
    request: TelegramWebhookRequest,  # Schema is identical
    db: Session = Depends(get_db),
    x_compatibility_mode: bool = Header(default=False)
):
    """
    **DEPRECATED:** Legacy WhatsApp ingestion endpoint.

    **Migration Notice:**
    - This endpoint is deprecated as of 2026-01-31
    - All requests are transparently forwarded to Telegram handler
    - Data is stored in source_telegram_chat column (WhatsApp column removed)
    - Removal date: {WHATSAPP_ENDPOINT_CUTOFF_DATE}
    - Migrate clients to /api/v1/ingest/telegram

    **Compatibility Mode:**
    - During transition period, this endpoint forwards to Telegram handler
    - After cutover date, returns HTTP 410 Gone
    """
    # Check if past cutover date
    from datetime import datetime
                    "message": f"The /whatsapp endpoint was removed on {WHATSAPP_ENDPOINT_CUTOFF_DATE}",
        if not COMPATIBILITY_MODE_ENABLED:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail={
                    "error": "endpoint_removed",
                    "message": "The /whatsapp endpoint was removed on {WHATSAPP_ENDPOINT_CUTOFF_DATE}",
                    "migration_guide": "Use /api/v1/ingest/telegram instead",
                    "breaking_change": True
                }
            )

    # Log deprecation warning
    logger.warning(
        f"Deprecated endpoint /whatsapp called. "
        f"Client should migrate to /telegram. "
        f"Request ID: {request.message.message_id}"
    )

    # Forward to Telegram handler (transparent proxy)
    return await handle_telegram_webhook(request, db)
```

**Versioning Alternative (API v2 approach):**

If stricter API versioning is required:

```python
# Option: Create v2 API with Telegram-only support
router_v2 = APIRouter(prefix="/api/v2/ingest", tags=["ingestion-v2"])

@router_v2.post("/telegram")
async def handle_telegram_webhook_v2(...):
    # Clean implementation without legacy compatibility
    pass

# Keep v1 with WhatsApp deprecation warnings
# Users must explicitly upgrade to v2 for clean migration
```

**Client Migration Checklist:**

- [ ] Update all Telegram Bot webhook URLs from `/whatsapp` to `/telegram`
- [ ] Update internal service clients to use new endpoint
- [ ] Update documentation and API client libraries
- [ ] Monitor deprecated endpoint usage via logging/metrics
- [ ] Notify external API consumers 14 days before cutover

#### 3. Rollback Procedures

**Objective:** Safely revert to WhatsApp-based schema and API endpoints if critical issues arise during migration.

**Scenario 1: Rollback During Compatibility Period (Days 1-30)**

If issues are detected while both columns exist:

1. **Re-enable WhatsApp Column Writes:**

   ```python
   # Temporarily patch ingestion handler
   context = SubmissionContext(
       image_id=image_id,
       source_whatsapp_group=chat_id,  # Write to BOTH columns
       source_telegram_chat=chat_id,
       ...
   )
   ```

2. **Copy Recent Data Back to WhatsApp Column:**

   ```sql
   -- Copy any new Telegram-only records to WhatsApp column
   UPDATE submission_contexts
   SET source_whatsapp_group = source_telegram_chat
   WHERE source_telegram_chat IS NOT NULL
     AND source_whatsapp_group IS NULL
     AND created_at >= '2026-01-31';  -- Migration start date
   ```

3. **Re-enable WhatsApp Endpoint (Remove Deprecation):**

   ```python
   @router.post("/whatsapp", deprecated=False)
   async def handle_whatsapp_webhook(...):
       # Remove deprecation warning, restore as primary endpoint
       pass
   ```

4. **Restore Database Backup (Nuclear Option):**

   ```bash
   # Stop application
   systemctl stop medcontext-api

   # Drop current database
   psql -U postgres -c "DROP DATABASE medcontext;"

   # Restore from backup
   psql -U postgres -c "CREATE DATABASE medcontext OWNER medcontext_user;"
   pg_restore -h localhost -U medcontext_user -d medcontext \
     backup_medcontext_20260131_120000.sql

   # Restart application
   systemctl start medcontext-api
   ```

**Scenario 2: Rollback After WhatsApp Column Removed (Day 31+)**

If critical regression discovered after old column dropped:

1. **Restore Database from Backup:**

   ```bash
   # Use most recent backup before column drop
   pg_restore -h localhost -U medcontext_user -d medcontext \
     --clean --if-exists \
     backup_medcontext_20260301_000000.sql
   ```

2. **Run Downgrade Migration:**

   ```bash
   # Use Alembic downgrade
   alembic downgrade -1  # Go back one revision

   # Verify schema
   psql -U medcontext_user -d medcontext -c "\d submission_contexts"
   ```

3. **Revert API Code:**

   ```bash
   # Roll back to pre-migration commit
   git revert <migration-commit-hash>
   git push origin main

   # Redeploy previous version
   docker-compose down
   docker-compose up -d --build
   ```

4. **Update Configuration:**
   ```bash
   # Disable Telegram endpoint, re-enable WhatsApp
   # Update environment variables
   ENABLE_WHATSAPP_INGESTION=true
   ENABLE_TELEGRAM_INGESTION=false
   ```

**Rollback Validation Checklist:**

- [ ] Verify `source_whatsapp_group` column exists and contains data
- [ ] Confirm `/whatsapp` endpoint responds successfully
- [ ] Test end-to-end ingestion flow with WhatsApp webhook
- [ ] Check logs for errors related to missing columns
- [ ] Validate data integrity (no missing or corrupted records)
- [ ] Notify stakeholders of rollback and revised timeline

**Post-Rollback Actions:**

1. **Root Cause Analysis:** Document why migration failed
2. **Fix Issues:** Address technical problems before retry
3. **Update Timeline:** Revise migration schedule based on findings
4. **Communication:** Inform users/clients of revised plan

**Monitoring During Migration:**

- **Database Metrics:** Track query latency on `submission_contexts` table
- **API Metrics:** Monitor error rates on both `/whatsapp` and `/telegram` endpoints
- **Data Validation:** Daily comparison of record counts between columns
- **Alerting:** Set up alerts for HTTP 500 errors on ingestion endpoints

**References:**

- **Affected Table:** `submission_contexts`
- **Affected Columns:** `source_whatsapp_group` (deprecated) → `source_telegram_chat` (current)
- **Affected Endpoints:** `/api/v1/ingest/whatsapp` (deprecated) → `/api/v1/ingest/telegram` (current)
- **Migration Script:** `alembic/versions/xxxx_migrate_whatsapp_to_telegram.py`
- **Schema Symbol:** `source_telegram_chat` (defined at line 140 of this document)

### API Endpoints

````python
# image_ingestion/api.py
from fastapi import APIRouter, UploadFile, File, Form

router = APIRouter(prefix="/api/v1/ingest", tags=["ingestion"])

@router.post("/telegram")
async def handle_telegram_webhook(request: TelegramWebhookRequest, db: Session = Depends(get_db)):
    """
    Receive image via Telegram Bot API webhook.

    **Telegram Update Payload Structure:**
    Telegram sends Update objects as JSON with nested message/photo arrays:

    ```json
    {
      "update_id": 123456789,
      "message": {
        "message_id": 12345,
        "from": {
          "id": 987654321,
          "is_bot": false,
          "first_name": "John",
          "username": "johndoe"
        },
        "chat": {
          "id": 987654321,
          "first_name": "John",
          "username": "johndoe",
          "type": "private"
        },
        "date": 1706745600,
        "photo": [
          {
            "file_id": "AgACAgIAAxkBAAIBY2Z...",
            "file_unique_id": "AQAD2XkxG-Qv9Hhy",
            "file_size": 1234,
            "width": 90,
            "height": 90
          },
          {
            "file_id": "AgACAgIAAxkBAAIBY2Z...",
            "file_unique_id": "AQAD2XkxG-Qv9Hhz",
            "file_size": 12345,
            "width": 320,
            "height": 320
          },
          {
            "file_id": "AgACAgIAAxkBAAIBY2Z...",
            "file_unique_id": "AQAD2XkxG-Qv9Hh-",
            "file_size": 123456,
            "width": 1280,
            "height": 1280
          }
        ],
        "caption": "MRI showing brain tumor in frontal lobe"
      }
    }
    ```

    **Note:** The `photo` array contains multiple resolutions (thumbnail → full-size).
    Always use the last element (highest resolution) for analysis.

    **Authentication & Webhook Setup:**

    1. **Bot Token:** Obtain from @BotFather on Telegram
       - Set as `TELEGRAM_BOT_TOKEN` environment variable (maps to `settings.telegram_bot_token`)
       - Used for all API calls: `https://api.telegram.org/bot<TOKEN>/method`

    2. **Webhook Registration:**
       ```bash
       curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
         -H "Content-Type: application/json" \
         -d '{
           "url": "https://your-domain.com/api/v1/monitoring/telegram",
           "secret_token": "your-secret-token-here",
           "allowed_updates": ["message", "callback_query"]
         }'
       ```

    3. **Secret Token Verification (RECOMMENDED):**
       - Generate a random secret token (32+ chars)
       - Set as `TELEGRAM_WEBHOOK_SECRET` environment variable (maps to `settings.telegram_webhook_secret`)
       - Telegram includes it in `X-Telegram-Bot-Api-Secret-Token` header
       - Verify on every webhook request:
       ```python
       secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
       if secret_token != settings.telegram_webhook_secret:
           raise HTTPException(status_code=403, detail="Invalid secret token")
       ```

    **Image Handling:**

    Images are NOT directly included in webhook payloads. Instead:

    1. **Extract `file_id`** from the photo array (use last/largest):
       ```python
       photo = update["message"]["photo"][-1]
       file_id = photo["file_id"]
       ```

    2. **Call `getFile` API** to get download path:
       ```bash
       GET https://api.telegram.org/bot<TOKEN>/getFile?file_id=<FILE_ID>
       ```
       Response:
       ```json
       {
         "ok": true,
         "result": {
           "file_id": "AgACAgIAAxkBAAIBY2Z...",
           "file_unique_id": "AQAD2XkxG-Qv9Hh-",
           "file_size": 123456,
           "file_path": "photos/file_123.jpg"
         }
       }
       ```

    3. **Download the file** using `file_path`:
       ```bash
       GET https://api.telegram.org/file/bot<TOKEN>/<file_path>
       ```
       Store the binary content for analysis.

    **Rate Limits & Retries:**

    - **Global Limit:** 30 requests/second per bot (all methods combined)
    - **Per-Chat Limit:** 1 message/second in groups, 20 messages/minute to same user
    - **File Downloads:** No explicit limit, but respect 429 responses
    - **Webhook Timeout:** Telegram expects response within 60 seconds

    **Retry Strategy:**
    - On 429 (Too Many Requests), check `Retry-After` header
    - Exponential backoff: 1s, 2s, 4s, 8s, 16s (max 5 retries)
    - On 5xx errors: retry up to 3 times with 2s delay
    - On network timeout: single retry after 5s

    **Webhook Verification Guidelines:**

    ✅ **Always Verify:**
    - Secret token in `X-Telegram-Bot-Api-Secret-Token` header
    - Request method is POST
    - Content-Type is application/json
    - Payload structure matches Update schema

    ⚠️ **Security Considerations:**
    - Use HTTPS only (required by Telegram)
    - Validate `update_id` is monotonically increasing (detect replay attacks)
    - Implement request logging for audit trails
    - Rate limit by `user_id` to prevent abuse (10 requests/hour per user)

    📋 **Error Responses:**
    - Return 200 OK even on validation errors (prevents Telegram retries)
    - Log errors internally for monitoring
    - Use 5xx only for unrecoverable server errors
    """
    pass

@router.post("/extension")
async def handle_extension_submission(
    file: UploadFile = File(...),
    context: str = Form(...),
    db: Session = Depends(get_db)
) -> SubmissionResponse:
    """Receive image via browser extension"""
    pass

@router.post("/web")
async def handle_web_upload(
    file: UploadFile = File(...),
    context: str = Form(...),
    db: Session = Depends(get_db)
) -> SubmissionResponse:
    """Simple web form upload"""
    pass
````

### Development Timeline

- **Week 1:** Telegram and web API setup, basic validation
- **Week 2:** Browser extension integration, image normalization
- **Week 3:** IPFS integration
- **Week 4:** Error handling and edge cases

### Success Criteria

- Accept images from all 3 channels
- Handle DICOM files correctly
- <2 second ingestion latency
- Proper error handling for oversized/invalid files

---

## Module 2: MedGemma Analysis Module

### Purpose

Use MedGemma 1.5 4B to understand medical images and their clinical context.

### Database Models

```python
# medgemma_analysis/models.py
class MedGemmaAnalysis(Base):
    __tablename__ = "medgemma_analyses"

    id: UUID = Column(UUID, primary_key=True)
    image_id: UUID = Column(UUID, ForeignKey("image_submissions.id"))

    # Image understanding
    modality: str = Column(String)
    anatomical_region: str = Column(String)
    key_findings: str = Column(Text)
    clinical_impression: str = Column(Text)
    findings_confidence: float = Column(Float)  # 0.0-1.0

    # Image quality assessment
    image_quality_score: float = Column(Float)  # 0.0-1.0
    quality_issues: str = Column(Text, nullable=True)

    # Context analysis
    claimed_condition_analyzed: bool = Column(Boolean, default=False)
    claimed_vs_actual_match: float = Column(Float, nullable=True)  # 0.0-1.0
    match_explanation: str = Column(Text, nullable=True)
    contextual_inconsistencies: str = Column(Text, nullable=True)

    # Metadata
    model_version: str = Column(String)  # "medgemma-1.5-4b"
    inference_time_ms: int = Column(Integer)
    tokens_used: int = Column(Integer)
    analyzed_at: DateTime = Column(DateTime, default=datetime.utcnow, index=True)
    created_at: DateTime = Column(DateTime, default=datetime.utcnow)

    image = relationship("ImageSubmission", back_populates="analyses")
```

### API Endpoints

```python
# medgemma_analysis/api.py
router = APIRouter(prefix="/api/v1/analyze", tags=["analysis"])

@router.post("/image/{image_id}")
async def analyze_image(
    image_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> AnalysisResponse:
    """Trigger MedGemma analysis"""
    pass

@router.get("/analysis/{analysis_id}")
async def get_analysis(analysis_id: UUID, db: Session = Depends(get_db)):
    """Retrieve completed analysis"""
    pass
```

### Development Timeline

- **Week 1:** Local MedGemma setup via Hugging Face or Vertex AI
- **Week 2:** Prompt engineering and structured output parsing
- **Week 3:** Context matching analysis
- **Week 4:** Error handling and optimization

### Success Criteria

- Accurate modality/anatomy identification
- Structured JSON output parsing
- Context matching >85% accuracy
- <10 seconds inference time per image

---

## Module 3: Reverse Image Search Module

### Purpose

Find all instances of a medical image across the web to build distribution patterns.

### Database Models

```python
# reverse_search/models.py
class ImageInstance(Base):
    __tablename__ = "image_instances"

    id: UUID = Column(UUID, primary_key=True)
    source_image_id: UUID = Column(UUID, ForeignKey("image_submissions.id"))

    # Instance details
    instance_url: str = Column(String, index=True)
    source_type: str = Column(String)  # 'web', 'telegram', 'forum', 'social_media'
    domain: str = Column(String, index=True)

    # Image matching
    similarity_score: float = Column(Float)  # 0.0-1.0
    match_type: str = Column(String)  # 'exact', 'cropped', 'resized', 'modified'
    modification_detected: str = Column(Text, nullable=True)

    # Instance context
    surrounding_text: str = Column(Text)
    claims_with_image: str = Column(Text)
    source_credibility: str = Column(String)  # 'high', 'medium', 'low', 'unknown'

    # Timeline
    first_seen: DateTime = Column(DateTime, index=True)
    last_seen: DateTime = Column(DateTime)
    occurrence_count: int = Column(Integer, default=1)

    # Metadata
    search_source: str = Column(String)  # 'tineye', 'google_vision', 'custom_crawler'
    discovered_at: DateTime = Column(DateTime, default=datetime.utcnow)
    created_at: DateTime = Column(DateTime, default=datetime.utcnow)

    source_image = relationship("ImageSubmission")
    semantic_cluster = relationship("SemanticCluster", back_populates="instances")
```

### API Endpoints

```python
# reverse_search/api.py
router = APIRouter(prefix="/api/v1/reverse-search", tags=["reverse-search"])

@router.post("/search/{image_id}")
async def trigger_reverse_search(
    image_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> SearchJobResponse:
    """Start parallel reverse image searches"""
    pass

@router.get("/results/{image_id}")
async def get_search_results(
    image_id: UUID,
    db: Session = Depends(get_db)
) -> SearchResultsResponse:
    """Get reverse search results"""
    pass
```

### Development Timeline

- **Week 1:** TinEye API integration
- **Week 2:** Google Vision API, parallel execution
- **Week 3:** Telegram crawler, context extraction
- **Week 4:** Deduplication, credibility scoring

### Success Criteria

- Find >50 instances per search
- <15 second search time
- > 80% unique URL deduplication accuracy
- Proper domain credibility assessment

---

## Module 4: Semantic Analysis Module

### Purpose

Extract claims from each image instance, classify them, and group similar claims.

### Database Models

```python
# semantic_analysis/models.py
class HealthClaim(Base):
    __tablename__ = "health_claims"

    id: UUID = Column(UUID, primary_key=True)
    image_instance_id: UUID = Column(UUID, ForeignKey("image_instances.id"))

    # Claim content
    claim_text: str = Column(Text)
    claim_type: str = Column(String)  # 'vaccine', 'treatment', 'disease', etc.
    condition_mentioned: str = Column(String)
    action_implied: str = Column(String, nullable=True)

    # Claim analysis
    medical_accuracy: float = Column(Float)  # 0.0-1.0
    accuracy_assessment: str = Column(Text)
    evidence_quality: str = Column(String)  # 'high', 'medium', 'low', 'none'

    # Image-claim alignment
    image_finding_match: float = Column(Float)  # 0.0-1.0
    temporal_consistency: bool = Column(Boolean, nullable=True)
    geographic_plausibility: bool = Column(Boolean, nullable=True)

    # Source context
    source_type: str = Column(String)  # 'educational', 'commercial', 'activist', etc.
    source_credibility_score: float = Column(Float)  # 0.0-1.0

    # Metadata
    extracted_by: str = Column(String)  # 'medgemma', 'nlp_pipeline', 'manual'
    confidence: float = Column(Float)
    created_at: DateTime = Column(DateTime, default=datetime.utcnow)

    image_instance = relationship("ImageInstance")
    cluster = relationship("SemanticCluster", back_populates="claims")


class SemanticCluster(Base):
    __tablename__ = "semantic_clusters"

    id: UUID = Column(UUID, primary_key=True)
    source_image_id: UUID = Column(UUID, ForeignKey("image_submissions.id"))

    # Cluster characterization
    cluster_name: str = Column(String)
    cluster_description: str = Column(Text)
    dominant_claim: str = Column(Text)

    # Statistics
    instance_count: int = Column(Integer)
    claim_count: int = Column(Integer)
    average_accuracy_score: float = Column(Float)
    average_credibility_score: float = Column(Float)

    # Temporal info
    first_appearance: DateTime = Column(DateTime)
    emergence_pattern: str = Column(String)  # 'sudden', 'gradual', 'cyclical'
    growth_rate: float = Column(Float)  # claims per week

    claims = relationship("HealthClaim", back_populates="cluster")
    instances = relationship("ImageInstance", back_populates="semantic_cluster")
```

### API Endpoints

```python
# semantic_analysis/api.py
router = APIRouter(prefix="/api/v1/semantic", tags=["semantic"])

@router.post("/analyze/{image_id}")
async def analyze_claims(
    image_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> SemanticAnalysisResponse:
    """Extract and cluster health claims"""
    pass

@router.get("/clusters/{image_id}")
async def get_semantic_clusters(
    image_id: UUID,
    db: Session = Depends(get_db)
) -> ClustersResponse:
    """Get semantic clusters"""
    pass
```

### Development Timeline

- **Week 2:** Claim extraction with regex + NLP
- **Week 3:** MedGemma analysis, semantic clustering
- **Week 4:** Clustering optimization

### Success Criteria

- Extract 3-8 claims per image instance
- Semantic clustering >0.80 coherence
- Proper medical terminology handling

---

## Module 5: Provenance & Blockchain Module

### Purpose

Build provenance chains showing image genealogy and detect consensus patterns over time, acting as a clinical audit trail with a tamper-proof history trusted by health authorities.

### Database Models

```python
# provenance/models.py
class ProvenanceChain(Base):
    __tablename__ = "provenance_chains"

    id: UUID = Column(UUID, primary_key=True)
    source_image_id: UUID = Column(UUID, ForeignKey("image_submissions.id"))

    # Chain characterization
    root_source: str = Column(String, nullable=True)
    root_source_type: str = Column(String, nullable=True)
    root_date: DateTime = Column(DateTime, nullable=True)

    # Consensus tracking
    dominant_consensus: str = Column(String)
    consensus_confidence: float = Column(Float)  # 0.0-1.0
    consensus_stability: str = Column(String)  # 'stable', 'emerging', 'shifting', 'disputed'

    # Divergence tracking
    has_divergent_uses: bool = Column(Boolean, default=False)
    divergent_cluster_count: int = Column(Integer, default=0)
    largest_divergence_size: int = Column(Integer, default=0)

    # Genealogy
    total_observations: int = Column(Integer, default=0)
    unique_instances: int = Column(Integer, default=0)
    time_span_days: int = Column(Integer, nullable=True)
    growth_rate: float = Column(Float, nullable=True)

    last_updated: DateTime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at: DateTime = Column(DateTime, default=datetime.utcnow)

    source_image = relationship("ImageSubmission")
    blocks = relationship("ProvenanceBlock", back_populates="chain")


class ProvenanceBlock(Base):
    __tablename__ = "provenance_blocks"

    id: UUID = Column(UUID, primary_key=True)
    chain_id: UUID = Column(UUID, ForeignKey("provenance_chains.id"))

    # Block sequence
    block_number: int = Column(Integer)
    previous_block_hash: str = Column(String, nullable=True)

    # Block content
    observation_type: str = Column(String)  # 'image_submission', 'instance_found', 'claim_added'
    observation_data: str = Column(Text)  # JSON

    # Cluster state
    consensus_at_block: str = Column(String)
    cluster_count_at_block: int = Column(Integer)
    instance_count_at_block: int = Column(Integer)

    # Metadata
    block_hash: str = Column(String, unique=True)  # SHA256
    timestamp: DateTime = Column(DateTime, default=datetime.utcnow)
    created_at: DateTime = Column(DateTime, default=datetime.utcnow)

    chain = relationship("ProvenanceChain", back_populates="blocks")


class ConsensusPattern(Base):
    __tablename__ = "consensus_patterns"

    id: UUID = Column(UUID, primary_key=True)
    provenance_chain_id: UUID = Column(UUID, ForeignKey("provenance_chains.id"))

    # Pattern data
    pattern_snapshot_date: DateTime = Column(DateTime)

    # Distribution percentages
    educational_percentage: float = Column(Float)  # 0-100
    unclear_percentage: float = Column(Float)
    misinformation_percentage: float = Column(Float)
    other_percentage: float = Column(Float)

    # Top cluster
    top_cluster_id: UUID = Column(UUID, ForeignKey("semantic_clusters.id"), nullable=True)
    top_cluster_name: str = Column(String)
    top_cluster_percentage: float = Column(Float)

    instances_sampled: int = Column(Integer)
    created_at: DateTime = Column(DateTime, default=datetime.utcnow)
```

### API Endpoints

```python
# provenance/api.py
router = APIRouter(prefix="/api/v1/provenance", tags=["provenance"])

@router.post("/build-chain/{image_id}")
async def build_provenance_chain(
    image_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> ProvenanceChainResponse:
    """Build complete provenance chain"""
    pass

@router.get("/chain/{image_id}")
async def get_provenance_chain(
    image_id: UUID,
    db: Session = Depends(get_db)
) -> ProvenanceChainDetailResponse:
    """Get full provenance chain"""
    pass

@router.get("/genealogy/{image_id}")
async def get_genealogical_tree(
    image_id: UUID,
    db: Session = Depends(get_db)
) -> GenealogicalTreeResponse:
    """Get genealogical tree visualization"""
    pass
```

### Development Timeline

- **Week 3:** PostgreSQL models for chains, blocks
- **Week 4:** Blockchain hashing, chain building
- **Week 5:** Genealogical timeline generation

### Success Criteria

- Blockchain integrity verification 100%
- Timeline generation <500ms
- Proper parent-child linking
- Accurate consensus calculation

---

## Module 6: Consensus Visualization Module

### Purpose

Generate visualizations showing image usage distribution and consensus patterns.

### Database Models

```python
# visualization/models.py
class VisualizationData(Base):
    __tablename__ = "visualization_data"

    id: UUID = Column(UUID, primary_key=True)
    image_id: UUID = Column(UUID, ForeignKey("image_submissions.id"))

    # Distribution data
    distribution_data: str = Column(Text)  # JSON with percentages
    timeline_data: str = Column(Text)  # JSON with temporal data
    cluster_sizes: str = Column(Text)  # JSON with cluster metadata

    # Confidence metrics
    overall_confidence_score: float = Column(Float)  # 0.0-1.0
    confidence_by_use: str = Column(Text)  # JSON breakdown

    # Visualization metadata
    generated_at: DateTime = Column(DateTime, default=datetime.utcnow)
    data_freshness: int = Column(Integer)  # hours since last update
    sample_size: int = Column(Integer)  # number of instances analyzed

    created_at: DateTime = Column(DateTime, default=datetime.utcnow)
    updated_at: DateTime = Column(DateTime, onupdate=datetime.utcnow)
```

### API Endpoints & Response Format

```python
# visualization/api.py
router = APIRouter(prefix="/api/v1/visualization", tags=["visualization"])

@router.get("/distribution/{image_id}")
async def get_distribution_chart(
    image_id: UUID,
    db: Session = Depends(get_db)
) -> DistributionChartResponse:
    """Get distribution visualization data"""
    # Returns:
    # {
    #   "image_id": "uuid",
    #   "distribution": {
    #     "educational": 45.2,
    #     "unclear": 32.1,
    #     "misinformation": 18.5,
    #     "other": 4.2
    #   },
    #   "confidence": 0.87,
    #   "instances_analyzed": 127,
    #   "top_claims": [
    #     {"claim": "...", "percentage": 28.3, "accuracy": 0.92}
    #   ]
    # }
    pass

@router.get("/timeline/{image_id}")
async def get_timeline(
    image_id: UUID,
    db: Session = Depends(get_db)
) -> TimelineResponse:
    """Get temporal evolution of image usage"""
    # Returns timeline of emergence, growth, and distribution changes
    pass

@router.get("/confidence/{image_id}")
async def get_confidence_metrics(
    image_id: UUID,
    db: Session = Depends(get_db)
) -> ConfidenceResponse:
    """Get confidence scoring details"""
    pass
```

### Response Schema Examples

```json
{
  "image_id": "550e8400-e29b-41d4-a716-446655440000",
  "distribution": {
    "educational": {
      "percentage": 45.2,
      "instance_count": 57,
      "primary_contexts": [
        "medical textbook",
        "educational website",
        "medical journal"
      ]
    },
    "unclear": {
      "percentage": 32.1,
      "instance_count": 41,
      "contexts": ["forum discussion", "blog post", "social media"]
    },
    "misinformation": {
      "percentage": 18.5,
      "instance_count": 24,
      "inaccuracies": [
        "Claim: COVID vaccine injury - Actual: unrelated condition",
        "Claim: Treatment for disease X - Actual: different modality"
      ]
    },
    "other": {
      "percentage": 4.2,
      "instance_count": 5
    }
  },
  "temporal_data": {
    "first_appearance": "2024-03-15",
    "peak_activity": "2024-08-22",
    "emergence_pattern": "gradual",
    "growth_rate_per_week": 2.3
  },
  "confidence_metrics": {
    "overall_confidence": 0.87,
    "confidence_by_use": {
      "educational": 0.94,
      "misinformation": 0.78,
      "unclear": 0.65
    },
    "basis": "127 instances analyzed across 43 unique domains"
  }
}
```

### Development Timeline

- **Week 4:** Distribution chart generation
- **Week 5:** Timeline creation, confidence calculation
- **Week 6:** UI integration, testing

### Success Criteria

- Accurate percentage calculations
- <300ms chart generation time
- Clear visual differentiation between use types
- Mobile-responsive design

---

## Module 7: Agentic Orchestrator & Decision Support Module

### Purpose

Coordinate agentic tool use and produce contextual authenticity assessments and recommendations for healthcare providers and the public.

### Agentic Orchestration Logic

MedGemma acts as a clinical investigator that dynamically selects tools based on the image context and its own findings. This pre-development spec describes intended behavior only (no file-level implementation references). The planned implementation includes:

- Deterministic orchestration for predictable, auditable flows
- Agentic workflows (e.g., graph-based routing) for adaptive tool selection

The flow emphasizes self-correction: anomalous clinical findings trigger deeper forensics and reverse search before synthesis.

### Contextual Authenticity Metric

Define a MedContext Integrity Score as a weighted average of:

- **Plausibility** (MedGemma)
- **Genealogy Consistency** (provenance/blockchain)
- **Source Reputation** (reverse search)

**Calculation formula (default):**

- `Integrity Score = (w1 × Plausibility) + (w2 × Genealogy_Consistency) + (w3 × Source_Reputation)`
- Default weights: `w1=0.5`, `w2=0.3`, `w3=0.2` (configurable per deployment or risk profile).
- Integrity Score is the **primary decision-support composite** used for risk labeling and downstream decisions.

**Score definitions (all normalized to 0.0-1.0):**

- **Plausibility (P):** Computed from MedGemma outputs by combining normalized plausibility/confidence signals.
  - Inputs: MedGemma finding confidence `F` (0-1), contradiction score `C` (0-1; higher = more contradictions), optional model self-rated plausibility `MP` (0-1).
  - Normalization: clamp each input to [0, 1]; if `MP` is unavailable, renormalize weights.
  - Aggregation (default): `P = (0.60 * F) + (0.40 * (1 - C))`, or `P = (0.50 * F) + (0.30 * (1 - C)) + (0.20 * MP)` when `MP` is available.
- **Genealogy Consistency (G):** Derived from provenance chains and tamper signals.
  - Inputs: percentage of uninterrupted provenance hops `PH` (0-1), tamper flag rate `TF` (0-1; higher = worse), chronological consistency `CH` (0-1).
  - Normalization: clamp to [0, 1]; map tamper rate to positive contribution via `(1 - TF)`.
  - Aggregation (default): `G = (0.50 * PH) + (0.30 * CH) + (0.20 * (1 - TF))`.
- **Source Reputation (S):** Derived from a single default reputation signal with an explicit fallback.
  - Default source (preferred): `global_reputation_store.score` (0-1).
  - Fallback: if default source is missing, use `ImageMetadata.reputation` (0-1) when available.
  - Optional separate computation: when neither source is present, compute from DR/CQ/MH if those signals exist.
  - Optional separate computation: domain reputation `DR` (0-1), citation quality `CQ` (0-1), misinformation history `MH` (0-1; higher = worse).
  - Aggregation (default if separate): `S = (0.50 * DR) + (0.30 * CQ) + (0.20 * (1 - MH))`.

**Relationship to Decision Support Engine metrics:**

- Integrity Score combines **plausibility + genealogy + reputation** into a single composite risk signal.
- Decision Support Engine metrics (authenticity, accuracy, credibility) remain **component-level diagnostics**:
  - **Authenticity** overlaps most with genealogy consistency but is reported separately for forensic transparency.
  - **Accuracy** aligns with plausibility but remains a standalone evidence trail from MedGemma outputs.
  - **Credibility** aligns with source reputation; Integrity Score uses it as an input rather than replacing it.

**Calculation steps (placeholder if signals missing):**

- Clamp each input metric to [0, 1] before weighting.
- If a sub-signal is unavailable, renormalize that component's sub-weights across available inputs.

**Missing data handling:**

- If a component is unavailable, compute a weighted score from available components and renormalize weights.
- Always attach an `incomplete_evidence` flag and a confidence interval or uncertainty score when any component is missing.

**Interpretation bands and actions:**

- **> 0.80 (High):** UI label "High Integrity"; default action "Proceed" or "Low Risk".
- **0.50–0.80 (Medium):** UI label "Moderate Integrity"; action "Review Evidence".
- **< 0.50 (Low):** UI label "Low Integrity"; action "Escalate" or "Flag for Expert Review".

**Consensus Scoring Architecture (crosswalk):**

The consensus scoring framework aligns with the Integrity Score by treating each layer as a normalized 0-1 component and aggregating with configurable weights.

- **Layer 1: Medical Consensus** → maps to **Plausibility (P)**.
  - Inputs: MedGemma analysis, anatomical verification, pathology consistency, medical plausibility.
  - Output: normalized medical consensus score `MC` (0-1).
- **Layer 2: Contextual Consensus** → contributes to **Genealogy Consistency (G)**.
  - Inputs: claim type distribution, semantic clustering, platform analysis, geo/linguistic patterns.
  - Output: normalized contextual continuity score `CCx` (0-1).
- **Layer 3: Misinformation Consensus** → maps to **Source Reputation (S)** and credibility risk.
  - Inputs: fact-check alignment, expert verdicts, claim family prevalence, risk severity.
  - Output: normalized misinformation risk score `MR` (0-1), inverted when used as reputation.
- **Layer 4: Temporal Consensus** → contributes to **Genealogy Consistency (G)**.
  - Inputs: usage evolution, narrative emergence timeline, geographic spread, trend stability.
  - Output: normalized temporal continuity score `TC` (0-1).

**Normalization note:** Each layer score is clamped to 0–1 before weighting; risk-aligned layers (e.g., misinformation) are inverted when used as reputation.

**Ensemble consensus score (default weights):**

- `ConsensusScore = (0.40 * MC) + (0.30 * CCx) + (0.20 * (1 - MR)) + (0.10 * TC)`
- Weights are configurable and should be aligned with Integrity Score weights in deployment settings.

**Relationship to Integrity Score:**

- Integrity Score remains the primary composite (P + G + S) for decision support and UI labeling.
- ConsensusScore (MC, CCx, MR, TC) is a supporting diagnostic used for explanation, triage, and analyst context.
- ConsensusScore may optionally feed into Genealogy Consistency via a configurable mapping, or remain parallel for explanatory UI.

**Configurable policy (example):**

- `G = α * provenance_metrics + β * ConsensusScore` (with `α + β = 1`, defaults `α=1.0`, `β=0.0` to keep scores independent).

### Database Models

```python
# decision_support/models.py
class ContextualIntegrityAssessment(Base):
    __tablename__ = "contextual_integrity_assessments"

    id: UUID = Column(UUID, primary_key=True)
    image_id: UUID = Column(UUID, ForeignKey("image_submissions.id"))

    # Assessment components
    image_authenticity_score: float = Column(Float)  # 0.0-1.0
    image_authenticity_reasoning: str = Column(Text)

    claim_accuracy_score: float = Column(Float)  # 0.0-1.0
    claim_accuracy_reasoning: str = Column(Text)

    source_credibility_score: float = Column(Float)  # 0.0-1.0
    source_credibility_reasoning: str = Column(Text)

    consensus_assessment: str = Column(String)  # 'strong_educational', 'mixed', 'predominantly_inaccurate'

    # Risk stratification
    risk_level: str = Column(String)  # 'low', 'medium', 'high', 'critical'
    risk_justification: str = Column(Text)

    # Recommendations
    primary_recommendation: str = Column(String)
    recommendation_details: str = Column(Text)
    target_audience: str = Column(String)  # 'clinician', 'public', 'researcher', 'journalist'

    # Metadata
    assessment_date: DateTime = Column(DateTime, default=datetime.utcnow)
    created_at: DateTime = Column(DateTime, default=datetime.utcnow)


class DecisionSupportOutput(Base):
    __tablename__ = "decision_support_outputs"

    id: UUID = Column(UUID, primary_key=True)
    assessment_id: UUID = Column(UUID, ForeignKey("contextual_integrity_assessments.id"))
    image_id: UUID = Column(UUID, ForeignKey("image_submissions.id"))

    # User-facing summary
    summary_for_clinician: str = Column(Text)
    summary_for_public: str = Column(Text)
    summary_for_researcher: str = Column(Text)
    summary_for_journalist: str = Column(Text)

    # Key findings to highlight
    key_findings: str = Column(Text)  # JSON array

    # Related resources
    related_resources: str = Column(Text)  # JSON array with links

    # Actionable guidance
    clinical_guidance: str = Column(Text, nullable=True)
    public_health_message: str = Column(Text, nullable=True)
    research_implications: str = Column(Text, nullable=True)
    media_guidance: str = Column(Text, nullable=True)

    created_at: DateTime = Column(DateTime, default=datetime.utcnow)
```

### Decision Support Logic

```python
# decision_support/assessment.py
class DecisionSupportEngine:
    """Generates contextual authenticity assessments and recommendations"""

    def __init__(self, db: Session):
        self.db = db

    def assess_image(self, image_id: UUID) -> ContextualIntegrityAssessment:
        """
        Comprehensive assessment combining all modules:
        1. Context alignment (MedGemma + provenance + reverse search)
        2. Claim accuracy (semantic analysis + fact-checking)
        3. Source credibility (domain reputation + instance tracking)
        4. Consensus (provenance analysis)
        """
        image = self.db.query(ImageSubmission).filter_by(id=image_id).first()

        # Get all data from previous modules
        medgemma = self.db.query(MedGemmaAnalysis).filter_by(image_id=image_id).first()
        instances = self.db.query(ImageInstance).filter_by(source_image_id=image_id).all()
        claims = self.db.query(HealthClaim).all()  # Associated with instances
        consensus = self.db.query(ConsensusPattern).join(
            ProvenanceChain
        ).filter(ProvenanceChain.source_image_id == image_id).first()

        # 1. Image Authenticity Assessment
        authenticity_score = self._assess_authenticity(medgemma, instances)

        # 2. Claim Accuracy Assessment
        claim_accuracy = self._assess_claim_accuracy(claims)

        # 3. Source Credibility Assessment
        source_credibility = self._assess_source_credibility(instances)

        # 4. Consensus Assessment
        consensus_assessment = self._assess_consensus(consensus, instances)

        # 5. Risk Stratification
        risk_level = self._stratify_risk(
            authenticity_score,
            claim_accuracy,
            source_credibility,
            consensus_assessment
        )

        # 6. Generate Recommendations
        recommendations = self._generate_recommendations(
            risk_level,
            authenticity_score,
            claim_accuracy,
            consensus_assessment
        )

        # Create and persist assessment
        assessment = ContextualIntegrityAssessment(
            image_id=image_id,
            image_authenticity_score=authenticity_score,
            claim_accuracy_score=claim_accuracy,
            source_credibility_score=source_credibility,
            consensus_assessment=consensus_assessment,
            risk_level=risk_level,
            primary_recommendation=recommendations['primary'],
            recommendation_details=recommendations['details'],
            target_audience='general'
        )

        self.db.add(assessment)
        self.db.commit()

        return assessment

    def _assess_authenticity(self, medgemma: MedGemmaAnalysis, instances: List[ImageInstance]) -> float:
        """
        Score image authenticity based on:
        - MedGemma quality assessment
        - Consistency across instances
        - Context integrity signals (future module)
        """
        if not medgemma:
            return 0.5  # Unknown

        quality_component = medgemma.image_quality_score  # 0.0-1.0
        consistency_component = self._assess_instance_consistency(instances)

        authenticity = (quality_component * 0.6) + (consistency_component * 0.4)
        return min(1.0, max(0.0, authenticity))

    def _assess_claim_accuracy(self, claims: List[HealthClaim]) -> float:
        """Average accuracy of all claims associated with image"""
        if not claims:
            return 0.5  # Unknown

        accuracies = [c.medical_accuracy for c in claims if c.medical_accuracy]
        if not accuracies:
            return 0.5

        return sum(accuracies) / len(accuracies)

    def _assess_source_credibility(self, instances: List[ImageInstance]) -> float:
        """
        Aggregate source credibility based on:
        - Domains sharing the image
        - Source type distribution
        - Reputation scores
        """
        if not instances:
            return 0.5

        credibility_scores = []
        for instance in instances:
            if instance.source_credibility == 'high':
                credibility_scores.append(0.9)
            elif instance.source_credibility == 'medium':
                credibility_scores.append(0.6)
            elif instance.source_credibility == 'low':
                credibility_scores.append(0.3)
            else:
                credibility_scores.append(0.5)

        return sum(credibility_scores) / len(credibility_scores)

    def _assess_consensus(self, consensus: ConsensusPattern, instances: List[ImageInstance]) -> str:
        """
        Categorize consensus type:
        - strong_educational: >70% educational, <10% misinformation
        - mixed: 30-70% split between categories
        - predominantly_inaccurate: >60% misinformation
        """
        if not consensus:
            return 'unknown'

        if consensus.educational_percentage > 70 and consensus.misinformation_percentage < 10:
            return 'strong_educational'
        elif consensus.misinformation_percentage > 60:
            return 'predominantly_inaccurate'
        else:
            return 'mixed'

    def _stratify_risk(
        self,
        authenticity: float,
        claim_accuracy: float,
        source_credibility: float,
        consensus: str
    ) -> str:
        """
        Risk stratification matrix:
        - low: high authenticity, high accuracy, high credibility, educational consensus
        - medium: mixed indicators
        - high: low authenticity OR low accuracy OR low credibility + inaccurate consensus
        - critical: severe context mismatch OR dangerous claims + low credibility
        """
        risk_score = 0.0

        # Authenticity component (0.3 weight)
        risk_score += (1.0 - authenticity) * 0.3

        # Accuracy component (0.3 weight)
        risk_score += (1.0 - claim_accuracy) * 0.3

        # Source credibility component (0.2 weight)
        risk_score += (1.0 - source_credibility) * 0.2

        # Consensus component (0.2 weight)
        if consensus == 'strong_educational':
            risk_score += 0.0 * 0.2
        elif consensus == 'mixed':
            risk_score += 0.5 * 0.2
        else:  # predominantly_inaccurate
            risk_score += 1.0 * 0.2

        # Map score to risk level
        if risk_score < 0.2:
            return 'low'
        elif risk_score < 0.5:
            return 'medium'
        elif risk_score < 0.8:
            return 'high'
        else:
            return 'critical'

    def _generate_recommendations(
        self,
        risk_level: str,
        authenticity: float,
        accuracy: float,
        consensus: str
    ) -> Dict[str, str]:
        """Generate context-specific recommendations"""

        recommendations = {
            'primary': '',
            'details': '',
            'clinician': '',
            'public': '',
            'researcher': '',
            'journalist': ''
        }

        # Base recommendation on risk level
        if risk_level == 'low':
            recommendations['primary'] = 'Safe for clinical and educational use'
            recommendations['details'] = (
                'This image has high authenticity, accurate associated claims, '
                'and strong educational consensus. Can be confidently used in teaching materials.'
            )

        elif risk_level == 'medium':
            recommendations['primary'] = 'Use with caution and context'
            recommendations['details'] = (
                'This image shows mixed usage patterns. While authenticity is acceptable, '
                'verify specific claims before clinical use.'
            )

        elif risk_level == 'high':
            recommendations['primary'] = 'Significant caution advised'
            recommendations['details'] = (
                'This image is associated with substantial inaccuracies or low credibility sources. '
                'Verify through authoritative sources before any use.'
            )

        else:  # critical
            recommendations['primary'] = 'Do not use'
            recommendations['details'] = (
                'This image is associated with significant risks including possible '
                'authenticity issues or dangerous medical misinformation.'
            )

        return recommendations

    def _assess_instance_consistency(self, instances: List[ImageInstance]) -> float:
        """How consistently is image used across instances?"""
        if len(instances) < 2:
            return 0.5  # Can't assess consistency with single instance

        # Check if all instances show similar claims/context
        claims_set = set()
        for instance in instances:
            if instance.claims_with_image:
                claims_set.add(instance.claims_with_image)

        # High consistency = low variance in claims
        if len(claims_set) < len(instances) * 0.3:  # <30% variance
            return 0.9
        elif len(claims_set) < len(instances) * 0.6:  # <60% variance
            return 0.6
        else:
            return 0.3
```

### API Endpoints

```python
# decision_support/api.py
router = APIRouter(prefix="/api/v1/decision-support", tags=["decision-support"])

@router.post("/assess/{image_id}")
async def assess_image(
    image_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> AssessmentResponse:
    """Generate contextual authenticity assessment"""
    engine = DecisionSupportEngine(db)
    assessment = engine.assess_image(image_id)

    return AssessmentResponse(
        assessment_id=assessment.id,
        risk_level=assessment.risk_level,
        primary_recommendation=assessment.primary_recommendation,
        authenticity_score=assessment.image_authenticity_score,
        accuracy_score=assessment.claim_accuracy_score,
        credibility_score=assessment.source_credibility_score
    )

@router.get("/recommendation/{image_id}")
async def get_recommendation(
    image_id: UUID,
    audience: str = Query("general"),  # clinician, public, researcher, journalist
    db: Session = Depends(get_db)
) -> RecommendationResponse:
    """Get tailored recommendation for specific audience"""
    # Returns audience-specific guidance
    pass

@router.get("/summary/{image_id}")
async def get_executive_summary(
    image_id: UUID,
    db: Session = Depends(get_db)
) -> SummaryResponse:
    """Get one-page summary for quick review"""
    pass
```

### Response Schema

```json
{
  "image_id": "550e8400-e29b-41d4-a716-446655440000",
  "assessment_id": "660e8400-e29b-41d4-a716-446655440000",
  "risk_level": "medium",
  "confidence": 0.85,
  "overall_assessment": "Use with caution and context",
  "detailed_findings": {
    "authenticity": {
      "score": 0.87,
      "assessment": "Image appears aligned with no signs of context mismatch",
      "basis": "Consistent across 45 instances, high quality score from MedGemma"
    },
    "accuracy": {
      "score": 0.62,
      "assessment": "Mixed accuracy in associated claims",
      "inaccuracies": [
        "COVID vaccine injury claim - No evidence in MedGemma analysis",
        "Rare disease diagnosis - Mismatches clinical presentation"
      ]
    },
    "source_credibility": {
      "score": 0.71,
      "assessment": "Moderate credibility across sources",
      "top_sources": [
        "Medical journals: 30%",
        "Health blogs: 25%",
        "Social media: 20%"
      ]
    },
    "consensus": {
      "type": "mixed",
      "distribution": {
        "educational": 45.2,
        "unclear": 32.1,
        "misinformation": 18.5,
        "other": 4.2
      }
    }
  },
  "recommendations": {
    "for_clinicians": {
      "guidance": "Can be used for teaching with appropriate context",
      "caveat": "Verify specific diagnostic claims against clinical findings"
    },
    "for_public": {
      "guidance": "Consult healthcare providers before accepting any claims about this image",
      "key_message": "This image is used for multiple purposes - get professional interpretation"
    },
    "for_researchers": {
      "guidance": "Document source carefully if using in publications",
      "consideration": "Wide usage variance suggests multiple contexts"
    },
    "for_media": {
      "guidance": "Include expert commentary if referencing this image",
      "context": "Image has contested interpretations"
    }
  },
  "next_steps": [
    "Verify specific clinical claims with radiologist",
    "Cross-reference with current medical literature",
    "Consider image context in original source"
  ]
}
```

### Development Timeline

- **Week 5:** Core assessment logic
- **Week 6:** Recommendation generation, audience personalization
- **Post-launch:** Refinement based on user feedback

### Success Criteria

- Risk stratification >90% accuracy
- Recommendations appropriate for target audience
- <1 second assessment generation time
- Clear actionable guidance

---

## Integration & Testing Framework

### End-to-End Test Cases

```python
# tests/e2e_test.py
class TestMedContextEndToEnd:
    """Integration tests across all modules"""

    def test_complete_pipeline(self, client: TestClient, db: Session):
        """Test complete image processing pipeline"""

        # 1. Submit image via web
        image_response = client.post(
            "/api/v1/ingest/web",
            files={"file": ("test.jpg", open("tests/fixtures/test_image.jpg", "rb"))},
            data={"context": "COVID vaccine injury claim"}
        )
        image_id = image_response.json()["image_id"]
        assert image_response.status_code == 200

        # 2. Verify image stored
        image = db.query(ImageSubmission).filter_by(id=image_id).first()
        assert image is not None
        assert image.source_channel == "web"

        # 3. Run MedGemma analysis (background task)
        time.sleep(5)  # Wait for background task
        analysis = db.query(MedGemmaAnalysis).filter_by(image_id=image_id).first()
        assert analysis is not None
        assert analysis.modality is not None

        # 4. Run reverse image search (background task)
        time.sleep(10)
        instances = db.query(ImageInstance).filter_by(source_image_id=image_id).all()

        # 5. Semantic analysis (background task)
        time.sleep(5)
        clusters = db.query(SemanticCluster).filter_by(source_image_id=image_id).all()
        assert len(clusters) > 0

        # 6. Build provenance (background task)
        time.sleep(5)
        chain = db.query(ProvenanceChain).filter_by(source_image_id=image_id).first()
        assert chain is not None

        # 7. Get visualization
        viz_response = client.get(f"/api/v1/visualization/distribution/{image_id}")
        assert viz_response.status_code == 200
        assert "distribution" in viz_response.json()

        # 8. Get decision support assessment
        assessment_response = client.post(f"/api/v1/decision-support/assess/{image_id}")
        assert assessment_response.status_code == 200
        assert "risk_level" in assessment_response.json()
```

### Performance Benchmarks

```python
# tests/performance_test.py
class TestPerformance:
    """Performance benchmarking"""

    def test_image_ingestion_latency(self):
        """<2 second ingestion"""
        start = time.time()
        # Submit image
        duration = time.time() - start
        assert duration < 2.0

    def test_medgemma_inference_time(self):
        """<10 seconds per image"""
        start = time.time()
        # Run analysis
        duration = time.time() - start
        assert duration < 10.0

    def test_reverse_search_time(self):
        """<15 seconds for parallel searches"""
        start = time.time()
        # Run all searches
        duration = time.time() - start
        assert duration < 15.0

    def test_visualization_generation(self):
        """<300ms for chart generation"""
        start = time.time()
        # Generate visualization
        duration = time.time() - start
        assert duration < 0.3
```

---

## Deployment Architecture

### Infrastructure Requirements

```yaml
# docker-compose.yml
version: "3.8"
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: medcontext
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  medgemma:
    image: medcontext/medgemma:latest
    environment:
      HUGGINGFACE_TOKEN: ${HF_TOKEN}
    ports:
      - "8001:8000"
    gpus: all # Requires GPU

  api:
    build: .
    environment:
      DATABASE_URL: postgresql://postgres:${DB_PASSWORD}@postgres:5432/medcontext
      REDIS_URL: redis://redis:6379
      MEDGEMMA_URL: http://medgemma:8000
      TINEYE_API_KEY: ${TINEYE_API_KEY}
      GOOGLE_VISION_API_KEY: ${GOOGLE_VISION_API_KEY}
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
      - medgemma

  ipfs:
    image: ipfs/kubo:latest
    ports:
      - "5001:5001"
      - "8080:8080"
    volumes:
      - ipfs_data:/data/ipfs

volumes:
  postgres_data:
  ipfs_data:
```

### Database Optimization

```sql
-- Key indices for performance
CREATE INDEX idx_image_submissions_hash ON image_submissions(image_hash);
CREATE INDEX idx_image_instances_source ON image_instances(source_image_id, similarity_score);
CREATE INDEX idx_health_claims_instance ON health_claims(image_instance_id);
CREATE INDEX idx_semantic_clusters_image ON semantic_clusters(source_image_id);
CREATE INDEX idx_provenance_blocks_chain ON provenance_blocks(chain_id, block_number);
CREATE INDEX idx_consensus_patterns_date ON consensus_patterns(pattern_snapshot_date);

-- Query optimization for common patterns
ANALYZE;
```

---

## Risk Mitigation & Security

### Potential Risks & Mitigations

| Risk                                        | Impact        | Mitigation                                                                                                                                                                                                            |
| ------------------------------------------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| API rate limiting from TinEye/Google        | Search delays | Queue system, caching, fallback to local database                                                                                                                                                                     |
| MedGemma hallucinations                     | False claims  | Post-processing validation, human review for critical analyses                                                                                                                                                        |
| False positives in misinformation detection | User distrust | Conservative confidence thresholds, transparent scoring                                                                                                                                                               |
| Privacy concerns (Telegram data)            | Legal/ethical | Explicit consent, data minimization, anonymization, note: Telegram uses cloud storage (not E2E encrypted by default); consider PHI/PII handling implications; avoid storing identifiable medical data in bot messages |
| IPFS availability                           | Data loss     | Redundant pinning, backup storage layer                                                                                                                                                                               |
| Malicious image submissions                 | System abuse  | File type validation, size limits, rate limiting                                                                                                                                                                      |

### Data Security

```python
# security/encryption.py
from cryptography.fernet import Fernet

class ImageEncryption:
    """Encrypt sensitive medical images at rest"""

    def __init__(self, key: str):
        self.cipher = Fernet(key)

    def encrypt_image(self, image_bytes: bytes) -> bytes:
        """Encrypt image before storage"""
        return self.cipher.encrypt(image_bytes)

    def decrypt_image(self, encrypted_bytes: bytes) -> bytes:
        """Decrypt image when needed"""
        return self.cipher.decrypt(encrypted_bytes)
```

---

## Post-Prototype Enhancements

### 7-Week Post-Launch Plan

**Week 7-8: Context Integrity Module**

- Integrate forensic analysis tools
- Train classifier on authentic vs. manipulated medical images
- Real-time detection on ingestion

**Week 9-10: Neo4j Graph Database**

- Migrate provenance chains to Neo4j
- Enable complex graph queries
- Implement temporal reasoning

**Week 11-12: Mobile Application**

- Native iOS/Android apps
- Offline image upload capability
- Push notifications for claims analysis

**Week 13-14: Public API & Integrations**

- Rate-limited API for researchers
- Integration with fact-checking platforms
- Feed to health authorities

---

## Key Success Metrics

### Functional Metrics

- Image processing latency <5 seconds end-to-end
- Reverse search coverage >80% of web instances
- Semantic clustering coherence >0.80
- Risk stratification accuracy >90%

### Operational Metrics

- System uptime >99.5%
- API response time p95 <500ms
- Database query p95 <100ms
- Background job success rate >99%

### Impact Metrics

- User trust score (survey-based)
- Reduction in spread of flagged misinformation
- Adoption by healthcare professionals
- Media citation accuracy improvements

---

## Appendix A: Database Schema Summary

```
ImageSubmission (1) ─── (N) SubmissionContext
         │
         ├─── (N) MedGemmaAnalysis
         │
         ├─── (N) ImageInstance ─── (N) HealthClaim ─┐
         │           │                                │
         │           └─── (1) SemanticCluster ────────┘
         │
         ├─── (1) ProvenanceChain ─── (N) ProvenanceBlock
         │
         ├─── (1) VisualizationData
         │
         └─── (1) ContextualIntegrityAssessment ─── (1) DecisionSupportOutput
```

---

## Appendix B: API Response Status Codes

```
200 OK - Successful request
201 Created - Resource created
202 Accepted - Request accepted (async processing)
400 Bad Request - Invalid input
401 Unauthorized - Authentication required
403 Forbidden - Permission denied
404 Not Found - Resource not found
429 Too Many Requests - Rate limit exceeded
500 Internal Server Error - Server error
503 Service Unavailable - External API down
```

---

## Appendix C: Environment Variables

```
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/medcontext

# APIs
TINEYE_API_KEY=xxx
GOOGLE_VISION_API_KEY=xxx
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_WEBHOOK_SECRET=xxx

# MedGemma
MEDGEMMA_URL=http://localhost:8001
HUGGINGFACE_TOKEN=xxx

# Storage
IPFS_GATEWAY=http://localhost:5001
S3_BUCKET=medcontext-images

# Redis
REDIS_URL=redis://localhost:6379

# Security
JWT_SECRET=xxx
ENCRYPTION_KEY=xxx

# Logging
LOG_LEVEL=INFO
SENTRY_DSN=xxx
```

### Environment Variable to Settings Mapping

| Environment Variable         | Settings Attribute                 | Description                                                                          | Used In               |
| ---------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------ | --------------------- |
| `TELEGRAM_BOT_TOKEN`         | `settings.telegram_bot_token`      | Bot authentication token from @BotFather                                             | Telegram ingestion    |
| `TELEGRAM_WEBHOOK_SECRET`    | `settings.telegram_webhook_secret` | Webhook verification secret for Telegram API                                         | Telegram ingestion    |
| `DATABASE_URL`               | `settings.database_url`            | PostgreSQL database connection string                                                | Database connections  |
| `MEDGEMMA_HF_TOKEN`          | `settings.medgemma_hf_token`       | HuggingFace token for MedGemma access                                                | MedGemma client       |
| `LLM_API_KEY`                | `settings.llm_api_key`             | API key for LLM provider (OpenRouter/Google)                                         | LLM orchestrator      |
| `SERP_API_KEY`               | `settings.serp_api_key`            | API key for search engine results                                                    | Search services       |
| `JWT_SECRET`                 | `settings.jwt_secret`              | Secret for JWT token generation                                                      | Authentication        |
| `ENCRYPTION_KEY`             | `settings.encryption_key`          | Key for data encryption                                                              | Data protection       |
| `MEDGEMMA_URL`               | `settings.medgemma_url`            | URL for MedGemma service endpoint                                                    | MedGemma client       |
| `REDIS_URL`                  | `settings.redis_url`               | Redis connection URL for caching                                                     | Caching layer         |
| `LOG_LEVEL`                  | `settings.log_level`               | Logging level (DEBUG, INFO, WARNING, ERROR)                                          | Logging system        |
| `VERTEX_API_KEY`             | `settings.vertexai_api_key`        | API key for Google Vertex AI services (aliases: VERTEXAI_API_KEY, VERTEX_AI_API_KEY) | Vertex AI integration |
| `APPWRITE_PROJECT_ID`        | `settings.appwrite_project_id`     | Project ID for Appwrite backend services                                             | Backend services      |
| `APPWRITE_ENDPOINT`          | `settings.appwrite_endpoint`       | Endpoint URL for Appwrite backend services                                           | Backend services      |
| `DEMO_ACCESS_CODE`           | `settings.demo_access_code`        | Access code for demo environment                                                     | Demo access control   |
| `SENTRY_DSN`                 | `settings.sentry_dsn`              | Data Source Name for Sentry error tracking                                           | Error monitoring      |
| `VITE_APPWRITE_PROJECT_NAME` | `settings.appwrite_project_name`   | Project name for Appwrite backend services                                           | Backend services      |

_Note: This table shows core settings mappings; see settings.py for complete list. Additional environment variables referenced in documentation can be found in Appendix C._

---

## Appendix D: Reference Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      User Interfaces                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Telegram Bot │  │   Extension  │  │   Web Application    │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└──────────┬──────────────────┬──────────────────┬────────────────┘
           │                  │                  │
┌──────────▼──────────────────▼──────────────────▼────────────────┐
│                    FastAPI Application Layer                     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  /api/v1/ingest    /analyze    /reverse-search            │ │
│  │  /semantic         /provenance /visualization             │ │
│  │  /decision-support                                        │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────┬──────────────────────────────────────────────────────┘
           │
┌──────────▼──────────────────────────────────────────────────────┐
│                  Processing Modules (Parallel)                   │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────────────────┐ │
│  │ MedGemma   │  │   Reverse   │  │  Semantic Analysis       │ │
│  │ Analysis   │  │   Search    │  │  + Clustering            │ │
│  └────────────┘  └─────────────┘  └──────────────────────────┘ │
│  ┌────────────┐  ┌──────────────────────────────────────────┐   │
│  │Provenance  │  │   Decision Support + Visualization       │   │
│  │ Blockchain │  │                                          │   │
│  └────────────┘  └──────────────────────────────────────────┘   │
└──────────┬──────────────────────────────────────────────────────┘
           │
┌──────────▼──────────────────────────────────────────────────────┐
│                        Data Layer                                │
│  ┌─────────────────────┐  ┌──────────────┐  ┌─────────────┐    │
│  │  PostgreSQL         │  │     IPFS     │  │    Redis    │    │
│  │  (Primary Database) │  │   (Storage)  │  │   (Cache)   │    │
│  └─────────────────────┘  └──────────────┘  └─────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

---

## Appendix E: Implementation Checklist

### Phase 1: Foundation (Weeks 1-2)

- [ ] PostgreSQL schema creation
- [ ] Telegram API integration
- [ ] Web form interface
- [ ] Image storage (IPFS)
- [ ] Unit tests for ingestion

### Phase 2: Analysis (Weeks 2-4)

- [ ] MedGemma integration
- [ ] TinEye + Google Vision
- [ ] Semantic analysis pipeline
- [ ] Integration tests
- [ ] Performance optimization

### Phase 3: Intelligence (Weeks 4-6)

- [ ] Provenance blockchain
- [ ] Visualization API
- [ ] Decision support engine
- [ ] End-to-end testing
- [ ] Documentation

### Phase 4: Hardening (Post-Launch)

- [ ] Security audit
- [ ] Load testing
- [ ] User feedback integration
- [ ] Context integrity module
- [ ] Neo4j migration planning

---

## Appendix F: Cost Estimation

| Component            | Cost/Month           | Notes                     |
| -------------------- | -------------------- | ------------------------- |
| Cloud Infrastructure | $500-1,500           | GPU for MedGemma, storage |
| TinEye API           | $100-500             | Based on searches         |
| Google Vision API    | $50-200              | Based on requests         |
| Telegram Bot API     | Free-100             | Volume-based pricing      |
| PostgreSQL Database  | $100-300             | Managed service           |
| IPFS Hosting         | 50-200               | Redundant pinning         |
| Monitoring/Logging   | 50-100               | Sentry, DataDog           |
| **Total Estimated**  | **$850-2,900/month** | Scales with usage         |

---

## Conclusion

MedContext provides a comprehensive, modular architecture for medical image misinformation detection. The phased 6-week development approach prioritizes functional capability and operational reliability over feature breadth.

Key design decisions:

- **PostgreSQL-first**: Simpler, faster development than Neo4j from start
- **Asynchronous processing**: Long-running tasks don't block user interactions
- **Modular architecture**: Each component can be tested, deployed, and scaled independently
- **Transparent scoring**: All confidence/accuracy scores are explainable
- **Audience-specific recommendations**: Content tailored to clinicians, public, researchers, journalists

The system is production-ready for launch with defined success criteria, comprehensive testing frameworks, and clear post-launch enhancement roadmap.

---

**Document Version:** 1.0  
**Last Updated:** January 14, 2026  
**Status:** Complete Pre-Development Planning
