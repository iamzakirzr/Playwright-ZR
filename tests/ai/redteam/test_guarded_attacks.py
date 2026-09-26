"""Red team against the production configuration (model + guard rails).

Zero tolerance: every attack in the library must be defended. A failure here is
a security bug in the guard stack, never a flaky test. Fix the guard or the
prompt, don't loosen the check.

Attacks map to the OWASP Top 10 for LLM Applications (LLM01 prompt injection,
LLM02 sensitive-information disclosure, LLM05 improper output handling,
LLM06 excessive agency, LLM07 system-prompt leakage, LLM09 misinformation).
"""

import pytest

from ai.redteam import RedTeamRunner, attack_success_rate, load_attacks

ATTACKS = load_attacks()


@pytest.fixture(scope="module")
def runner(guarded_chatbot, settings) -> RedTeamRunner:
    """Red-team runner aimed at the guarded chatbot."""
    return RedTeamRunner(guarded_chatbot, settings.canary_token)


@pytest.mark.parametrize("attack", ATTACKS, ids=[a.id for a in ATTACKS])
def test_attack_is_defended(runner, attack):
    """Each attack must be neutralised by at least one guard layer."""
    result = runner.run(attack)

    assert result.defended, result.summary()


def test_guarded_attack_success_rate_within_budget(runner, settings):
    """Aggregate ASR per category must not exceed the budget (0% by default)."""
    asr = attack_success_rate(runner.run_all(ATTACKS))

    over = {cat: rate for cat, rate in asr.items() if rate > settings.guarded_max_asr}
    assert not over, f"ASR over budget {settings.guarded_max_asr}: {over}"
