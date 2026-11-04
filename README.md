# Provenance Guard

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first.**
>
> Once `python test.py` passes, in one terminal:
>
> ```bash
> python app.py
> ```
>
> and in another:
>
> ```bash
> curl -X POST http://127.0.0.1:5000/ping \
>   -H "Content-Type: application/json" \
>   -d '{"message": "hello"}'
> ```
>
> That's a web service. Something sent it text and it sent something back.
> Everything this unit is filling in the middle.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     Unit 7 asks for the first five sections. Unit 8 adds the five below.

     Everything is pasted as TEXT. A pasted curl response gets full credit;
     a picture of your terminal gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 7 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- The path a submission takes, from arriving to the label a reader sees.
     Six or seven steps — this is the trace you wrote in Milestone 1. -->



---

## Signals and Scoring

<!-- For each signal: what property it measures, why that might differ between
     human and AI writing, and WHAT IT CAN'T SEE.

     The blind spot is not optional. If you can't name it you don't understand
     the signal yet — and unit 8's attack set is built out of blind spots. -->

### Signal one — the model signal

**What it measures:** How predictable the text is to a language model.
`detector.py` runs gpt2 locally over the first 400 tokens and computes
perplexity, which is how surprised the model is by each next token. A
logistic curve centred on perplexity 45 maps that onto 0–1, so low
perplexity gives a high score (more AI-like).

**Why that might differ between human and AI writing:** A language model
writes by picking high-probability next tokens over and over, so its output
sits where another language model finds it easy to predict. People make
choices a model wouldn't, such as an odd word, a specific name or a sudden
turn, and each one costs perplexity.

**What it can't see:** Who wrote the text. It measures predictability, and
plenty of people write predictably. Second-language writers, younger writers
and anyone writing plainly on purpose all score as AI. Measured on this
machine:

| Text | Perplexity | `model_score` |
|---|---|---|
| `samples/clearly_ai.json` | 22.3 | 0.7544 |
| a plain human paragraph (written in the style of a second-language writer) | 19.4 | **0.7936** |
| `samples/clearly_human.json` | 59.2 | 0.3923 |

The plain human paragraph scores *more* AI-like than the AI sample, so no
threshold on this signal alone separates them. It is blind the other way too.
Rare words, jargon, proper nouns and typos raise perplexity, so AI text with
unusual vocabulary or a few misspellings reads as human. And it only reads the
first 400 tokens (about 300 words).

### Signal two — the style signal

**What it measures:** The text's shape, without reading it. `stylometry.py`
uses three measures:

- **Sentence-length spread:** the standard deviation of words per sentence
  divided by the mean. Low spread is flipped to mean more AI-like.
- **Type-token ratio:** unique words over total words, averaged over 50-word
  windows so length doesn't decide it. **High** variety counts as more
  AI-like. That's the opposite of what I expected. On my calibration inputs
  the AI texts scored 0.94–0.96 and the human ones 0.72–0.86, because
  generated prose reaches for a fresh word every time while people repeat
  "I", "the" and "and". Six texts is thin evidence for flipping a measure, so
  it's the first thing I'll recheck against my own writing.
- **Punctuation density:** non-full-stop punctuation (`, ; : — – ( ) ! ? "`)
  per 100 words, plus how many distinct kinds appear. Low density and variety
  are flipped to mean more AI-like.

Each measure is mapped linearly onto 0–1 between two fixed ends (in
`stylometry._SCALES`), clipped, and the three are averaged with equal weight
into `style_score`. Higher means more AI-like, the same direction as signal
one.

**Why that might differ between human and AI writing:** Generated prose tends
toward even, mid-length sentences, safe vocabulary and regular punctuation,
because that's what "most likely next token" produces on average. Human
writing is lumpier. `clearly_human.json` puts "Twice now." (2 words) next to
a sentence of about 40, and uses dashes, a colon and quotation marks.

