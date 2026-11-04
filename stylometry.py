"""
Signal two: the style signal. ← YOU BUILD THIS IN MILESTONE 4

Signal one reads the text for meaning. This one measures it *as text* — the
shape of it, without understanding a word.

Three measures are stubbed below because the brief names those three. They are
stubs, not implementations: what they compute is yours, and so is how you
combine them.

    sentence_length_spread   do sentences vary in length, or march in step?
    type_token_ratio         how much of the vocabulary repeats?
    punctuation_density      how much punctuation, and how varied?

Why these might differ between human and AI writing: generated prose tends
toward even, mid-length sentences and a narrower band of vocabulary, because
that's what "most likely next word" produces on average. Human writing is
lumpier — a three-word sentence next to a forty-word one.

⚠️ **The blind spot, which you have to name in Milestone 1.**

This signal cannot read. It has no idea what the text says. Anything that
changes the shape without changing the substance moves it — adding typos,
breaking up sentences, pasting in a quotation. That is a very cheap thing for
someone to do on purpose, and unit 8's attack set will do it to you.

Build each function on its own and call it from a terminal before you wire
anything together:

    python stylometry.py "some text to look at"
"""

import re
import statistics

# Words per window for type_token_ratio, so a long text and a short one compare.
TTR_WINDOW = 50

# Punctuation that varies between writers. Full stops are left out on purpose.
# Straight and curly quotes and apostrophes-as-quotes are separate characters.
EXPRESSIVE_PUNCTUATION = ",;:—–()!?\"“”"


