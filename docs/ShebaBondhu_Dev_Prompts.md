# ShebaBondhu: Development Prompts Playbook

Put this file in `docs/dev-prompts.md`. It holds every prompt needed to build the rest of the project with Antigravity. It works without Claude: any AI assistant can use it.

Status when this file was written: **Slice 0 (backend skeleton + Flutter skeleton) is done.** Next is Slice 1.1.

---

## 0. How to use this file

1. Start a **new chat/session in Antigravity for every slice** (keeps the context clean).
2. Paste the **Standard Header** (section 1), then the slice prompt (section 4 onwards).
3. Set the **thinking level** written above the prompt. If the agent keeps making mistakes, raise it one level or split the task in two.
4. Run the **manual checks** listed under the prompt. Do not merge until they pass.
5. One git branch per slice. Merge into `main` through a pull request.
6. If the docs need to change, **change the docs first**, then the code.

### Git routine for every slice

```
git checkout main
git pull
git checkout -b slice-X-Y-name
# ... work ...
git add .
git commit -m "feat: slice X.Y - short description"
git push -u origin slice-X-Y-name
# open a Pull Request on GitHub, merge, delete the branch
```

Safety check before every merge (should list only `.env.example`):

```
git ls-files | grep -i -E "serviceAccount|\.env"
```

---

## 1. Standard Header (paste at the top of every prompt)

```
Project: ShebaBondhu (Flutter + FastAPI + Firebase Auth + Firestore). I am a solo developer.
Read first: docs/architecture.md, docs/repo-structure.md, docs/api-spec.md, docs/firestore-schema.md, docs/build-plan.md.
Rules:
- Do ONLY the task below. Do not start other slices or add features that are not listed.
- Follow the docs exactly. If the docs are wrong or unclear, stop and tell me. Do not invent.
- Keep it simple: no extra abstractions and no libraries that are not in the docs without asking me.
- Never commit or print secrets (.env, service account JSON).
- Never log request bodies or chat content (health data).
- After coding, run the tests and the server/app, and show the exact commands and results.
- End with: files created or changed, how to run it, what I should test manually, and anything you assumed.
```

## 2. Thinking levels

| Level | Use for |
|---|---|
| Low | Scaffolding, config, UI placeholders, translations |
| Medium | Normal features with tests |
| High | Auth, roles, guardian permissions, triage rules, adherence and missed-dose logic, PDF access control |

## 3. Handoff prompt (use this in a NEW AI chat if the previous one is unavailable)

```
I am building ShebaBondhu, a healthcare companion app (Flutter + FastAPI + Firebase Auth + Firestore), solo, using Antigravity. The project docs are in the repo under docs/ (overview, tech stack, architecture, repo-structure, firestore-schema, api-spec, build-plan, risks, dev-prompts). Slice order: 0.1, 0.2, 1.1, 1.2, 2.1, 2.2, 6.1, 2.3, 3.1, 6.2, 4.1, 4.2 (milestone M1), then 4.3, 5.1-5.3, 7.1, 7.2, 8.1-8.3. Completed so far: [LIST SLICES]. Currently working on: [SLICE]. Please act as my reviewer and mentor: review my code and diffs against the docs, find bugs and security problems (especially auth, roles, guardian privacy, health data), and give me the next Antigravity prompt in the style of docs/dev-prompts.md. Explain things simply; I am a student. I write in Banglish.
```

---

## 4. Slice 1.1: Registration + Login

**Before you start (you, manually):**
- Google sign-in on Android needs your debug SHA-1 in Firebase. Run `cd mobile/android` then `gradlew signingReport` (Windows) or `./gradlew signingReport` (Mac/Linux). Copy the **debug SHA-1**. Firebase Console → Project settings → your Android app → Add fingerprint. Then run `flutterfire configure` again in `mobile/`.
- Make sure Email/Password and Google providers are enabled.

### 4.1 Backend (thinking: HIGH)

