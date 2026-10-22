# ShebaBondhu: Architecture

Version 1.0 | 22 October 2026

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          FLUTTER APP                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │  Home    │ │ Sheba AI │ │ Medicine │ │  Doctor  │ │  Family  │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │
│       │            │            │            │            │          │
│  ┌────┴────────────┴────────────┴────────────┴────────────┴────┐    │
│  │              Dio HTTP Client + Auth Interceptor              │    │
│  │         (attaches Firebase ID token to every request)        │    │
│  └──────────────────────────┬───────────────────────────────────┘    │
│                             │                                        │
│  ┌──────────────────────────┴───────────────────────────────────┐    │
│  │        Firebase Auth SDK (email/Google sign-in only)          │    │
│  └──────────────────────────────────────────────────────────────┘    │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Local Notifications (flutter_local_notifications)           │    │
│  └──────────────────────────────────────────────────────────────┘    │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Speech-to-Text (device speech recognition, Bangla/English)  │    │
│  └──────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                              │  HTTPS
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND (Docker)                          │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                   Middleware Layer                              │  │
│  │  • Firebase ID Token verification                              │  │
│  │  • Role-based access control                                   │  │
│  │  • Request logging & correlation ID                            │  │
│  │  • Rate limiting (per-user)                                    │  │
│  │  • CORS                                                        │  │
│  └──────────────────────────┬─────────────────────────────────────┘  │
│                             │                                        │
│  ┌──────────────────────────┴─────────────────────────────────────┐  │
│  │                   Router / API Layer                            │  │
│  │  auth │ profile │ medicine │ reading │ doctor │ appointment │   │  │
│  │  guardian │ chat │ notification │ admin │ cron                  │  │
│  └──────────────────────────┬─────────────────────────────────────┘  │
│                             │                                        │
│  ┌──────────────────────────┴─────────────────────────────────────┐  │
│  │                   Service Layer                                 │  │
│  │  AuthService │ ProfileService │ MedicineService │               │  │
│  │  ReadingService │ DoctorService │ AppointmentService │          │  │
│  │  GuardianService │ ChatService │ NotificationService │          │  │
│  │  AgentOrchestrator │ AdminService │ CronService                │  │
│  └──────────────────────────┬─────────────────────────────────────┘  │
│                             │                                        │
│  ┌──────────────────────────┴─────────────────────────────────────┐  │
│  │                   Agent Layer                                   │  │
│  │  Orchestrator → Triage │ Medicine │ Guardian Alert │            │  │
│  │                 Doctor Match (+ PDF generation)                 │  │
│  │  ┌──────────────┐                                               │  │
│  │  │ LLM Wrapper  │ (provider-agnostic: Gemini / Claude / GPT)   │  │
│  │  └──────────────┘                                               │  │
│  └──────────────────────────┬─────────────────────────────────────┘  │
│                             │                                        │
│  ┌──────────────────────────┴─────────────────────────────────────┐  │
│  │                 Repository Layer                                │  │
│  │  UserRepo │ MedicineRepo │ ReadingRepo │ DoctorRepo │          │  │
│  │  AppointmentRepo │ GuardianRepo │ ChatRepo │ AlertRepo │       │  │
│  │  NotificationRepo                                               │  │
│  │  ─────────────────────────────────────────────                  │  │
│  │  All Firestore access is encapsulated here.                     │  │
│  │  Swap to Postgres by replacing only this layer.                 │  │
│  └──────────────────────────┬─────────────────────────────────────┘  │
│                             │                                        │
└─────────────────────────────┼───────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
      ┌──────────────┐ ┌──────────┐  ┌───────────────┐
      │  Firestore   │ │ FCM      │  │ Gemini Flash  │
      │  (Spark)     │ │ (push)   │  │ (LLM API)     │
      └──────────────┘ └──────────┘  └───────────────┘
```

External trigger:
```
  cron-job.org ──(POST /internal/cron/missed-doses)──▶ FastAPI
