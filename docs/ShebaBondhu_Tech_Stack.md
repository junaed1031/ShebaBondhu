# ShebaBondhu: Recommended Tech Stack

Status legend: **Fixed** = already decided by the team | **Recommended** = suggested | **Later** = after the MVP.
Prices and free-tier limits change often; check the official pages before committing.

## 1. Tech Stack

| Part | Choice | Details | Status |
| --- | --- | --- | --- |
| Mobile app | Flutter | Packages: firebase_auth, firebase_messaging, flutter_local_notifications, speech_to_text, geolocator, url_launcher, dio, Riverpod | Fixed |
| Backend | FastAPI (Docker) | Verifies the Firebase ID token on every request | Fixed |
| Authentication | Firebase Auth (email / Google) | Phone OTP comes later | Fixed |
| LLM | Hosted LLM API behind a wrapper class | Dev: free tier with fake test data only. Pilot: paid tier. Pick the model with 30-50 Bangla test prompts (Gemini Flash, Claude Haiku or another cheap model) | Fixed (API); model to be chosen |
| Database | Cloud Firestore | Only FastAPI writes. Client access blocked by security rules. Repository layer so a later move to Postgres is easy | Recommended |
| Push notifications | Firebase Cloud Messaging | Free | Recommended |
| Medicine reminders | Local notifications on the phone | Free and works offline | Recommended |
| Missed-dose check | External free cron (e.g. cron-job.org) | Calls a FastAPI endpoint every 5-10 minutes | Recommended |
| Doctor summary PDF | WeasyPrint + Noto Sans Bengali font | Generated on demand, not stored. Bangla rendering to be tested from day one | Recommended |
| Nearby hospitals | Curated hospital list + phone GPS distance | Opens in Google Maps for directions | Recommended |
| Backend hosting | Render free (dev/demo), then $7/month always-on (pilot) | Free instances sleep after 15 minutes idle | Recommended |
| Monitoring | Firebase Crashlytics + Sentry | Both have free tiers | Recommended |
| WhatsApp call button | wa.me link | Free; included in MVP | Recommended |
| WhatsApp automatic alerts | WhatsApp Business Platform | Needs Meta Business account, approved template and paid messages. Separate channel, push comes first | Later |
| File storage (reports) | To be decided in Phase 2 | Cloud Storage for Firebase needs a billing account (Blaze plan) | Later |

## 2. Why Firestore (and the rules that go with it)

Verdict: Firestore is a good fit for the MVP. The earlier version of the Project Overview said PostgreSQL; the Project Overview v1.1 now matches this file.

| Type | Point | Detail | Source |
| --- | --- | --- | --- |
| Pro | Same ecosystem as Auth and FCM, easy setup | Spark plan needs no payment method | https://www.verdent.ai/guides/devtools/firebase-pricing |
| Pro | Free quota is enough for a pilot | Spark: 1 GB storage, 20K writes/day, 50K reads/day. Rough estimate: enough for a few hundred active users | https://blog.back4app.com/firebase-pricing/ |
| Pro | Database does not sleep or expire | Render free Postgres expires 30 days after creation, which is unsuitable for health data | https://livemy.app/blog/render-pricing |
| Pro | Data fits documents | Medicines, dose logs, readings and alerts sit naturally under each patient | Team analysis |
| Con | No joins or aggregations | Store a daily summary document so weekly adherence does not need many reads | Team analysis |
| Con | Billing is per read/write | Keep dashboard reads low; set budget alerts (they do not stop usage) | https://www.verdent.ai/guides/devtools/firebase-pricing |
| Rule | App talks only to FastAPI (login excepted) | Guardian permissions and emergency rules live in one place. Firestore client access is denied by security rules | Team decision to confirm |
| Rule | Use a repository layer | A later move to Postgres then only touches that layer | Team decision to confirm |

## 3. Five Things That Change the Plan

| # | Issue | What it means | Plan | Source |
| --- | --- | --- | --- | --- |
| 1 | Cloud Storage needs a card | Since 3 Feb 2026 Cloud Storage for Firebase needs a billing account (Blaze plan) | MVP does not store the doctor PDF (generated on demand). Decide report storage in Phase 2 | https://dev.to/androve2k/spark-vs-blaze-the-firebase-pricing-guide-i-wish-id-read-sooner-onb |
| 2 | WhatsApp automatic alerts cost money and need setup | Needs a Meta Business account and an approved template. Bangladesh utility message about $0.0113 (aggregator figure) | Push notification first. WhatsApp alert added later as a separate channel. The wa.me call button stays free | https://whautomate.com/whatsapp-business-api-pricing |
| 3 | Do not put real data into the LLM free tier | Google may use free-tier data to improve its products | Fake test data in development. Paid tier once real users join | https://hashnode.com/blog/gemini-api-pricing-2026 |
| 4 | Free hosting sleeps | Render free web services stop after 15 minutes idle and take about a minute to wake | Fine for dev/demo. Use the $7 always-on instance for the pilot | https://temps.sh/blog/render-pricing-2026 |
| 5 | Bangla in PDF | A Bangla font must be embedded and some PDF libraries do not render conjunct letters correctly | Use WeasyPrint with Noto Sans Bengali and test on day one | Team note (to verify while building) |

## 4. Monthly Cost Estimate (USD)

Inputs marked ASSUMPTION are placeholders: replace them with your own estimates.

| Input | Value | Note / Source |
| --- | --- | --- |
| Development cost ($/month) | 0 | Free tiers with fake data |
| Backend hosting, always-on ($/month) | 7 | Render Starter instance: https://temps.sh/blog/render-pricing-2026 |
| LLM usage ($/month) | 5 | ASSUMPTION placeholder. Depends on model and users; replace after testing |
| WhatsApp utility message price ($/message) | 0.0113 | Bangladesh rate from aggregator: https://whautomate.com/whatsapp-business-api-pricing |
| WhatsApp alerts per month (count) | 200 | ASSUMPTION placeholder. Set after the pilot size is known |

| Stage | Monthly ($) | How it is calculated |
| --- | --- | --- |
| Development | 0.00 | Development cost |
| WhatsApp alerts (optional) | 2.26 | Price per message x alerts per month (0.0113 x 200) |
| Pilot (without WhatsApp) | 12.00 | Hosting + LLM usage (7 + 5) |
| Pilot (with WhatsApp) | 14.26 | Pilot without WhatsApp + WhatsApp alerts |

## 5. Open Question and Next Steps

| Item | Detail | Owner |
| --- | --- | --- |
| Open question | Does anyone on the team have an international or virtual card? With a card, Blaze, paid LLM and WhatsApp can all be enabled. Without one, start with push + manual alerts and add the rest later. | Team |
| Next step 1 | Confirm this stack | Team |
| Next step 2 | Design the Firestore collection schema | Claude / Antigravity |
| Next step 3 | Write the API list | Claude / Antigravity |
