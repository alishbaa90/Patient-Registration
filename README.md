# Voice AI Agent — Patient Registration System

A voice agent you can actually call on the phone. It talks to you naturally,
collects your basic patient info (name, DOB, address, etc.), saves it to a
database, and you can look it up later through a simple API.

## Try it

- **Call this number:** +1 (516) 990-9232
- **API:** https://patient-registration-production-21ad.up.railway.app
- **Code:** https://github.com/alishbaa90/Patient-Registration

## How it's put together

```
Caller (phone)
      │
      ▼
Vapi — handles the actual phone call, speech-to-text, text-to-speech,
       and the LLM conversation
      │  (calls my API when it needs to save/check data)
      ▼
FastAPI backend on Railway
      │
      ▼
SQLite database (on a persistent volume, so it survives restarts)
```

I kept the voice/telephony side and the backend completely separate. Vapi
handles the whole conversation — deciding what to ask, understanding the
caller, correcting mistakes — and only talks to my backend through three
simple tools when it actually needs to save or look up a patient. This means
the backend doesn't care where the request comes from — it could be a phone
call today, a web form tomorrow, and the validation rules would still hold.

## Why these tools

| Part | What I used | Why |
|---|---|---|
| Phone + voice | **Vapi** | Gives you a free US number instantly, handles speech-to-text/text-to-speech/LLM orchestration out of the box, and has a simple UI for wiring up tools to a backend. Given the 3-hour limit, this was clearly the fastest path to something that actually works end to end. |
| LLM | **GPT-4.1** (through Vapi) | Needed something that could follow a fairly long, multi-step conversation (collect info → confirm → handle corrections → save) without wandering off track. |
| Backend | **FastAPI** | Quick to write, validates requests automatically, and comes with a built-in `/docs` page that made testing everything by hand a lot faster. |
| Database | **SQLite** | No setup at all — a file is the whole database. Good enough for a project like this. The obvious trade-off is it's not built for a lot of concurrent writes, which is fine here but wouldn't be for a real clinic. |
| Hosting | **Railway** | Push to GitHub, it deploys automatically, gives you a public URL right away. Free tier was more than enough for this. |

## What the API looks like

Every response comes back the same shape: `{ "data": {...}, "error": null }`.

| Method | Endpoint | What it does |
|---|---|---|
| GET | `/patients` | List patients. Can filter by `?last_name=`, `?date_of_birth=`, `?phone_number=` |
| GET | `/patients/lookup?phone_number=` | Look someone up by phone number — this is what the voice agent uses to recognize returning callers |
| GET | `/patients/{id}` | Get one patient |
| POST | `/patients` | Create a patient |
| PUT | `/patients/{id}` | Update a patient (you can send just the fields that changed) |
| DELETE | `/patients/{id}` | Soft delete — it sets a `deleted_at` timestamp instead of actually removing the row |
| GET | `/health` | Just tells you the server's alive |

You can also just open `/docs` on the live URL and try everything from there.

## What data it collects

Everything from the spec is in there — required fields like name, date of
birth, sex, phone number, and address, plus optional ones like email,
insurance info, and emergency contact. `patient_id`, `created_at`, and
`updated_at` are generated automatically.

All the validation happens on the server, not just in the voice agent's
prompt — so a bad date of birth, an invalid phone number, or a wrong state
abbreviation gets rejected no matter where the request came from.

## How the voice agent is set up

The system prompt tells it to:
1. Get the caller's name, then their phone number.
2. As soon as it has the phone number, check if that person already exists
   (`lookup_patient`). If they do, offer to update their info instead of
   creating a new record.
3. Ask for the rest of the required info a couple of fields at a time — not
   a giant list all at once. If something's invalid (future birthdate, a
   phone number that's not 10 digits), it just asks again for that one
   thing.
4. Offer the optional stuff once ("want to give insurance info or an
   emergency contact, or should we skip that?") instead of asking for
   every field regardless.
5. Read everything back before saving, and actually handle it if the caller
   wants to correct something.
6. Save the record, and either confirm it worked or, if it failed, tell the
   caller honestly and offer to try again — never just go quiet.
7. Start over cleanly if the caller asks to.

The full prompt is in `docs/system_prompt.txt` if you want to see the exact
wording.

## Running it yourself

```bash
git clone https://github.com/alishbaa90/Patient-Registration.git
cd Patient-Registration
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 seed.py               # optional — adds 2 demo patients
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then go to `http://localhost:8000/docs` to poke around.

## Env variables

None needed for the backend itself when running locally with SQLite. The
Vapi assistant keeps its own API key inside the Vapi dashboard — nothing is
hardcoded in this repo.

## Things I ran into / trade-offs I made

- **The update flow doesn't work end-to-end over the phone yet.** The agent
  correctly recognizes a returning caller by phone number (via
  `lookup_patient`) and offers to update their info — that part works. But
  the actual save through the `update_patient` voice tool fails. The
  `PUT /patients/{id}` endpoint itself works correctly — I verified this
  directly through `/docs` (partial updates succeed as expected). The issue
  is isolated to how the Vapi tool is wired up (getting the caller's
  existing patient ID and changed fields into that specific tool call), not
  the backend logic. Given the time limit, I'm documenting this rather than
  leaving it half-fixed. **Workaround for now:** a returning caller's info
  can still be updated directly via the API (`PUT /patients/{id}`) even
  though the phone flow can't complete it yet.
- **SQLite on Railway resets by default.** I actually caught this while
  testing — I registered a patient, restarted the service, and the record
  was gone. Turns out Railway's filesystem doesn't persist between restarts
  unless you attach storage to it. Fixed it by adding a Railway volume
  mounted at `/data` and pointing the database there instead
  (`app/models.py`). Tested again after the fix — restarted the service,
  the patient was still there.
- **Vapi sends empty strings for fields the caller skipped, not null.** My
  API originally rejected an empty `emergency_contact_phone` as if it were
  an invalid phone number, which caused a save to fail even when the field
  was never supposed to be filled in. Fixed by treating blank strings as
  "not provided" before validation runs (`app/schemas.py`).
- **Phone numbers said digit-by-digit sometimes get garbled by the
  speech-to-text layer.** The agent is built to notice an incomplete number
  and ask again rather than saving something wrong, but it does add extra
  back-and-forth to the call.
- **No automated tests** — with the time limit, I tested everything by hand
  through `/docs` and live test calls instead of writing a test suite.
- **No appointment scheduling, multi-language support, or dashboard** — all
  listed as bonus/optional in the brief, and I prioritized getting the core
  flow solid over adding extras.

## If I kept working on this

- Move off SQLite to a proper managed Postgres database.
- Write actual tests for the API (pytest + FastAPI's test client).
- Save call transcripts against each patient record.
- Build a simple page to browse registered patients.