```

---

## 2. Backend Layering (Modular Monolith)

### 2.1 Layers (top → bottom)

| Layer | Responsibility | Rules |
|-------|---------------|-------|
| **Middleware** | Auth verification, RBAC, rate limiting, CORS, logging | No business logic. Every request gets a correlation ID. |
| **Router / API** | HTTP endpoint definitions, request validation (Pydantic), response serialization | Thin. Calls service layer. Never touches Firestore directly. |
| **Service** | Business logic, orchestration between repos and agents | May call multiple repos in a single operation. Raises domain exceptions. |
| **Agent** | AI agent logic: orchestration, triage rules, medicine logic, guardian alerts, doctor matching, PDF generation | Accesses LLM wrapper for AI calls. Uses repos for data. |
| **Repository** | Firestore CRUD, query building, denormalization writes | Only layer that imports `google-cloud-firestore`. One repo class per collection family. |
| **LLM Wrapper** | Provider-agnostic interface for language model calls | Abstracts model selection, prompt formatting, token limits, retries, caching. |

### 2.2 Dependency direction

```
Router → Service → Agent → LLM Wrapper
                 ↘        ↗
                  Repository
```

- Routers depend on Services, never on Repos.
- Services depend on Repos and may invoke Agents.
- Agents depend on Repos (for data) and LLM Wrapper (for AI).
- Repos depend only on the Firestore SDK.
- No circular dependencies. No layer skipping.

### 2.3 Module boundaries

Each domain module (auth, medicine, doctor, etc.) has its own:
- `router.py` — endpoint definitions
- `service.py` — business logic
- `schemas.py` — Pydantic request/response models
- `repository.py` — Firestore access
- `exceptions.py` — domain-specific errors

Shared code lives in `core/` (auth, config, middleware, base classes).

---

## 3. Flutter App Structure

### 3.1 Architecture pattern: Feature-first + Riverpod

```
lib/
├── core/              # Shared utilities, theme, routing, DI
│   ├── config/        # Environment config, API base URL
│   ├── theme/         # Colors, typography, Bangla font setup
│   ├── routing/       # GoRouter setup, route guards
│   ├── network/       # Dio client, auth interceptor, error handler
│   ├── l10n/          # Bangla/English localization
│   └── utils/         # Date formatting, validators, etc.
├── features/
│   ├── auth/          # Login, registration, onboarding
│   ├── home/          # Patient dashboard
│   ├── chat/          # Sheba AI chat + voice input
│   ├── medicine/      # Medicine list, schedule, adherence
│   ├── reading/       # Sugar/BP manual entry + trends
│   ├── doctor/        # Doctor search, profiles, appointments
│   ├── family/        # Guardian connection, invite codes
│   ├── profile/       # Health profile editing
│   ├── guardian_home/ # Guardian dashboard
│   ├── doctor_home/   # Doctor view (requests, prescriptions)
│   └── emergency/     # SOS screen, hospital list, 999
├── shared/
│   ├── widgets/       # Reusable UI components
│   ├── models/        # Shared data models
│   └── providers/     # Shared Riverpod providers (auth state, user)
└── main.dart
```

### 3.2 Key Flutter packages

| Package | Purpose |
|---------|---------|
| `firebase_auth` | Email/Google sign-in |
| `firebase_messaging` | Receive push notifications |
| `flutter_local_notifications` | Medicine reminders (offline) |
| `speech_to_text` | Bangla/English voice input |
| `dio` | HTTP client to FastAPI |
| `flutter_riverpod` | State management + DI |
| `go_router` | Declarative routing with auth guards |
| `geolocator` | GPS for emergency/hospital distance |
| `url_launcher` | wa.me links, 999 call, Google Maps |
| `flutter_localizations` + `intl` | Bangla/English i18n |
| `fl_chart` | Reading trend charts |

### 3.3 State management approach

- **Riverpod** for all state. No StatefulWidgets for business logic.
- `authStateProvider` → watches Firebase Auth state, triggers route guards.
- Feature-level providers: `medicineListProvider`, `chatMessagesProvider`, etc.
- API calls via `AsyncNotifier` pattern (loading / data / error states).
- Optimistic UI updates where safe (e.g., marking a dose taken).

---

## 4. Request Flow (Happy Path)

```
Flutter App                    FastAPI Backend                    Firestore
    │                               │                               │
    │  1. User action               │                               │
    │  (e.g., mark dose taken)      │                               │
    │                               │                               │
    │  2. Dio interceptor attaches  │                               │
    │     Firebase ID token         │                               │
    │──── POST /medicines/doses ───▶│                               │
    │     { medicine_id, taken_at } │                               │
    │                               │  3. Middleware verifies token  │
    │                               │     with Firebase Admin SDK   │
    │                               │     → extracts uid + role     │
    │                               │                               │
    │                               │  4. Router validates body     │
    │                               │     (Pydantic)                │
    │                               │                               │
    │                               │  5. Service: MedicineService  │
    │                               │     .record_dose()            │
    │                               │                               │
    │                               │  6. Repo: writes dose_log,    │
    │                               │─────updates daily adherence──▶│
    │                               │                               │
    │                               │  7. Service: checks if all    │
    │                               │     daily doses are taken,    │
    │                               │     updates adherence summary │
    │                               │                               │
    │◀── 200 { dose_log } ─────────│                               │
    │                               │                               │
    │  8. UI updates optimistically │                               │
