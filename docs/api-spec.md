# ShebaBondhu: API Specification

Version 1.0 | 22 October 2026

---

## Conventions

- **Base URL:** `https://api.shebabondhu.com` (production) / `http://localhost:8000` (dev)
- **Auth:** All endpoints require `Authorization: Bearer <firebase_id_token>` unless marked `[public]` or `[cron]`.
- **Roles:** `patient`, `guardian`, `doctor`, `admin`. Each endpoint lists its allowed roles.
- **Response format:** All responses are JSON. Errors use the standard error envelope:
  ```json
  { "error": { "code": "ERROR_CODE", "message": "Human-readable message", "details": {}, "request_id": "uuid" } }
  ```
- **Pagination:** List endpoints accept `?limit=N&cursor=<last_doc_id>` (cursor-based, Firestore-friendly).
- **Timestamps:** ISO 8601 with timezone (`2026-10-22T08:00:00+06:00`).

---

## 1. Auth Module

### 1.1 Register

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/auth/register` |
| **Auth dependency** | `get_firebase_user` (token only — no existing user doc required) |
| **Screen** | Registration Step 1 |
| **Description** | Creates the user document in Firestore after Firebase Auth sign-in. Accepted roles: `patient`, `guardian`, `doctor`. Doctors are created with `verification_status = "pending"`. |

**Request body:**

```json
{
  "name": "Rahela Begum",
  "date_of_birth": "1964-03-15",
  "gender": "female",
  "role": "patient",
  "language": "bn",
  "phone": "+8801712345678"
}
```

`role` must be one of `patient`, `guardian`, or `doctor`. The `admin` role cannot be self-assigned.

**Response (201):**

```json
{
  "uid": "firebase-uid-abc123",
  "name": "Rahela Begum",
  "role": "patient",
  "language": "bn",
  "created_at": "2026-10-22T10:00:00+06:00"
}
```

**Errors:**
- `409 ALREADY_REGISTERED` — User document already exists.
- `422 VALIDATION_ERROR` — Missing or invalid fields (including invalid role).

---

> **Auth dependency design:**
>
> - `get_firebase_user(token)` — Verifies the Firebase ID token only. Returns the decoded token (uid, email). Used by `/auth/register` where no user doc exists yet.
> - `get_current_user(token)` — Verifies the token AND loads the user doc from Firestore. Returns the full user object. Used by all other authenticated endpoints. If the user doc does not exist, the request is rejected.

---

## 2. Profile Module

### 2.1 Get current user profile

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/me` |
| **Auth dependency** | `get_firebase_user` (token only) |
| **Screen** | App startup, Profile screen |
| **Description** | Returns the user profile. Used at app startup to determine whether the user has registered. |

**Response (200):** Full user document (fields vary by role).

**Errors:**
- `404 NOT_REGISTERED` — No user document found for this Firebase UID. App should redirect to registration.

> **Note:** This endpoint returns `404 NOT_REGISTERED` (not 401) when the user has a valid Firebase token but no user doc in Firestore. This distinguishes "not registered" from "bad/expired token" (which is a 401 from the auth middleware).

---

### 2.2 Update profile

| | |
|---|---|
| **Method** | `PATCH` |
| **Path** | `/me` |
| **Roles** | `patient`, `guardian`, `doctor` |
| **Screen** | Registration Step 2, Profile edit screen |

**Request body (partial update):**

```json
{
  "conditions": ["diabetes", "hypertension"],
  "allergies": ["penicillin"],
  "blood_group": "B+",
  "height_cm": 155,
  "weight_kg": 65,
  "emergency_contact": "+8801798765432"
}
```

**Response (200):** Updated user document.

**Errors:**
- `422 VALIDATION_ERROR` — Invalid field values.

---

### 2.3 Give consent

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/me/consent` |
| **Roles** | `patient`, `guardian`, `doctor` |
| **Screen** | Consent screen (registration) |

**Request body:**

```json
{
  "consent_given": true
}
```

**Response (200):** `{ "consent_given": true, "consent_given_at": "..." }`

---

## 3. Medicine Module

### 3.1 List medicines

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/medicines` |
| **Roles** | `patient` |
| **Screen** | Medicine tab, Home dashboard |
| **Query params** | `?active_only=true` (default: true) |

**Response (200):**

