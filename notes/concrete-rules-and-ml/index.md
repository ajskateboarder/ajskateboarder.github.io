# Combining concrete rules and machine learning for classification

february 5, 2024

Currently, I am developing (or have developed?) [Wordsmyth](https://github.com/ajskateboarder/wordsmyth), a star rating prediction model designed to tackle the bias and incorrectness of the consumer star system through sentiment analysis and rules. This system allows you to use the pros of both rule-based systems:

- simple to build and interpret
- less computationally expensive
- high precision due to domain expertise

and machine learning:

- higher overall accuracy
- very dynamic
- easy to adapt to situations

With my project, I use the output of pre-trained sentiment analysis networks as inputs to a rule-based process to correct the outputs and quantify the sentiment information as a star rating using a weighting system.

<figure>
  <img src="./concrete-rules-and-ml.png" alt="Wordsmyth flow" />
</figure>

In simpler terms, this is the layout of the system:

<figure>
  <img src="./simple-layout.png" alt="Simpler layout" />
</figure>

What's honestly weird about this approach is that, in this ever-growing ecosystem of machine learning, there are so few applications of this approach online!! Aside from the [few blogs](#related) I found that cover this idea, there are no projects to be found that apply a similar methodology; everybody is just talking about how nice the approach is. So let me fix that - by reviewing code that applies this logic in action.

Obviously, the code being reviewed will be domain-specific, and I know this just looks like a whole explanation of an algorithm I developed, but this post should hopefully help for those who want an example of how to implement a ML -> rules system.

## Teeny-tiny code review

### Initialization/model prediction

```py
output = Output(
    sentiment=flair.predict(text),
    emojis=torchmoji.predict(text, emojis),
    text=text
)

rater = Rater(output)
```

Initially, the program passes the input data to a set of pretrained models which both predict various facets of emotion in the text. `flair` simply classifies text as either positive or negative, while `torchmoji` predicts ten emojis that match the sentiment of the text. This is then wrapped and passed into the main rule logic.

In the rule logic initialization, we get some information from the predictions and wrap them to be passed around to the main steps:

```py
class Rater:
    def __init__(output):
        metadata = Evaluation(
            content=output.text,
            emoji=None,
            emojis=output.emojis,
            position=None,
            sentiment_flair=output.sentiment["sentiment"],
            score=output.sentiment["score"],
            ...
        )
        ...
```

### Step 1. Resolving sentiment between models

The reasoning for this rule is that `flair` tends to be correct in objective sentiment, but is lacking any detailed sentiment, like specific emotions. To make up for this, we bring in `torchmoji`, an emoji prediction model, but it seems to make a lot more false predictions than `flair`, so this rule is used to help `torchmoji` choose a better prediction based on `flair` while having detailed sentiment.

<small>This rule is so painfully written and I am so close to just rewriting it all.</small>

In the first of three phases involved, the first phase attempts to fix false-negatives/positives in the emoji using some.. expert knowledge, I guess?

```py
m = self.metadata

target_emojis = [
    ":confused:", ":thumbsup:", 
    ":eyes:", ":smile:",
    ":persevere:",
]
emoji_indices = self.find_indices(output.emojis, target_emojis)

if not emoji_indices:
    return

m.sentiment_emoji = (
    emojimap[output.emojis[min(emoji_indices)]]
)["sentiment"]
```

Here, the rule assumes that `output.emojis` should contain any emojis from a list of emojis that often show up in `torchmohi` responses, `target_emojis`. If none exist, the rules fail immediately so the next steps don't produce any weird results. 

If at least one exists, the rule can continue on to set the sentiment provided by the most accurate emoji predicted by `torchmoji` among the ten that were predicted. This can be determined by:

- finding the list indices of each target emoji in `output.emojis`
- creating a list from that information
- and picking the item from that list closest to index 0  

We can find the precise sentiment of that emoji by looking up the emoji in the `emojimap` dictionary, a dedicated resource which maps emojis to sentiment. 

```py
if m.sentiment_flair != m.sentiment_emoji:
    matching = [
        e
        for e in output.emojis
        if emojimap[e]["sentiment"] == m.sentiment_flair
        and emojimap[e]["repr"] in m.emojis
    ]
    
    sequence = [m.emojis.index(emojimap[e]["repr"]) for e in matching]  
    closest_index = min(sequence) if sequence else None

    # FIXME: this .get() and if-else stuff sucks v
    fixed_emoji = (
        emojimap.get(m.emojis[closest_index], {})
        if closest_index is not None
        else {}
    )

    if m.sentiment_flair == fixed_emoji.get("sentiment"):
        m.fixed_emoji = fixed_emoji.get("repr")
        # TODO: supposed to return here
```

If the sentiment of `flair` and the chosen emoji do not match, we attempt to find emojis in the entire `emojimap` that match `flair`'s sentiment. After this, we essentially apply the same process as before to pick a more correct emoji to represent `torchmoji`'s sentiment. I'm pretty sure the rule is supposed to finish if the sentiment finally matches, but it doesn't??

```py
    # still in the if block
    if (
        [e["sentiment"] == "pos" for e in matching_emojis].count(True)
    ) > (
        [e["sentiment"] == "neg" for e in matching_emojis].count(True)
    ):
        m.sentiment_emoji = "pos"
    else:
        m.sentiment_emoji = "neg"
```

The rest of this rule is basically fallback behavior if the sentiment still does not match. This portion uses a super basic assumption to pick a sentiment if it still doesn't match: if more emojis are negative than positive, the sentiment is (likely) negative, and if not, it's (likely) positive.

```py
    target_emojis.remove(m.emoji)

    try:
        m.fixed_emoji = emojimap[
            [
                e
                for e in m.emojis
                if emojimap[e]["sentiment"] == m.sentiment_flair
            ][0]
        ]["repr"]
    except IndexError:
        m.status = "incorrect"
        # TODO: also supposed to return here

    m.status = "fixed"
    # TODO: also supposed to return here? lol??

m.status = "correct"
```

In addition to choosing better sentiment, this part attempts to choose a better emoji by choosing the first emoji from the entire `emojimap` that matches with `flair`'s sentiment. 

If it fails once again, which is thankfully quite rare, the rule system just calls it a day and gives a note that the results of the next rules may yield incorrect results.

### Step 2. Flagging

This part is a bit simpler; all that is done is flagging a given text based on conditions made from the previous step.

```py
m = self.metadata
emojimap = self.rate_map

emojis_are_positive = [
    e["repr"] in m.emojis
    for e in [e for e in emojimap if e["sentiment"] == "pos"]
]
emojis_are_negative = [
    e["repr"] in m.emojis
    for e in [e for e in emojimap if e["sentiment"] == "neg"]
]

contradicting = m.score < 0.8 and emojis_are_negative.count(
    True
) < emojis_are_positive.count(True)
```

Here, the rule groups up some information and save boolean conditions in variables for better readability. Pretty self explanatory.

Not going to lie, the rules used for defining `contradicting` is a little arbitrary. The condition for this is true if `flair`'s prediction certainty is below 80% and if `torchmoji` predicted more negative emojis than positive ones. Umm, anyways...

```py
conjunctions = ["but", "although", "however"]
has_conjugations = (
    any(word in m.content.lower().strip() for word in conjunctions)
    and not contradicting
)
```

Usually, people use conjunctions such as "but", "although", and "however" to give contrasting information. Knowing this, a rule is used to check if the given text has any specified [conjunctions](https://en.wikipedia.org/wiki/Conjunction_(grammar)). Totally expert knowledge :d Now we get into the meat of this rule step.

```py
# defined in a seperate file and imported
class Flags(str, Enum):
    POS_SENTIMENT = "pos_sentiment"
    NEG_SENTIMENT = "neg_sentiment"
    NEG_FLAIR_SENTIMENT = "neg_flair_sentiment"
    NEG_EMOJI_SENTIMENT = "neg_map_sentiment"
    EMOJIS_ARE_POSITIVE = "any_emojis_are_positive"
    NEG_FLAIR_CONTRADICTING = "neg_flair_and_contradicting"
    NEG_EMOJI_CONTRADICTING = "neg_map_and_contradicting"
    CONTAINS_LAUGHING_EMOJI = "contains_laughing_emoji"
    NEG_FLAIR_CONJUGATIONS = "neg_flair_and_conjugations"
    POS_FLAIR_CONJUGATIONS = "pos_flair_and_conjugations"
```

```py
conditions = {
    Flags.NEG_FLAIR_SENTIMENT: m.sentiment_flair == "neg",
    Flags.NEG_EMOJI_SENTIMENT: m.sentiment_emoji == "neg",
    Flags.POS_SENTIMENT: m.sentiment_emoji == "pos" and m.sentiment_flair == "pos",
    Flags.CONTAINS_LAUGHING_EMOJI: "🤣" in m.content,
    Flags.EMOJIS_ARE_POSITIVE: any(emojis_are_positive),
    Flags.NEG_SENTIMENT: m.sentiment_emoji == "neg" and m.sentiment_flair == "neg",
    Flags.NEG_FLAIR_CONTRADICTING: contradicting and m.sentiment_flair == "neg",
    Flags.NEG_EMOJI_CONTRADICTING: contradicting and m.sentiment_emoji == "neg",
    Flags.NEG_FLAIR_CONJUGATIONS: has_conjugations and m.sentiment_flair == "neg",
    Flags.POS_FLAIR_CONJUGATIONS: has_conjugations and m.sentiment_flair == "pos"
}

self.flags = [flag for flag, condition in conditions.items() if condition]
```

Here are descriptions for flags that aren't particularly self-explainable:

- **`EMOJIS_ARE_POSITIVE`:** any of the emojis predicted by `torchmoji` are positive - this implies that the text is at least somewhat positive
- **`NEG_FLAIR_CONTRADICTING`/`NEG_EMOJI_CONTRADICTING`:** the responses of either model are negative and there are conjugations present in the text
- **`POS_FLAIR_CONTRADICTING`/`POS_EMOJI_CONTRADICTING`:** the responses of either model are negative and there are certain conjugations present in the text
- **`POS_FLAIR_CONJUGATIONS`/`NEG_FLAIR_CONJUGATIONS`:** the responses of `flair` are positive or negative and there are certain conjugations present in the text

This is pretty simple to interpret thanks to Python's syntax. The flags are chosen based on if each flag's condition from the dictionary is true.

### Step 3. Scoring

The step which produces the final value.

```py
m = self.metadata

emoji_repr = m.fixed_emoji or m.emoji or m.emojis[0]
picked = [e for e in self.emoji_rate_map if e["repr"] == emoji_repr][0]
negativity_score = 0.333
```

Before beginning scoring, we select the emoji chosen from [step 1](#step-1-resolving-sentiment-between-models) and initialize a negativity score of 0.333 to be modified. In my case, 0.333 is basically a middle value: 3 stars.

```py
for flag in self.flags:
    negativity_score = _match(
        flag,
        {
            Flags.NEG_FLAIR_SENTIMENT: (
                negativity_score - 0.2 * float(picked["pos"])
            )
            * 2,
            Flags.NEG_MAP_SENTIMENT: negativity_score
            - 0.2 * float(picked["neg"]),
            Flags.POS_SENTIMENT: negativity_score - 0.2,
            Flags.CONTAINS_LAUGHING_EMOJI: negativity_score - 0.2,
            Flags.EMOJIS_ARE_POSITIVE: negativity_score - 0.2,
            Flags.NEG_SENTIMENT: negativity_score + 0.5,
            Flags.NEG_FLAIR_CONTRADICTING: negativity_score - 0.2,
            Flags.NEG_FLAIR_CONJUGATIONS: negativity_score - 0.2,
            Flags.POS_FLAIR_CONJUGATIONS: negativity_score + 0.2,
        },
    )

rating = min(5, (round(1 - negativity_score, 4) / 2))
return round(min(5, rating * 10))
```

For every flag that was collected in [step 2](#step-2-flagging), we modify the score according to the value associated with the flag. These values were chosen mostly out of rigorous testing :p And there you have it.

## Conclusion

This approach definitely has some room for improvement, and it admittedly has very little use case. This approach seems to work optimally for **classification problems** where **training models avoids the solution**, and/or when you want to **repurpose information provided by one or more existing models** to create new information.

In my case, I wanted to predict star ratings with as little bias as possible, in which training a model on some architecture with a dataset of labelled reviews would defeat the point of my task: prediction with minimal bias.

I also wanted to use differently-formatted information from multiple models (emoji prediction and plain sentiment prediction) to create a complete sentimental view of text, which can't be solved with transfer-learning, ensemble modelling, or even anything related to machine learning.

If your next classification project involves either of these things by any chance, you might want to consider trying out this layout for your project - it does work alright 😁

## Check out

- [https://kislayverma.com/programming/combining-rule-systems-and-machine-learning/](https://kislayverma.com/programming/combining-rule-systems-and-machine-learning/)
- [https://nlathia.github.io/2020/10/ML-and-rule-engines.html](https://nlathia.github.io/2020/10/ML-and-rule-engines.html)
- [https://www.capitalone.com/tech/machine-learning/rules-vs-machine-learning](https://www.capitalone.com/tech/machine-learning/rules-vs-machine-learning) - Specifically the "Patterns for Using Machine Learning and Rules Engines Together" section
- [https://github.com/conaticus/ebay-account-summarizer](https://github.com/conaticus/ebay-account-summarizer) - applies similar flagging and scoring system to the one used here, though there's no ML involved (see [server/src/sellerRater.ts](https://github.com/conaticus/ebay-account-summarizer/blob/master/server/src/sellerRater.ts))