```

---

## 5. Authentication Flow

### 5.1 Sign-in (client-side)

```
┌────────────────────────────────────────────────┐
│                  Flutter App                    │
│                                                 │
│  1. User taps "Sign in with Google" or enters   │
│     email/password                              │
│                                                 │
│  2. firebase_auth SDK → Firebase Auth servers   │
│     → returns UserCredential                    │
│                                                 │
│  3. App calls user.getIdToken()                 │
│     → JWT with uid, email, provider             │
│                                                 │
│  4. App stores token in memory (Riverpod)       │
│     Dio interceptor attaches:                   │
│     Authorization: Bearer <idToken>             │
│                                                 │
│  5. App calls POST /auth/register or            │
│     GET /me to create/fetch profile              │
└────────────────────────────────────────────────┘
```

### 5.2 Token verification (server-side, every request)

The backend has two auth dependencies:

```python
# Pseudocode — dependencies

async def get_firebase_user(request):
    """Verifies Firebase ID token only. Returns decoded token.
    Used by /auth/register and GET /me (where no user doc may exist yet)."""
    token = request.headers["Authorization"].split("Bearer ")[1]
    decoded = firebase_admin.auth.verify_id_token(token)
    # decoded contains: uid, email, sign_in_provider
    return decoded  # No user doc lookup

async def get_current_user(request):
    """Verifies token AND loads user doc. Returns full user object.
    Used by all endpoints that require an existing user."""
    decoded = await get_firebase_user(request)
    user_doc = await user_repo.get_by_uid(decoded["uid"])
    if not user_doc:
        raise 404  # NOT_REGISTERED
    return user_doc  # uid, role, etc.
