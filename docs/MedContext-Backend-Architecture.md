# MedContext: Context Integrity, Blockchain Provenance, Real-Time Monitoring
## Backend Architecture for Context Alignment Verification and Learning

**Prepared for:** Purpose Africa, HERO Organization, MedContext Project  
**Date:** January 14, 2026  
**Purpose:** Implement context alignment checks, immutable provenance tracking, and real-time learning architecture

---

## Executive Summary

This document specifies the backend infrastructure that powers MedContext's user-facing verification system.

**User-Facing Frontend**
- Medical professional / journalist / public uploads an image
- System analyzes and returns a context alignment verdict within minutes
- Simple visual interface: "Aligned" / "Misleading" / "Uncertain"

**Hidden Backend Learning System**
- Every upload becomes training data
- Context alignment models improve continuously
- Provenance genealogy accumulates as a learning corpus
- Misinformation narratives tracked across platforms
- Pattern recognition identifies emerging threats

**Key Components**
1. Context Integrity Module (reverse search + provenance + semantic checks)
2. Blockchain-Like Provenance System (immutable genealogy)
3. Real-Time Social Monitoring (WhatsApp, Facebook, Twitter, Telegram)
4. Learning Algorithm (federated learning approach)
5. Pattern Recognition Engine (emerging narrative detection)

---

## Part 1: Context Integrity Module

### 1.1 Problem Statement
Medical images are frequently reused out of context. No single artifact guarantees proper usage, so MedContext uses a multi-signal alignment strategy.

### 1.2 Three-Layer Architecture

Layer 1: Context Signals  
- Reverse image search results  
- Source credibility checks  
- Prior usage context  

Layer 2: Semantic/Content Analysis  
- Medical plausibility scoring  
- Claim-to-image alignment  
- Domain-specific consistency checks  

Layer 3: Provenance and Metadata  
- Provenance chain validation  
- Capture/source metadata checks  
- Timeline consistency  

**Ensemble Decision Logic**
- All 3 layers agree: high confidence  
- 2 of 3 agree: medium confidence  
- 1 or 0 agree: low confidence and expert review  

### 1.3 Module in Repository
Planned implementations (stubs are now in place):
- `src/app/forensics/service.py`: legacy integrity signal stub
- `src/app/api/v1/endpoints/forensics.py`: legacy integrity signal endpoint

---

## Part 2: Blockchain Provenance System

### 2.1 Purpose
Create an immutable, auditable record of image origin and usage. MedContext uses a hybrid approach: database for operational speed, blockchain-style hashes for tamper-evidence.

### 2.2 Core Capabilities
- Register image (hash + metadata)
- Record usage (claims, platforms, timestamps)
- Record authenticity verdicts
- Query genealogy and audit trail

### 2.3 Module in Repository
Implemented with blockchain-like hashing for blocks:
- `src/app/provenance/service.py`: hash-chained block construction
- `/api/v1/provenance/*` endpoints return chain data

---

## Part 3: Real-Time Social Monitoring

### 3.1 Architecture
Monitor multiple platforms, extract medical images and context, and push them through the analysis pipeline. Focus on consent-based ingestion and de-identification where needed.

### 3.2 Planned Integrations
- Telegram channels (public channels, low overhead)
- Facebook pages and groups (public API where allowed)
- Twitter/X keyword searches (public data)
- WhatsApp health groups (consent-based, future)

### 3.3 Module in Repository
Monitoring interface stubs:
- `src/app/monitoring/telegram.py`
- `src/app/monitoring/whatsapp.py` (legacy stub)
- `src/app/monitoring/facebook.py`
- `src/app/monitoring/twitter.py`
- `src/app/api/v1/endpoints/monitoring.py`

---

## Part 4: Learning System (Federated Approach)

### 4.1 Goal
Use each processed image as a training example to improve context alignment while preserving privacy.

### 4.2 Planned Capabilities
- Model updates triggered by new training batches
- Validation gate to avoid regressions
- Model distribution to edge/field nodes

---

## Part 5: User Experience

User experience remains simple:
- Upload image
- Receive verdict: Authentic / Manipulated / Uncertain
- View provenance history and supporting context

The complexity lives behind the interface, where provenance, monitoring, and learning continuously improve trust in outcomes.
