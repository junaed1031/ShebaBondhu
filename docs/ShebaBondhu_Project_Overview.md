# ShebaBondhu: Project Overview

Prepared by the ShebaBondhu team | Version 1.1 | 22 October 2026

## 1. What is ShebaBondhu?

ShebaBondhu (roughly, “care friend”) is an AI-powered healthcare companion app, built first for Bangladesh. It helps a person manage their own health day to day, lets a trusted family member (a **guardian**) keep an eye on them from anywhere, and gives doctors a clear picture of the patient before a visit.

### The problem

- Many people, especially older adults and people with long-term conditions such as diabetes and high blood pressure, forget doses, skip readings and do not know when a symptom is serious.
- Family members often live in a different city or country and cannot check in every day.
- Doctors get short appointments and incomplete history, so patients must repeat their story every time.
- Most health apps are English-only and not designed for Bangladeshi users.

### Our answer

1. **A daily companion for the patient:** medicine reminders, reading logs, a Bangla/English AI assistant (text and voice), and simple daily health tips.
2. **A safety net for the family:** a guardian is alerted when doses are missed or something looks dangerous, and can see the patient’s status at a glance, only with the patient’s approval.
3. **A bridge to doctors:** the app finds suitable doctors, handles appointment requests, and generates a one-page medical summary PDF so the doctor understands the patient quickly.

## 2. Who Uses It

| Role | Who they are | What they do in the app |
| --- | --- | --- |
| **Patient** | Any adult, of any age, who wants to manage their health; mainly older adults and people with chronic conditions | Logs medicines and readings, chats with the AI assistant, books doctors, connects guardians |
| **Guardian** | A family member who cares for the patient | Receives alerts, sees the patient’s status, calls the patient, helps pick a doctor |
| **Doctor** | A verified medical doctor | Receives appointment requests, reads the patient’s summary (with permission), uploads prescriptions |
| **Admin** | The ShebaBondhu team | Manually verifies doctors before they go live |

## 3. Features at a Glance

- Registration in two short steps, in Bangla or English
- Home dashboard with today’s medicines, latest readings, a daily tip and a one-tap SOS button
- **Sheba AI**: chat assistant with Bangla voice input, symptom triage (green, yellow, red) and safety rules
- Medicine tracking with reminders, missed-dose follow-up and weekly adherence
- Doctor search, appointment requests and prescription history
- Auto-generated **doctor summary PDF**
- Guardian connection by invite code, with alerts by push notification and WhatsApp
- Emergency handling: nearest hospitals, 999 call button, instant guardian alert
- Report and prescription upload with automatic reading of the content (Phase 2)

## 4. The App Through the User’s Eyes (UI)

### 4.1 Registration and onboarding

Registration is split into two steps so that nobody gets tired before they start.

**Step 1: Account (about 30 seconds)**

- Choose language: Bangla or English
- Sign in with Google or email (Firebase Authentication; phone OTP comes later)
- Name, date of birth, gender
- Choose a role: “For myself” (Patient), “For a family member” (Guardian), or Doctor

**Step 2: Health profile (optional, can be finished later from Profile)**

- Known conditions (checklist plus “other”), for example diabetes or high blood pressure
- Allergies
- Current medicines: name, dose, timing
- Blood group, height, weight
- One emergency contact number

**Consent screen (required):** explains how health data is used, states that the AI gives guidance and is not a replacement for a doctor, and makes clear that family members see data only if the patient allows it.

**Guardian registration** is shorter: sign-in, name, role, and a phone number (used for WhatsApp calls). The guardian then connects to a patient using an invite code (see Section 7).

**Doctor registration** asks for name, specialty, BMDC registration number, supporting document, and chamber or hospital. The account stays inactive until an admin verifies it manually.

### 4.2 Home dashboard (patient)

From top to bottom:

1. **Greeting and date**, for example “Assalamu alaikum, Rahela apa”.
2. **Today’s medicines**: a card listing each dose and time, with a big “Taken” button.
3. **Health snapshot**: latest sugar or blood pressure reading (entered manually by the user) and a small trend.
4. **Today’s tip**: a personalized suggestion from the Lifestyle Agent.
5. **Next appointment**, if any.
6. **Family status**: who is connected as guardian, or a prompt to connect one.
7. **SOS button**, always visible: quick access to emergency actions.

### 4.3 Navigation: five tabs

**Home | Sheba AI | Medicine | Doctor | Family**

**Sheba AI** is a chat screen. The patient types or speaks in Bangla or English, for example “I feel dizzy and my sugar is 280”. The reply is shown with a short disclaimer. From here the patient can also generate a **doctor summary PDF**.

**Medicine** shows the medicine list, schedule and history of taken and missed doses, plus weekly adherence. New medicines are added manually or, in Phase 2, by photographing a prescription.

**Doctor** lets the patient search by specialty or symptom, view doctor profiles and send an appointment request. It also holds past appointments, prescription history and the summary PDF.

**Family** lists connected guardians, lets the patient invite a new one, and lets them revoke access at any time.

**Profile** (top corner) covers health profile editing, report upload, language and logout.

### 4.4 Guardian dashboard

- Today’s medicine status for the patient, color coded: green (all taken), yellow (late), red (missed)
- Latest sugar and blood pressure readings with a weekly trend
- Alert history
- Shared medical reports
- **Call** button, which opens a WhatsApp call to the patient
- **Doctor** button, showing a list of suggested doctors so the guardian can help arrange a visit
- If a patient has several guardians, each one is connected separately

### 4.5 Doctor view

- List of appointment requests and upcoming visits
- The patient’s summary PDF, visible only after the patient allows it
- Prescription upload; the patient confirms before medicines are added to their list

### 4.6 Admin

A simple back-office step where the team reviews each doctor’s BMDC number and documents and approves or rejects the account. In the MVP this is a manual flag on the doctor’s record.

## 5. The AI Agent System

Behind the screens, an **Orchestrator** receives every user message and system event and decides which agent should handle it. Agents are deliberately small: mostly plain rules or functions with at most one language-model call. This keeps running costs low.

| Agent | What it does | When it runs |
| --- | --- | --- |
| **Triage Agent** | Rule-based safety check first, then the language model. Classifies a symptom conversation as green (minor), yellow (see a doctor soon) or red (emergency). | When the patient describes symptoms |
| **Medicine Agent** | Sends reminders, follows up on missed doses, tracks adherence, checks for known medicine interactions | On schedule, and when a dose is missed |
| **Guardian Alert Agent** | Decides what the guardian should be told and when, and sends it by push notification and WhatsApp | When another agent raises an event |
| **Doctor Match Agent** | Suggests suitable doctors, supports appointment requests, and builds the doctor summary PDF | When the patient wants a doctor |
| **Records Agent** | Reads uploaded reports and prescriptions (text extraction) and writes a short summary | On upload |
| **Intake Agent** | Turns the extracted content into a structured medical history in the patient’s profile | After the Records Agent finishes |
| **Lifestyle Agent** | Gives personalized daily tips on food, activity and sleep | Each morning, or when readings change |

The Records and Intake agents work together as one upload pipeline: first the content is read, then it is stored in a structured form.

**Build order**

- **Phase 1 (core):** Orchestrator, Triage, Medicine, Guardian Alert, Doctor Match
- **Phase 2:** Records and Intake pipeline, Lifestyle

## 6. A Day in the Life: End-to-End Scenario

**Characters:** Rahela Begum (62) lives in Dhaka with diabetes and high blood pressure; she uses a smartphone but is not very comfortable with technology. Her son Sajid (32) works in Chattogram and worries about her. Dr. Nasrin is a verified medicine specialist.

**Setup.** Sajid installs the app on his mother’s phone, registers her as a patient in Bangla and fills in her medicines. Then he registers as a guardian on his own phone and connects using Rahela’s invite code. Rahela accepts the request.

**8:00 AM.** The Medicine Agent sends a reminder: “Time for your Metformin.” Rahela does not notice.

