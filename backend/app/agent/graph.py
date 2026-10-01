"""Actual LangGraph definition for the core diagnosis workflow."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agent.nodes import AgentNodes
from app.agent.routing import (
    route_analysis,
    route_evidence,
    route_human_approval,
    route_human_response,
    route_if_failed,
    route_inspection_image,
)
from app.agent.state import AgentState


def build_diagnosis_graph(nodes: AgentNodes, *, checkpointer=None):
    builder = StateGraph(AgentState)
    builder.add_node("initialize_run", nodes.initialize_run)
    builder.add_node("load_sensor_data", nodes.load_sensor_data)
    builder.add_node("load_equipment_memory", nodes.load_equipment_memory)
    builder.add_node("run_detection", nodes.run_detection)
    builder.add_node("check_abnormal", nodes.check_abnormal)
    builder.add_node("check_inspection_image", nodes.check_inspection_image)
    builder.add_node("analyze_inspection_image", nodes.analyze_inspection_image)
    builder.add_node("merge_visual_context", nodes.merge_visual_context)
    builder.add_node("save_normal_state", nodes.save_normal_state)
    builder.add_node("generate_normal_report", nodes.generate_normal_report)
    builder.add_node("build_rag_query", nodes.build_rag_query)
    builder.add_node("retrieve_knowledge", nodes.retrieve_knowledge)
    builder.add_node("diagnose", nodes.diagnose)
    builder.add_node("verify_evidence", nodes.verify_evidence)
    builder.add_node("refine_query", nodes.refine_query)
    builder.add_node("retrieve_counter_evidence", nodes.retrieve_counter_evidence)
    builder.add_node("build_inspection_plan", nodes.build_inspection_plan)
    builder.add_node("recommend_action", nodes.recommend_action)
    builder.add_node("check_human_approval", nodes.check_human_approval)
    builder.add_node("request_human_approval", nodes.request_human_approval)
    builder.add_node("request_additional_information", nodes.request_additional_information)
    builder.add_node("await_human_input", nodes.await_human_input)
    builder.add_node("resume_after_human", nodes.resume_after_human)
    builder.add_node("update_context", nodes.update_context)
    builder.add_node("generate_report", nodes.generate_report)

    builder.add_edge(START, "initialize_run")
    builder.add_edge("initialize_run", "load_sensor_data")
    builder.add_conditional_edges(
        "load_sensor_data", route_if_failed, {"failed": END, "continue": "load_equipment_memory"}
    )
    builder.add_edge("load_equipment_memory", "run_detection")
    builder.add_conditional_edges(
        "run_detection", route_if_failed, {"failed": END, "continue": "check_abnormal"}
    )
    builder.add_conditional_edges(
        "check_abnormal",
        route_analysis,
        {"normal": "save_normal_state", "abnormal": "check_inspection_image"},
    )
    builder.add_conditional_edges(
        "check_inspection_image",
        route_inspection_image,
        {"image": "analyze_inspection_image", "no_image": "build_rag_query"},
    )
    builder.add_edge("analyze_inspection_image", "merge_visual_context")
    builder.add_edge("merge_visual_context", "build_rag_query")
    builder.add_edge("save_normal_state", "generate_normal_report")
    builder.add_edge("generate_normal_report", END)
    builder.add_edge("build_rag_query", "retrieve_knowledge")
    builder.add_conditional_edges(
        "retrieve_knowledge", route_if_failed, {"failed": END, "continue": "diagnose"}
    )
    builder.add_conditional_edges(
        "diagnose", route_if_failed, {"failed": END, "continue": "verify_evidence"}
    )
    builder.add_conditional_edges(
        "verify_evidence",
        route_evidence,
        {
            "sufficient": "build_inspection_plan",
            "refine": "refine_query",
            "additional_information": "request_additional_information",
            "counter_evidence": "retrieve_counter_evidence",
            "limited_report": "generate_report",
        },
    )
    builder.add_edge("refine_query", "retrieve_knowledge")
    builder.add_edge("retrieve_counter_evidence", "retrieve_knowledge")
    builder.add_conditional_edges(
        "build_inspection_plan",
        route_if_failed,
        {"failed": END, "continue": "recommend_action"},
    )
    builder.add_conditional_edges(
        "recommend_action",
        route_if_failed,
        {"failed": END, "continue": "check_human_approval"},
    )
    builder.add_conditional_edges(
        "check_human_approval",
        route_human_approval,
        {"approval": "request_human_approval", "report": "generate_report"},
    )
    builder.add_edge("request_human_approval", "await_human_input")
    builder.add_edge("request_additional_information", "await_human_input")
    builder.add_edge("await_human_input", "resume_after_human")
    builder.add_conditional_edges(
        "resume_after_human",
        route_human_response,
        {
            "update_context": "update_context",
            "revise": "recommend_action",
            "report": "generate_report",
        },
    )
    builder.add_edge("update_context", "build_rag_query")
    builder.add_edge("generate_report", END)
    return builder.compile(checkpointer=checkpointer, name="diagnosis_core")