```json
{
  "medicines": [
    {
      "id": "med-001",
      "name": "Metformin",
      "dose": "500mg",
      "frequency": "twice",
      "times": ["08:00", "20:00"],
      "instructions": "After meals",
      "is_active": true
    }
  ]
}
```

---

### 3.2 Add medicine

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/medicines` |
| **Roles** | `patient` |
| **Screen** | Add medicine screen |

**Request body:**

```json
{
  "name": "Metformin",
  "dose": "500mg",
  "frequency": "twice",
  "times": ["08:00", "20:00"],
  "instructions": "After meals",
  "start_date": "2026-10-22"
}
```

**Response (201):** Created medicine document.

**Side effects:**
- Returns updated local notification schedule for the client to set.

---

### 3.3 Update medicine

| | |
|---|---|
| **Method** | `PATCH` |
| **Path** | `/medicines/{medicine_id}` |
| **Roles** | `patient` |
| **Screen** | Edit medicine screen |

---

### 3.4 Delete (deactivate) medicine

| | |
|---|---|
| **Method** | `DELETE` |
| **Path** | `/medicines/{medicine_id}` |
| **Roles** | `patient` |
| **Screen** | Medicine list |
| **Note** | Soft delete: sets `is_active = false`. |

---

### 3.5 Get today's doses

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/medicines/doses/today` |
| **Roles** | `patient` |
| **Screen** | Home dashboard, Medicine tab |

**Lazy generation:** If today's dose_log documents do not yet exist, this endpoint generates them from the patient's active medicine schedules before returning the response. Dose log IDs are deterministic: `{date}_{time}_{medicine_id}` (e.g., `20261022_0800_med-001`).

**Response (200):**

```json
{
  "date": "2026-10-22",
  "doses": [
    {
      "id": "20261022_0800_med-001",
      "medicine_id": "med-001",
      "medicine_name": "Metformin",
      "scheduled_time": "08:00",
      "status": "taken",
      "taken_at": "2026-10-22T08:25:00+06:00",
      "taken_late": false
    },
    {
      "id": "20261022_2000_med-001",
      "medicine_id": "med-001",
      "medicine_name": "Metformin",
      "scheduled_time": "20:00",
      "status": "pending",
      "taken_at": null,
      "taken_late": false
    }
  ],
  "summary": {
    "total": 4,
    "taken": 2,
    "missed": 0,
    "pending": 2,
    "due": 3,
    "adherence_pct": 67,
    "adherence_status": "yellow"
  }
}
```

> **Adherence calculation:** `adherence_pct` and `adherence_status` are computed only over doses already due (taken + missed + overdue pending). `due = taken + missed + (pending doses whose scheduled_time + MISSED_GRACE_MINUTES < now)`. If nothing is due yet (e.g., early morning before first dose), `adherence_pct = 100` and `adherence_status = "green"`.
```

---

### 3.6 Record dose (mark as taken)

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/medicines/doses` |
| **Roles** | `patient` |
| **Screen** | Home dashboard ("Taken" button), notification action |
| **Description** | Transitions a dose from `pending` or `missed` to `taken`. |

**Request body:**

```json
{
  "dose_log_id": "20261022_0800_med-001",
  "taken_at": "2026-10-22T08:25:00+06:00"
}
```

**Response (200):**

```json
{
  "id": "20261022_0800_med-001",
  "status": "taken",
  "taken_at": "2026-10-22T08:25:00+06:00",
  "taken_late": true
}
```

**Allowed transitions:** `pending → taken`, `missed → taken`.

**`taken_late` (boolean):** Set to `true` if the dose was already missed (i.e., the previous status was `missed`) or if `taken_at` is more than `MISSED_GRACE_MINUTES` after the scheduled time.

**Side effects:**
- Updates `daily_summaries/{today}`.
- If the dose was previously `missed`: adjusts the daily summary (`missed_doses -= 1`, `taken_doses += 1`) and sends a "dose taken" push notification to all connected guardians.

**Errors:**
- `404 NOT_FOUND` — Dose log not found.
- `409 CONFLICT` — Dose is already in `taken` status.

---