```
[Standard Header]

TASK: Backend part of Slice 1.1. Work only inside backend/.
Create:
1. modules/auth: POST /auth/register (uses get_firebase_user, NOT get_current_user). Accept only role patient|guardian|doctor; reject admin. Doctors start with verification_status "pending"; other roles have none. Return 409 ALREADY_REGISTERED if the user document exists. Validate date_of_birth is in the past and fields match docs/api-spec.md.
2. modules/profile: GET /me (full user document; 404 NOT_REGISTERED if missing), POST /me/consent (sets consent_given and consent_given_at).
3. modules/notification: PUT /notifications/fcm-token (store token, device_id, platform in fcm_tokens/{uid}; upsert by device_id).
4. UserRepository (create, get_by_uid, update) and FcmTokenRepository. Only repositories touch Firestore.
5. Pydantic schemas for all request and response bodies.
6. Tests (mock Firebase): test_register_creates_user, test_register_duplicate_409, test_register_rejects_admin_role, test_doctor_starts_pending, test_me_returns_profile, test_me_unregistered_404, test_consent_recorded, test_fcm_token_upsert.
Do not add /auth/login. Do not create other modules.
```

**Manual checks:** `pytest` passes. In `/docs` (Swagger), click Authorize with a real Firebase ID token (see "Get a test token" below), then try `POST /auth/register` and `GET /me`. Check the document appears in Firestore.

Get a test token: ask the agent for a tiny script `backend/scripts/get_test_token.py` that signs in with email/password through the Firebase REST API using the Web API key (kept in `.env`, never committed).

### 4.2 Flutter (thinking: MEDIUM)

```
[Standard Header]

TASK: Flutter part of Slice 1.1. Work only inside mobile/.
Create under features/auth (data / providers / screens / widgets, as in docs/architecture.md):
1. Login screen: email+password sign in/sign up and "Continue with Google". Use the currently documented API for the installed package versions (google_sign_in has had breaking changes); if unsure, use FirebaseAuth.signInWithProvider(GoogleAuthProvider()) on Android.
2. Registration Step 1 screen: name, date of birth, gender, role (Patient / Guardian / Doctor, shown with friendly labels), language (bn/en). Calls POST /auth/register.
3. Consent screen: explains data use, AI is guidance not diagnosis, family sees data only with permission. Calls POST /me/consent. The user cannot continue without agreeing.
4. authStateProvider watching FirebaseAuth, and a session provider that after sign-in calls GET /me: 404 NOT_REGISTERED -> registration; consent missing -> consent screen; otherwise -> home. Add the auth guard to GoRouter.
5. After login, get the FCM token (firebase_messaging, ask notification permission) and call PUT /notifications/fcm-token.
6. Home placeholder shows the user's name and a Sign out button.
7. All visible text goes through ARB files (bn and en).
8. Widget tests for the login screen and the registration form validation.
Do not build Step 2 (health profile), dashboards or other tabs.
```

**Manual checks (real Android phone preferred):** new Google user -> register -> consent -> home. Sign out, sign in again -> goes straight to home. Email sign-up works. User document and FCM token appear in Firestore.

### 4.3 Deploy to Render (thinking: LOW, after 4.1 and 4.2 pass)

**You (manually):** Render dashboard -> New Web Service -> connect the GitHub repo -> Root directory `backend` -> Runtime Docker. Add a Secret File named `serviceAccountKey.json` and set `GOOGLE_APPLICATION_CREDENTIALS=/etc/secrets/serviceAccountKey.json`. Add the other env vars from `.env.example`.

```
[Standard Header]

TASK: Make the backend deployable on Render. Work only inside backend/.
1. Dockerfile (python:3.12-slim, install requirements, run uvicorn on the PORT env var, non-root user). Do NOT install WeasyPrint dependencies yet.
2. .dockerignore (exclude .env, serviceAccountKey.json, tests, .venv).
3. Add the Render steps and required env vars to backend/README.md.
4. Update docs/repo-structure.md only if you add files.
Do not change any application code.
```

Check: `https://<your-service>.onrender.com/health` returns ok. Then build the Flutter app with `--dart-define=API_BASE_URL=https://<your-service>.onrender.com` and sign in from a real phone. Free instances sleep after 15 minutes, so the first request can take about a minute.

---

## 5. Slice 1.2: Profile completion (Step 2)

Thinking: MEDIUM (review the field allowlist yourself).