def sentences(text: str) -> list[str]:
    """Split into sentences. Rough and good enough — given to you."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def words(text: str) -> list[str]:
    """Split into lowercase words, punctuation stripped. Given to you."""
    return re.findall(r"[a-z0-9']+", text.lower())


# ── The three measures — YOU BUILD THESE ─────────────────────────────────────

def sentence_length_spread(text: str) -> float:
    """
    How much sentence length varies. ← TODO

    Returns:
        A float. Decide yourself what scale it's on and which direction means
        "more human" — then write that down, because your combining rule
        depends on knowing it.

    A hint on what you're reaching for: the standard deviation of sentence
    lengths, probably divided by the mean so a long text and a short one are
    comparable. `statistics.stdev` is imported for you.

    Watch the edge case: a one-sentence submission has no spread at all, and
    `stdev` raises on fewer than two values. Decide what that should return
    before the attack set decides for you.

    Mine: coefficient of variation (stdev ÷ mean) of words per sentence.
    Higher means more varied, which reads as more human. Fewer than two
    sentences returns 0.0 — no spread to measure, which `style_signal` then
    reads as the most AI-like value. A one-sentence submission is refused
    upstream by the 30-word minimum unless it's one very long sentence.
    """
    lengths = [len(words(s)) for s in sentences(text)]
    lengths = [n for n in lengths if n > 0]
    if len(lengths) < 2:
        return 0.0
    return statistics.stdev(lengths) / statistics.mean(lengths)


def type_token_ratio(text: str) -> float:
    """
    Unique words over total words. ← TODO

    Returns:
        A float between 0 and 1. Higher means more varied vocabulary.

    Worth knowing before you rely on it: this measure falls as text gets
    longer, because common words repeat. Two texts of different lengths aren't
    directly comparable on it, and if your test inputs vary a lot in length,
    that alone can look like a signal.

    Mine is windowed to stop length deciding it: the mean TTR over
    consecutive 50-word windows (the last partial window is dropped unless it
    is the only one). Higher means more varied vocabulary.

    ⚠️ On my calibration inputs this ran the *opposite* way to the theory:
    the AI samples scored 0.94–0.96 and the human ones 0.72–0.86. Generated
    prose reaches for a fresh word every time; people repeat "I", "the" and
    "and". So `style_signal` reads HIGH variety as more AI-like. Six inputs is
    thin evidence — check it again on your own writing.
    """
    tokens = words(text)
    if not tokens:
        return 0.0
    windows = [tokens[i:i + TTR_WINDOW] for i in range(0, len(tokens), TTR_WINDOW)]
    full = [w for w in windows if len(w) == TTR_WINDOW] or windows
    return statistics.mean(len(set(w)) / len(w) for w in full)


def punctuation_density(text: str) -> float:
    """
    How much punctuation, relative to length. ← TODO

    Returns:
        A float. Whether you count all punctuation or only some kinds — commas,
        semicolons, dashes — is a real choice. Semicolons and em dashes are
        more interesting than full stops, because they vary more between
        writers.

    Mine ignores full stops, which every writer uses, and counts the marks in
    `EXPRESSIVE_PUNCTUATION` per 100 words. Higher means more human.
    """
    n_words = len(words(text))
    if n_words == 0:
        return 0.0
    marks = sum(text.count(ch) for ch in EXPRESSIVE_PUNCTUATION)
    return 100 * marks / n_words


def punctuation_variety(text: str) -> int:
    """How many distinct kinds of `EXPRESSIVE_PUNCTUATION` appear at all."""
    return sum(1 for ch in EXPRESSIVE_PUNCTUATION if ch in text)


# ── Combining them ───────────────────────────────────────────────────────────

def style_signal(text: str) -> float:
    """
    The style signal as a 0–1 score. **Higher means more likely AI.** ← TODO

    Combine your three measures into one number. Same direction as
    `detector.model_signal`, so that `scoring.combine_signals` can treat them
    the same way — if one of your signals runs backwards, everything above it
    is wrong in a way that's hard to see.

    Two things to decide and write down:

      1. Which direction each measure points. Low spread means more AI-ish, so
         it needs flipping. Work out which of your three need that.
      2. How to get each onto a comparable scale. A raw type-token ratio sits
         between 0 and 1; a raw punctuation count doesn't. Adding them
         unscaled means whichever has the bigger numbers wins by default.

    Test it on the four calibration inputs from Milestone 4 — clearly AI,
    clearly human, plain conventional human writing, lightly-edited AI — before
    you trust it. Plain and ordinary, not formal: formal prose reads as *human*
    to signal one, and it is plain writing that gets accused.

    Mine: each measure is mapped linearly onto 0–1 AI-ness between the two
    ends in `_SCALES`, clipped, and the three parts are averaged with equal
    weight. Punctuation's part is itself the mean of density and variety.

        spread   0.30 or less -> 1.0 (AI) … 0.90 or more -> 0.0   (flipped)
        ttr      0.70 or less -> 0.0      … 0.98 or more -> 1.0 (AI)
        density  0 per 100 words -> 1.0 (AI) … 12 or more -> 0.0  (flipped)
        variety  0 kinds -> 1.0 (AI)      … 4 or more -> 0.0      (flipped)

    The ends come from the calibration inputs, so they're fitted to six texts
    and nothing more.
    """
    spread = _scale(sentence_length_spread(text), *_SCALES["spread"])
    ttr = _scale(type_token_ratio(text), *_SCALES["ttr"])
    punctuation = (
        _scale(punctuation_density(text), *_SCALES["density"])
        + _scale(punctuation_variety(text), *_SCALES["variety"])
    ) / 2
    return round((spread + ttr + punctuation) / 3, 4)


# (value that scores 0.0, value that scores 1.0). A reversed pair flips it.
_SCALES = {
    "spread": (0.90, 0.30),
    "ttr": (0.70, 0.98),
    "density": (12.0, 0.0),
    "variety": (4, 0),
}


def _scale(value: float, human_end: float, ai_end: float) -> float:
    """Map `value` onto 0 (at human_end) … 1 (at ai_end), clipped."""
    return min(max((value - human_end) / (ai_end - human_end), 0.0), 1.0)


if __name__ == "__main__":
    import sys

    text = " ".join(sys.argv[1:]) or (
        "The system works well. It handles most cases correctly and provides "
        "good results. Users generally find it easy to use and understand."
    )

    print(f"{len(sentences(text))} sentences, {len(words(text))} words\n")
    print(f"sentence_length_spread   {sentence_length_spread(text)}")
    print(f"type_token_ratio         {type_token_ratio(text)}")
    print(f"punctuation_density      {punctuation_density(text)}")
    print(f"punctuation_variety      {punctuation_variety(text)}")
    print(f"style_signal             {style_signal(text)}   (higher = more likely AI)")