### 3.7 Get weekly adherence

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/medicines/adherence` |
| **Roles** | `patient` |
| **Screen** | Adherence screen |
| **Query params** | `?days=7` (default 7) |

**Response (200):**

```json
{
  "days": [
    { "date": "2026-10-22", "adherence_pct": 75, "status": "yellow" },
    { "date": "2026-10-21", "adherence_pct": 100, "status": "green" }
  ],
  "average_pct": 87.5
}
```

---

## 4. Reading Module

### 4.1 Add reading

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/readings` |
| **Roles** | `patient` |
| **Screen** | Add reading screen |

**Request body (sugar):**

```json
{
  "type": "sugar",
  "value": 180,
  "context": "fasting",
  "recorded_at": "2026-10-22T07:00:00+06:00",
  "notes": ""
}
```

**Request body (blood pressure):**

```json
{
  "type": "blood_pressure",
  "value": 140,
  "value_secondary": 90,
  "recorded_at": "2026-10-22T07:00:00+06:00"
}
```

**Response (201):** Created reading document.

**Side effects:**
- Updates `daily_summaries/{today}` with latest reading.
- If the reading triggers a safety rule (e.g., sugar > 400), raises an event that the Triage Agent + Guardian Alert Agent can process.

**Errors:**
- `422 VALIDATION_ERROR` — Value out of reasonable range (sugar: 20–600, systolic: 60–300, diastolic: 30–200).

---

### 4.2 Get readings

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/readings` |
| **Roles** | `patient` |
| **Screen** | Reading history screen |
| **Query params** | `?type=sugar&days=30&limit=50` |

**Response (200):**

```json
{
  "readings": [ ... ],
  "trend": {
    "type": "sugar",
    "direction": "stable",
    "average_7d": 165,
    "average_30d": 172
  }
}
```

---

## 5. Chat Module (Sheba AI)

### 5.1 Send message

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/chat/messages` |
| **Roles** | `patient` |
| **Screen** | Sheba AI chat screen |
| **Rate limit** | 50 messages/user/day |

**Request body:**

```json
{
  "session_id": "session-001",
  "content": "আমার মাথা ঘুরছে, সুগার ৩২০",
  "language": "bn",
  "location": { "lat": 23.8103, "lng": 90.4125 }
}
```

If `session_id` is null, a new session is created.

`location` is optional. If provided, the coordinates are included in any guardian emergency alert triggered by this message.

**Response (200):**

```json
{
  "session_id": "session-001",
  "user_message": {
    "id": "msg-001",
    "role": "user",
    "content": "আমার মাথা ঘুরছে, সুগার ৩২০",
    "created_at": "2026-10-22T14:00:00+06:00"
  },
  "assistant_message": {
    "id": "msg-002",
    "role": "assistant",
    "content": "আপনার সুগার অনেক বেশি...",
    "severity": "red",
    "metadata": {
      "show_emergency_card": true,
      "nearest_hospitals": true
    },
    "created_at": "2026-10-22T14:00:02+06:00"
  }
}
```

**Side effects:**
- If `severity == "red"`: Guardian Alert Agent sends emergency push to all connected guardians.
- If `severity == "yellow"`: Guardian gets summary-only notification.
- Emergency alert data: patient name, emergency notice, latest reading, location.

**Errors:**
- `429 RATE_LIMITED` — Daily message limit exceeded.
- `503 LLM_UNAVAILABLE` — LLM provider is down; response includes rule-based fallback if possible.

---

### 5.2 Get chat sessions

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/chat/sessions` |
| **Roles** | `patient` |
| **Screen** | Chat screen (session list) |
| **Query params** | `?limit=10&cursor=<id>` |

**Response (200):**

```json
{
  "sessions": [
    {
      "id": "session-001",
      "title": "মাথা ঘোরা নিয়ে",
      "last_severity": "red",
      "message_count": 12,
      "updated_at": "2026-10-22T14:05:00+06:00"
    }
  ]
}
```

---

### 5.3 Get session messages

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/chat/sessions/{session_id}/messages` |
| **Roles** | `patient` |
| **Screen** | Chat screen (message history) |
| **Query params** | `?limit=50&cursor=<id>` |

---

## 6. Doctor Module

