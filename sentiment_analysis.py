import pandas as pd

# Load comments
df = pd.read_csv("comments.csv")
df["Comment"] = df["Comment"].fillna("").astype(str).str.lower()

# ─────────────────────────────────────────────
# Keyword Dictionary
# ─────────────────────────────────────────────
FAKE_SCRIPTED = [
    "fake", "scripted", "ai voice", "bot", "obviously fake",
    "made up", "not real", "this is fake", "clearly fake",
    "ai generated", "text to speech", "tts", "robot voice",
    "generated", "no way this is real", "obviously made up"
]

FATIGUE = [
    "tired of this", "same story", "unsubscribing", "unsubscribed",
    "skip", "boring now", "getting old", "used to be good",
    "not as good", "gone downhill", "lost interest", "moved on",
    "used to watch", "not worth", "waste of time", "stopped watching"
]

CREATOR_CALLOUT = [
    "just for views", "clickbait", "stolen", "doesnt care",
    "sold out", "cash grab", "sellout", "money hungry",
    "rage bait", "ragebait", "farming", "view farming",
    "karma farming", "not the same", "changed for the worse",
    "disappointing"
]

OUT_OF_TOUCH = [
    "out of touch", "tone deaf", "privileged", "she doesn't get it",
    "he doesn't get it", "easy for her to say", "easy for him to say",
    "must be rich", "not realistic", "real world", "not everyone",
    "not relatable", "so privileged", "rich people problems",
    "detached", "lives in a bubble", "echo chamber", "entitled",
    "never struggled", "has no idea", "clueless", "disconnected",
    "does she even", "does he even", "out of reality",
    "not how it works", "must not have bills"
]

POSITIVE = [
    "love this", "keep going", "so good", "nta", "satisfying",
    "best reaction", "love your content", "amazing", "great video",
    "so entertaining", "cant stop watching", "addicted",
    "favourite channel", "favorite channel", "please keep making",
    "love the content", "great job", "well done", "love it",
    "this is great", "awesome", "perfect"
]

# ─────────────────────────────────────────────
# Scoring Function
# ─────────────────────────────────────────────
def score_comment(comment):
    fake = 0
    fatigue = 0
    callout = 0
    out_of_touch = 0
    positive = 0

    for kw in FAKE_SCRIPTED:
        if kw in comment:
            fake = 1
            break

    for kw in FATIGUE:
        if kw in comment:
            fatigue = 1
            break

    for kw in CREATOR_CALLOUT:
        if kw in comment:
            callout = 1
            break

    for kw in OUT_OF_TOUCH:
        if kw in comment:
            out_of_touch = 1
            break

    for kw in POSITIVE:
        if kw in comment:
            positive = 1
            break

    # Overall backlash = any of the four negative signals
    backlash = 1 if (fake or fatigue or callout or out_of_touch) else 0

    return fake, fatigue, callout, out_of_touch, backlash, positive

# Apply scoring
df[["fake", "fatigue", "callout", "out_of_touch", "backlash", "positive"]] = df["Comment"].apply(
    lambda c: pd.Series(score_comment(c))
)

# ─────────────────────────────────────────────
# Aggregate per channel per quarter
# ─────────────────────────────────────────────
agg = df.groupby(["Channel Name", "Quarter"]).agg(
    total_comments=("Comment", "count"),
    backlash_comments=("backlash", "sum"),
    fake_comments=("fake", "sum"),
    fatigue_comments=("fatigue", "sum"),
    callout_comments=("callout", "sum"),
    out_of_touch_comments=("out_of_touch", "sum"),
    positive_comments=("positive", "sum")
).reset_index()

agg["backlash_ratio"] = agg["backlash_comments"] / agg["total_comments"]
agg["fake_ratio"] = agg["fake_comments"] / agg["total_comments"]
agg["fatigue_ratio"] = agg["fatigue_comments"] / agg["total_comments"]
agg["callout_ratio"] = agg["callout_comments"] / agg["total_comments"]
agg["out_of_touch_ratio"] = agg["out_of_touch_comments"] / agg["total_comments"]
agg["positive_ratio"] = agg["positive_comments"] / agg["total_comments"]

agg.to_csv("sentiment_scores.csv", index=False)
print("Done! sentiment_scores.csv created.")
print(f"\nTotal channel-quarter combinations: {len(agg)}")
print(f"\nSample output:")
print(agg.head(10))