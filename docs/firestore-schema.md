# ShebaBondhu: Firestore Schema

Version 1.0 | 22 October 2026

---

## Design Principles

1. **Backend-only access.** Firestore security rules deny all client reads/writes. Only the FastAPI service account accesses Firestore.
2. **Document-oriented.** Data is structured to minimize reads per screen. Denormalized summaries avoid expensive aggregation queries.
3. **Subcollections for owned data.** Medicines, readings, and dose logs live under the patient's user document to enforce ownership naturally.
4. **Repository layer.** All Firestore access goes through repository classes, so a future migration to PostgreSQL touches only that layer.

---

## 1. Collections Overview

```
firestore-root/
├── users/                          # All user profiles (patient, guardian, doctor, admin)
│   └── {user_id}/
│       ├── medicines/              # Patient's medicines (subcollection)
│       │   └── {medicine_id}
│       ├── dose_logs/              # Individual dose events (subcollection)
│       │   └── {dose_log_id}       # Deterministic ID: {date}_{time}_{medicine_id}
│       ├── readings/               # Sugar and BP readings (subcollection)
│       │   └── {reading_id}
│       ├── chat_sessions/          # AI chat sessions (subcollection)
│       │   └── {session_id}/
│       │       └── messages/       # Chat messages (sub-subcollection)
│       │           └── {message_id}
│       ├── daily_summaries/        # Denormalized daily adherence + readings (subcollection)
│       │   └── {date}              # doc ID = "2026-10-22"
│       └── usage/                  # Per-user daily usage counters (subcollection)
│           └── {date}              # doc ID = "2026-10-22"
│
├── guardian_links/                  # Guardian ↔ Patient connections
│   └── {link_id}
│
├── appointments/                   # Appointment requests and bookings
│   └── {appointment_id}
│
├── alerts/                         # Notification history (all types)
│   └── {alert_id}
│
├── invite_codes/                   # Active invite codes for guardian connection
│   └── {code}                      # Random 8-char alphanumeric code
│
├── fcm_tokens/                     # FCM device tokens for push notifications
│   └── {user_id}
│
└── hospitals/                      # (Optional) Curated hospital list
    └── {hospital_id}              # May be a static JSON asset instead
```

---

## 2. Collection Details

### 2.1 `users/{user_id}`

The user document stores identity, role, and profile. The `user_id` is the Firebase Auth UID.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `uid` | string | ✓ | Firebase Auth UID (same as doc ID) |
| `email` | string | ✓ | Email address |
| `name` | string | ✓ | Display name |
| `date_of_birth` | timestamp | ✓ | Date of birth |
| `gender` | string | ✓ | "male" / "female" / "other" |
| `role` | string | ✓ | "patient" / "guardian" / "doctor" / "admin" |
| `language` | string | ✓ | "bn" / "en" |
| `phone` | string | | Phone number (used for wa.me link) |
| `consent_given` | boolean | ✓ | Data usage consent |
| `consent_given_at` | timestamp | | When consent was given |
| `created_at` | timestamp | ✓ | Account creation time |
| `updated_at` | timestamp | ✓ | Last profile update |
| `is_active` | boolean | ✓ | Account active status |
| **Patient-only fields** |
| `conditions` | array\<string\> | | Known conditions: ["diabetes", "hypertension", ...] |
| `allergies` | array\<string\> | | Known allergies |
| `blood_group` | string | | Blood group (e.g., "B+") |
| `height_cm` | number | | Height in cm |
| `weight_kg` | number | | Weight in kg |
| `emergency_contact` | string | | Emergency contact phone number |
| **Guardian-only fields** |
| `whatsapp_number` | string | | WhatsApp number for wa.me link |
| **Doctor-only fields** |
| `specialty` | string | | Medical specialty |
| `bmdc_number` | string | | BMDC registration number (primary verification method) |
| `verification_status` | string | | "pending" / "approved" / "rejected" |
| `verified_at` | timestamp | | When admin approved |
| `verified_by` | string | | Admin UID who approved |
| `city` | string | | City for doctor search |
| `area` | string | | Area/locality for doctor search |
| `chamber_address` | string | | Chamber or hospital address |
| `consultation_fee` | string | | Fee info (text, no payment processing) |