### 6.1 Search doctors

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/doctors/search` |
| **Roles** | `patient`, `guardian` |
| **Screen** | Doctor search screen |
| **Query params** | `?specialty=medicine&city=dhaka&area=dhanmondi&limit=20` |

**Response (200):**

```json
{
  "doctors": [
    {
      "id": "uid-dr-nasrin",
      "name": "Dr. Nasrin Akter",
      "specialty": "Medicine",
      "city": "Dhaka",
      "area": "Dhanmondi",
      "chamber_address": "Lab Aid Hospital, Dhanmondi",
      "consultation_fee": "800 BDT",
      "verification_status": "approved"
    }
  ]
}
```

**Note:** Only returns doctors with `verification_status == "approved"`.

---

### 6.2 Get doctor profile

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/doctors/{doctor_id}` |
| **Roles** | `patient`, `guardian` |
| **Screen** | Doctor profile screen |

---

### 6.3 Update doctor profile

| | |
|---|---|
| **Method** | `PATCH` |
| **Path** | `/doctors/me` |
| **Roles** | `doctor` |
| **Screen** | Doctor profile edit |

**Request body:**

```json
{
  "chamber_address": "Lab Aid Hospital, Dhanmondi",
  "consultation_fee": "800 BDT",
  "city": "Dhaka",
  "area": "Dhanmondi"
}
```

---

### 6.4 Get doctor suggestions (AI-powered)

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/doctors/suggestions` |
| **Roles** | `patient` |
| **Screen** | Chat screen (after yellow/red triage), Doctor tab |

Returns AI-recommended doctors based on the patient's conditions and latest triage result.

**Response (200):**

```json
{
  "suggestions": [
    {
      "doctor_id": "uid-dr-nasrin",
      "name": "Dr. Nasrin Akter",
      "specialty": "Medicine",
      "match_reason": "Specialist in diabetes management"
    }
  ],
  "based_on": "diabetes, recent high sugar reading"
}
```

---

## 7. Appointment Module

### 7.1 Request appointment

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/appointments` |
| **Roles** | `patient` |
| **Screen** | Doctor profile screen |

**Request body:**

```json
{
  "doctor_id": "uid-dr-nasrin",
  "requested_date": "2026-10-25",
  "notes": "High sugar, need consultation",
  "allow_summary": true
}
```

**Response (201):** Created appointment document.

**Side effects:**
- Sends FCM push to the doctor.

---

### 7.2 List appointments

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/appointments` |
| **Roles** | `patient`, `doctor` |
| **Screen** | Appointment list (patient), Doctor dashboard |
| **Query params** | `?status=requested&limit=20` |

Returns appointments filtered by the caller's role (patient sees theirs, doctor sees theirs).

---

### 7.3 Update appointment status

| | |
|---|---|
| **Method** | `PATCH` |
| **Path** | `/appointments/{appointment_id}` |
| **Roles** | `doctor`, `patient` |
| **Screen** | Doctor dashboard, Appointment detail |

**Request body:**

```json
{
  "status": "confirmed",
  "confirmed_date": "2026-10-25T10:00:00+06:00"
}
```

**Allowed transitions:**
- Doctor: `requested → confirmed`, `requested → cancelled`, `confirmed → completed`
- Patient: `requested → cancelled`, `confirmed → cancelled`

**Side effects:**
- Sends FCM push to the other party.

---

### 7.4 Upload prescription

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/appointments/{appointment_id}/prescription` |
| **Roles** | `doctor` |
| **Screen** | Doctor dashboard |
| **Note** | Phase 1: text-only prescription. Phase 2: file upload. |

**Request body:**

```json
{
  "medicines": [
    { "name": "Amlodipine", "dose": "5mg", "frequency": "once", "times": ["08:00"], "instructions": "Before breakfast" }
  ],
  "notes": "Continue Metformin. Add Amlodipine for BP control."
}
```

**Response (200):** Created prescription. Patient gets an FCM notification.

**Side effects:**
- Patient receives notification to review and confirm the prescription.
- On patient confirmation (separate endpoint), medicines are added to their list.

---

### 7.5 Confirm prescription (patient)

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/appointments/{appointment_id}/prescription/confirm` |
| **Roles** | `patient` |
| **Screen** | Notification or appointment detail |

Adds the prescribed medicines to the patient's medicine list and creates dose_logs for today's remaining scheduled times.

---

## 8. Guardian Module

### 8.1 Generate invite code

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/guardian/invite-code` |
| **Roles** | `patient` |
| **Screen** | Family tab (invite screen) |

**Response (201):**

