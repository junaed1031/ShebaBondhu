# ShebaBondhu: Build Plan

Version 1.0 | 22 October 2026

---

## Approach

Each **slice** is a vertical feature: backend endpoints + Firestore documents + Flutter screens + tests. Every slice produces a working, testable increment. Effort is calibrated for a **solo developer** working part-time (~3–4 hours/day).

**Effort key:**
- 🟢 S = 1–2 days
- 🟡 M = 3–5 days
- 🔴 L = 6–10 days

---

## Phase 0: Project Setup

### Slice 0.1 — Monorepo scaffold

**Effort:** 🟢 S (1 day)

**What to build:**
- Create the monorepo structure as per `repo-structure.md`
- Initialize `backend/` with FastAPI + Docker + `requirements.txt`
- Initialize `mobile/` with Flutter (`flutter create`)
- Setup `.gitignore`, `README.md`
- Create Firebase project, download config files
- Set up Firestore emulator for local development
- Create `docker-compose.yml` for backend + emulator
- Deploy "Hello World" FastAPI to Render free tier

**Acceptance criteria:**
- [ ] `docker compose up` starts the backend and Firestore emulator
- [ ] `GET /health` returns `{ "status": "ok" }` locally
- [ ] Flutter app runs on Android emulator
- [ ] Render deployment succeeds (free tier)
- [ ] Firebase project created with Auth, Firestore, FCM enabled

**Tests:**
- Backend: `test_health_endpoint` returns 200

---

### Slice 0.2 — Core infrastructure

**Effort:** 🟡 M (3 days)

**What to build:**
- **Backend:**
  - Firebase Admin SDK initialization
  - Auth middleware (verify Firebase ID token)
  - RBAC dependency (`require_role`)
  - Exception hierarchy + global error handlers
  - Pydantic `Settings` class (config from env vars)
  - Request logging middleware with correlation IDs
  - Firestore client singleton
  - Base repository class
- **Flutter:**
  - Riverpod setup (`ProviderScope`)
  - Dio client with auth interceptor (attaches ID token, handles 401 refresh)
  - GoRouter setup with auth guard
  - App theme (colors, typography, Noto Sans Bengali font)
  - L10n setup with Bangla and English ARB files (a few sample strings)

**Acceptance criteria:**
- [ ] Unauthenticated requests return 401
- [ ] Invalid tokens return 401
- [ ] Requests with wrong role return 403
- [ ] Error responses follow the standard envelope format
- [ ] Flutter app shows a placeholder screen with Bangla text correctly rendered
- [ ] Dio interceptor attaches token and handles refresh

**Tests:**
- Backend: `test_auth_middleware_rejects_no_token`, `test_auth_middleware_rejects_bad_token`, `test_rbac_rejects_wrong_role`
- Flutter: Widget test for theme rendering

---

## Phase 1: Walking Skeleton (Auth → Profile)

### Slice 1.1 — Registration + Profile fetch + FCM token

**Effort:** 🟡 M (4 days)

**What to build:**
- **Backend:**
  - `POST /auth/register` — create user doc in Firestore (accepted roles: `patient`, `guardian`, `doctor`; doctors start with `verification_status = "pending"`)
  - `GET /me` — return current user profile. Returns `404 NOT_REGISTERED` if no user doc exists (not 401).
  - `POST /me/consent` — record consent
  - `PUT /notifications/fcm-token` — register/update FCM device token
  - Two auth dependencies: `get_firebase_user` (token only, for `/auth/register` and `GET /me`) and `get_current_user` (token + user doc, for all other endpoints)
  - User repository (CRUD for `users` collection)
  - FCM token repository
- **Flutter:**
  - Login screen (email + Google sign-in via Firebase Auth)
  - Registration Step 1 screen (name, DOB, gender, role, language)
  - Consent screen
  - Auth state provider (watches Firebase Auth, redirects)
  - Post-login flow: call `GET /me`, if 404 → redirect to register
  - FCM token registration on app startup via `PUT /notifications/fcm-token`