**Example document:**

```json
{
  "uid": "firebase-uid-abc123",
  "email": "rahela@example.com",
  "name": "Rahela Begum",
  "date_of_birth": "1964-03-15T00:00:00Z",
  "gender": "female",
  "role": "patient",
  "language": "bn",
  "phone": "+8801712345678",
  "consent_given": true,
  "consent_given_at": "2026-10-20T10:00:00Z",
  "created_at": "2026-10-20T10:00:00Z",
  "updated_at": "2026-10-20T10:05:00Z",
  "is_active": true,
  "conditions": ["diabetes", "hypertension"],
  "allergies": ["penicillin"],
  "blood_group": "B+",
  "height_cm": 155,
  "weight_kg": 65,
  "emergency_contact": "+8801798765432"
}
```

---

### 2.2 `users/{user_id}/medicines/{medicine_id}`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✓ | Auto-generated doc ID |
| `name` | string | ✓ | Medicine name |
| `dose` | string | ✓ | Dosage (e.g., "500mg") |
| `frequency` | string | ✓ | "once" / "twice" / "thrice" / "custom" |
| `times` | array\<string\> | ✓ | Scheduled times: ["08:00", "20:00"] |
| `instructions` | string | | "After meals", "Before sleep", etc. |
| `prescribed_by` | string | | Doctor name or "self" |
| `start_date` | timestamp | ✓ | When to start |
| `end_date` | timestamp | | When to stop (null = ongoing) |
| `is_active` | boolean | ✓ | Currently active |
| `created_at` | timestamp | ✓ | |
| `updated_at` | timestamp | ✓ | |

**Example:**

```json
{
  "id": "med-001",
  "name": "Metformin",
  "dose": "500mg",
  "frequency": "twice",
  "times": ["08:00", "20:00"],
  "instructions": "After meals",
  "prescribed_by": "Dr. Nasrin",
  "start_date": "2026-10-01T00:00:00Z",
  "end_date": null,
  "is_active": true,
  "created_at": "2026-10-01T00:00:00Z",
  "updated_at": "2026-10-01T00:00:00Z"
}
```

---

### 2.3 `users/{user_id}/dose_logs/{dose_log_id}`

One document per scheduled dose instance per day. **Doc ID is deterministic:** `{date}_{time}_{medicine_id}` (e.g., `20261022_0800_med-001`). This makes dose generation idempotent and allows lazy creation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✓ | Deterministic: `{date}_{time}_{medicine_id}` |
| `medicine_id` | string | ✓ | Reference to medicine doc |
| `medicine_name` | string | ✓ | Denormalized for quick display |
| `scheduled_date` | string | ✓ | "2026-10-22" (partition key) |
| `scheduled_time` | string | ✓ | "08:00" |
| `scheduled_at` | timestamp | ✓ | Full datetime for queries |
| `status` | string | ✓ | "pending" / "taken" / "missed" / "skipped" |
| `taken_at` | timestamp | | When user marked as taken |
| `taken_late` | boolean | | `true` if taken after the dose was missed or after grace period |
| `marked_missed_at` | timestamp | | When cron marked as missed |
| `created_at` | timestamp | ✓ | |

**Example:**

```json
{
  "id": "20261022_0800_med-001",
  "medicine_id": "med-001",
  "medicine_name": "Metformin",
  "scheduled_date": "2026-10-22",
  "scheduled_time": "08:00",
  "scheduled_at": "2026-10-22T08:00:00+06:00",
  "status": "taken",
  "taken_at": "2026-10-22T08:25:00+06:00",
  "taken_late": false,
  "marked_missed_at": null,
  "created_at": "2026-10-22T00:00:00+06:00"
}
```

---

### 2.4 `users/{user_id}/readings/{reading_id}`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✓ | Auto-generated |
| `type` | string | ✓ | "sugar" / "blood_pressure" |
| `value` | number | ✓ | Sugar: mg/dL. BP: systolic |
| `value_secondary` | number | | BP only: diastolic |
| `unit` | string | ✓ | "mg/dL" / "mmHg" |
| `context` | string | | "fasting" / "after_meal" / "random" (sugar only) |
| `recorded_at` | timestamp | ✓ | When the reading was taken |
| `notes` | string | | Optional user note |
| `created_at` | timestamp | ✓ | |