```
[Standard Header]

TASK: Slice 1.2.
Backend: PATCH /me. Allow only the fields that belong to the caller's role (patient: conditions, allergies, blood_group, height_cm, weight_kg, emergency_contact; guardian: whatsapp_number; doctor: specialty, bmdc_number, city, area, chamber_address, consultation_fee; all roles: name, language, phone). Reject fields outside the role's list with 422. A user can never change role, uid, email, verification_status or consent fields through this endpoint. Tests for validation and for forbidden fields.
Flutter: Registration Step 2 (patient health profile, with "Skip for now"), guardian short form, doctor form with BMDC number and specialty. Profile view/edit screen. Home shows a "complete your profile" prompt while incomplete.
```

Manual checks: a patient saves a health profile and reopens it; a doctor sees pending status; try changing `role` through Swagger and confirm it is rejected.

---

## 6. Slice 2.1: Medicine CRUD + schedule

Thinking: HIGH for backend dose generation, MEDIUM for Flutter.

```
[Standard Header]

TASK: Slice 2.1.
Backend:
1. Medicine CRUD: POST/GET/PATCH/DELETE (soft delete) /medicines, patient role only.
2. Dose generation: deterministic dose_log IDs {date}_{time}_{medicine_id} so generation is idempotent. Generate today's dose_logs lazily inside GET /medicines/doses/today (create missing ones) and in POST /internal/cron/generate-doses (X-Cron-Secret header, POST). Timezone Asia/Dhaka (UTC+6) everywhere.
3. Editing a medicine updates future doses; deactivating removes future pending dose_logs.
4. daily_summaries documents are created with the doses (total_doses etc.).
5. Tests: test_add_medicine, test_list_medicines, test_generate_daily_doses_idempotent, test_deactivate_removes_future_doses, test_cron_rejects_bad_secret.
Flutter: medicine list, add medicine form (name, dose, frequency, times), edit screen, and local notification scheduling with flutter_local_notifications (Android 13 notification permission, exact alarms, reschedule after reboot, rebuild the schedule whenever the medicine list is fetched).
Do not build the "Taken" flow yet.
```

Manual checks (real phone): a reminder fires at the set time with the screen locked and with the app closed. Call the generate endpoint twice and confirm no duplicate doses.

---

## 7. Slice 2.2: Dose tracking + adherence

Thinking: HIGH.

```
[Standard Header]

TASK: Slice 2.2.
Backend:
1. GET /medicines/doses/today, POST /medicines/doses, GET /medicines/adherence as in docs/api-spec.md.
2. POST /medicines/doses must allow pending -> taken AND missed -> taken. Set taken_late=true when the dose was already missed. When a missed dose is marked taken, update daily_summary (missed-1, taken+1) and create an alert record "dose taken late" for guardians (the push comes in Slice 2.3).
3. daily_summary adherence_pct and adherence_status are computed only over doses already due (taken + missed + overdue pending). If nothing is due yet the status is green.
4. Tests: test_record_dose, test_record_dose_late_after_missed, test_adherence_not_red_in_morning, test_adherence_calculation, test_cannot_mark_other_users_dose.
Flutter: Home dashboard medicine card with "Taken" buttons, today's dose list (pending/taken/missed), weekly adherence chart (fl_chart), and a "Taken" action button on the local notification that calls the API.
```

Manual checks: tap Taken on a dose, status updates instantly and survives app restart. Adherence is not red at 7 AM with all doses still in the future.

---

## 8. Slice 6.1: Guardian connection

Thinking: HIGH.

```
[Standard Header]

TASK: Slice 6.1 (guardian connection) as in docs/build-plan.md and docs/api-spec.md section 8.
Backend:
1. Invite code: random 8 characters (not based on the patient's name), expires after 48h, one active code per patient (a new one invalidates the old). Remove any invite_code field from the users document.
2. POST /guardian/connect with a rate limit of 5 failed attempts per hour per guardian. Creates a guardian_link with status pending and sends an FCM push to the patient.
3. PATCH /guardian/links/{id} (patient: accept/decline), DELETE (revoke), GET /guardian/my-guardians, GET /guardian/my-patients.
4. Create the NotificationChannel interface and FCMChannel in modules/notification as in docs/architecture.md section 8, and use it for all pushes.
5. Authorization: only the patient named in the link can accept, decline or revoke it; a guardian can never accept their own link.
6. Tests: test_generate_invite_code, test_connect_with_code, test_expired_code_rejected, test_used_code_rejected, test_accept_guardian, test_revoke_guardian, test_other_patient_cannot_accept, test_connect_rate_limit.
Flutter: Family tab (patient: guardians list, invite code screen with share button, pending requests with accept/decline, revoke), guardian connect screen (enter code), foreground and background push handling (firebase_messaging).
```

