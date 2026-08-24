# NEXA PRIME v2: VISUAL ARCHITECTURE BLUEPRINTS & DATA FLOW SCHEMATICS

**Component:** System Architecture Diagrams, Sequence Visuals & Entity Relationship Schemas  
**Version:** 2.4.0-BLUEPRINTS | **Status:** Approved Production

---

## 🗺️ BLUEPRINT 1: END-TO-END SYSTEM COMPONENT MAP

```mermaid
graph TB
    subgraph ExternalSources ["EXTERNAL WORLD & PRODUCERS"]
        GDRIVE["Google Drive Folder
(1wl6IORLksewhrWqpCOfjFNgjlC_rAhZT)"]
        CBVIP["Coldwell Banker VIP Portal
(officeid=470 & officeuserid=17983)"]
        INVESTOR["Investors & Property Buyers
(Mobile Safari, Chrome, Desktop)"]
        ADMINUSER["Suzanne Tenekecioğlu (VIP Admin)
(PIN: nexa2026vip)"]
    end

    subgraph SecurityPerimeter ["ENTERPRISE SECURITY PERIMETER"]
        IPCHECK["Client IP Real Source Resolver
(_get_client_ip)"]
        BRUTE["Admin PIN Brute-Force Limiter
(5 attempts / 60s lockout)"]
        CSRF["Origin / Referer Strict Whitelist
(_validate_origin_and_csrf)"]
        PATHGUARD["Path Traversal Neutralizer
(.is_relative_to(PROJELER_DIR))"]
    end

    subgraph ApplicationCore ["APPLICATION CORE & WEBSERVER (app.py)"]
        ROUTES["RESTful API Endpoints
(/api/projects, /api/appointments, /api/admin/*)"]
        MEDIA["HTTP 206 Partial Content Streamer
(/stream/video, /stream/pdf)"]
        STATIC["Static Asset & Hydration Server
(site.html, admin.html, static/)"]
    end

    subgraph CognitiveBrain ["COGNITIVE AI & HYBRID VECTOR RAG"]
        FTS5["SQLite FTS5 BM25 Engine
(documents, document_chunks)"]
        VEC["768-D Dense Vector Embeddings
(text-embedding-004 BLOBs)"]
        FUSION["Adaptive Score Fusion Core
S(d,q) = α·Dense + (1-α)·Lex"]
        GUARD["Cadastral & Contract Guardrail
(TKGM, Notary, BTS Insurance)"]
        CASCADE["3-Tier Execution Cascade
(Gemini ➔ Ollama ➔ Heuristic Matrix)"]
    end

    subgraph StorageLayer ["DATA STORAGE & SSOT ENGINE"]
        SQLITEDB[("SQLite Database in WAL Mode
nexa_database.db")]
        MAPJSON["projects_map.json
(32 Projects SSOT)"]
        PORTJSON["nexa_portfolio_data.json
(CB VIP Live Listings)"]
        ORDERJSON["display_order.json
(Custom Showcase Ranking)"]
    end

    subgraph AutonomousDaemons ["SRE AUTONOMOUS DAEMONS"]
        PULLER["nexa_drive_puller.py
(Tokenless Drive Poller)"]
        WATCHDOG["nexa_watchdog.py
(Filesystem Event Daemon)"]
        SENTINEL["nexa_self_healing.py
(5-Phase Integrity Sentinel)"]
        CRON["GitHub Actions Daily Cron
(scripts/ci_sync.py at 02:00 UTC)"]
    end

    INVESTOR --> IPCHECK --> CSRF --> ROUTES --> STATIC
    ADMINUSER --> IPCHECK --> BRUTE --> ROUTES --> STATIC
    
    GDRIVE --> PULLER --> StorageLayer
    CBVIP --> CRON --> StorageLayer
    WATCHDOG --> StorageLayer
    SENTINEL <--> StorageLayer

    ROUTES <--> CognitiveBrain
    CognitiveBrain <--> StorageLayer
    ROUTES <--> StorageLayer
    MEDIA --> PATHGUARD --> StorageLayer
```