**Example (sugar):**

```json
{
  "id": "read-001",
  "type": "sugar",
  "value": 180,
  "value_secondary": null,
  "unit": "mg/dL",
  "context": "fasting",
  "recorded_at": "2026-10-22T07:00:00+06:00",
  "notes": "",
  "created_at": "2026-10-22T07:05:00+06:00"
}
```

**Example (blood pressure):**

```json
{
  "id": "read-002",
  "type": "blood_pressure",
  "value": 140,
  "value_secondary": 90,
  "unit": "mmHg",
  "context": null,
  "recorded_at": "2026-10-22T07:00:00+06:00",
  "notes": "Felt slightly dizzy",
  "created_at": "2026-10-22T07:05:00+06:00"
}
```

---

### 2.5 `users/{user_id}/chat_sessions/{session_id}`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✓ | Auto-generated |
| `title` | string | | Auto-generated from first message |
| `created_at` | timestamp | ✓ | |
| `updated_at` | timestamp | ✓ | Last message time |
| `is_active` | boolean | ✓ | |
| `last_severity` | string | | Latest triage severity in this session |
| `message_count` | number | ✓ | Total messages (denormalized) |

### 2.6 `users/{user_id}/chat_sessions/{session_id}/messages/{message_id}`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✓ | Auto-generated |
| `role` | string | ✓ | "user" / "assistant" |
| `content` | string | ✓ | Message text |
| `language` | string | ✓ | "bn" / "en" |
| `severity` | string | | "green" / "yellow" / "red" (assistant messages only) |
| `metadata` | map | | Agent output metadata (e.g., doctor suggestions) |
| `created_at` | timestamp | ✓ | |

**Example:**

```json
{
  "id": "msg-001",
  "role": "user",
  "content": "আমার মাথা ঘুরছে, সুগার ৩২০",
  "language": "bn",
  "severity": null,
  "metadata": {},
  "created_at": "2026-10-22T14:00:00+06:00"
}
```

---

### 2.7 `users/{user_id}/daily_summaries/{date}`

**Denormalized summary for the dashboard and guardian view.** Updated on every dose log change and reading entry. Avoids querying all dose_logs and readings per dashboard load.

Doc ID is the date string: `"2026-10-22"`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `date` | string | ✓ | "2026-10-22" |
| `total_doses` | number | ✓ | Total scheduled doses today |
| `taken_doses` | number | ✓ | Doses marked taken |
| `missed_doses` | number | ✓ | Doses marked missed |
| `pending_doses` | number | ✓ | Doses still pending |
| `due_doses` | number | ✓ | Doses already due: taken + missed + overdue pending |
| `adherence_pct` | number | ✓ | (taken / due) * 100. If `due == 0`, value is 100. |
| `adherence_status` | string | ✓ | "green" / "yellow" / "red" |
| `latest_sugar` | map | | `{ value, context, recorded_at }` |
| `latest_bp` | map | | `{ systolic, diastolic, recorded_at }` |
| `has_emergency` | boolean | ✓ | Any RED alert today |
| `updated_at` | timestamp | ✓ | |

**Adherence status logic:**
- Computed only over doses already due (taken + missed + overdue pending where `scheduled_time + MISSED_GRACE_MINUTES < now`).
- If nothing is due yet (e.g., early morning), status is **green** and `adherence_pct = 100`.
- **green**: adherence ≥ 80%
- **yellow**: adherence 50–79%
- **red**: adherence < 50% OR missed ≥ 2 doses

**Example:**

```json
{
  "date": "2026-10-22",
  "total_doses": 4,
  "taken_doses": 3,
  "missed_doses": 1,
  "pending_doses": 0,
  "due_doses": 4,
  "adherence_pct": 75,
  "adherence_status": "yellow",
  "latest_sugar": { "value": 180, "context": "fasting", "recorded_at": "2026-10-22T07:00:00+06:00" },
  "latest_bp": { "value": 140, "diastolic": 90, "recorded_at": "2026-10-22T07:00:00+06:00" },
  "has_emergency": false,
  "updated_at": "2026-10-22T20:15:00+06:00"
}
```

