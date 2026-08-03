from langgraph.graph import StateGraph, START, END
from .state import RedTeamState
from .nodes.planner import planner_node
from .nodes.executor import executor_node
from .nodes.judge import judge_node
from .nodes.reporter import reporter_node

def create_workflow():
    workflow = StateGraph(RedTeamState)
    workflow.add_node("planner", planner_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("judge", judge_node)
    workflow.add_node("reporter", reporter_node)
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", "judge")
    workflow.add_edge("judge", "reporter")
    workflow.add_edge("reporter", END)
    return workflow.compile()