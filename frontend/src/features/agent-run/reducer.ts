import { AGENT_ROLES, GRAPH_NODES, NODE_AGENT, RAG_ROUTE_NODES } from "./event-mapper.ts";
import type {
  AgentEvent,
  AgentRole,
  AgentRun,
  AgentRunUIState,
  ConnectionStatus,
  Evidence,
  FinalReport,
  GraphNodeState,
} from "./types.ts";

const agentStates = () => Object.fromEntries(AGENT_ROLES.map((role) => [role, "IDLE"])) as AgentRunUIState["agentStates"];
const graphStates = () => Object.fromEntries(GRAPH_NODES.map((node) => [node, "PENDING"])) as Record<string, GraphNodeState>;

export const initialAgentRunState: AgentRunUIState = {
  workflowStatus: "IDLE",
  agentStates: agentStates(),
  graphNodeStates: graphStates(),
  equipmentStatus: "ANALYZING",
  evidenceCount: 0,
  retryCount: 0,
  timeline: [],
  reportReady: false,
  evidence: [],
  connectionStatus: "idle",
};

export type AgentRunAction =
  | { type: "RESET" }
  | { type: "HYDRATE"; run: AgentRun; events: AgentEvent[] }
  | { type: "RUN_SYNC"; run: AgentRun }
  | { type: "EVENT"; event: AgentEvent }
  | { type: "EVIDENCE"; evidence: Evidence[] }
  | { type: "REPORT"; report: FinalReport }
  | { type: "CONNECTION"; status: ConnectionStatus }
  | { type: "ERROR"; message: string }
  | { type: "CLEAR_ERROR" };

function eventRole(event: AgentEvent): AgentRole | undefined {
  if (AGENT_ROLES.includes(event.agent_role as AgentRole)) return event.agent_role as AgentRole;
  return NODE_AGENT[event.node];
}

function syncRun(state: AgentRunUIState, run: AgentRun): AgentRunUIState {
  return {
    ...state,
    run,
    runId: run.run_id,
    workflowStatus: run.workflow_status,
    currentNode: run.current_node,
    analysisSummary: run.analysis_result ?? state.analysisSummary,
    evidenceStatus: run.evidence_status ?? state.evidenceStatus,
    evidenceCount: run.evidence_count,
    retryCount: run.retrieval_retry_count,
    pendingHumanRequest: run.pending_human_request ?? undefined,
    reportReady: run.final_report_available,
    startedAt: run.created_at,
  };
}

export function reduceEvent(state: AgentRunUIState, event: AgentEvent): AgentRunUIState {
  if (state.timeline.some((item) => item.event_id === event.event_id || item.sequence === event.sequence)) {
    return state;
  }
  const timeline = [...state.timeline, event].sort((a, b) => a.sequence - b.sequence).slice(-500);
  const role = eventRole(event);
  const graphNode = event.node === "generate_normal_report" ? "generate_report" : event.node;
  const next: AgentRunUIState = {
    ...state,
    timeline,
    currentNode: event.node,
    activeAgent: role,
    agentStates: { ...state.agentStates },
    graphNodeStates: { ...state.graphNodeStates },
    error: undefined,
  };

  if (event.event_type === "workflow_started") {
    next.workflowStatus = "RUNNING";
    next.equipmentStatus = "ANALYZING";
  }
  if (event.event_type === "node_started") {
    if (role) next.agentStates[role] = "WORKING";
    if (graphNode in next.graphNodeStates) next.graphNodeStates[graphNode] = "ACTIVE";
  }
  if (event.event_type === "node_completed") {
    if (role) next.agentStates[role] = "DONE";
    if (graphNode in next.graphNodeStates) next.graphNodeStates[graphNode] = "COMPLETED";
    if (event.node === "check_inspection_image" && Number(event.payload.image_count ?? 0) === 0) {
      next.graphNodeStates.analyze_inspection_image = "SKIPPED";
    }
  }
  if (event.event_type === "detection_normal") {
    next.selectedEdge = "NORMAL";
    next.equipmentStatus = "NORMAL";
    for (const node of RAG_ROUTE_NODES) next.graphNodeStates[node] = "SKIPPED";
  }
  if (event.event_type === "detection_abnormal") {
    next.selectedEdge = "ABNORMAL";
    next.equipmentStatus = "ABNORMAL";
  }
  if (event.event_type === "retrieval_completed") {
    next.evidenceCount = Number(event.payload.evidence_count ?? next.evidenceCount);
    next.equipmentStatus = "DIAGNOSING";
  }
  if (event.event_type === "evidence_status_changed") {
    const status = String(event.payload.evidence_status ?? "");
    next.evidenceStatus = status;
    next.retryCount = Number(event.payload.retry_count ?? next.retryCount);
    if (status !== "SUFFICIENT") {
      next.agentStates.RAG_AGENT = "RETRYING";
      next.graphNodeStates.retrieve_knowledge = "RETRYING";
    }
  }
  if (event.event_type === "inspection_plan_created") next.equipmentStatus = "NEEDS_CHECK";
  if (event.event_type === "action_recommended") next.equipmentStatus = "MAINTENANCE_RECOMMENDED";
  if (event.event_type === "human_input_required") {
    next.workflowStatus = "WAITING";
    if (role) next.agentStates[role] = "NEEDS_HUMAN";
    if (graphNode in next.graphNodeStates) next.graphNodeStates[graphNode] = "WAITING";
  }
  if (event.event_type === "human_input_received" || event.event_type === "workflow_resumed") {
    next.workflowStatus = "RUNNING";
    next.pendingHumanRequest = undefined;
    if (role) next.agentStates[role] = "WORKING";
  }
  if (event.event_type === "report_generated") next.reportReady = true;
  if (event.event_type === "workflow_completed") {
    next.workflowStatus = "COMPLETED";
    next.activeAgent = undefined;
  }
  if (event.event_type === "workflow_error") {
    next.workflowStatus = "FAILED";
    next.equipmentStatus = "ERROR";
    next.error = event.message;
    if (role) next.agentStates[role] = "ERROR";
    if (graphNode in next.graphNodeStates) next.graphNodeStates[graphNode] = "ERROR";
  }
  return next;
}

export function agentRunReducer(state: AgentRunUIState, action: AgentRunAction): AgentRunUIState {
  switch (action.type) {
    case "RESET":
      return { ...initialAgentRunState, agentStates: agentStates(), graphNodeStates: graphStates() };
    case "HYDRATE": {
      const rebuilt = [...action.events]
        .sort((a, b) => a.sequence - b.sequence)
        .reduce(reduceEvent, { ...initialAgentRunState, agentStates: agentStates(), graphNodeStates: graphStates() });
      return syncRun(rebuilt, action.run);
    }
    case "RUN_SYNC":
      return syncRun(state, action.run);
    case "EVENT":
      return reduceEvent(state, action.event);
    case "EVIDENCE":
      return { ...state, evidence: action.evidence, evidenceCount: action.evidence.length };
    case "REPORT":
      return { ...state, report: action.report, reportReady: true };
    case "CONNECTION":
      return { ...state, connectionStatus: action.status };
    case "ERROR":
      return { ...state, error: action.message };
    case "CLEAR_ERROR":
      return { ...state, error: undefined };
    default:
      return state;
  }
}