---

### 2.8 `guardian_links/{link_id}`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✓ | Auto-generated |
| `guardian_id` | string | ✓ | Guardian's user UID |
| `patient_id` | string | ✓ | Patient's user UID |
| `guardian_name` | string | ✓ | Denormalized |
| `patient_name` | string | ✓ | Denormalized |
| `status` | string | ✓ | "pending" / "active" / "revoked" |
| `requested_at` | timestamp | ✓ | |
| `accepted_at` | timestamp | | |
| `revoked_at` | timestamp | | |

**Example:**

```json
{
  "id": "link-001",
  "guardian_id": "uid-sajid",
  "patient_id": "uid-rahela",
  "guardian_name": "Sajid",
  "patient_name": "Rahela Begum",
  "status": "active",
  "requested_at": "2026-10-20T12:00:00+06:00",
  "accepted_at": "2026-10-20T12:05:00+06:00",
  "revoked_at": null
}
```

---

### 2.9 `appointments/{appointment_id}`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✓ | Auto-generated |
| `patient_id` | string | ✓ | Patient UID |
| `doctor_id` | string | ✓ | Doctor UID |
| `patient_name` | string | ✓ | Denormalized |
| `doctor_name` | string | ✓ | Denormalized |
| `specialty` | string | ✓ | Denormalized |
| `status` | string | ✓ | "requested" / "confirmed" / "completed" / "cancelled" |
| `requested_date` | timestamp | | Preferred appointment date |
| `confirmed_date` | timestamp | | Confirmed date/time |
| `notes` | string | | Patient's message to doctor |
| `patient_allows_summary` | boolean | ✓ | Patient permits doctor to view PDF |
| `created_at` | timestamp | ✓ | |
| `updated_at` | timestamp | ✓ | |

---

### 2.10 `alerts/{alert_id}`

Notification/alert history for auditing and the guardian's alert history screen.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✓ | Auto-generated |
| `type` | string | ✓ | "missed_dose" / "emergency" / "yellow_triage" / "appointment" / "guardian_invite" / "prescription" |
| `severity` | string | | "info" / "warning" / "critical" |
| `sender_id` | string | ✓ | User or system that triggered |
| `recipient_id` | string | ✓ | Target user |
| `patient_id` | string | | Relevant patient (for guardian alerts) |
| `title` | string | ✓ | Notification title |
| `body` | string | ✓ | Notification body |
| `data` | map | | Extra data (e.g., reading value, location) |
| `channel` | string | ✓ | "fcm" / "whatsapp" / "local" |
| `delivered` | boolean | ✓ | Whether delivery succeeded |
| `read` | boolean | ✓ | Whether recipient opened it |
| `created_at` | timestamp | ✓ | |

---

### 2.11 `invite_codes/{code}`

Short-lived invite codes for guardian connection.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | string | ✓ | Random 8-char alphanumeric code (doc ID) |
| `patient_id` | string | ✓ | Patient who created it |
| `patient_name` | string | ✓ | Denormalized |
| `expires_at` | timestamp | ✓ | Code expiry (e.g., 48 hours) |
| `used` | boolean | ✓ | Whether it's been used |
| `used_by` | string | | Guardian UID who used it |
| `created_at` | timestamp | ✓ | |

---

### 2.13 `users/{user_id}/usage/{date}`

Per-user daily usage counters. Doc ID is the date string (e.g., `"2026-10-22"`).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `date` | string | ✓ | "2026-10-22" |
| `chat_messages` | number | ✓ | Number of chat messages sent today |
| `updated_at` | timestamp | ✓ | |

---

### 2.12 `fcm_tokens/{user_id}`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | ✓ | User UID (doc ID) |
| `tokens` | array\<map\> | ✓ | `[{ token, device_id, platform, updated_at }]` |
| `updated_at` | timestamp | ✓ | |

---

