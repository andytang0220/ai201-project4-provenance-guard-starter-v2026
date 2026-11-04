# Acceptance criteria — Provenance Guard

Five criteria that say what "working" means for this service, written in unit 7
**before** you built it.

**All five are yours.** None are given.

An acceptance criterion names a number or something plainly observable. *"The
detector is accurate"* is an opinion — and perfect AI detection isn't possible
anyway, so it's an opinion about something nobody can deliver. *"Of 10 pieces I
wrote myself, at most 1 is labelled high-confidence AI"* is a criterion.

Under each, write a sentence or two on **why that target**. *"I allow at most 1
false positive in 10 because on a writing site a wrong accusation costs more
than a missed detection"* is a real answer.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## Pick numbers you can defend

**Cover at least three of these five areas.** They're prompts, not a form.

| Area | A question it could answer |
|---|---|
| False positives | How often may a human's writing get called AI? |
| Score spread | How far apart should clearly-AI and clearly-human text score? |
| Label coverage | Is every one of your three labels actually reachable? |
| The appeal path | Does an appeal always change status and always get recorded? |
| Bad input | What happens when `text` is missing, empty, or enormous? |

Two things worth knowing before you pick numbers:

- **The expensive mistake is one-sided.** Missing some AI text costs the site a
  little. Accusing a real writer costs that person a lot. A criterion that
  treats both errors as equally bad is describing a system nobody would ship.
- **Unit 8 tests across three trials, and the target has to hold across all
  three.** Your first signal runs a model, so identical input can score
  differently twice. A target of "at most 1 in 10" against trials of 2, 1, 2 is
  a **miss**.

---
## 1. My own writing is almost never called AI

Of 10 pieces I wrote myself, **at most 1** is labelled high-confidence AI
(`guess == "ai"`), in **each** of the three trials.

**Why this target:** On a writing site a wrong accusation costs the writer far
more than a missed detection costs the site, so false positives get the
tightest limit here. It's 1 and not 0 because signal one runs a model and its
scores wobble between trials. A target that only holds on a lucky run is not
one I can defend.

---

## 2. Plain human writing is never called AI

Of 5 paragraphs written by people (not generated) in plain style, meaning
short sentences and common words only, **0** are labelled high-confidence AI
in **any** of the three trials.

**Why this target:** This is the false positive I traced in Milestone 1. A
plain paragraph scored 0.7936 on signal one, higher than the clearly-AI
sample's 0.7544. Second-language and younger writers are the people this
system is most likely to accuse and the least able to argue back, so for this
group the allowance is zero, not one in ten.

---

## 3. Clearly-AI and clearly-human text land far apart

The mean `confidence` of 5 clearly AI-generated texts is **at least 0.30
higher** than the mean `confidence` of 5 clearly human texts, in each of the
three trials.

**Why this target:** My human and AI labels sit at least 0.30 apart, with the
unsure band in between. If the two clear groups are closer than that, no
threshold puts both of them in the right band, and the labels are mostly
noise. The gap is measured on the easy cases on purpose: if the system can't
separate those, it can't separate anything.

---

## 4. Bad input gets a clear refusal, never a crash

Of these 5 request bodies, **5 of 5** return a 4xx status with a JSON body
containing an `error` field, **0** return a 500 or a 200, and each one adds a
`rejected` entry to the audit log, in each of the three trials:

- `text` is `""`
- `text` is missing
- `text` is `null`
- `text` is 250,000 characters
- `text` is under 30 words

**Why this target:** A 500 on malformed input is one of the most common real
failures, and the unit 8 attack set sends exactly these. It's 5 of 5 because
this is deterministic code, not a model, so there is no noise to excuse a
miss. The log entry matters because a refused request that leaves no trace is
an attack I can never find afterwards.

---

## 5. Every appeal changes status and is recorded

For 5 real submissions appealed using the `content_id` each one returned,
**5 of 5** appeals return 200 with `status: "under_review"`, and each adds
**exactly one** appeal entry with that `content_id` to the log. An appeal
with a made-up `content_id` returns **404** and adds no appeal entry.

**Why this target:** The appeal is the only thing between a wrong accusation
and nothing at all, so a single silent failure here is a writer with no way
out. The made-up id case is in the target because "appeal accepted for a
submission that doesn't exist" looks like success and fixes nothing.
`run_eval.py` only sends text, so I test this one by hand with `curl`, and the
write-up says so.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 8 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath, like this:

         ## 2. Uncertain cases land in the unsure band

         The system handles uncertain cases well.

         **Why this target:** ...

         > **Revised in unit 8:** Text I judged borderline scores between
         > 0.4 and 0.6 in at least 4 of 5 cases.
         >
         > **Why revised:** "well" gave me nothing to check. I couldn't
         > reach a verdict from it at all.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "At most 1 of 10 of my own pieces flagged as AI" → "at most 3
            of 10", because 1 of 10 turned out to be hard.

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