**Acceptance criteria:**
- [ ] New user: Google sign-in → `GET /me` returns 404 → register screen → consent → home (placeholder)
- [ ] Returning user: Google sign-in → `GET /me` returns profile → home
- [ ] Email sign-up works
- [ ] User document appears in Firestore (or emulator)
- [ ] Role is stored correctly (patient, guardian, doctor)
- [ ] Doctor registration sets `verification_status = "pending"`
- [ ] `admin` role is rejected at registration
- [ ] Consent timestamp is recorded
- [ ] FCM token is stored on login

**Tests:**
- Backend: `test_register_creates_user`, `test_register_duplicate_409`, `test_register_rejects_admin_role`, `test_get_me_returns_profile`, `test_get_me_unregistered_404`, `test_fcm_token_update`
- Flutter: Widget test for login screen, integration test for sign-in flow

---

### Slice 1.2 — Profile completion (Step 2)

**Effort:** 🟢 S (2 days)

**What to build:**
- **Backend:**
  - `PATCH /me` — update profile fields
- **Flutter:**
  - Registration Step 2 screen (conditions, allergies, medicines, blood group, height, weight, emergency contact)
  - Profile view/edit screen
  - "Skip for now" option

**Acceptance criteria:**
- [ ] Patient can fill health profile after registration
- [ ] Profile can be edited later from Profile screen
- [ ] Guardian registration is shorter (no health fields)
- [ ] Doctor registration shows BMDC number + specialty fields

**Tests:**
- Backend: `test_update_profile`, `test_update_profile_validation`

---

## Phase 2: Medicine Core

### Slice 2.1 — Medicine CRUD + schedule

**Effort:** 🟡 M (4 days)

**What to build:**
- **Backend:**
  - `POST /medicines` — add medicine
  - `GET /medicines` — list medicines
  - `PATCH /medicines/{id}` — update
  - `DELETE /medicines/{id}` — deactivate
  - `POST /internal/cron/generate-doses` — create daily dose_logs with deterministic IDs (`{date}_{time}_{medicine_id}`)
  - Medicine and dose_log repositories
- **Flutter:**
  - Medicine list screen
  - Add medicine screen (name, dose, frequency, times)
  - Medicine detail/edit screen
  - Local notification scheduling (flutter_local_notifications)

**Acceptance criteria:**
- [ ] Patient adds a medicine with schedule
- [ ] Medicine appears in list with correct times
- [ ] Editing a medicine updates future doses
- [ ] Deactivating a medicine sets `is_active = false`
- [ ] Local notification fires at scheduled time
- [ ] Daily dose generation cron creates correct dose_logs with deterministic IDs
- [ ] Re-running the cron is idempotent (existing dose_logs not overwritten)

**Tests:**
- Backend: `test_add_medicine`, `test_list_medicines`, `test_generate_daily_doses`
- Flutter: Widget test for medicine list, add form

---

### Slice 2.2 — Dose tracking + adherence

**Effort:** 🟡 M (4 days)

**What to build:**
- **Backend:**
  - `GET /medicines/doses/today` — today's doses with status (lazy generation: creates dose_logs if they don't exist)
  - `POST /medicines/doses` — mark dose as taken (allows `pending|missed → taken`; adds `taken_late` boolean)
  - `GET /medicines/adherence` — weekly adherence from daily_summaries
  - Daily summary update logic (on dose taken, including missed→taken correction)
  - Adherence calculation: `adherence_pct` computed only over doses already due (taken + missed + overdue pending). If nothing is due yet, status is green.
  - Environment variable: `MISSED_GRACE_MINUTES` (default: 30)
- **Flutter:**
  - Home dashboard medicine card with "Taken" buttons
  - Today's dose list (pending/taken/missed status)
  - Weekly adherence chart (fl_chart)
  - Notification action button "Taken" → calls API