```

### 5.3 Role-based access

```python
# Dependency injection for role checking
def require_role(*allowed_roles):
    def checker(user = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise 403
        return user
    return checker

# Usage in a router
@router.get("/guardian/patients")
async def list_patients(user = Depends(require_role("guardian"))):
    ...
```

### 5.4 Token refresh

- Firebase ID tokens expire after 1 hour.
- The Dio interceptor catches 401 responses, calls `user.getIdToken(forceRefresh: true)`, and retries the request once.
- If refresh fails → redirect to login screen.

---

## 6. Agent Orchestration Flow

### 6.1 Architecture

```
                   ┌─────────────────┐
  Chat message ──▶ │  Orchestrator   │
  System event ──▶ │                 │
                   └───────┬─────────┘
                           │ routes to
              ┌────────────┼────────────────┐
              ▼            ▼                ▼
     ┌──────────────┐ ┌──────────┐  ┌─────────────┐
     │ Triage Agent │ │ Medicine │  │ Doctor Match │
     │              │ │  Agent   │  │    Agent     │
     └──────┬───────┘ └────┬─────┘  └──────┬──────┘
            │              │               │
            ▼              ▼               ▼
     ┌─────────────────────────────────────────────┐
     │          Guardian Alert Agent                │
     │  (triggered by events from other agents)     │
     └─────────────────────────────────────────────┘
```

### 6.2 Chat message flow

```
1. User sends message via POST /chat/messages
2. ChatService saves user message to Firestore
3. ChatService calls Orchestrator.handle(message, context)
4. Orchestrator classifies intent:
   a. Symptom/health concern → Triage Agent
   b. Medicine question → Medicine Agent
   c. Doctor/appointment request → Doctor Match Agent
   d. General health question → Direct LLM call with safety prompt
5. Selected agent processes:
   - Triage: safety rules first → if ambiguous → LLM → severity (green/yellow/red)
   - If RED: agent raises EmergencyEvent
   - If YELLOW: agent returns doctor recommendation context
6. Orchestrator collects agent response
7. If EmergencyEvent raised → Guardian Alert Agent fires
8. ChatService saves assistant message to Firestore
9. Response returned to Flutter → displayed in chat
```

### 6.3 Agent interface

```python
# All agents implement this interface
class BaseAgent(ABC):
    @abstractmethod
    async def handle(self, input: AgentInput) -> AgentOutput:
        """Process input, return output with optional events."""
        pass

@dataclass
class AgentInput:
    user_id: str
    message: str          # may be empty for system events
    context: dict         # user profile, recent readings, medicines
    conversation_id: str

@dataclass
class AgentOutput:
    response_text: str
    severity: str | None          # green / yellow / red
    events: list[AgentEvent]      # e.g., EmergencyEvent, DoctorRecommendEvent
    metadata: dict                # extra data for the UI
```

### 6.4 LLM Wrapper interface

```python
class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str,
                       max_tokens: int = 500) -> str:
        pass

class GeminiProvider(LLMProvider):
    """Google Gemini Flash implementation (default)."""
    ...

class ClaudeProvider(LLMProvider):
    """Anthropic Claude Haiku implementation."""
    ...

# Factory
def get_llm_provider(config: Settings) -> LLMProvider:
    providers = {"gemini": GeminiProvider, "claude": ClaudeProvider}
    return providers[config.LLM_PROVIDER](api_key=config.LLM_API_KEY)
```

### 6.5 Triage Agent safety rules (rule-based layer)

Before any LLM call, a deterministic rule engine checks for emergencies:

```python
RED_RULES = [
    # (pattern, condition)
    ("sugar > 400 or sugar < 50", "Dangerously abnormal glucose"),
    ("bp_systolic > 180 or bp_diastolic > 120", "Hypertensive crisis"),
    ("keywords: chest pain, breathing difficulty, unconscious, seizure", "Acute emergency"),
    ("sugar > 300 AND symptoms: dizzy/vomiting/blurred vision", "DKA risk"),
]
# If any rule matches → RED immediately, no LLM needed
# If no rule matches → LLM classifies as green/yellow/red with structured output
```

### 6.6 Phase 2 extension points

```python
# Stub agents registered but not implemented
class RecordsAgent(BaseAgent):
    async def handle(self, input: AgentInput) -> AgentOutput:
        raise NotImplementedError("Phase 2: Records processing")

class IntakeAgent(BaseAgent):
    async def handle(self, input: AgentInput) -> AgentOutput:
        raise NotImplementedError("Phase 2: Intake extraction")

class LifestyleAgent(BaseAgent):
    async def handle(self, input: AgentInput) -> AgentOutput:
        raise NotImplementedError("Phase 2: Lifestyle tips")
