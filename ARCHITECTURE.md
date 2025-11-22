# 🏗️ Architecture Documentation

## System Overview

Browser Isolation implements a **Zero Trust Remote Browser Isolation (RBI)** architecture where web pages are fetched, sanitized, and rendered in a completely isolated environment before being transmitted to the user.

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                           │
│  ┌────────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │   Dashboard    │  │   CLI Tool   │  │   API Clients      │  │
│  │  (Streamlit)   │  │ (isolationctl)│  │   (HTTP/REST)      │  │
│  └────────┬───────┘  └──────┬───────┘  └─────────┬──────────┘  │
└───────────┼──────────────────┼─────────────────────┼─────────────┘
            │                  │                     │
            └──────────────────┼─────────────────────┘
                               │
┌──────────────────────────────┼─────────────────────────────────┐
│                       API LAYER (FastAPI)                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Routes: /render, /check-url, /audit, /policies, /health│  │
│  └───────────────────────┬──────────────────────────────────┘  │
└──────────────────────────┼──────────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────────┐
│                   ISOLATION ENGINE                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │    Policy    │  │   Remote     │  │   DOM Sanitizer      │  │
│  │   Checker    │→ │   Fetcher    │→ │  (JS Removal)        │  │
│  └──────────────┘  └──────┬───────┘  └──────┬───────────────┘  │
│                            │                  │                  │
│                            ↓                  ↓                  │
│                    ┌───────────────┐  ┌──────────────────────┐  │
│                    │  Headless     │  │  Remote Renderer     │  │
│                    │  Chromium     │  │  (Safe DOM)          │  │
│                    └───────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────────┐
│                  SUPPORT SERVICES                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │    Audit     │  │   Report     │  │   Configuration      │  │
│  │   Logger     │  │  Generator   │  │   Management         │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Request Initiation
```
User → Dashboard/CLI/API → API Server
```

### 2. Policy Check
```
API Server → PolicyChecker → Block Rules → Decision (Allow/Block)
```

### 3. Remote Fetch (if allowed)
```
RemoteFetcher → Playwright → Headless Chromium → Target URL
                                                 ↓
                                          Raw HTML + Resources
```

### 4. Sanitization
```
Raw HTML → DOMSanitizer → Parser → Remove Scripts
                       → Remove Event Handlers
                       → Remove Trackers
                       → Remove Dangerous URLs
                       → Sanitize CSS
                       → Calculate Risk Score
                       ↓
                   Safe HTML
```

### 5. Rendering
```
Safe HTML → RemoteRenderer → Package Metadata
                          → Add Warnings
                          → Build Safe DOM
                          ↓
                      Safe DOM Object
```

### 6. Response
```
Safe DOM → API Response → Client
                       → Dashboard Display
                       → CLI Output
```

### 7. Audit Trail
```
Every Step → AuditLogger → JSON Logs → isolation_audit.log
```

## Core Components

### 1. **RemoteFetcher** (`engine/fetcher.py`)
- **Purpose**: Fetch URLs in isolated headless browser
- **Technology**: Playwright + Chromium
- **Key Features**:
  - Headless browser execution
  - Resource blocking (scripts, WebSockets)
  - Network request tracking
  - Console log capture
  - Error handling

### 2. **DOMSanitizer** (`engine/dom_sanitizer.py`)
- **Purpose**: Remove all JavaScript and dangerous content
- **Technology**: BeautifulSoup + bleach
- **Sanitization Actions**:
  - Remove `<script>` tags
  - Strip event handlers (onclick, onload, etc.)
  - Block javascript: URLs
  - Remove iframes
  - Remove tracking pixels
  - Sanitize CSS
  - Remove HTML comments
  - Risk scoring

### 3. **PolicyChecker** (`engine/policy_checker.py`)
- **Purpose**: Enforce URL and content policies
- **Policy Types**:
  - Domain blocklists/allowlists
  - URL pattern matching
  - Malware domain detection
  - Phishing site detection
  - Content type validation
  - Size limits

### 4. **RemoteRenderer** (`engine/remote_renderer.py`)
- **Purpose**: Package sanitized content for transmission
- **Output**: Safe DOM object with:
  - Sanitized HTML
  - Metadata (risk score, size, timing)
  - Warnings
  - Blocked content list
  - Resources

### 5. **AuditLogger** (`logging_mod/events.py`)
- **Purpose**: Comprehensive security audit trail
- **Logged Events**:
  - Render operations
  - Policy decisions
  - Sanitization actions
  - Threats detected
  - API requests