Manual checks (two phones or phone + emulator): full flow patient <-> guardian, revoke, expired code.

---

## 9. Slice 2.3: Missed-dose cron + guardian alert

Thinking: HIGH. Needs the Render deploy (4.3) to be live.

```
[Standard Header]

TASK: Slice 2.3.
Backend:
1. POST /internal/cron/missed-doses (X-Cron-Secret header). Use a collection-group query on dose_logs (status == "pending", scheduled_at < now - MISSED_GRACE_MINUTES). Tell me the composite/collection-group index I must create and add it to the index file in docs/firestore-schema.md.
2. For each overdue dose: mark missed, update daily_summary, then group by patient and send ONE alert per patient to all active guardians through the Guardian Alert Agent and FCMChannel. Log every alert in the alerts collection.
3. Make the job idempotent: running it twice must not send duplicate alerts.
4. Guardian Alert Agent also sends the "dose taken late" push created in Slice 2.2.
5. Tests: test_missed_dose_detection, test_cron_auth_rejects_bad_secret, test_one_alert_per_patient, test_cron_is_idempotent, test_no_guardians_no_error.
```

**You (manually):** create the index (Firestore error message gives a link), register on cron-job.org with a POST to `https://<render-url>/internal/cron/missed-doses`, header `X-Cron-Secret`, every 10 minutes, timezone Asia/Dhaka. Set `MISSED_GRACE_MINUTES` on Render.

Manual checks: do not mark a dose, wait past the grace time, guardian phone receives a push. Mark it late and the guardian gets the "taken" push.

---

## 10. Slice 3.1: Readings + trends

Thinking: MEDIUM.

```
[Standard Header]

TASK: Slice 3.1.
Backend: POST /readings, GET /readings with trend, validation ranges (sugar 20-600, systolic 60-300, diastolic 30-200), update daily_summary latest_sugar/latest_bp. Put a clear hook function raise_reading_event(reading) that does nothing yet (triage comes in Slice 4.2). Tests: add sugar, add BP, validation, trend.
Flutter: add reading screen (sugar/BP toggle), reading history with fl_chart, health snapshot card on Home.
```

---

## 11. Slice 6.2: Guardian dashboard

Thinking: HIGH (privacy).

```
[Standard Header]

TASK: Slice 6.2.
Backend: GET /guardian/patients/{id}/status, /readings, GET /guardian/alerts. Every endpoint first checks for an ACTIVE guardian_link between caller and patient (revoked -> 403). Return only an explicit allowlist of fields (medicine status, readings, alerts, whatsapp_call_url). Never read chat collections in guardian code.
Tests: test_guardian_sees_status, test_guardian_cannot_see_chats, test_revoked_guardian_403, test_unlinked_guardian_403, test_response_has_only_allowed_fields.
Flutter: guardian home (patient list), per-patient dashboard (green/yellow/red medicine status, latest readings with trend, alert history), WhatsApp call button (url_launcher wa.me), doctor suggestions button (leave it opening the doctor search placeholder).
```

---

## Milestone M1 check (after 4.2)

Test the whole story with two phones: register a patient and a guardian, connect, add medicines, miss a dose (guardian gets a push), mark it late, add a high sugar reading, chat "my sugar is 450 and I feel dizzy" and see RED, guardian gets the emergency push. Fix bugs, then record a short demo video.

---

## 12. Slice 4.1: Chat infrastructure + LLM

Thinking: MEDIUM.

**You (manually):** create a Gemini API key in Google AI Studio and put it in `.env` as `LLM_API_KEY`. Use the free tier with **fake test data only**. Check the provider's current model list yourself and set `LLM_MODEL` (the docs must not hard-code one). Free-tier limits change, so do not rely on any number.