**8:30 AM.** A second reminder, in simpler words.

**9:30 AM.** The dose is still not marked. The Guardian Alert Agent notifies Sajid: “Rahela apa has not taken her morning medicine.” Sajid calls his mother through the app’s WhatsApp call button. She takes the tablet and taps the tick mark in the app, so the status turns green.

**2:00 PM.** Rahela opens Sheba AI and says by voice: “I feel dizzy, my sugar is 320.”

1. The Orchestrator sends the message to the Triage Agent.
2. A safety rule recognises the pattern of very high sugar plus dizziness and marks it **red**.
3. The app tells her this may be serious, to call someone nearby or go to a hospital now, and shows the nearest hospitals and a 999 button.
4. The Guardian Alert Agent sends Sajid an urgent alert by push and WhatsApp.

**If it had been yellow instead:** the app would advise seeing a doctor within a few days. The Doctor Match Agent would suggest doctors and generate a summary PDF, so the doctor can understand Rahela’s condition at a glance. Sajid would receive only a short summary, not an emergency alert.

**Later that week.** Rahela requests an appointment with Dr. Nasrin and allows her to read the summary. After the visit the doctor uploads a prescription. Rahela confirms it and the new medicines appear in her Medicine tab.

**9:00 PM.** Evening reminder, Rahela taps “Taken”, and the day’s adherence is recorded for the weekly view.

## 7. Guardian Connection and Privacy

1. The guardian registers with the Guardian role.
2. In the Family tab they enter the patient’s **invite code**.
3. The patient receives a request: “Sajid wants to connect as your guardian. Accept or decline?”
4. When the patient accepts, the guardian can see: medicine status, health readings (sugar and blood pressure), emergency alerts, and medical reports.
5. The patient can **revoke** access at any time from the Family tab.

**What guardians never see:** the patient’s private chats with Sheba AI.

## 8. Emergency Handling

- Every symptom conversation is checked by fixed safety rules before the language model answers. The AI never relies on itself alone for emergencies.
- A **red** result shows clear, urgent instructions, the nearest hospitals and a 999 call button.
- The guardian alert for a red event contains three things: that an emergency happened, the patient’s location, and the latest reading. This applies even if other details are not normally shared.
- The app always states that it gives guidance only and does not diagnose.

## 9. The Doctor Summary PDF

A one-document snapshot designed so a doctor can understand the patient in a minute. It can be generated from the Sheba AI tab or the Doctor tab and includes:

- Basic details: age, gender, blood group, height and weight
- Known conditions, allergies and current medicines
- Recent sugar and blood pressure readings and their trend
- Medicine adherence, including missed doses
- Recent symptoms and a short summary of the AI conversation
- Key points from uploaded reports (from Phase 2 onward)

The patient decides whether a doctor can see it.

## 10. Technical Architecture

| Layer | Choice | Why |
| --- | --- | --- |
| Mobile app | Flutter (Android first) | One codebase, good Bangla text support, built-in speech recognition options |
| Backend | Python with FastAPI, one modular service in a Docker container | Fast to build, automatic API documentation, easy to move between hosts. Verifies the Firebase ID token on every request |
| Database | Cloud Firestore | Same ecosystem as Auth and push, generous free quota, does not sleep or expire. Only the backend writes to it; client access is blocked by security rules |
| Authentication | Firebase Authentication (email and Google) | Secure and free at small scale |
| Notifications | Firebase Cloud Messaging for push; medicine reminders as local notifications on the phone; WhatsApp alerts as a later channel | Push and local reminders are free. WhatsApp automatic alerts need a business account and paid messages |
| AI | Hosted language-model API behind a provider-independent wrapper, plus rule-based safety checks and a small curated health knowledge base | No model training needed at the start; pay per use; the model can be swapped later |
| Doctor PDF | WeasyPrint with a Bangla font, generated on demand | Correct Bangla rendering, nothing to store |
| Hosting | Render (free for development and demo, small always-on instance for the pilot), with an external cron for missed-dose checks | Cheap and simple |
| Monitoring | Firebase Crashlytics and Sentry | Early warning on free tiers |
| File storage | Decided in Phase 2 | Cloud Storage for Firebase needs a billing account |