**Acceptance criteria:**
- [ ] Patient sees today's doses on home screen
- [ ] `GET /medicines/doses/today` lazily generates dose_logs if they don't exist
- [ ] Tapping "Taken" on a pending dose marks it taken and updates summary
- [ ] Tapping "Taken" on a missed dose transitions it to taken with `taken_late = true`, adjusts daily summary (missed-1, taken+1), and sends guardian a "dose taken" push
- [ ] Weekly adherence shows last 7 days with color coding
- [ ] Adherence percentage is calculated only over due doses
- [ ] Before any dose is due, adherence status is green

**Tests:**
- Backend: `test_record_dose`, `test_record_dose_from_missed`, `test_adherence_calculation_due_only`, `test_lazy_dose_generation`
- Flutter: Widget test for dose card, adherence chart

---

### Slice 2.3 — Missed-dose cron + guardian alert

**Effort:** 🟡 M (3 days)

> **Dependency:** Slice 6.1 (guardian connection) should be completed before this slice, so guardians can receive alerts.

**What to build:**
- **Backend:**
  - `POST /internal/cron/missed-doses` — detect and process missed doses using a collection-group query on `dose_logs` (`status == "pending" AND scheduled_at < now - MISSED_GRACE_MINUTES`)
  - Cron secret auth middleware
  - Guardian Alert Agent (MVP: sends FCM push)
  - FCM notification channel implementation
  - Alert repository (log all alerts)
  - Required Firestore index: collection-group composite on `dose_logs` (`status` ASC, `scheduled_at` ASC)
- **Setup:**
  - Register cron-job.org to call the endpoint every 10 minutes (POST, not GET)
- **Flutter:**
  - Receive and display FCM push notifications

**Acceptance criteria:**
- [ ] Dose not taken after MISSED_GRACE_MINUTES → marked "missed" by cron
- [ ] Guardian receives push notification for missed dose
- [ ] Cron endpoint rejects requests without valid secret
- [ ] Cron endpoint uses POST method
- [ ] Collection-group query works across all users' dose_logs
- [ ] Alert is logged in Firestore
- [ ] FCM push is received and displayed on guardian's device

**Tests:**
- Backend: `test_missed_dose_detection`, `test_cron_auth_rejects_bad_secret`, `test_guardian_alert_sent`, `test_collection_group_query`

---

## Phase 3: Health Readings

### Slice 3.1 — Sugar and BP entry + trends

**Effort:** 🟡 M (3 days)

**What to build:**
- **Backend:**
  - `POST /readings` — add sugar or BP reading
  - `GET /readings` — reading history with trend
  - Reading validation (reasonable ranges)
  - Daily summary update on new reading
  - If reading triggers safety rule → raise event (for future triage integration)
- **Flutter:**
  - Add reading screen (sugar or BP toggle)
  - Reading history with trend chart
  - Health snapshot card on home dashboard

**Acceptance criteria:**
- [ ] Patient enters sugar reading → stored and visible
- [ ] Patient enters BP reading (systolic + diastolic) → stored
- [ ] Out-of-range values are rejected with clear error
- [ ] Trend chart shows last 7–30 days
- [ ] Home dashboard shows latest reading
- [ ] Daily summary updates with latest reading

**Tests:**
- Backend: `test_add_sugar_reading`, `test_add_bp_reading`, `test_reading_validation`, `test_trend_calculation`

---

## Phase 4: Sheba AI Chat

### Slice 4.1 — Chat infrastructure + basic LLM

**Effort:** 🟡 M (5 days)

**What to build:**
- **Backend:**
  - `POST /chat/messages` — send message, get AI response
  - `GET /chat/sessions` — list sessions
  - `GET /chat/sessions/{id}/messages` — message history
  - Chat session and message repositories
  - LLM wrapper (provider-agnostic interface)
  - Gemini Flash provider implementation
  - Orchestrator agent (basic: route all to LLM with health system prompt)
  - Rate limiting (50 messages/user/day)
- **Flutter:**
  - Chat screen with message bubbles
  - Text input + send button
  - Session list
  - Loading state while LLM responds