```
[Standard Header]

TASK: Slice 4.1.
Backend: modules/chat (POST /chat/messages, GET /chat/sessions, GET /chat/sessions/{id}/messages), LLMProvider interface plus a Gemini provider (LLM_PROVIDER, LLM_API_KEY, LLM_MODEL from env, no default model name), the basic Orchestrator (everything goes to the LLM with a health system prompt in the user's language), a persisted per-user daily counter at users/{uid}/usage/{date} (50 messages/day, 429 RATE_LIMITED), token limit per request, graceful 503 LLM_UNAVAILABLE. Chat content must never appear in logs. Never send name, phone or email to the LLM. Tests with a fake LLM provider.
Flutter: chat screen with bubbles, text input, session list, loading state, disclaimer "This is guidance, not diagnosis", correct Bangla rendering.
```

---

## 13. Slice 4.2: Triage Agent + safety rules + voice

Thinking: HIGH.

```
[Standard Header]

TASK: Slice 4.2.
Backend:
1. Triage Agent with a deterministic rule engine that runs BEFORE any LLM call (docs/architecture.md 6.5). Put the rules and the keyword lists (Bangla and English) in a data file backend/app/agents/triage_rules.json so I can review and edit them. Do not invent medical thresholds beyond the docs; mark each rule with a comment "REVIEW".
2. If no rule matches, the LLM classifies green/yellow/red with structured JSON output; invalid JSON falls back to rule-based only; LLM down -> the message from docs/architecture.md 9.4.
3. RED -> emergency event -> Guardian Alert Agent sends the guardian push with only: emergency notice, location, latest reading. Add the optional location {lat,lng} to POST /chat/messages. YELLOW -> summary-only push. If the patient has no guardians, skip the alert and log it.
4. Hook readings: implement raise_reading_event from Slice 3.1 so very abnormal readings also trigger RED rules.
5. Tests: the acceptance examples in docs/build-plan.md (sugar 450 + dizzy -> RED without LLM, chest pain keyword -> RED, mild headache -> GREEN via fake LLM), test_llm_down_falls_back_to_rules, test_guardian_alert_content_is_minimal, test_no_guardian_no_crash.
Flutter: severity banner, red emergency card (hospitals placeholder + 999 button), yellow doctor prompt, voice input with speech_to_text for bn and en (text input always works).
```

You must review `triage_rules.json` yourself and, if possible, ask a Bangla-speaking medical person to check it. Test voice on a real phone.

---

## 14. Slice 4.3: Medicine Agent

Thinking: MEDIUM.

```
[Standard Header]

TASK: Slice 4.3. Medicine Agent answers schedule questions from the patient's own medicine list and checks a small curated interaction list stored in backend/app/agents/interactions.json (mark it REVIEW; do not claim it is complete). Orchestrator routes medicine intent to it; other questions must not be routed to it. Always end interaction answers with advice to ask a doctor or pharmacist. Tests: schedule query, interaction warning, routing.
```

---

## 15. Slice 5.1: Doctor search

Thinking: MEDIUM.

```
[Standard Header]

TASK: Slice 5.1. GET /doctors/search (only verification_status "approved"), GET /doctors/{id}, PATCH /doctors/me. Add the composite indexes to docs. Flutter: search screen (specialty, city, area), doctor profile card, doctor profile edit. Until the admin panel exists, I will approve doctors by editing verification_status in the Firebase Console. Tests: search by specialty, excludes unverified, profile update.
```

## 16. Slice 5.2: Appointments + prescriptions

Thinking: HIGH (state transitions and permissions).

```
[Standard Header]

TASK: Slice 5.2 as in docs/api-spec.md section 7. Enforce the allowed status transitions exactly; each role can only change its own side. Patient sets allow_summary at request time. Prescription is text-only in the MVP. Confirming a prescription adds medicines and generates doses. FCM pushes for every status change. Tests: create, transitions (valid and invalid), prescription upload, confirm adds medicines, wrong doctor/patient gets 403.
Flutter: appointment request (from doctor profile), appointment list, doctor dashboard (requests, confirm/cancel, write prescription), patient prescription review.
```

## 17. Slice 5.3: Doctor Match Agent + PDF

Thinking: HIGH for access control, MEDIUM for the PDF.

**Before the prompt:** ask the agent to first prove Bangla rendering with a tiny script (a PDF containing conjunct letters) and open the PDF yourself. Only continue if it looks right.