```

---

## 7. Missed-Dose Cron Job Flow

```
┌──────────────┐        ┌─────────────────────────┐        ┌───────────┐
│ cron-job.org │─POST──▶│ /internal/cron/          │        │ Firestore │
│ (every 10m)  │        │   missed-doses           │        │           │
└──────────────┘        │                          │        │           │
                        │ 1. Verify CRON_SECRET    │        │           │
                        │    header                │        │           │
                        │                          │        │           │
                        │ 2. Collection group query│──read─▶│           │
                        │    on dose_logs:         │        │           │
                        │    status == "pending"   │        │           │
                        │    AND scheduled_at      │        │           │
                        │    < now - GRACE_MINUTES │        │           │
                        │                          │        │           │
                        │ 3. For each missed dose: │        │           │
                        │    a. Mark as "missed"   │─write─▶│           │
                        │    b. Update daily       │─write─▶│           │
                        │       adherence summary  │        │           │
                        │    c. GuardianAlertAgent  │        │           │
                        │       .send_missed_dose  │        │           │
                        │       _alert(patient_id) │        │           │
                        │                          │        │           │
                        │ 4. Return { processed: N}│        │           │
                        └─────────────────────────┘        └───────────┘
                                     │
                                     ▼
                              ┌─────────────┐
                              │     FCM      │
                              │ (push to     │
                              │  guardian)   │
                              └─────────────┘
```

### Security for the cron endpoint

- **Not** behind Firebase Auth (no user token).
- Protected by a shared secret in the `X-Cron-Secret` header.
- The secret is set as an environment variable on both cron-job.org and the backend.
- The endpoint returns 403 if the secret doesn't match.
- Rate-limited to prevent abuse even if the secret leaks.

### Timing

- Cron runs every **10 minutes**.
- A dose is considered missed if `scheduled_time + MISSED_GRACE_MINUTES < now` and `status == "pending"`.
- `MISSED_GRACE_MINUTES` is an environment variable (default: 30). The grace period prevents false alerts when a user is just a few minutes late.
- The cron uses a collection-group query on `dose_logs` (not a per-user query), so cost scales with the number of overdue doses, not the number of users.

---

## 8. Notification Flow

### 8.1 Channel architecture (interface-based)

```python
class NotificationChannel(ABC):
    @abstractmethod
    async def send(self, recipient_id: str, message: NotificationMessage) -> bool:
        pass

class FCMChannel(NotificationChannel):
    """Push notification via Firebase Cloud Messaging. MVP default."""
    async def send(self, recipient_id: str, message: NotificationMessage) -> bool:
        # Look up FCM token for recipient
        # Send via firebase_admin.messaging
        ...

class WhatsAppChannel(NotificationChannel):
    """WhatsApp Business API. Phase 2 channel."""
    async def send(self, recipient_id: str, message: NotificationMessage) -> bool:
        raise NotImplementedError("WhatsApp channel: needs Business account + card")

class NotificationService:
    def __init__(self, channels: list[NotificationChannel]):
        self.channels = channels  # MVP: [FCMChannel]

    async def notify(self, recipient_id: str, message: NotificationMessage):
        for channel in self.channels:
            try:
                await channel.send(recipient_id, message)
            except Exception as e:
                logger.error(f"Channel {channel.__class__.__name__} failed: {e}")
                # Continue to next channel