**Acceptance criteria:**
- [ ] Patient sends message → receives AI response
- [ ] Chat history persists across app restarts
- [ ] Multiple sessions supported
- [ ] Response includes Bangla text correctly
- [ ] Rate limit enforced at 50/day
- [ ] LLM failure → graceful error message (not crash)

**Tests:**
- Backend: `test_send_message`, `test_chat_history`, `test_rate_limit`, `test_llm_wrapper_gemini`, `test_llm_fallback_on_error`

---

### Slice 4.2 — Triage Agent + safety rules

**Effort:** 🟡 M (5 days)

**What to build:**
- **Backend:**
  - Triage Agent with rule-based safety layer
  - Red/yellow/green classification
  - Integration with Orchestrator (symptom → Triage)
  - Emergency event handling → Guardian Alert Agent
  - Update chat response with severity metadata
- **Flutter:**
  - Severity banner on chat messages (green/yellow/red)
  - Red alert: emergency card with hospitals + 999
  - Yellow alert: doctor recommendation prompt
  - Voice input (speech_to_text for Bangla/English)

**Acceptance criteria:**
- [ ] "My sugar is 450 and I feel dizzy" → RED (rule-based, no LLM needed)
- [ ] "I have a mild headache" → GREEN (LLM classifies)
- [ ] "I've had chest pain for 2 hours" → RED (keyword rule)
- [ ] RED → emergency card shown + guardian push notification
- [ ] YELLOW → "Consider seeing a doctor" + doctor suggestion
- [ ] Voice input in Bangla → transcribed → sent as message
- [ ] LLM failure → rule-based fallback only

**Tests:**
- Backend: `test_red_rules_sugar_high`, `test_red_rules_keywords`, `test_llm_triage_green`, `test_emergency_triggers_guardian_alert`
- Flutter: Widget test for severity banner, emergency card

---

### Slice 4.3 — Medicine Agent integration

**Effort:** 🟢 S (2 days)

**What to build:**
- **Backend:**
  - Medicine Agent: answers medicine questions using patient's medicine list
  - Orchestrator routing: medicine-related intent → Medicine Agent
  - Basic interaction check (warn about known dangerous combinations)

**Acceptance criteria:**
- [ ] "When should I take Metformin?" → checks schedule, responds correctly
- [ ] "Can I take X with Y?" → checks for known interactions, warns if found
- [ ] Non-medicine questions are NOT routed to Medicine Agent

**Tests:**
- Backend: `test_medicine_agent_schedule_query`, `test_medicine_agent_interaction_check`, `test_orchestrator_routing`

---

## Phase 5: Doctor & Appointments

### Slice 5.1 — Doctor search + profiles

**Effort:** 🟡 M (3 days)

**What to build:**
- **Backend:**
  - `GET /doctors/search` — search by specialty + city/area
  - `GET /doctors/{id}` — doctor profile
  - `PATCH /doctors/me` — doctor updates own profile
- **Flutter:**
  - Doctor search screen (specialty dropdown + city/area filter)
  - Doctor profile card
  - Doctor profile edit (for doctor role)

**Acceptance criteria:**
- [ ] Search returns only verified doctors
- [ ] Filter by specialty works
- [ ] Filter by city/area works
- [ ] Doctor can update their chamber address and fee info

**Tests:**
- Backend: `test_doctor_search_by_specialty`, `test_doctor_search_excludes_unverified`, `test_doctor_profile_update`

---

### Slice 5.2 — Appointments + prescriptions

**Effort:** 🟡 M (4 days)

**What to build:**
- **Backend:**
  - `POST /appointments` — patient requests
  - `GET /appointments` — list by role
  - `PATCH /appointments/{id}` — status transitions
  - `POST /appointments/{id}/prescription` — doctor uploads
  - `POST /appointments/{id}/prescription/confirm` — patient adds to medicines
  - FCM notifications for status changes