**What it can't see:** Meaning. It has no idea what the text says, so any
edit that changes the shape without changing the substance moves it.
Splitting sentences, adding a fragment, sprinkling in dashes and semicolons,
or pasting a quotation all push the score toward human, and all of them are
cheap to do on purpose. (Typos raise type-token ratio, which my direction
reads as *more* AI-like, so that one attack partly backfires here, though it
still works on signal one.) It also shares signal one's blind spot. Plain
writing has even sentence lengths and only full stops, so the writer signal
one wrongly accuses is accused here too: `samples/plain_human.json` scored
0.69 on style. When they're wrong, the two signals agree. Short texts are noise:
one sentence has no spread at all. And because modern chat models use em
dashes heavily, "varied punctuation means human" may already be out of date.

### The combining rule

<!-- Write the rule in words, then give the numbers. What happens when the two
     signals disagree? -->

**The rule:** A text is only as AI-like as its *least* AI-like signal. The
combined score is the lower of the two signal scores. When they disagree, the
one that reads more human wins, so neither signal can put a text in the AI
band on its own. Both have to be fooled at once.

I didn't use a weighted average because of one measurement. A plainly written
human paragraph scored **0.794** on the model signal, higher than the
clearly-AI sample's **0.754**. Any weighting that leans on the model signal
accuses that writer before it catches the AI. The cost is the other way
round: AI text that fools *either* signal drops out of the AI band. I chose
missed detections over wrong accusations.

**The numbers:** `combined = min(model_score, style_score)`, with no weights
(`WEIGHT_*` in `config.py` is left unused). Thresholds (provisional, to be
tested in Milestone 5): `HUMAN_THRESHOLD = 0.35`, `AI_THRESHOLD = 0.72`.

The calibration inputs (all in `samples/`) through `/submit`:

| Input | `model_score` | `style_score` | combined | Band |
|---|---|---|---|---|
| `clearly_ai` | 0.7544 | 0.8113 | 0.7544 | AI |
| `lightly_edited_ai` | 0.6738 | 0.7600 | 0.6738 | unsure |
| `plain_human` | 0.7936 | 0.6905 | 0.6905 | unsure |
| `formal_human` | 0.4929 | 0.3425 | 0.3425 | human |
| `borderline` | 0.2925 | 0.5161 | 0.2925 | human |
| `clearly_human` | 0.3923 | 0.1232 | 0.1232 | human |

`clearly_human`, `clearly_ai` and `borderline` came with the starter. I wrote
`formal_human`, `plain_human` and `lightly_edited_ai` as stand-ins: they
aren't real submissions. `lightly_edited_ai` is `clearly_ai` with
contractions and plainer words swapped in.

What surprised me, and which signal was off:

- **Lightly-edited AI escapes to unsure.** A few contractions and plainer
  words dropped the *model* signal from 0.754 to 0.674. Style barely moved
  (0.811 → 0.760), because the edits didn't change the shape. Under `min()`
  the weaker signal decides, so the text drops out of the AI band. That's the
  trade working as designed, and it's also an evasion that cost me five
  minutes.
- **The plain writer is protected by 0.03.** `plain_human` combines to 0.691
  against an AI threshold of 0.72. It's out of the AI band, but only because
  style read it slightly more human than the model did. A plainer paragraph
  could cross.
- **Formal human prose sits right on the human threshold.** It combines to
  0.343, just under 0.35. The model signal (0.493) was the hesitant one,
  because formal prose is still fairly predictable to gpt2.

**Where it lives:** `scoring.py::combine_signals`

<!-- ⚠️ The grader checks your code against that line. If your rule lives
     somewhere else, say where. -->

**A case where my two signals split, and what my rule does with it:**

`samples/borderline.json`, the time-management paragraph in casual British
English. The model signal says human (**0.2925**): words like "frazzled",
"wreck" and "genuinely" surprise gpt2. Style leans AI (**0.5161**): sentence
lengths are fairly even (spread 0.47) and the vocabulary is varied (TTR
0.86), and only its dashes and semicolon pull it back toward human. That's a
0.22 gap. `min()` takes the model's 0.2925, so it lands in **human**.

A weighted average would have given 0.40, which is unsure. My rule settles a
split in the writer's favour every time. On this text that's probably right.
On an AI text someone has salted with rare words, it's the hole the attack set
will go through.



---

## Label Variants

<!-- The exact text of all three labels, as a reader would see them, and the
     score range each covers.

     Write them for someone who has never heard the word "threshold". -->