```json
{
  "code": "A7X9K2BM",
  "expires_at": "2026-10-24T10:00:00+06:00"
}
```

Code is a random 8-character alphanumeric string. Invalidates any previous active code.

---

### 8.2 Connect with invite code

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/guardian/connect` |
| **Roles** | `guardian` |
| **Screen** | Family tab (connect screen) |

**Request body:**

```json
{
  "invite_code": "RAHELA-7X9K"
}
```

**Response (201):** Guardian link document (status: "pending").

**Side effects:**
- Patient receives FCM notification to accept/decline.

**Errors:**
- `404 CODE_NOT_FOUND` — Invalid or expired code.
- `409 ALREADY_CONNECTED` — Guardian already linked to this patient.
- `429 RATE_LIMITED` — More than 5 failed connect attempts per hour for this guardian.

---

### 8.3 Accept/decline guardian request

| | |
|---|---|
| **Method** | `PATCH` |
| **Path** | `/guardian/links/{link_id}` |
| **Roles** | `patient` |
| **Screen** | Family tab (pending requests) |

**Request body:**

```json
{
  "action": "accept"
}
```

`action` = "accept" or "decline".

---

### 8.4 Revoke guardian access

| | |
|---|---|
| **Method** | `DELETE` |
| **Path** | `/guardian/links/{link_id}` |
| **Roles** | `patient` |
| **Screen** | Family tab |

Sets `status = "revoked"`. Guardian loses access immediately.

---

### 8.5 List my guardians (patient)

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/guardian/my-guardians` |
| **Roles** | `patient` |
| **Screen** | Family tab |

---

### 8.6 List my patients (guardian)

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/guardian/my-patients` |
| **Roles** | `guardian` |
| **Screen** | Guardian dashboard |

---

### 8.7 Get patient status (guardian view)

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/guardian/patients/{patient_id}/status` |
| **Roles** | `guardian` |
| **Screen** | Guardian dashboard |

**Authorization:** Checks that an active guardian_link exists between the caller and the patient.

**Response (200):**

```json
{
  "patient_name": "Rahela Begum",
  "today": {
    "adherence_status": "yellow",
    "adherence_pct": 75,
    "total_doses": 4,
    "taken_doses": 3,
    "missed_doses": 1,
    "latest_sugar": { "value": 180, "context": "fasting", "recorded_at": "..." },
    "latest_bp": { "systolic": 140, "diastolic": 90, "recorded_at": "..." },
    "has_emergency": false
  },
  "weekly_adherence": [ ... ],
  "whatsapp_call_url": "https://wa.me/8801712345678"
}
```

**Privacy:** No chat content. No full medical history. Only status data.

---

### 8.8 Get patient readings (guardian view)

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/guardian/patients/{patient_id}/readings` |
| **Roles** | `guardian` |
| **Screen** | Guardian dashboard (readings trend) |
| **Query params** | `?type=sugar&days=7` |

---

### 8.9 Get alert history (guardian)

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/guardian/alerts` |
| **Roles** | `guardian` |
| **Screen** | Guardian alert history |
| **Query params** | `?limit=20&cursor=<id>` |

---

## 9. Notification Module

### 9.1 Update FCM token

| | |
|---|---|
| **Method** | `PUT` |
| **Path** | `/notifications/fcm-token` |
| **Roles** | `patient`, `guardian`, `doctor` |
| **Screen** | App startup |

**Request body:**

```json
{
  "token": "fcm-device-token-xyz",
  "device_id": "device-abc",
  "platform": "android"
}
```

---

### 9.2 Get notification history

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/notifications` |
| **Roles** | `patient`, `guardian`, `doctor` |
| **Screen** | Notification bell / alert history |
| **Query params** | `?limit=20&cursor=<id>` |

---

### 9.3 Mark notification as read

| | |
|---|---|
| **Method** | `PATCH` |
| **Path** | `/notifications/{alert_id}/read` |
| **Roles** | `patient`, `guardian`, `doctor` |
| **Screen** | Any notification |

---

## 10. PDF Module

### 10.1 Generate doctor summary PDF

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/pdf/doctor-summary` |
| **Roles** | `patient` |
| **Screen** | Sheba AI tab, Doctor tab |
| **Response type** | `application/pdf` |

**Query params:** `?appointment_id=<id>` (optional, to tailor the summary for a specific appointment).

