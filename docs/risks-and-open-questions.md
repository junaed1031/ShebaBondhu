# ShebaBondhu: Risks and Open Questions

Version 1.0 | 22 October 2026

---

## Risk Register

### 🔴 High Risks

| # | Risk | Impact | Likelihood | Mitigation |
|---|------|--------|------------|------------|
| R1 | **Firestore Spark read limit exceeded** — The 50K reads/day free limit may be hit with as few as 16 active users without cron optimization, or ~112 with optimization. | Firestore stops responding or data is lost if unmonitored. | High (during pilot) | Use the `pending_doses` optimization from day one. Monitor reads/writes via Firebase console. Set up Firestore budget alerts. Consider moving to Blaze plan once a card is available. |
| R2 | **No payment card blocks scaling** — Without a card, cannot use Firebase Blaze, paid LLM APIs, WhatsApp Business, or Cloud Storage. | Stuck on free tiers. Cannot serve real users with real health data through the LLM (free tier may use data for model training). | High | Design everything to work within free limits. Use fake data with LLM free tier. Make getting a card the top priority for pilot launch. Document which features unlock with a card. |
| R3 | **LLM Bangla quality insufficient** — Gemini Flash may not handle medical Bangla well enough for symptom triage. | Incorrect triage could have health consequences. Users lose trust. | Medium | Safety rules catch critical cases before the LLM. Test with 30–50 Bangla prompts before committing to a model. The swap interface lets you switch models quickly. Always state "this is guidance, not diagnosis." |
| R4 | **Solo developer burnout / pace** — 66+ working days as a solo dev is ambitious. Unexpected issues (Bangla rendering, Firestore quirks, LLM prompting) will add time. | Project stalls or quality drops. | High | Stick to vertical slices — each delivers a working feature. Cut scope aggressively if behind. Skip polish (Slice 8) for the initial demo if needed. The walking skeleton (Phase 0+1) should be the first goal. |
| R5 | **Render free tier cold starts** — Free instances sleep after 15 minutes, taking ~60 seconds to wake. | Poor user experience. Missed-dose cron may time out on cold start. | Medium | Acceptable for development. For pilot/demo: upgrade to $7/month always-on. cron-job.org requests will wake the instance, but first cron of the day may be slow. |

---

### 🟡 Medium Risks