```

### 8.2 Notification types

| Type | Trigger | Recipient | Channel (MVP) |
|------|---------|-----------|---------------|
| Medicine reminder | Scheduled time | Patient | Local notification (phone) |
| Missed dose follow-up | Scheduled + 15 min | Patient | Local notification |
| Missed dose alert | Cron job (30 min past) | Guardian | FCM push |
| Emergency (RED) | Triage agent | Guardian | FCM push |
| Yellow triage | Triage agent | Guardian | FCM push (summary only) |
| Appointment request | Patient action | Doctor | FCM push |
| Appointment confirmed | Doctor action | Patient | FCM push |
| Guardian invite | Patient action | Guardian | FCM push |
| Prescription uploaded | Doctor action | Patient | FCM push |

### 8.3 Medicine reminders (local, on-device)

- When a user adds/updates a medicine schedule, the Flutter app schedules local notifications via `flutter_local_notifications`.
- These work **offline** — no server involved.
- The schedule is synced from the backend on each medicine list fetch.
- A "Taken" action button on the notification calls `POST /medicines/doses` when tapped.

### 8.4 Guardian alert content (privacy rules)

For a RED (emergency) alert, the guardian receives **only**:

```json
{
  "type": "emergency",
  "title": "Emergency Alert",
  "body": "Rahela needs urgent help.",
  "data": {
    "patient_name": "Rahela Begum",
    "emergency_notice": "Very high sugar detected with symptoms",
    "latest_reading": { "type": "sugar", "value": 320, "unit": "mg/dL" },
    "location": { "lat": 23.8103, "lng": 90.4125 }
  }
}
```

Guardians **never** receive chat content, AI conversation details, or full medical history.

---

## 9. Error Handling Strategy

### 9.1 Backend error hierarchy

```python
class ShebaBondhuError(Exception):
    """Base exception for all app errors."""
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred"

class AuthenticationError(ShebaBondhuError):
    status_code = 401
    error_code = "AUTH_ERROR"

class AuthorizationError(ShebaBondhuError):
    status_code = 403
    error_code = "FORBIDDEN"

class NotFoundError(ShebaBondhuError):
    status_code = 404
    error_code = "NOT_FOUND"

class ValidationError(ShebaBondhuError):
    status_code = 422
    error_code = "VALIDATION_ERROR"

class RateLimitError(ShebaBondhuError):
    status_code = 429
    error_code = "RATE_LIMITED"

class LLMError(ShebaBondhuError):
    status_code = 503
    error_code = "LLM_UNAVAILABLE"
```

### 9.2 Standardized error response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Medicine name is required",
    "details": { "field": "name" },
    "request_id": "abc-123-def"
  }
}
```

### 9.3 Flutter error handling

- Dio interceptor catches HTTP errors and maps to typed exceptions.
- Riverpod `AsyncNotifier` exposes `AsyncValue` (loading / data / error).
- UI shows user-friendly error messages (in Bangla/English based on locale).
- Network errors → "No internet connection. Please try again."
- 503 (LLM down) → "AI assistant is temporarily unavailable. Please try again later."
- Retry with exponential backoff for transient failures (5xx, network).

### 9.4 LLM error fallback

- If the LLM call fails, the Triage Agent falls back to rule-based-only classification.
- If rules can't classify → respond with: "I couldn't process that right now. If you feel unwell, please contact a doctor or call 999."
- Never silently swallow an LLM failure during a health conversation.

---

## 10. Configuration and Environment Handling

### 10.1 Backend configuration

All config via environment variables (12-factor app). No secrets in code.

```
# .env.example (never committed)

# Firebase
FIREBASE_PROJECT_ID=shebabondhu-dev
GOOGLE_APPLICATION_CREDENTIALS=/app/firebase-service-account.json

# LLM
LLM_PROVIDER=gemini           # gemini | claude | openai
LLM_API_KEY=<key>
LLM_MODEL=                    # required, no default — must match provider's current model list
LLM_MAX_TOKENS_PER_REQUEST=500
LLM_DAILY_LIMIT_PER_USER=50   # rate limit

# Cron security
CRON_SECRET=<random-secret>

# Missed dose
MISSED_GRACE_MINUTES=30       # minutes after scheduled time before a dose is marked missed

# App
APP_ENV=development            # development | staging | production
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Sentry
SENTRY_DSN=<optional>
```

### 10.2 Flutter configuration