```
[Standard Header]

TASK: Slice 5.3.
1. Update the Dockerfile with the WeasyPrint system libraries and the Noto Sans Bengali font. Prove Bangla rendering with a small test PDF first and show me.
2. Doctor Match Agent + GET /doctors/suggestions (reasons based on conditions and the latest triage; never send name/phone/email to the LLM).
3. GET /pdf/doctor-summary (patient) and GET /pdf/doctor-summary/{patient_id} (doctor). The doctor endpoint requires a confirmed appointment with patient_allows_summary == true. The PDF is generated on demand and never stored. Content as in docs/overview section 9.
4. Tests: test_pdf_generation, test_pdf_bangla_rendering (check the PDF bytes are produced and contain the font), test_pdf_denied_without_permission, test_pdf_denied_for_cancelled_appointment.
Flutter: doctor suggestion cards in chat after yellow triage, "Generate summary" buttons (chat tab and doctor tab), PDF view/share.
```

---

## 18. Slice 7.1: Emergency handling

Thinking: MEDIUM.

**Important:** hospital data (names, phones, coordinates) must be **correct**. Do not let the AI invent it. Prepare a list of 20-30 hospitals yourself with verified phone numbers and locations, or ask the agent to create the file structure with placeholders and fill it in yourself.

```
[Standard Header]

TASK: Slice 7.1. Create mobile/assets/hospitals_bd.json with the structure only (name, address, phone, lat, lng) and 3 clearly marked EXAMPLE entries; I will fill the real data. Backend: POST /emergency/alert (manual SOS; sends the minimal guardian push with location and latest reading) and GET /emergency/hospitals if still needed by the docs. Flutter: always-visible SOS button on Home, emergency screen (nearest 5 hospitals via geolocator, Google Maps via url_launcher, 999 call button, guardian alert status), works without GPS. Tests as in docs/build-plan.md.
```

## 19. Slice 7.2: Admin panel (optional)

Thinking: MEDIUM. If time is short, skip it: approve doctors in the Firebase Console and set the admin role by hand.

```
[Standard Header]

TASK: Slice 7.2. Backend admin endpoints (pending doctors, verify/reject, users list) with require_role("admin"). A minimal static admin page in admin/ (HTML/CSS/JS, Firebase Auth email sign-in) that lists pending doctors with BMDC number and approve/reject buttons. The admin role is set manually in Firestore. Tests: list pending, approve, reject, non-admin 403.
```

---

## 20. Slice 8.1: Notifications polish

Thinking: MEDIUM.

```
[Standard Header]

TASK: Slice 8.1. GET /notifications (history), PATCH /notifications/{id}/read, unread badge count, notification bell screen, deep links from push notifications to the right screen, FCM token refresh on every launch.
```

## 21. Slice 8.2: Localization + UI polish

Thinking: LOW to MEDIUM.

```
[Standard Header]

TASK: Slice 8.2. Complete all Bangla and English strings in the ARB files, Bangla date/time formatting, language switch in settings, loading/empty/error states for every screen, chat disclaimer, About/Help screen. No new features.
```

## 22. Slice 8.3: Testing + deployment + account deletion

Thinking: MEDIUM.

```
[Standard Header]

TASK: Slice 8.3.
1. DELETE /me: account deletion that removes the user's document and all subcollections, guardian links, appointments data owned by the user, fcm tokens and the Firebase Auth account. Test it.
2. GitHub Actions: backend lint + tests, Flutter analyze + tests.
3. Sentry on the backend, Crashlytics in Flutter.
4. Firestore security rules (deny all client access) and the composite indexes as files in the repo, with deploy instructions.
5. A deployment runbook in docs/runbook.md (Render env vars, secret file, cron-job.org jobs, how to roll back).
```

---

## 23. When the agent gets stuck

- Paste the **exact error** and the file name; ask: "Explain the root cause first, then fix."
- Open a **new session** and paste only the header and the task, if the session became long and confused.
- Raise the thinking level, or split the task in two.
- If the agent says "I assumed...", check the assumption against the docs.
- Ask for a **diff summary** and read it before merging.
- Never accept changes that touch files outside the slice.

## 24. After each slice: what to bring to your reviewer

1. The agent's final message (files changed, assumptions).
2. The result of the tests and the manual checks.
3. Anything you did not understand.