| # | Risk | Impact | Likelihood | Mitigation |
|---|------|--------|------------|------------|
| R6 | **Bangla PDF rendering issues** — WeasyPrint may not render all Bangla conjunct characters correctly (e.g., যুক্তবর্ণ). | PDF looks broken for Bangla users. | Medium | Test WeasyPrint + Noto Sans Bengali on day one (Slice 0.1). If broken, fall back to ReportLab or generate PDF client-side. |
| R7 | **Device speech recognition quality for Bangla** — On-device STT (Google's built-in) may struggle with Bangla medical terms, dialects, or older users' speech patterns. | Voice input is frustrating, users abandon the feature. | Medium | Voice input is a convenience, not a requirement. Text input always works. Test on real Android devices early. Cloud STT (Google Cloud Speech) is a fallback but needs a card. |
| R8 | **Firestore no-join data model complexity** — Denormalization means keeping multiple documents in sync (e.g., daily_summaries, medicine_name in dose_logs). | Data inconsistency if update logic has bugs. | Medium | Repository layer handles all denormalization. Write integration tests for consistency. Consider Firestore batch writes (atomic across up to 500 docs). |
| R9 | **Guardian privacy leak** — A bug in the guardian endpoints could expose patient chat data or more health info than intended. | Privacy violation, loss of trust. | Low (but high impact) | Explicit allowlist of fields returned by guardian endpoints. Never query chat collections from guardian routes. Test with "guardian cannot see X" negative test cases. Code review all guardian endpoints carefully. |
| R10 | **Prompt injection in chat** — Malicious or accidental prompt injection through user messages could make the LLM behave unexpectedly. | LLM gives dangerous medical advice or reveals system prompts. | Low–Medium | Sanitize user input before injection into prompts. Use structured output (JSON mode) for triage classification. Safety rules always run before LLM. System prompt includes guardrails. Rate limiting prevents abuse. |
| R11 | **FCM delivery reliability** — Push notifications may be unreliable on some Android devices (Chinese OEMs, battery optimization, Doze mode). | Guardian misses critical alerts. | Medium | Document that the user should disable battery optimization for the app. Show in-app notification history as backup. WhatsApp channel (Phase 2) is more reliable. |
| R12 | **Cron-job.org reliability** — External free cron service may have downtime or rate limits. | Missed doses not detected for a period. | Low–Medium | cron-job.org is well-established but still a free service. Monitor via the `/health` endpoint. Have a manual fallback (admin can trigger the cron endpoint). Consider Render's built-in cron on the $7 plan. |

---

### 🟢 Low Risks

| # | Risk | Impact | Likelihood | Mitigation |
|---|------|--------|------------|------------|
| R13 | **Firebase Auth outage** — Firebase Auth service goes down. | Users cannot log in. | Very low | Firebase Auth has 99.95% SLA. App caches the ID token, so already-logged-in users are unaffected until token expires (1 hour). |
| R14 | **LLM API cost spiral** — If the app gets unexpected traction, LLM API costs could grow. | Unexpected bills once on paid tier. | Low | Daily per-user rate limit (50 messages). Token limit per request (500). Response caching for common queries. Monitor usage closely. |
| R15 | **Firestore pricing changes** — Google could change Spark plan limits. | Need to migrate or pay. | Low | Repository layer makes migration to PostgreSQL feasible. Stay informed about Firebase announcements. |

---

## Open Questions

### Must resolve before building

| # | Question | Options | Impact | Suggested resolution |
|---|----------|---------|--------|---------------------|
| Q1 | **When can you get an international/virtual card?** | Soon / Not soon / Never | Determines when you can launch a pilot with real users and a paid LLM tier. | If "never" for the foreseeable future: explore Bkash/Nagad → virtual card services, or find a team member with a card. All infrastructure decisions assume no card for now. |
| Q2 | **Hospital list: how many hospitals to curate initially?** | 10 major hospitals / Top hospitals per division / Crowdsource | Affects usefulness of the emergency feature. | Start with 20–30 major hospitals in Dhaka + divisional capitals. Add more from user feedback. Store as a JSON asset, not a database collection. |
| Q3 | **What Bangla safety rule terms to include?** | Need a list of Bangla medical emergency keywords. | Triage Agent accuracy depends on this. | Compile a list of 50–100 Bangla health terms and their English equivalents for the rule engine. Consult a Bangla-speaking medical professional if possible. |

---

### Should resolve during Phase 1–2

| # | Question | Options | Impact | Suggested resolution |
|---|----------|---------|--------|---------------------|
| Q4 | **How should dose_logs be generated for users in different timezones?** | All UTC / User's timezone / Bangladesh only (UTC+6) | Scheduling correctness. | MVP: assume all users are in Bangladesh (UTC+6). Store times with timezone. Add timezone field to user profile if needed later. |
| Q5 | **Should the admin panel be a separate static site or a Flutter web build?** | Static HTML/JS / Flutter web | Scope and maintenance. | Static HTML/JS is faster to build and has zero shared state with the mobile app. Recommended for MVP. |
| Q6 | **How to handle doctor profile photos?** | No photos (MVP) / Placeholder avatar / Cloud Storage (needs card) | Doctor search UX. | No photos in MVP. Use a generated avatar (first letter of name). Add photos when Cloud Storage is available. |
| Q7 | **What happens when a patient has 0 guardians and a RED alert fires?** | Alert is not sent / Log it only / Show in-app emergency screen only | Safety. | The in-app emergency screen (hospitals, 999) always shows. The guardian alert is simply skipped if no guardians are connected. Log the event. Show a prompt to connect a guardian. |

---

### Can resolve later (Phase 3+)

| # | Question | Options | Impact | Suggested resolution |
|---|----------|---------|--------|---------------------|
| Q8 | **Should chat sessions auto-expire or persist indefinitely?** | Delete after 30 days / Archive / Keep forever | Storage costs. | Keep for 30 days in MVP. Add cleanup in Phase 8 polish. Chat is never critical data — triage decisions are logged separately as alerts. |
| Q9 | **How to handle medicine name standardization?** | Free text / Dropdown from drug database / Both | Data quality for interaction checks. | Free text in MVP. The Medicine Agent works with fuzzy matching. Phase 2: integrate a drug database for autocomplete and better interaction checks. |
| Q10 | **Should guardians be able to add medicines on behalf of the patient?** | Yes / No (patient only) / With patient approval | Convenience for elderly patients whose guardians set things up. | No in MVP — patient only. Sajid sets up Rahela's phone directly. Consider in Phase 2 with a "delegate" permission. |
| Q11 | **Multi-language LLM prompts: one prompt per language or auto-detect?** | Separate Bangla/English prompts / Single prompt, LLM detects language / User setting controls | LLM response quality. | Use the user's `language` setting to select the system prompt language. LLM responds in the same language. Test both Bangla and English prompts for quality. |

---

## Free Tier Limits Quick Reference

| Service | Free limit | Our estimate | Risk level |
|---------|-----------|--------------|------------|
| **Firestore reads** | 50K/day | ~443/user/day (optimized) → ~112 users max | 🔴 High |
| **Firestore writes** | 20K/day | ~41/user/day → ~487 users max | 🟢 Low |
| **Firestore storage** | 1 GB | ~2 MB/user → ~500 users | 🟢 Low |
| **Firebase Auth** | Unlimited (email/Google) | No limit | 🟢 None |
| **FCM** | Unlimited | No limit | 🟢 None |
| **Render free** | 750 hours/month, sleeps after 15 min | 1 instance OK | 🟡 Medium (cold starts) |
| **Gemini Flash free** | 15 RPM, 1M tokens/day | ~500 messages/day | 🟡 Medium (RPM limit) |
| **Sentry free** | 5K errors/month | Sufficient for pilot | 🟢 Low |
| **cron-job.org free** | Unlimited jobs, 1-min interval | 1 job every 10 min | 🟢 Low |

---

## Features Unlocked by Getting a Payment Card

| Feature | Requires | Cost |
|---------|----------|------|
| Firebase Blaze plan (higher Firestore limits) | Card | Pay-as-you-go (still has free tier included) |
| Paid LLM API (safe for real user data) | Card | ~$5–10/month for pilot |
| Cloud Storage (report uploads, Phase 2) | Card (Blaze) | Included in Blaze free tier up to 5 GB |
| WhatsApp Business API (auto-alerts) | Card + Meta Business account | ~$0.011/message |
| Render always-on ($7/month) | Card | $7/month |
| Google Cloud Speech-to-Text (better Bangla STT) | Card | $0.006/15 seconds |

> **Getting a card is the single most impactful action for moving from demo to pilot.**
