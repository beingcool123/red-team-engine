import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from ..state import RedTeamState

def execute_single_attack(system_prompt, user_input, attack):
    # Instantiate target LLM inside the function
    target_llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.7
    )
    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", f"{user_input}\n\n[ATTACK PROMPT]: {attack}")
        ])
        return target_llm.invoke(prompt.format_messages()).content
    except Exception as e:
        return f"[ERROR: {str(e)}]"

def executor_node(state: RedTeamState) -> RedTeamState:
    responses = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(
                execute_single_attack,
                state["target_system_prompt"],
                state["target_user_input"],
                attack
            ): attack for attack in state["attack_prompts"]
        }
        for future in as_completed(futures):
            responses.append(future.result())
    state["responses"] = responses
    return state