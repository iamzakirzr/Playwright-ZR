"""Prompt testing against the live model: does each prompt make the model behave as designed?

Covers the families of prompt tests used in production:

* format adherence: closed label sets, Yes/No, JSON schema
* instruction following: hard word limits
* task accuracy: the classifier routes labelled questions correctly
* prompt regression (A/B): a new prompt version must not score worse than the old one
* robustness: paraphrased questions get semantically consistent answers
"""
import itertools

import pytest
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from pydantic import BaseModel, ConfigDict

from ai.chains import INTENTS, IntentStep
from ai.chatbot import OllamaChatbot
from ai.datasets import golden_case, load_golden
from ai.evaluators import JsonSchemaMetric, KeywordCoverageMetric, WordLimitMetric, cosine_similarity
from ai.prompts import default_registry

REGISTRY = default_registry()

INTENT_CASES = [
    ("I want to send my jacket back", "returns"),
    ("How much does delivery cost?", "shipping"),
    ("My bike light stopped working after a month", "warranty"),
    ("Are you open on Sunday?", "support_hours"),
    ("Can I pay with PayPal?", "payments"),
    ("Write me a poem about the ocean", "out_of_scope"),
    ("Who is the president of France?", "out_of_scope"),
    ("When will my refund arrive?", "returns"),
]


class OrderDetails(BaseModel):
    """Expected output schema of the ``json_extractor`` prompt."""

    model_config = ConfigDict(extra="forbid")
    order_id: str | None
    product: str | None
    issue: str


EXTRACTION_CASES = [
    ("Order #A1234: my Sauce Labs Backpack arrived with a torn strap.", {"order_id": "A1234", "issue": "damaged"}),
    ("It's been three weeks and order B-777 with the Fleece Jacket still hasn't arrived!", {"order_id": "B-777", "issue": "late"}),
    ("I ordered a Onesie but got a Bike Light instead. Order 555.", {"order_id": "555", "issue": "wrong_item"}),
]


def test_intent_classifier_accuracy(chatbot):
    """Routing accuracy on a labelled set must be at least 75%, and every reply must normalise to a known label."""
    step = IntentStep(chatbot)
    predictions = [(q, IntentStep.normalise(chatbot.run_prompt(step.prompt, question=q).text), gold) for q, gold in INTENT_CASES]

    assert all(pred in INTENTS for _, pred, _ in predictions)
    accuracy = sum(pred == gold for _, pred, gold in predictions) / len(predictions)
    misses = [(q, pred, gold) for q, pred, gold in predictions if pred != gold]
    assert accuracy >= 0.75, f"accuracy={accuracy:.2f} misses={misses}"


@pytest.mark.parametrize("message, expected", EXTRACTION_CASES, ids=["damaged", "late", "wrong-item"])
def test_json_extractor_output_matches_schema(chatbot, message, expected):
    """JSON mode plus a strict schema: output parses, validates, and the key fields are right."""
    reply = chatbot.run_prompt(REGISTRY.get("json_extractor"), json_mode=True, message=message).text

    assert_test(LLMTestCase(input=message, actual_output=reply), [JsonSchemaMetric(OrderDetails)])
    parsed = OrderDetails.model_validate_json(reply)
    assert expected["order_id"] in (parsed.order_id or ""), parsed
    assert parsed.issue == expected["issue"], parsed


def test_json_correctness_metric_agrees(chatbot, metrics):
    """DeepEval's JsonCorrectnessMetric agrees with the rule-based schema check."""
    message, _ = EXTRACTION_CASES[0]
    reply = chatbot.run_prompt(REGISTRY.get("json_extractor"), json_mode=True, message=message).text

    assert_test(LLMTestCase(input=message, actual_output=reply), [metrics.json_correctness(OrderDetails)])


@pytest.mark.parametrize("max_words", [12, 25])
def test_constrained_answer_respects_word_limit(chatbot, max_words):
    """Hard length instruction: the reply must stay within ``max_words`` words."""
    case = golden_case("warranty")
    reply = chatbot.run_prompt(
        REGISTRY.get("constrained_answer"),
        max_words=max_words,
        context="\n".join(case["context"]),
        question=case["question"],
    ).text

    assert_test(LLMTestCase(input=case["question"], actual_output=reply), [WordLimitMetric(max_words)])


@pytest.mark.parametrize(
    "question, expected",
    [("Is water damage covered?", "no"), ("Is battery failure covered?", "yes")],
    ids=["no", "yes"],
)
def test_yes_no_prompt_is_closed_form_and_correct(chatbot, question, expected):
    """Closed-form output: exactly one word, Yes or No, and the right one."""
    context = "\n".join(golden_case("warranty")["context"])
    reply = chatbot.run_prompt(REGISTRY.get("yes_no"), context=context, question=question).text

    word = reply.strip().strip(".!").lower()
    assert word in {"yes", "no"}, f"not closed-form: {reply!r}"
    assert word == expected


def test_prompt_alignment_judge(chatbot, metrics):
    """LLM-judged instruction following on the constrained-answer prompt."""
    case = golden_case("support-hours")
    reply = chatbot.run_prompt(
        REGISTRY.get("constrained_answer"), max_words=20, context="\n".join(case["context"]), question=case["question"]
    ).text

    metric = metrics.prompt_alignment(["Reply in a single sentence.", "Do not use lists or markdown."])
    assert_test(LLMTestCase(input=case["question"], actual_output=reply), [metric])


def test_new_prompt_version_is_not_a_regression(chatbot, settings):
    """A/B regression: grounded_qa latest must cover at least as many helpful facts as v1."""

    def coverage(bot: OllamaChatbot) -> float:
        """Mean keyword coverage of ``bot`` across the golden set."""
        scores = []
        for case in load_golden("cases"):
            metric = KeywordCoverageMetric(case["helpful_facts"])
            scores.append(metric.measure(LLMTestCase(input="", actual_output=bot.ask(case["question"], case["context"]).text)))
        return sum(scores) / len(scores)

    v1_bot = OllamaChatbot(
        chatbot.request, chatbot.model, seed=settings.chatbot_seed, canary=settings.canary_token,
        grounded_prompt=REGISTRY.get("grounded_qa", version=1),
    )
    latest, baseline = coverage(chatbot), coverage(v1_bot)

    assert latest >= baseline, f"grounded_qa v{REGISTRY.get('grounded_qa').version}={latest:.2f} < v1={baseline:.2f}"


def test_paraphrased_questions_get_consistent_answers(chatbot, settings):
    """Robustness: three phrasings of one question give pairwise-similar answers."""
    case = golden_case("returns-window")
    paraphrases = [
        "How many days do I have to return an item?",
        "What's the time limit for sending a purchase back?",
        "until when can I return stuff I bought",
    ]
    answers = [chatbot.ask(q, case["context"]).text for q in paraphrases]

    for a, b in itertools.combinations(answers, 2):
        score = cosine_similarity(a, b, settings.embedding_model)
        assert score >= 0.6, f"inconsistent ({score:.2f}): {a!r} vs {b!r}"


def test_summarizer_keeps_every_number(chatbot):
    """The summary keeps every number and limit from the source document."""
    document = " ".join(golden_case("shipping-cost")["context"])
    summary = chatbot.run_prompt(REGISTRY.get("summarizer"), document=document).text

    assert_test(LLMTestCase(input=document, actual_output=summary), [KeywordCoverageMetric(["4.99", "75", "14.99"])])