- **Output**: JSON-structured logs

## Security Architecture

### Defense in Depth

1. **Network Layer**
   - URL policy enforcement
   - Domain blocklists
   - Protocol validation

2. **Execution Layer**
   - Isolated browser sandbox
   - Resource blocking
   - No local code execution

3. **Content Layer**
   - DOM sanitization
   - JavaScript removal
   - Event handler stripping
   - URL validation

4. **Application Layer**
   - Read-only rendering
   - No user interaction with original content
   - Safe DOM transmission

5. **Audit Layer**
   - Complete event logging
   - Risk scoring
   - Threat detection tracking

### Threat Model

| Threat | Mitigation |
|--------|------------|
| **Drive-by Downloads** | Headless isolation + script removal |
| **XSS Attacks** | Complete JavaScript stripping |
| **Phishing** | URL blocklist + content inspection |
| **Malware Execution** | No local execution environment |
| **Tracking** | Tracker/beacon removal |
| **Cryptominers** | Script blocking + resource limits |
| **Zero-Day Exploits** | Air-gapped rendering |
| **CSRF** | Read-only mode |
| **Clickjacking** | iframe removal |

## Deployment Architecture

### Docker Compose Stack

```yaml
┌─────────────────────────────────┐
│     Load Balancer (Optional)    │
└────────────┬────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼────┐      ┌────▼─────┐
│  API   │      │Dashboard │
│:8000   │      │:8501     │
└───┬────┘      └────┬─────┘
    │                │
    └────────┬───────┘
             │
   ┌─────────▼────────────┐
   │  Isolation Network   │
   └──────────────────────┘
```

### Scaling Considerations

1. **Horizontal Scaling**
   - Multiple API instances behind load balancer
   - Shared volume for logs/reports
   - Session-less design

2. **Resource Limits**
   - ~200MB RAM per isolation instance
   - ~2-5s per page render
   - 50+ concurrent sessions on 8GB RAM

3. **Performance Optimization**
   - Browser instance pooling
   - DOM caching (optional)
   - Async rendering
   - Resource prefetching

## API Architecture

### RESTful Endpoints

```
POST /api/v1/render
  → Isolate and render URL
  → Returns: Safe DOM + metadata

POST /api/v1/check-url
  → Check URL policy
  → Returns: Allow/block decision

GET /api/v1/audit
  → Retrieve audit logs
  → Returns: Event list

GET /api/v1/policies
  → Get active policies
  → Returns: Policy summary

GET /api/v1/health
  → Health check
  → Returns: System status
```

### Authentication (Optional)

For production deployment:
- API key authentication
- JWT tokens
- Rate limiting
- IP whitelisting

## Configuration Management

### Config Files

1. **block_rules.yaml**
   - Domain lists
   - URL patterns
   - Categories
   - Risk thresholds

2. **sanitization_policies.json**
   - JavaScript rules
   - Content rules
   - Resource rules
   - Tracking rules

3. **.env**
   - Runtime configuration
   - Port settings
   - Feature flags

## Monitoring & Observability

### Metrics to Track

- Total renders
- Average risk score
- High-risk detections
- Blocked URLs
- Render time
- Error rate
- Resource usage

### Log Aggregation

Logs are SIEM-ready:
- Splunk
- ELK Stack
- Azure Sentinel
- Generic JSON

## Extension Points

### Adding New Features

1. **Custom Sanitizers**
   - Extend `DOMSanitizer`
   - Add to sanitization pipeline

2. **Policy Providers**
   - Implement `PolicyChecker` interface
   - Add threat intelligence feeds

3. **Report Formats**
   - Extend `ReportGenerator`
   - Add exporters (PDF, CSV, etc.)

4. **Storage Backends**
   - Database integration
   - Cloud storage
   - Redis caching

## Performance Characteristics

### Typical Metrics

- **Render Time**: 2-5 seconds
- **Memory**: 200MB per instance
- **Throughput**: 100+ pages/minute
- **Latency**: <500ms sanitization
- **Concurrent**: 50+ sessions (8GB RAM)

## Security Considerations

### Production Hardening

1. Enable HTTPS
2. Add authentication
3. Implement rate limiting
4. Use read-only file systems
5. Enable audit logging
6. Regular security updates
7. Monitor for anomalies

---

**For implementation details, see source code and inline documentation.**