```dart
// Environments via --dart-define
// flutter run --dart-define=API_BASE_URL=http://localhost:8000
class AppConfig {
  static const apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000',
  );
}
```

### 10.3 Docker

```dockerfile
FROM python:3.12-slim
# Install WeasyPrint dependencies (pango, cairo, etc.)
# Install Noto Sans Bengali font
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY ./app /app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Render deploys directly from the Docker image.

---

## 11. Security and Privacy Measures

### 11.1 Data in transit

- All client-to-backend traffic over HTTPS (TLS 1.2+).
- Render provides free TLS certificates.
- Firebase Auth SDK uses HTTPS internally.
- HSTS headers enabled.

### 11.2 Data at rest

- Firestore encrypts data at rest by default (Google-managed keys).
- No health data is stored on the client device beyond the Firebase Auth token and cached UI state.
- Chat history is fetched from the server, not persisted locally.

### 11.3 Access control

| Layer | Mechanism |
|-------|-----------|
| Firestore | Security rules deny ALL client reads/writes. Only the service account (backend) can access. |
| API endpoints | Firebase ID token verified on every request. Role checked via dependency injection. |
| Guardian data | Patient must explicitly accept the guardian connection. Patient can revoke at any time. Guardian endpoints filter data to permitted fields only. |
| Doctor data | Patient must grant permission before the doctor can view the summary PDF. |
| Admin endpoints | Restricted to users with `role: "admin"`. Admin role is set manually in Firestore (not self-assignable). |

### 11.4 Firestore security rules (deny all client access)

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Deny all client access. Only the backend service account writes.
    match /{document=**} {
      allow read, write: if false;
    }
  }
}
```

### 11.5 Health data privacy

- **Minimal data collection:** Only health data necessary for the app's function is collected.
- **Consent required:** The registration flow includes a mandatory consent screen.
- **Guardian visibility is limited:** Guardians see medicine status, readings, alerts, and reports — never AI chat content.
- **Emergency override:** In a RED alert, the guardian receives the emergency notice, patient's location, and latest reading — regardless of other sharing settings.
- **LLM data handling:**
  - Development: Only fake/synthetic data sent to LLM free tier.
  - Production (when card available): Paid tier with data processing agreements.
  - Prompts include instructions not to store or learn from the conversation.
  - No patient-identifiable data in LLM prompts — use anonymized context.
- **No analytics on health data** without explicit opt-in consent.
- **Audit trail:** All data access is logged with user ID, action, and timestamp (via request logging middleware).

### 11.6 Rate limiting

- Per-user rate limits on all endpoints (configurable via env vars).
- Stricter limits on LLM-consuming endpoints (chat): e.g., 50 messages/user/day.
- Cron endpoint rate-limited to 10 calls/minute (prevents abuse).
- 429 responses include `Retry-After` header.

### 11.7 Input validation

- All inputs validated via Pydantic models with strict types and constraints.
- Chat messages sanitized before LLM prompt injection.
- Medicine names and readings validated against reasonable ranges.
- File uploads restricted (Phase 2) to specific types and sizes.

---

## 12. Assumptions Made

| # | Assumption | Impact if wrong |
|---|-----------|-----------------|
| 1 | Gemini Flash free tier is sufficient for development with fake data | May need to switch to another free-tier model |
| 2 | 10-minute cron interval is acceptable granularity for missed-dose checks | Could increase to 5 min if users want faster alerts |
| 3 | 30-minute grace period before a dose is "missed" | Configurable per medicine if needed later |
| 4 | Firestore Spark (50K reads/day, 20K writes/day) is enough for the pilot | Monitor closely; see firestore-schema.md for estimates |
| 5 | Render free tier is acceptable for development (15-min sleep) | Cold starts may frustrate during demos |
| 6 | Device speech recognition quality for Bangla is acceptable | May need to add a cloud STT fallback later |
| 7 | The admin panel is a separate minimal web app (not part of the Flutter app) | Could be a Flutter web build if preferred |