**How the pieces connect:** the Flutter app talks only to the FastAPI backend over a secure REST API; the only exception is signing in with Firebase. The backend contains modules for authentication, profiles, medicines, doctors and appointments, notifications and the AI agents. It reads and writes Firestore and calls the language-model API only when needed.

**Design principles**

1. One modular service instead of many microservices.
2. The app talks only to the backend, so permissions and emergency rules live in one place.
3. A repository layer sits between business logic and the database, so the database can be changed later.
4. Docker, environment-based configuration and automated deployment from day one.
5. The AI layer sits behind a single interface, so models can be swapped later without touching the rest of the app.

## 11. Core Data Entities

A high-level list, to be detailed in the database design: users and profiles, guardian links and permissions, medicines and dose logs, health readings, chat sessions and messages, uploaded reports and extracted history, doctors, appointments, alerts and notifications, and health knowledge chunks for retrieval.

## 12. Cost Strategy and Growth Path

**Goal:** finish the MVP with almost no infrastructure cost, then scale as funding arrives.

- **MVP:** free tiers for the database, authentication, push notifications and development hosting. The real running costs are language-model usage and, for the pilot, a small always-on host. LLM cost is controlled with response caching, token limits, per-user daily limits and cheaper models for simple tasks. Real user data is never sent to a free LLM tier.
- **Pilot:** a small group of real users, usage and feedback collected with consent.
- **Funded production:** managed hosting with auto-scaling, backups, a staging environment, a security review, a custom or fine-tuned Bangla health model, WhatsApp alerts, and partnerships with clinics and hospitals.

Free-tier limits change often, so they will be checked before final decisions. See the Tech Stack file for current figures and sources.

## 13. MVP Scope

**In the MVP**

- Patient, Guardian and Doctor roles, with manual doctor verification
- Registration with Firebase login
- Home, Sheba AI (with Bangla voice input), Medicine, Doctor and Family tabs
- Manual entry of sugar and blood pressure readings
- Phase 1 agents
- Doctor summary PDF
- Appointment requests (no payment)
- Guardian alerts by push, with WhatsApp added as a second channel once a business account and billing are ready

**Later (Phase 2 and beyond)**

- Report and prescription reading (Records and Intake pipeline)
- Lifestyle Agent
- Phone OTP login
- Connected medical devices
- Payments for appointments
- A custom Bangla health model

## 14. Safety, Privacy and Responsibility

- Health data is sensitive: all traffic is encrypted, only the minimum data is collected, and credentials are handled by Firebase.
- Sharing with guardians and doctors always requires the patient’s permission, and the patient can withdraw it.
- The AI gives guidance, not diagnosis, and always points to a doctor or emergency services when a case looks serious.
- Chat or health data is used to improve the system only with consent and in anonymised form.

## 15. Confirmed Decisions

1. Main users are adults of all ages; guardians are family members.
2. Roles: Patient, Guardian, Doctor (doctor included in the MVP), plus a manual admin check.
3. Login through Firebase Authentication (email and Google); phone OTP later.
4. Five tabs: Home, Sheba AI, Medicine, Doctor, Family.
5. Sugar and blood pressure readings are entered manually; no devices in the MVP.
6. Seven agents plus an Orchestrator, built in two phases as listed in Section 5.
7. Doctors are verified manually by an admin.
8. Emergency alerts show an emergency notice, location and latest reading.
9. Guardian access to medical reports is granted when the patient accepts the connection.
10. Guardian alerts go by push notification and WhatsApp (push first, WhatsApp as a second channel).
11. Bangla voice input is part of the MVP.
12. Doctor appointments are request and booking only, with no payment.
13. Database is Cloud Firestore; the app talks only to the FastAPI backend.

## 16. Next Steps

1. Detailed **Firestore schema** for all entities in Section 11.
2. Complete **API list** for the app, backend and agents.
3. Cost-conscious **deployment plan** and development timeline.
