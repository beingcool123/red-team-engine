from typing import TypedDict, List, Dict, Any

class RedTeamState(TypedDict):
    target_system_prompt: str
    target_user_input: str
    attack_categories: List[str]
    attack_prompts: List[str]
    responses: List[str]
    scores: List[int]
    vulnerabilities: List[Dict[str, Any]]
    final_report: str
    current_index: int