## 3. Required Indexes

Firestore automatically indexes each field. The following **composite indexes** are needed for multi-field queries:

| Collection | Fields | Query purpose |
|-----------|--------|--------------|
| `users/{uid}/dose_logs` | `scheduled_date` ASC, `scheduled_time` ASC | Today's doses sorted by time |
| `dose_logs` (collection group) | `status` ASC, `scheduled_at` ASC | Cron: find pending doses before a cutoff time |
| `users/{uid}/readings` | `type` ASC, `recorded_at` DESC | Latest readings by type |
| `users/{uid}/daily_summaries` | `date` DESC | Weekly adherence view (last 7 days) |
| `guardian_links` | `guardian_id` ASC, `status` ASC | Guardian's active patients |
| `guardian_links` | `patient_id` ASC, `status` ASC | Patient's active guardians |
| `appointments` | `patient_id` ASC, `status` ASC, `created_at` DESC | Patient's appointment list |
| `appointments` | `doctor_id` ASC, `status` ASC, `created_at` DESC | Doctor's appointment requests |
| `alerts` | `recipient_id` ASC, `created_at` DESC | User's alert history |
| `alerts` | `patient_id` ASC, `type` ASC, `created_at` DESC | Guardian: patient alert history |
| `users` | `role` ASC, `verification_status` ASC | Admin: pending doctor list |
| `users` | `role` ASC, `specialty` ASC, `city` ASC | Doctor search by specialty + city |
| `invite_codes` | `patient_id` ASC, `used` ASC | Patient's active invite code |

**Note:** Firestore allows max 200 composite indexes per database. We need ~14, well within limits. The `dose_logs` collection group index is required for the missed-dose cron job.

---

## 4. Access Patterns per Screen

### Patient screens

| Screen | Collection(s) read | Query | Estimated reads |
|--------|-------------------|-------|-----------------|
| **Home dashboard** | `daily_summaries/{today}` | 1 doc by date | **1** |
| | `medicines` (active only) | where `is_active == true` | **3–6** |
| **Medicine list** | `medicines` | all for user | **3–8** |
| **Today's doses** | `dose_logs` | where `scheduled_date == today` | **3–6** |
| **Adherence (7 days)** | `daily_summaries` | last 7 docs | **7** |
| **Add reading** | — | write only | **0** |
| **Reading history** | `readings` | last 30 by type | **30** |
| **Chat (open session)** | `chat_sessions/{id}/messages` | last 50 messages | **51** |
| **Chat (session list)** | `chat_sessions` | last 10 sessions | **10** |
| **Doctor search** | `users` | where `role==doctor`, `specialty`, `city` | **5–20** |
| **Appointment list** | `appointments` | where `patient_id`, last 10 | **10** |
| **Family (guardians)** | `guardian_links` | where `patient_id`, `status==active` | **1–3** |
| **Profile** | `users/{uid}` | 1 doc | **1** |

### Guardian screens

| Screen | Collection(s) read | Estimated reads |
|--------|-------------------|-----------------|
| **Guardian dashboard** (per patient) | `daily_summaries/{today}` + `users/{patient}` | **2** |
| **Alert history** | `alerts` where `recipient_id` | **10–20** |
| **Patient readings** | `readings` (via API, last 7 days) | **14** |

### Doctor screens

| Screen | Collection(s) read | Estimated reads |
|--------|-------------------|-----------------|
| **Appointment requests** | `appointments` where `doctor_id`, `status==requested` | **5–10** |
| **Patient summary (PDF)** | `users/{patient}` + medicines + readings + dose_logs + chat summary | **~30** |

### Cron job

| Action | Collections | Estimated per run |
|--------|-------------|-------------------|
| **Missed-dose check** | `dose_logs` (collection group query: `status == pending, scheduled_at < cutoff`) | **1 query + N result reads** (N = number of overdue doses across all users, typically 0–10) |
| | Write: update status + daily_summary + create alert | **3 writes per missed dose** |

---

## 5. Estimated Daily Reads/Writes per User

