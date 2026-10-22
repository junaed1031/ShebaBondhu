# ShebaBondhu: Repository Structure

Version 1.0 | 22 October 2026

---

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Python files | `snake_case` | `medicine_service.py` |
| Python classes | `PascalCase` | `MedicineService` |
| Dart files | `snake_case` | `medicine_list_screen.dart` |
| Dart classes | `PascalCase` | `MedicineListScreen` |
| API routes | `kebab-case` | `/medicine/dose-logs` |
| Firestore collections | `snake_case` | `dose_logs` |
| Environment variables | `UPPER_SNAKE_CASE` | `FIREBASE_PROJECT_ID` |
| Docker images | `kebab-case` | `shebabondhu-backend` |
| Feature folders | `snake_case` | `guardian_home` |
| Test files | `test_<module>.py` / `<name>_test.dart` | `test_medicine_service.py` |

---

## Monorepo Tree

```
ShebaBondhu/
│
├── docs/                                    # All planning and design documents
│   ├── ShebaBondhu_Project_Overview.md      # Product vision, UI, workflows
│   ├── ShebaBondhu_Tech_Stack.md            # Stack decisions, costs, gotchas
│   ├── architecture.md                      # System architecture
│   ├── repo-structure.md                    # This file
│   ├── firestore-schema.md                  # Database schema and access patterns
│   ├── api-spec.md                          # REST API specification
│   ├── build-plan.md                        # Ordered build slices
│   └── risks-and-open-questions.md          # Risk register
│
├── backend/                                 # FastAPI modular monolith
│   ├── Dockerfile                           # Production Docker image
│   ├── docker-compose.yml                   # Local dev with Firestore emulator
│   ├── requirements.txt                     # Pinned Python dependencies
│   ├── requirements-dev.txt                 # Dev/test dependencies (pytest, etc.)
│   ├── .env.example                         # Template for environment variables
│   ├── pytest.ini                           # Test configuration
│   │
│   ├── app/                                 # Application source code
│   │   ├── __init__.py
│   │   ├── main.py                          # FastAPI app factory, middleware, startup
│   │   │
│   │   ├── core/                            # Shared infrastructure
│   │   │   ├── __init__.py
│   │   │   ├── config.py                    # Pydantic Settings (env vars)
│   │   │   ├── auth.py                      # Firebase token verification dependency
│   │   │   ├── rbac.py                      # Role-based access control helpers
│   │   │   ├── middleware.py                # Logging, correlation ID, rate limiting
│   │   │   ├── exceptions.py               # Base exception hierarchy
│   │   │   ├── error_handlers.py            # FastAPI exception handlers
│   │   │   ├── firestore.py                 # Firestore client singleton
│   │   │   └── dependencies.py              # Shared FastAPI dependencies
│   │   │
│   │   ├── modules/                         # Domain modules (one per business area)
│   │   │   │
│   │   │   ├── auth/                        # Registration and login
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py                # POST /auth/register, POST /auth/login
│   │   │   │   ├── service.py               # Registration logic, profile creation
│   │   │   │   ├── schemas.py               # RegisterRequest, LoginResponse, etc.
│   │   │   │   └── repository.py            # User document CRUD
│   │   │   │
│   │   │   ├── profile/                     # Health profile management
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py                # GET/PATCH /profile, GET /me
│   │   │   │   ├── service.py               # Profile update logic
│   │   │   │   ├── schemas.py               # ProfileResponse, ProfileUpdateRequest
│   │   │   │   └── repository.py            # Profile read/write
│   │   │   │
│   │   │   ├── medicine/                    # Medicines, schedules, dose tracking
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py                # CRUD medicines, POST doses, GET adherence
│   │   │   │   ├── service.py               # Dose recording, adherence calculation
│   │   │   │   ├── schemas.py               # MedicineCreate, DoseLog, AdherenceSummary
│   │   │   │   └── repository.py            # Medicine + dose_log + adherence docs
│   │   │   │
│   │   │   ├── reading/                     # Sugar and blood pressure readings
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py                # POST readings, GET history, GET trends
│   │   │   │   ├── service.py               # Reading validation, trend calculation
│   │   │   │   ├── schemas.py               # ReadingCreate, ReadingTrend
│   │   │   │   └── repository.py            # Readings subcollection CRUD
│   │   │   │
│   │   │   ├── chat/                        # Sheba AI conversations
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py                # POST message, GET history
│   │   │   │   ├── service.py               # Message handling, orchestrator invocation
│   │   │   │   ├── schemas.py               # ChatMessage, ChatResponse
│   │   │   │   └── repository.py            # Chat session + message docs
│   │   │   │
│   │   │   ├── doctor/                      # Doctor profiles and search
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py                # GET search, GET profile, PATCH profile
│   │   │   │   ├── service.py               # Search logic, profile management
│   │   │   │   ├── schemas.py               # DoctorProfile, DoctorSearchResult
│   │   │   │   └── repository.py            # Doctor document queries
│   │   │   │
│   │   │   ├── appointment/                 # Appointment requests and management
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py                # POST request, PATCH status, GET list
│   │   │   │   ├── service.py               # Request/confirm/cancel logic
│   │   │   │   ├── schemas.py               # AppointmentRequest, AppointmentStatus
│   │   │   │   └── repository.py            # Appointment document CRUD
│   │   │   │
│   │   │   ├── guardian/                    # Guardian connections and data sharing
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py                # POST connect, GET patients, GET status
│   │   │   │   ├── service.py               # Invite code, accept/revoke logic
│   │   │   │   ├── schemas.py               # GuardianLink, PatientStatus
│   │   │   │   └── repository.py            # Guardian link docs, filtered patient data
│   │   │   │
│   │   │   ├── notification/                # Push notification management
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py                # PUT /notification/fcm-token, GET history
│   │   │   │   ├── service.py               # Channel orchestration, send logic
│   │   │   │   ├── schemas.py               # NotificationMessage, FCMTokenUpdate
│   │   │   │   ├── repository.py            # Notification log, FCM token storage
│   │   │   │   └── channels/                # Notification channel implementations
│   │   │   │       ├── __init__.py
│   │   │   │       ├── base.py              # NotificationChannel ABC
│   │   │   │       ├── fcm.py               # FCM push (MVP)
│   │   │   │       └── whatsapp.py          # WhatsApp Business API (stub, Phase 2)
│   │   │   │
│   │   │   ├── admin/                       # Admin operations
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py                # GET pending doctors, PATCH verify
│   │   │   │   ├── service.py               # Verification logic
│   │   │   │   ├── schemas.py               # DoctorVerification
│   │   │   │   └── repository.py            # Doctor status updates
│   │   │   │
│   │   │   ├── cron/                        # Internal cron endpoints
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py                # GET /internal/cron/missed-doses
│   │   │   │   ├── service.py               # Missed-dose detection and processing
│   │   │   │   └── schemas.py               # CronResult
│   │   │   │
│   │   │   └── pdf/                         # Doctor summary PDF generation
│   │   │       ├── __init__.py
│   │   │       ├── service.py               # Gather data, render PDF
│   │   │       ├── templates/               # Jinja2 HTML templates for WeasyPrint
│   │   │       │   └── doctor_summary.html  # PDF template with Bangla support
│   │   │       └── fonts/                   # Embedded Noto Sans Bengali font
│   │   │           └── NotoSansBengali.ttf
│   │   │
│   │   └── agents/                          # AI agent system
│   │       ├── __init__.py
│   │       ├── base.py                      # BaseAgent ABC, AgentInput, AgentOutput
│   │       ├── orchestrator.py              # Routes messages to the right agent
│   │       ├── triage.py                    # Safety rules + LLM symptom classification
│   │       ├── medicine.py                  # Medicine interaction checks, advice
│   │       ├── guardian_alert.py            # Decides and sends guardian notifications
│   │       ├── doctor_match.py              # Doctor suggestions, PDF trigger
│   │       ├── prompts/                     # System prompts and prompt templates
│   │       │   ├── triage_prompt.py         # Triage classification prompt
│   │       │   ├── orchestrator_prompt.py   # Intent classification prompt
│   │       │   └── doctor_match_prompt.py   # Doctor recommendation prompt
│   │       ├── safety_rules.py              # Deterministic red/yellow rules
│   │       ├── llm/                         # Provider-agnostic LLM wrapper
│   │       │   ├── __init__.py
│   │       │   ├── base.py                  # LLMProvider ABC
│   │       │   ├── gemini.py                # Google Gemini implementation
│   │       │   ├── claude.py                # Anthropic Claude implementation
│   │       │   └── factory.py               # Provider factory from config
│   │       └── stubs/                       # Phase 2 agent stubs
│   │           ├── records.py               # Records Agent (not implemented)
│   │           ├── intake.py                # Intake Agent (not implemented)
│   │           └── lifestyle.py             # Lifestyle Agent (not implemented)
│   │
│   └── tests/                               # Backend tests
│       ├── conftest.py                      # Fixtures: test client, mock Firestore
│       ├── unit/                            # Unit tests (service + agent logic)
│       │   ├── test_auth_service.py
│       │   ├── test_medicine_service.py
│       │   ├── test_triage_agent.py
│       │   ├── test_safety_rules.py
│       │   └── ...
│       ├── integration/                     # Integration tests (API endpoints)
│       │   ├── test_auth_endpoints.py
│       │   ├── test_medicine_endpoints.py
│       │   └── ...
│       └── fixtures/                        # Shared test data
│           ├── users.py                     # Sample user documents
│           ├── medicines.py                 # Sample medicine data
│           └── readings.py                  # Sample sugar/BP readings
│
├── mobile/                                  # Flutter app
│   ├── pubspec.yaml                         # Dependencies
│   ├── analysis_options.yaml                # Lint rules
│   ├── android/                             # Android platform files
│   ├── ios/                                 # iOS platform files (future)
│   │
│   ├── lib/                                 # Dart source code
│   │   ├── main.dart                        # App entry point, provider scope
│   │   │
│   │   ├── core/                            # Shared app infrastructure
│   │   │   ├── config/
│   │   │   │   └── app_config.dart          # API URL, env settings
│   │   │   ├── theme/
│   │   │   │   ├── app_theme.dart           # Light/dark theme definitions
│   │   │   │   ├── app_colors.dart          # Color palette
│   │   │   │   └── app_typography.dart      # Text styles, Bangla font config
│   │   │   ├── routing/
│   │   │   │   ├── app_router.dart          # GoRouter config with guards
│   │   │   │   └── route_names.dart         # Named route constants
│   │   │   ├── network/
│   │   │   │   ├── api_client.dart          # Dio singleton + interceptors
│   │   │   │   ├── auth_interceptor.dart    # Attaches Firebase ID token
│   │   │   │   └── api_exceptions.dart      # Typed HTTP error mapping
│   │   │   ├── l10n/
│   │   │   │   ├── app_bn.arb              # Bangla strings
│   │   │   │   └── app_en.arb              # English strings
│   │   │   └── utils/
│   │   │       ├── date_utils.dart          # Bangla/English date formatting
│   │   │       ├── validators.dart          # Form validation helpers
│   │   │       └── constants.dart           # App-wide constants
│   │   │
│   │   ├── features/                        # Feature modules
│   │   │   ├── auth/
│   │   │   │   ├── data/
│   │   │   │   │   ├── auth_repository.dart   # API calls for register/login
│   │   │   │   │   └── auth_models.dart       # Request/response models
│   │   │   │   ├── providers/
│   │   │   │   │   └── auth_provider.dart     # Auth state + token management
│   │   │   │   └── screens/
│   │   │   │       ├── login_screen.dart       # Email/Google sign-in
│   │   │   │       ├── register_step1_screen.dart # Account basics
│   │   │   │       ├── register_step2_screen.dart # Health profile (optional)
│   │   │   │       └── consent_screen.dart    # Data usage consent
│   │   │   │
│   │   │   ├── home/
│   │   │   │   ├── data/
│   │   │   │   │   └── dashboard_repository.dart
│   │   │   │   ├── providers/
│   │   │   │   │   └── dashboard_provider.dart
│   │   │   │   ├── screens/
│   │   │   │   │   └── home_screen.dart       # Patient dashboard
│   │   │   │   └── widgets/
│   │   │   │       ├── medicine_card.dart      # Today's doses
│   │   │   │       ├── health_snapshot.dart    # Latest readings
│   │   │   │       ├── tip_card.dart           # Daily tip (static in MVP)
│   │   │   │       └── sos_button.dart         # Emergency quick access
│   │   │   │
│   │   │   ├── chat/
│   │   │   │   ├── data/
│   │   │   │   │   ├── chat_repository.dart
│   │   │   │   │   └── chat_models.dart
│   │   │   │   ├── providers/
│   │   │   │   │   └── chat_provider.dart
│   │   │   │   ├── screens/
│   │   │   │   │   └── chat_screen.dart       # Sheba AI chat interface
│   │   │   │   └── widgets/
│   │   │   │       ├── message_bubble.dart     # Chat message display
│   │   │   │       ├── voice_input_button.dart # Bangla/English STT
│   │   │   │       ├── severity_banner.dart    # Green/yellow/red indicator
│   │   │   │       └── emergency_card.dart     # Hospital list + 999
│   │   │   │
│   │   │   ├── medicine/
│   │   │   │   ├── data/
│   │   │   │   │   ├── medicine_repository.dart
│   │   │   │   │   └── medicine_models.dart
│   │   │   │   ├── providers/
│   │   │   │   │   └── medicine_provider.dart
│   │   │   │   ├── screens/
│   │   │   │   │   ├── medicine_list_screen.dart # All medicines + schedule
│   │   │   │   │   ├── add_medicine_screen.dart  # Manual medicine entry
│   │   │   │   │   └── adherence_screen.dart     # Weekly adherence chart
│   │   │   │   └── widgets/
│   │   │   │       ├── dose_tile.dart
│   │   │   │       └── adherence_chart.dart
│   │   │   │
│   │   │   ├── reading/
│   │   │   │   ├── data/
│   │   │   │   │   ├── reading_repository.dart
│   │   │   │   │   └── reading_models.dart
│   │   │   │   ├── providers/
│   │   │   │   │   └── reading_provider.dart
│   │   │   │   ├── screens/
│   │   │   │   │   ├── add_reading_screen.dart    # Sugar or BP entry
│   │   │   │   │   └── reading_history_screen.dart # Trend chart + history
│   │   │   │   └── widgets/
│   │   │   │       └── trend_chart.dart
│   │   │   │
│   │   │   ├── doctor/
│   │   │   │   ├── data/
│   │   │   │   │   ├── doctor_repository.dart
│   │   │   │   │   └── doctor_models.dart
│   │   │   │   ├── providers/
│   │   │   │   │   └── doctor_provider.dart
│   │   │   │   ├── screens/
│   │   │   │   │   ├── doctor_search_screen.dart  # Search by specialty/area
│   │   │   │   │   ├── doctor_profile_screen.dart # Doctor detail view
│   │   │   │   │   └── appointment_list_screen.dart
│   │   │   │   └── widgets/
│   │   │   │       └── doctor_card.dart
│   │   │   │
│   │   │   ├── family/
│   │   │   │   ├── data/
│   │   │   │   │   ├── guardian_repository.dart
│   │   │   │   │   └── guardian_models.dart
│   │   │   │   ├── providers/
│   │   │   │   │   └── guardian_provider.dart
│   │   │   │   ├── screens/
│   │   │   │   │   ├── family_screen.dart         # Guardian list
│   │   │   │   │   ├── invite_screen.dart         # Show/share invite code
│   │   │   │   │   └── connect_screen.dart        # Enter invite code
│   │   │   │   └── widgets/
│   │   │   │       └── guardian_card.dart
│   │   │   │
│   │   │   ├── profile/
│   │   │   │   ├── data/
│   │   │   │   │   └── profile_repository.dart
│   │   │   │   ├── providers/
│   │   │   │   │   └── profile_provider.dart
│   │   │   │   └── screens/
│   │   │   │       ├── profile_screen.dart        # View/edit health profile
│   │   │   │       └── settings_screen.dart       # Language, logout
│   │   │   │
│   │   │   ├── guardian_home/
│   │   │   │   ├── data/
│   │   │   │   │   └── guardian_dashboard_repository.dart
│   │   │   │   ├── providers/
│   │   │   │   │   └── guardian_dashboard_provider.dart
│   │   │   │   ├── screens/
│   │   │   │   │   └── guardian_dashboard_screen.dart  # Patient status view
│   │   │   │   └── widgets/
│   │   │   │       ├── patient_medicine_status.dart
│   │   │   │       ├── patient_readings.dart
│   │   │   │       └── alert_history.dart
│   │   │   │
│   │   │   ├── doctor_home/
│   │   │   │   ├── data/
│   │   │   │   │   └── doctor_dashboard_repository.dart
│   │   │   │   ├── providers/
│   │   │   │   │   └── doctor_dashboard_provider.dart
│   │   │   │   ├── screens/
│   │   │   │   │   ├── doctor_dashboard_screen.dart   # Appointment requests
│   │   │   │   │   └── patient_summary_screen.dart    # View patient PDF
│   │   │   │   └── widgets/
│   │   │   │       └── appointment_request_card.dart
│   │   │   │
│   │   │   └── emergency/
│   │   │       ├── data/
│   │   │       │   └── emergency_repository.dart
│   │   │       ├── screens/
│   │   │       │   └── emergency_screen.dart      # SOS: hospitals, 999, alert
│   │   │       └── widgets/
│   │   │           └── hospital_list.dart         # Curated list + distance
│   │   │
│   │   └── shared/                              # Cross-feature shared code
│   │       ├── widgets/
│   │       │   ├── loading_overlay.dart
│   │       │   ├── error_banner.dart
│   │       │   ├── role_badge.dart
│   │       │   └── bangla_text.dart              # Bangla text rendering helper
│   │       ├── models/
│   │       │   └── user_model.dart               # Shared user/role model
│   │       └── providers/
│   │           ├── user_provider.dart             # Current user state
│   │           └── locale_provider.dart           # Language selection
│   │
│   ├── test/                                    # Flutter tests
│   │   ├── unit/                                # Provider and model tests
│   │   ├── widget/                              # Widget tests
│   │   └── integration/                         # Integration/E2E tests
│   │
│   └── assets/                                  # Static assets
│       ├── images/                              # App images, icons
│       ├── fonts/                               # Bundled Bangla fonts
│       │   └── NotoSansBengali/
│       ├── hospitals/                           # Curated hospital list JSON
│       │   └── hospitals_bd.json
│       └── l10n/                                # Generated localization
│
├── admin/                                       # Minimal admin web panel
│   ├── index.html                               # Single-page admin UI
│   ├── style.css                                # Admin panel styles
│   └── app.js                                   # Doctor verification logic
│   # NOTE: The admin panel is a minimal static site.
│   # It uses Firebase Auth (admin email login) and calls
│   # the same FastAPI backend endpoints.
│   # Alternative: build as Flutter web from the same codebase.
│
├── .github/                                     # CI/CD configuration
│   └── workflows/
│       ├── backend-ci.yml                       # Lint + test backend on PR
│       └── mobile-ci.yml                        # Lint + test Flutter on PR
│
├── .gitignore                                   # Git ignore rules
├── LICENSE                                      # MIT License
└── README.md                                    # Project overview and setup guide
```

---

## Notes

1. **Phase 2 stubs** exist in `backend/app/agents/stubs/` — they raise `NotImplementedError` and serve as extension points for Records, Intake, and Lifestyle agents.

2. **The admin panel** (`admin/`) is a minimal HTML/CSS/JS page for doctor verification. It authenticates via Firebase Auth (admin email) and calls the same FastAPI endpoints. This avoids adding a full framework for a single admin screen.

3. **Hospital data** (`mobile/assets/hospitals/hospitals_bd.json`) is a curated static list of major hospitals in Bangladesh with name, address, latitude, longitude, and phone number. The app calculates distance using the device GPS. Google Maps is opened for directions.

4. **Localization** files (`app_bn.arb`, `app_en.arb`) use Flutter's `intl` package. Every user-facing string goes through localization — no hardcoded strings.

5. **Each feature folder** in Flutter follows the same `data/ → providers/ → screens/ → widgets/` structure for consistency and discoverability.