---

## 🗄️ BLUEPRINT 2: ENTITY RELATIONSHIP DIAGRAM (DATABASE SCHEMA)

```mermaid
erDiagram
    PROJECTS ||--o{ DOCUMENTS : "contains"
    DOCUMENTS ||--o{ DOCUMENT_CHUNKS : "chunked_into"
    PROJECTS ||--o{ CUSTOMERS : "inquired_by"
    
    PROJECTS {
        INTEGER id PK
        TEXT name
        TEXT title
        TEXT location
        TEXT il
        TEXT ilce
        REAL price_numeric
        TEXT price_display
        TEXT room_info
        TEXT ada_no
        TEXT parsel_no
        INTEGER tkgm_verified
        INTEGER is_portfolio
        TEXT developer
        TEXT delivery_date
        INTEGER bts_insurance_verified
        TEXT image
        TEXT drive_video_preview
        DATETIME created_at
    }

    DOCUMENTS {
        INTEGER id PK
        INTEGER project_id FK
        TEXT doc_type
        TEXT title
        TEXT file_path
        TEXT content
        TEXT category
        DATETIME updated_at
    }

    DOCUMENT_CHUNKS {
        INTEGER id PK
        INTEGER document_id FK
        INTEGER chunk_index
        TEXT chunk_text
        BLOB embedding_vector
        REAL semantic_norm
        DATETIME created_at
    }

    CUSTOMERS {
        INTEGER id PK
        TEXT project_id FK
        TEXT name
        TEXT phone
        TEXT email
        TEXT notes
        TEXT stage
        TEXT assigned_agent
        DATETIME created_at
    }

    AUDIT_LOGS {
        INTEGER id PK
        TEXT client_ip
        TEXT action
        TEXT payload
        DATETIME timestamp
    }
```

---

## 🔄 BLUEPRINT 3: 3-TIER AI INFERENCE FALLBACK SEQUENCE

```mermaid
sequenceDiagram
    autonumber
    participant Client as Mira AI Client
    participant Gateway as app.py (/api/nexa-ai-chat)
    participant Tier1 as Tier 1: Cloud Gemini 1.5 Pro
    participant Tier2 as Tier 2: Local Edge Ollama (Qwen 2.5)
    participant Tier3 as Tier 3: Deterministik Heuristic Matrix
    participant DB as SQLite WAL Storage

    Client->>Gateway: POST /api/nexa-ai-chat with user query
    Gateway->>Gateway: Classify intent & assemble RAG context from DB
    
    alt Tier 1 Operational (Nominal State)
        Gateway->>Tier1: Request inference with temperature=0.2 & grounded system prompt
        Tier1-->>Gateway: HTTP 200 OK with natural consultant response
        Gateway-->>Client: Deliver verified response (Latency ~420ms)
    else Tier 1 Quota Exceeded (HTTP 429) or Network Drop
        Gateway->>Tier1: Request inference
        Tier1-->>Gateway: HTTP 429 / 503 Outage
        Note over Gateway: Seamless Failover to Tier 2
        Gateway->>Tier2: Forward context to http://localhost:11434/api/generate
        alt Tier 2 Available
            Tier2-->>Gateway: HTTP 200 OK from local neural model
            Gateway-->>Client: Deliver local AI response (Latency ~180ms)
        else Tier 2 Unavailable / Off-Grid
            Note over Gateway: Seamless Failover to Tier 3
            Gateway->>Tier3: Query canonical projects_map.json & SQLite
            Tier3->>DB: Pull exact price, down payment, ada/parsel
            Tier3-->>Gateway: Format deterministic markdown table
            Gateway-->>Client: Deliver guaranteed accurate response (Latency ~4ms)
        end
    end
```

---
*Blueprint Collection Certified for NEXA PRIME v2 Enterprise Deployment.*