- **Flutter:**
  - Appointment request screen (from doctor profile)
  - Appointment list screen
  - Doctor dashboard: incoming requests, confirm/cancel
  - Prescription review screen (patient confirms → medicines added)

**Acceptance criteria:**
- [ ] Patient requests appointment → doctor gets push notification
- [ ] Doctor confirms → patient notified + status updated
- [ ] Doctor uploads prescription → patient notified
- [ ] Patient confirms prescription → medicines added to their list + dose logs created
- [ ] Status transitions are enforced (no invalid changes)

**Tests:**
- Backend: `test_create_appointment`, `test_appointment_status_transitions`, `test_prescription_upload`, `test_prescription_confirm_adds_medicines`

---

### Slice 5.3 — Doctor Match Agent + PDF

**Effort:** 🟡 M (4 days)

**What to build:**
- **Backend:**
  - Doctor Match Agent (suggests doctors based on conditions + triage)
  - `GET /doctors/suggestions` — AI-powered recommendations
  - `GET /pdf/doctor-summary` — generate PDF for patient
  - `GET /pdf/doctor-summary/{patient_id}` — doctor views (with permission)
  - WeasyPrint template with Bangla font
  - PDF includes: profile, conditions, medicines, readings, adherence, symptom summary
- **Flutter:**
  - Doctor suggestion cards (in chat after yellow triage)
  - "Generate Summary" button (chat tab + doctor tab)
  - PDF viewer / share

**Acceptance criteria:**
- [ ] After yellow triage → doctor suggestions shown in chat
- [ ] PDF generates correctly with Bangla text
- [ ] PDF includes all required sections
- [ ] Doctor can only view PDF if patient allows (`patient_allows_summary`)
- [ ] PDF is not stored — generated fresh each time

**Tests:**
- Backend: `test_doctor_match_suggestions`, `test_pdf_generation`, `test_pdf_bangla_rendering`, `test_pdf_access_denied_without_permission`

---

## Phase 6: Guardian System

### Slice 6.1 — Guardian connection flow

**Effort:** 🟡 M (4 days)

**What to build:**
- **Backend:**
  - `POST /guardian/invite-code` — generate code
  - `POST /guardian/connect` — guardian uses code
  - `PATCH /guardian/links/{id}` — patient accepts/declines
  - `DELETE /guardian/links/{id}` — patient revokes
  - `GET /guardian/my-guardians`, `GET /guardian/my-patients`
  - Invite code repository (with expiry)
  - Guardian link repository
- **Flutter:**
  - Family tab (patient): list guardians, invite button
  - Invite screen: show code, share button
  - Connect screen (guardian): enter code
  - Accept/decline notification handling
  - Revoke access button

**Acceptance criteria:**
- [ ] Patient generates invite code (valid 48 hours)
- [ ] Guardian enters code → request sent to patient
- [ ] Patient accepts → guardian sees patient in their list
- [ ] Patient revokes → guardian loses access immediately
- [ ] Expired/used codes are rejected
- [ ] Previous code is invalidated when a new one is generated

**Tests:**
- Backend: `test_generate_invite_code`, `test_connect_with_code`, `test_accept_guardian`, `test_revoke_guardian`, `test_expired_code_rejected`

---

### Slice 6.2 — Guardian dashboard

**Effort:** 🟡 M (3 days)