Generated on demand using WeasyPrint. Not stored. Includes:
- Basic details, conditions, allergies, medicines
- Recent readings and trends
- Adherence summary
- Recent symptom conversations (summary, not full chat)

---

### 10.2 View patient summary (doctor)

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/pdf/doctor-summary/{patient_id}` |
| **Roles** | `doctor` |
| **Screen** | Doctor dashboard (patient summary) |
| **Authorization** | Requires an active appointment where `patient_allows_summary == true` |

---

## 11. Admin Module

### 11.1 List pending doctor verifications

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/admin/doctors/pending` |
| **Roles** | `admin` |
| **Screen** | Admin web panel |

**Response (200):**

```json
{
  "doctors": [
    {
      "uid": "uid-dr-new",
      "name": "Dr. Karim",
      "specialty": "Cardiology",
      "bmdc_number": "A-12345",
      "verification_status": "pending",
      "created_at": "2026-10-22T09:00:00+06:00"
    }
  ]
}
```

---

### 11.2 Verify/reject doctor

| | |
|---|---|
| **Method** | `PATCH` |
| **Path** | `/admin/doctors/{doctor_id}/verify` |
| **Roles** | `admin` |
| **Screen** | Admin web panel |

**Request body:**

```json
{
  "action": "approve",
  "notes": "BMDC number verified"
}
```

`action` = "approve" or "reject".

**Side effects:**
- If approved: `verification_status = "approved"`, doctor becomes searchable.
- If rejected: `verification_status = "rejected"`, doctor is notified via FCM.

---

### 11.3 List all users (admin)

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/admin/users` |
| **Roles** | `admin` |
| **Screen** | Admin web panel |
| **Query params** | `?role=patient&limit=50` |

---

## 12. Emergency Module

### 12.1 Get nearest hospitals

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/emergency/hospitals` |
| **Roles** | `patient` |
| **Screen** | Emergency screen, Sheba AI (red triage) |
| **Query params** | `?lat=23.8103&lng=90.4125&limit=5` |

Returns curated hospitals sorted by distance. Opens Google Maps for directions.

**Response (200):**

```json
{
  "hospitals": [
    {
      "name": "Dhaka Medical College Hospital",
      "address": "Secretariat Rd, Dhaka",
      "phone": "+880-2-555-0001",
      "distance_km": 2.3,
      "maps_url": "https://maps.google.com/?q=23.7260,90.3975"
    }
  ]
}
```

---

### 12.2 Trigger emergency alert

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/emergency/alert` |
| **Roles** | `patient` |
| **Screen** | SOS button |

**Request body:**

```json
{
  "location": { "lat": 23.8103, "lng": 90.4125 },
  "trigger": "manual_sos"
}
```

**Side effects:**
- Sends emergency push to all connected guardians.
- Creates an alert record.

---

## 13. Internal Cron Endpoints

### 13.1 Process missed doses

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/internal/cron/missed-doses` |
| **Auth** | `X-Cron-Secret` header (not Firebase token) |
| **Trigger** | cron-job.org every 10 minutes |

**Response (200):**

```json
{
  "processed": 3,
  "alerts_sent": 2,
  "errors": 0,
  "run_at": "2026-10-22T08:40:00+06:00"
}
```

**Logic:**
1. Collection-group query on `dose_logs`: `where status == "pending" AND scheduled_at < now - MISSED_GRACE_MINUTES`.
2. For each result: mark dose_log as `"missed"`, update the parent user's `daily_summaries/{today}`.
3. Group missed doses by patient, send one guardian alert per patient.

> **Required index:** Collection-group composite index on `dose_logs` with fields `status` ASC + `scheduled_at` ASC. This must be deployed to Firestore before the cron can run.

**Errors:**
- `403 FORBIDDEN` — Invalid or missing cron secret.

---

### 13.2 Generate daily dose logs

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/internal/cron/generate-doses` |
| **Auth** | `X-Cron-Secret` header |
| **Trigger** | cron-job.org daily at midnight (00:00 +06:00) |

Creates today's dose_log entries for all active patients based on their medicine schedules. Dose log IDs are deterministic (`{date}_{time}_{medicine_id}`), so re-running this endpoint is idempotent — existing dose_logs are not overwritten.

> **Note:** Doses are also generated lazily by `GET /medicines/doses/today` when a patient opens the app, so the cron serves as a safety net ensuring dose_logs exist for the missed-dose cron to query.

**Response (200):**

```json
{
  "users_processed": 5,
  "doses_created": 24,
  "run_at": "2026-10-22T00:00:05+06:00"
}
```

---

### 13.3 Health check

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/health` |
| **Auth** | `[public]` — no auth required |

