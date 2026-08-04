from typing import Any

from typing_extensions import TypedDict


class RedTeamState(TypedDict, total=False):
    target_system_prompt: str
    target_user_input: str
    attack_categories: list[str]
    attack_prompts: list[str]
    responses: list[str]
    scores: list[Any]
    vulnerabilities: list[dict[str, Any]]
    final_report: str
    current_index: int
    # Carries per-run model/provider credentials so nodes don't mutate os.environ.
    # Keys: attack_provider, attack_model, attack_api_key, attack_base_url,
    #        target_provider, target_model, target_api_key, target_base_url
    run_config: dict[str, str] | None
