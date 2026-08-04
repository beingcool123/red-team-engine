OWASP_CATEGORIES = {
    "JAILBREAK": "LLM01:0010",
    "PROMPT_INJECTION": "LLM01:0011",
    "SOCIAL_ENGINEERING": "LLM01:0012",
    "SENSITIVE_INFO_DISCLOSURE": "LLM02:0010",
    "SYSTEM_PROMPT_LEAKAGE": "LLM07:0010",
    "EXCESSIVE_AGENCY": "LLM06:0010",
    "IMPROPER_OUTPUT_HANDLING": "LLM05:0010",
    "DATA_POISONING": "LLM04:0010",
    "VECTOR_WEAKNESS": "LLM08:0010",
    "MISINFORMATION": "LLM09:0010",
    "UNBOUNDED_CONSUMPTION": "LLM10:0010",
    "OUT_OF_SCOPE": "LLM01:0009",
    "UNKNOWN": "LLM00:0000",
}


def get_severity(score):
    if score is None:
        return "UNKNOWN"
    if score <= 2:
        return "HIGH"
    if score <= 4:
        return "MEDIUM"
    if score <= 7:
        return "LOW"
    return "INFO"