### Assumptions
- 1 active patient with 4 medicines (6 daily doses)
- Opens app 5 times/day
- 1 guardian checking 2 times/day
- 1 chat session with 10 messages/day
- 2 readings/day
- Cron runs 144 times/day (every 10 min)

### Patient daily usage

| Action | Reads | Writes |
|--------|-------|--------|
| Open home dashboard (×5) | 5 × 7 = **35** | 0 |
| View today's doses (×3) | 3 × 6 = **18** | 0 |
| Mark doses taken (×6) | 0 | 6 dose_logs + 6 summary updates = **12** |
| Add 2 readings | 0 | 2 readings + 2 summary updates = **4** |
| Chat (10 messages) | **51** (open session) | 20 (10 user + 10 assistant msgs) + 2 session updates + 10 usage counter updates = **32** |
| View weekly adherence (×1) | **7** | 0 |
| Browse doctors (×1) | **15** | 0 |
| View appointments (×1) | **10** | 0 |
| **Patient subtotal** | **~136 reads** | **~48 writes** |

### Guardian daily usage

| Action | Reads | Writes |
|--------|-------|--------|
| View dashboard (×2) | 2 × 2 = **4** | 0 |
| View alert history (×1) | **15** | 0 |
| **Guardian subtotal** | **~19 reads** | **~0 writes** |

### Cron job daily

The missed-dose cron uses a **collection-group query** on `dose_logs` (`status == "pending" AND scheduled_at < cutoff`). This is a single query per cron run, not per user. Firestore charges 1 read per document returned plus 1 read for the query itself.

| Action | Reads | Writes |
|--------|-------|--------|
| 144 cron runs × (1 query + ~0-2 overdue docs on average) | **~432** | 0 |
| Process ~1 missed dose/day | 0 | **~3** |
| **Cron subtotal (global, not per user)** | **~432 reads** | **~3 writes** |

### Daily total per patient-guardian pair

| Metric | Count |
|--------|-------|
| **Reads** | ~155 (per user) + ~432 (cron, shared across all users) |
| **Writes** | ~48 (per user) + ~3 (cron, shared) |

### Firebase Spark Free Tier Comparison

| Resource | Spark limit/day | Our estimate | Max users before limit |
|----------|----------------|--------------------------|----------------------|
| **Reads** | 50,000 | ~155/user/day + ~432 cron (shared) | **~320 users** |
| **Writes** | 20,000 | ~48/user/day + ~3 cron | **~416 users** |
| **Storage** | 1 GB | ~2 MB per user (estimate) | **~500 users** |

> **Note:** The cron job's collection-group query cost is **not** per-user. It runs a single query that returns only the overdue dose_log documents across all users. With typical usage (most doses are taken on time), each cron run returns very few documents. This is much cheaper than the per-user-query approach described in earlier versions of this document.

---

## 6. Collection Group Index for Missed-Dose Cron

The missed-dose cron requires a **collection group index** on the `dose_logs` subcollection:

```python
# Collection group query (crosses all users' dose_logs subcollections)
db.collection_group("dose_logs")
  .where("status", "==", "pending")
  .where("scheduled_at", "<", cutoff_time)  # cutoff = now - MISSED_GRACE_MINUTES
```

This requires a **collection group composite index** on `dose_logs` with fields:
- `status` ASC
- `scheduled_at` ASC

This index must be deployed to Firestore (via `firestore.indexes.json` or the Firebase console) before the cron job can run.

---

## 7. Data Retention and Cleanup

| Data | Retention | Cleanup method |
|------|-----------|----------------|
| `dose_logs` | 90 days | Cron job deletes logs older than 90 days (Phase 2) |
| `chat_sessions/messages` | 30 days of messages | Archive or delete old messages (Phase 2) |
| `daily_summaries` | 90 days | Keep for trend analysis, then archive |
| `alerts` | 60 days | Auto-delete old alerts |
| `invite_codes` | Delete after 48h or on use | Cron cleanup or TTL |
| `usage` | 90 days | Delete old usage docs |
| All user data | On account deletion | Cascade delete all subcollections |

> **Note:** Firestore does not support TTL natively. Cleanup requires a scheduled job or manual deletion. For MVP, manual cleanup is acceptable.