| Label | Score range | The exact text a reader sees |
|---|---|---|
| high-confidence human |  |  |
| unsure |  |  |
| high-confidence AI |  |  |

**Why I worded the "unsure" one this way:**
<!-- It's the hardest of the three. It has to admit uncertainty without
     sounding like an accusation, because the person reading it may well have
     written every word themselves. -->



---

## Sample Run

<!-- One submission and one appeal, pasted as text: the request, the response,
     and the log entries. -->

**A submission**

<!-- The response needs content_id, guess, confidence, label, AND both
     signal scores - model_score and style_score. Unit 8's tools read those
     two off the response, so leaving them out costs you next unit's
     diagnostics. -->

```bash
$ curl -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "...", "creator_id": "..."}'
```

```json

```

**An appeal**

```bash
$ curl -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "...", "reasoning": "..."}'
```

```json

```

**What the log shows afterwards**

```bash
$ curl "http://127.0.0.1:5000/log?limit=3"
```

```json

```

---

## How I Used AI

**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** ___ per minute, ___ per day

**Why those numbers and not others:**
<!-- Think about two people: a real writer submitting their own work a few
     times an hour, and a script sending a thousand variations to map your
     thresholds. Your numbers have to be liveable for the first and hostile to
     the second. -->

**What a caller counts as:** <!-- per address, or per creator_id? They fail
differently — one script can look like a thousand callers, and one household
can look like one. -->

**The run of status codes when I pushed past it:**

<!-- python run_attacks.py --flood 15 -->

```

```

---

## Attack Run — Before

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->



**Ten audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

```json

```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:



---

## Run Log and Verdicts

<!-- Your five criteria across three trials. `run_eval.py --label before`. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |
| 2.  |  |  |  |  |  |
| 3.  |  |  |  |  |  |
| 4.  |  |  |  |  |  |
| 5.  |  |  |  |  |  |

**Real output from one trial**, pasted as text, naming the file and function
that produced it:

```json

```

**Diagnoses**

<!-- For each miss AND each broken attack: the stage and the mechanism.

     Your service has five stages: the route, signal one, signal two, the
     combining rule, and the label mapping.

     Not a diagnosis:  "The evasion attacks got through."
     A diagnosis:      "Four evasion inputs got through. All four had typos
                        added to AI-generated text. My second signal measures
                        word variety, and typos raise word variety — so it read
                        them as more human. My combining rule weights that
                        signal at 0.6, so it dragged the whole score down."

     Look for a pattern. Five failures on one signal is one problem, not five. -->



---

## The Improvement

**What I changed:**

**Which diagnosis pointed at it:**

### Attack Run — After

<!-- Same format. `run_attacks.py --label after` -->



**Did it help, and how do I know:**

<!-- Widening the unsure band usually fixes one problem and creates another.
     Reporting that trade honestly is worth full credit. -->



---

## What's Still Broken

<!-- For each attack still getting through and each criterion still missed:
     what you'd do, and why you stopped. -->



**The trade I'd make if this ran for real:**

<!-- Two sentences. Fewer wrong accusations means more AI text getting through.
     Say which way you'd go and WHO PAYS FOR IT. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 7

       [ ] criteria.md has five numbered criteria, each naming a target
       [ ] Each has a reason underneath
       [ ] POST /submit returns content_id, guess, confidence, label,
           model_score and style_score
       [ ] Two signals that measure DIFFERENT things, each with a named blind spot
       [ ] Three label variants, all reachable, written out in full
       [ ] POST /appeal changes status and writes to the log
       [ ] Signals and Scoring names scoring.py::combine_signals
       [ ] Sample Run: a submission AND an appeal, as pasted text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN

     SUBMISSION CHECKLIST — unit 8

       [ ] Rate limiting on /submit, with your numbers justified
       [ ] The pasted run of status codes showing 429
       [ ] Audit log with all nine fields, recording rejections too
       [ ] The attack set run IN FULL, every input with an outcome
       [ ] Ten audit log entries pasted as text
       [ ] Five criteria across three trials
       [ ] A diagnosis for every miss and every broken attack — stage AND mechanism
       [ ] One improvement, with Attack Run — After
       [ ] What's Still Broken, including the production trade
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