**What to build:**
- **Backend:**
  - `GET /guardian/patients/{id}/status` — patient status (today's summary)
  - `GET /guardian/patients/{id}/readings` — patient readings (trend)
  - `GET /guardian/alerts` — alert history
  - Privacy enforcement: guardian sees only permitted data
- **Flutter:**
  - Guardian dashboard screen (per patient)
  - Medicine status card (green/yellow/red)
  - Latest readings card with trend
  - Alert history list
  - WhatsApp call button (`url_launcher` → `wa.me/...`)
  - Doctor suggestion button (links to doctor search)

**Acceptance criteria:**
- [ ] Guardian sees patient's today adherence status
- [ ] Guardian sees latest sugar and BP readings
- [ ] Guardian sees alert history (missed doses, emergencies)
- [ ] Guardian can call patient via WhatsApp
- [ ] Guardian CANNOT see chat history
- [ ] Revoked guardian gets 403 on all patient endpoints

**Tests:**
- Backend: `test_guardian_sees_status`, `test_guardian_cannot_see_chats`, `test_revoked_guardian_403`

---

## Phase 7: Emergency & Admin

### Slice 7.1 — Emergency handling

**Effort:** 🟢 S (2 days)

**What to build:**
- **Backend:**
  - `GET /emergency/hospitals` — curated list sorted by distance
  - `POST /emergency/alert` — manual SOS button trigger
- **Flutter:**
  - SOS button on home dashboard (always visible)
  - Emergency screen: hospital list, 999 call button, guardian alert status
  - Curated hospital JSON asset (`hospitals_bd.json`)
  - Distance calculation using geolocator

**Acceptance criteria:**
- [ ] SOS button triggers guardian push with location + latest reading
- [ ] Hospital list shows nearest 5 hospitals with distance
- [ ] Tapping hospital opens Google Maps
- [ ] 999 call button opens phone dialer
- [ ] Works even if GPS is unavailable (shows all hospitals without sorting)

**Tests:**
- Backend: `test_hospitals_sorted_by_distance`, `test_manual_sos_alert`
- Flutter: Widget test for SOS button, emergency screen

---

### Slice 7.2 — Admin panel

**Effort:** 🟢 S (2 days)

**What to build:**
- **Backend:**
  - `GET /admin/doctors/pending` — list unverified doctors
  - `PATCH /admin/doctors/{id}/verify` — approve/reject
  - `GET /admin/users` — list users by role
- **Admin panel:**
  - Minimal HTML/CSS/JS page
  - Firebase Auth (admin email sign-in)
  - Table of pending doctors with approve/reject buttons
  - Basic user list

**Acceptance criteria:**
- [ ] Admin logs in via Firebase Auth
- [ ] Pending doctors are listed with BMDC number
- [ ] Approve → doctor becomes searchable
- [ ] Reject → doctor is notified, stays hidden from search
- [ ] Non-admin users get 403

**Tests:**
- Backend: `test_admin_list_pending`, `test_admin_approve_doctor`, `test_admin_reject_doctor`, `test_non_admin_403`

---

## Phase 8: Polish & Launch Prep

### Slice 8.1 — Notifications polish

**Effort:** 🟢 S (2 days)

**What to build:**
- `GET /notifications` — notification history
- `PATCH /notifications/{id}/read` — mark as read
- Notification badge count on app
- Deep linking from push notifications to relevant screen

> **Note:** `PUT /notifications/fcm-token` is implemented in Slice 1.1.

**Acceptance criteria:**
- [ ] FCM token updates on every app launch (already from 1.1)
- [ ] Notification history screen lists all past notifications
- [ ] Tapping a push notification opens the relevant screen
- [ ] Unread count badge on notification bell

---

### Slice 8.2 — Localization + UI polish

**Effort:** 🟡 M (3 days)

**What to build:**
- Complete all Bangla translations in ARB files
- Bangla date/time formatting throughout
- Responsive layouts for different screen sizes
- Loading states, empty states, error states for all screens
- Disclaimer text on chat screen
- About/help screen

**Acceptance criteria:**
- [ ] Full Bangla UI when language = "bn"
- [ ] Full English UI when language = "en"
- [ ] Language can be switched from settings
- [ ] All screens have proper loading and error states
- [ ] AI chat shows disclaimer: "This is guidance, not diagnosis"

---

### Slice 8.3 — Testing + deployment

**Effort:** 🟡 M (3 days)

**What to build:**
- Increase test coverage for critical paths (auth, triage safety rules, guardian privacy)
- Set up CI (GitHub Actions) for backend lint + test
- Set up CI for Flutter lint + test
- Deploy backend to Render (free → $7 always-on for pilot)
- Set up Sentry error tracking
- Set up Firebase Crashlytics
- Create Firestore security rules (deny all client access)
- Deploy Firestore indexes
- Write deployment runbook

**Acceptance criteria:**
- [ ] CI passes on PRs (backend + mobile)
- [ ] Backend deployed and healthy on Render
- [ ] Sentry captures backend errors
- [ ] Crashlytics captures Flutter crashes
- [ ] Firestore security rules deployed and verified
- [ ] All composite indexes created

---

### Slice 8.4 — Account deletion

**Effort:** 🟢 S (1 day)

**What to build:**
- **Backend:**
  - `DELETE /me` — account deletion with cascade (deletes all subcollections: medicines, dose_logs, readings, chat_sessions, daily_summaries, usage; revokes guardian links; deletes FCM tokens; deletes Firebase Auth user)
- **Flutter:**
  - "Delete my account" button in settings with confirmation dialog

**Acceptance criteria:**
- [ ] Patient deletes account → all data removed from Firestore
- [ ] Guardian links are revoked on deletion
- [ ] Firebase Auth user is deleted
- [ ] Confirmation dialog prevents accidental deletion

**Tests:**
- Backend: `test_delete_me_cascades`, `test_delete_me_revokes_guardian_links`

---

## Summary Timeline

| Phase | Slices | Est. effort | Cumulative |
|-------|--------|-------------|------------|
| **0: Setup** | 0.1, 0.2 | 4 days | 4 days |
| **1: Auth** | 1.1, 1.2 | 6 days | 10 days |
| **2: Medicine** | 2.1, 2.2 | 8 days | 18 days |
| **6: Guardian (connection)** | 6.1 | 4 days | 22 days |
| **2: Medicine (cron)** | 2.3 | 3 days | 25 days |
| **3: Readings** | 3.1 | 3 days | 28 days |
| **6: Guardian (dashboard)** | 6.2 | 3 days | 31 days |
| **4: Sheba AI** | 4.1, 4.2 | 10 days | 41 days |
| **Milestone M1** | — | — | **41 days** |
| **4: Sheba AI (cont.)** | 4.3 | 2 days | 43 days |
| **5: Doctor** | 5.1, 5.2, 5.3 | 11 days | 54 days |
| **7: Emergency & Admin** | 7.1, 7.2 | 4 days | 58 days |
| **8: Polish** | 8.1, 8.2, 8.3, 8.4 | 9 days | 67 days |

**Total estimated effort: ~67 working days (~3.5 months at 3–4 hours/day)**

> **Note:** This is an optimistic estimate for a solo developer. Add 20–30% buffer for unknowns, debugging, and learning curves. Realistic timeline: **4–5 months**.

---

## Build Order

The recommended build order interleaves guardian and medicine features so that guardian alerts can be tested end-to-end:

```
0.1 (scaffold) → 0.2 (core infra)
  → 1.1 (auth + FCM token) → 1.2 (profile)
    → 2.1 (medicine CRUD) → 2.2 (dose tracking + adherence)
      → 6.1 (guardian connection)      ← moved earlier
        → 2.3 (missed-dose cron)       ← now has guardians to alert
        → 3.1 (readings)
          → 6.2 (guardian dashboard)
            → 4.1 (chat + LLM) → 4.2 (triage + safety)
              ─── Milestone M1 ───
              → 4.3 (medicine agent)
              → 5.1 (doctor search) → 5.2 (appointments) → 5.3 (doctor match + PDF)
              → 7.1 (emergency) → 7.2 (admin panel)
              → 8.1 (notifications polish) → 8.2 (l10n + UI) → 8.3 (testing + deploy) → 8.4 (account deletion)
```

**Key change:** Guardian connection (6.1) is moved before the missed-dose cron (2.3) so that guardian alerts can be tested with real guardian links. Guardian dashboard (6.2) follows readings (3.1) since it displays reading data.