**Response (200):**

```json
{
  "status": "ok",
  "version": "1.0.0",
  "firestore": "connected",
  "timestamp": "2026-10-22T08:00:00+06:00"
}
```

Used by Render health checks and uptime monitoring.

---

## Endpoint Summary Table

| # | Method | Path | Roles | Module |
|---|--------|------|-------|--------|
| 1 | POST | `/auth/register` | any authed (token only) | Auth |
| 2 | GET | `/me` | any authed (token only) | Profile |
| 3 | PATCH | `/me` | patient, guardian, doctor | Profile |
| 4 | DELETE | `/me` | patient, guardian, doctor | Profile |
| 5 | POST | `/me/consent` | all roles | Profile |
| 6 | GET | `/medicines` | patient | Medicine |
| 7 | POST | `/medicines` | patient | Medicine |
| 8 | PATCH | `/medicines/{id}` | patient | Medicine |
| 9 | DELETE | `/medicines/{id}` | patient | Medicine |
| 10 | GET | `/medicines/doses/today` | patient | Medicine |
| 11 | POST | `/medicines/doses` | patient | Medicine |
| 12 | GET | `/medicines/adherence` | patient | Medicine |
| 13 | POST | `/readings` | patient | Reading |
| 14 | GET | `/readings` | patient | Reading |
| 15 | POST | `/chat/messages` | patient | Chat |
| 16 | GET | `/chat/sessions` | patient | Chat |
| 17 | GET | `/chat/sessions/{id}/messages` | patient | Chat |
| 18 | GET | `/doctors/search` | patient, guardian | Doctor |
| 19 | GET | `/doctors/{id}` | patient, guardian | Doctor |
| 20 | PATCH | `/doctors/me` | doctor | Doctor |
| 21 | GET | `/doctors/suggestions` | patient | Doctor |
| 22 | POST | `/appointments` | patient | Appointment |
| 23 | GET | `/appointments` | patient, doctor | Appointment |
| 24 | PATCH | `/appointments/{id}` | patient, doctor | Appointment |
| 25 | POST | `/appointments/{id}/prescription` | doctor | Appointment |
| 26 | POST | `/appointments/{id}/prescription/confirm` | patient | Appointment |
| 27 | POST | `/guardian/invite-code` | patient | Guardian |
| 28 | POST | `/guardian/connect` | guardian | Guardian |
| 29 | PATCH | `/guardian/links/{id}` | patient | Guardian |
| 30 | DELETE | `/guardian/links/{id}` | patient | Guardian |
| 31 | GET | `/guardian/my-guardians` | patient | Guardian |
| 32 | GET | `/guardian/my-patients` | guardian | Guardian |
| 33 | GET | `/guardian/patients/{id}/status` | guardian | Guardian |
| 34 | GET | `/guardian/patients/{id}/readings` | guardian | Guardian |
| 35 | GET | `/guardian/alerts` | guardian | Guardian |
| 36 | PUT | `/notifications/fcm-token` | all roles | Notification |
| 37 | GET | `/notifications` | all roles | Notification |
| 38 | PATCH | `/notifications/{id}/read` | all roles | Notification |
| 39 | GET | `/pdf/doctor-summary` | patient | PDF |
| 40 | GET | `/pdf/doctor-summary/{patient_id}` | doctor | PDF |
| 41 | GET | `/admin/doctors/pending` | admin | Admin |
| 42 | PATCH | `/admin/doctors/{id}/verify` | admin | Admin |
| 43 | GET | `/admin/users` | admin | Admin |
| 44 | GET | `/emergency/hospitals` | patient | Emergency |
| 45 | POST | `/emergency/alert` | patient | Emergency |
| 46 | POST | `/internal/cron/missed-doses` | cron | Cron |
| 47 | POST | `/internal/cron/generate-doses` | cron | Cron |
| 48 | GET | `/health` | public | Health |

**Total: 48 endpoints**
