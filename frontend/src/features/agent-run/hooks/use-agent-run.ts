"use client";

import { useCallback, useEffect, useReducer, useRef, useState } from "react";

import {
  API_V1,
  createAgentRun,
  fetchAgentEvents,
  fetchAgentEvidence,
  fetchAgentReport,
  fetchAgentRun,
  submitHumanInput,
  stageInspectionImage,
  uploadRunInspectionImage,
  type HumanInputPayload,
} from "@/lib/api";
import { agentRunReducer, initialAgentRunState } from "../reducer";
import { isMissingAgentRun, restorePersistedAgentRun } from "../active-run-recovery";
import type { AgentEvent, AgentRun } from "../types";

const STORAGE_KEY = "agent-office.active-run";
const MAX_SSE_RECONNECT_ATTEMPTS = 4;
const SSE_RECONNECT_DELAYS_MS = [1000, 2000, 4000, 8000] as const;
const EVENT_TYPES = [
  "workflow_started",
  "node_started",
  "node_completed",
  "equipment_memory_loaded",
  "inspection_image_uploaded",
  "vision_analysis_completed",
  "visual_context_added",
  "detection_normal",
  "detection_abnormal",
  "retrieval_completed",
  "evidence_status_changed",
  "inspection_plan_created",
  "action_recommended",
  "human_input_required",
  "human_input_received",
  "workflow_resumed",
  "report_generated",
  "workflow_completed",
  "workflow_error",
];

export function useAgentRun() {
  const [state, dispatch] = useReducer(agentRunReducer, initialAgentRunState);
  const [loadingPhase, setLoadingPhase] = useState<string>();
  const sourceRef = useRef<EventSource | undefined>(undefined);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const reconnectAttemptsRef = useRef(0);
  const runIdRef = useRef<string | undefined>(undefined);
  const lastSequenceRef = useRef(0);

  const loadDetails = useCallback(async (run: AgentRun) => {
    dispatch({ type: "RUN_SYNC", run });
    const requests: Promise<void>[] = [];
    if (run.evidence_count > 0) {
      requests.push(
        fetchAgentEvidence(run.run_id).then((evidence) => dispatch({ type: "EVIDENCE", evidence })),
      );
    }
    if (run.final_report_available) {
      requests.push(
        fetchAgentReport(run.run_id).then((report) => dispatch({ type: "REPORT", report })),
      );
    }
    await Promise.all(requests);
  }, []);

  const recover = useCallback(
    async (runId: string) => {
      const [run, events] = await Promise.all([
        fetchAgentRun(runId),
        fetchAgentEvents(runId, lastSequenceRef.current),
      ]);
      for (const event of events) {
        lastSequenceRef.current = Math.max(lastSequenceRef.current, event.sequence);
        dispatch({ type: "EVENT", event });
      }
      await loadDetails(run);
      return run;
    },
    [loadDetails],
  );

  const connect = useCallback(
    (runId: string) => {
      sourceRef.current?.close();
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      dispatch({ type: "CONNECTION", status: "connecting" });
      const source = new EventSource(
        `${API_V1}/agent/runs/${encodeURIComponent(runId)}/events/stream?after_sequence=${lastSequenceRef.current}`,
      );
      sourceRef.current = source;
      source.onopen = () => {
        dispatch({ type: "CLEAR_ERROR" });
        dispatch({ type: "CONNECTION", status: "live" });
      };

      const receive = (message: MessageEvent<string>) => {
        try {
          const event = JSON.parse(message.data) as AgentEvent;
          reconnectAttemptsRef.current = 0;
          lastSequenceRef.current = Math.max(lastSequenceRef.current, event.sequence);
          dispatch({ type: "EVENT", event });
          if (
            [
              "detection_normal",
              "detection_abnormal",
              "retrieval_completed",
              "evidence_status_changed",
              "human_input_required",
              "report_generated",
              "workflow_completed",
              "workflow_error",
            ].includes(event.event_type)
          ) {
            fetchAgentRun(runId).then(loadDetails).catch(() => undefined);
          }
        } catch {
          dispatch({ type: "ERROR", message: "실시간 스트림에서 잘못된 이벤트를 수신했습니다." });
        }
      };
      EVENT_TYPES.forEach((type) => source.addEventListener(type, receive as EventListener));
      source.onerror = () => {
        if (sourceRef.current !== source) return;
        source.close();
        dispatch({ type: "CONNECTION", status: "reconnecting" });
        const scheduleReconnect = () => {
          const attempt = reconnectAttemptsRef.current + 1;
          if (attempt > MAX_SSE_RECONNECT_ATTEMPTS) {
            dispatch({
              type: "ERROR",
              message: "실시간 연결이 끊겼습니다. 진단 실행 상태는 서버에 보존되어 있습니다.",
            });
            dispatch({ type: "CONNECTION", status: "error" });
            return;
          }
          reconnectAttemptsRef.current = attempt;
          reconnectRef.current = setTimeout(
            () => connect(runId),
            SSE_RECONNECT_DELAYS_MS[attempt - 1],
          );
        };
        recover(runId)
          .then((run) => {
            if (run.workflow_status === "RUNNING" || run.workflow_status === "CREATED") {
              scheduleReconnect();
            } else {
              reconnectAttemptsRef.current = 0;
              dispatch({ type: "CONNECTION", status: "closed" });
            }
          })
          .catch(scheduleReconnect);
      };
    },
    [loadDetails, recover],
  );

  const hydrate = useCallback(
    async (runId: string) => {
      setLoadingPhase("저장된 진단 실행을 복구하는 중…");
      const [run, events] = await Promise.all([fetchAgentRun(runId), fetchAgentEvents(runId)]);
      lastSequenceRef.current = events.at(-1)?.sequence ?? 0;
      runIdRef.current = runId;
      dispatch({ type: "HYDRATE", run, events });
      await loadDetails(run);
      setLoadingPhase(undefined);
      return run;
    },
    [loadDetails],
  );

  useEffect(() => {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (saved) {
      restorePersistedAgentRun({
        runId: saved,
        load: hydrate,
        connect,
        markClosed: () => dispatch({ type: "CONNECTION", status: "closed" }),
        clearStale: () => {
          sourceRef.current?.close();
          if (reconnectRef.current) clearTimeout(reconnectRef.current);
          reconnectAttemptsRef.current = 0;
          runIdRef.current = undefined;
          lastSequenceRef.current = 0;
          window.localStorage.removeItem(STORAGE_KEY);
          setLoadingPhase(undefined);
          dispatch({ type: "RESET" });
        },
      }).catch((error: unknown) => {
          setLoadingPhase(undefined);
          dispatch({ type: "ERROR", message: error instanceof Error ? error.message : "진단 실행 복구에 실패했습니다." });
          dispatch({ type: "CONNECTION", status: "error" });
        });
    }
    return () => {
      sourceRef.current?.close();
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
    };
  }, [connect, hydrate]);

  const startRun = useCallback(
    async (equipmentId: string, measurementId: string, inspectionImage?: File, demoScenario?: "HITL_CONTROLLED") => {
      sourceRef.current?.close();
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      reconnectAttemptsRef.current = 0;
      dispatch({ type: "RESET" });
      setLoadingPhase("AI 에이전트를 시작하는 중…");
      try {
        const imageIds = inspectionImage
          ? [(await stageInspectionImage(equipmentId, inspectionImage)).image_id]
          : [];
        const created = await createAgentRun(equipmentId, measurementId, imageIds, demoScenario);
        runIdRef.current = created.run_id;
        lastSequenceRef.current = 0;
        window.localStorage.setItem(STORAGE_KEY, created.run_id);
        const run = await fetchAgentRun(created.run_id);
        dispatch({ type: "HYDRATE", run, events: [] });
        connect(created.run_id);
      } catch (error: unknown) {
        dispatch({ type: "ERROR", message: error instanceof Error ? error.message : "AI 진단 시작에 실패했습니다." });
      } finally {
        setLoadingPhase(undefined);
      }
    },
    [connect],
  );

  const uploadHumanInspectionImage = useCallback(async (file: File) => {
    const runId = runIdRef.current;
    if (!runId) throw new Error("활성 진단 실행이 없습니다.");
    return (await uploadRunInspectionImage(runId, file)).image_id;
  }, []);

  const submitHuman = useCallback(
    async (payload: HumanInputPayload) => {
      const runId = runIdRef.current;
      if (!runId) return;
      setLoadingPhase("작업자 판단을 제출하는 중…");
      try {
        const run = await submitHumanInput(runId, payload);
        dispatch({ type: "RUN_SYNC", run });
        connect(runId);
      } catch (error: unknown) {
        dispatch({ type: "ERROR", message: error instanceof Error ? error.message : "작업자 입력 제출에 실패했습니다." });
      } finally {
        setLoadingPhase(undefined);
      }
    },
    [connect],
  );

  const clearRun = useCallback(() => {
    sourceRef.current?.close();
    if (reconnectRef.current) clearTimeout(reconnectRef.current);
    reconnectAttemptsRef.current = 0;
    window.localStorage.removeItem(STORAGE_KEY);
    runIdRef.current = undefined;
    lastSequenceRef.current = 0;
    dispatch({ type: "RESET" });
  }, []);

  const retryConnection = useCallback(async () => {
    const runId = runIdRef.current ?? window.localStorage.getItem(STORAGE_KEY) ?? undefined;
    if (!runId) return;
    runIdRef.current = runId;
    reconnectAttemptsRef.current = 0;
    dispatch({ type: "CLEAR_ERROR" });
    dispatch({ type: "CONNECTION", status: "connecting" });
    try {
      const run = await recover(runId);
      if (run.workflow_status === "RUNNING" || run.workflow_status === "CREATED") connect(runId);
      else dispatch({ type: "CONNECTION", status: "closed" });
    } catch (error: unknown) {
      if (isMissingAgentRun(error)) {
        clearRun();
        return;
      }
      dispatch({ type: "ERROR", message: error instanceof Error ? error.message : "실시간 연결 복구에 실패했습니다." });
      dispatch({ type: "CONNECTION", status: "error" });
    }
  }, [clearRun, connect, recover]);

  return { state, loadingPhase, startRun, submitHuman, uploadHumanInspectionImage, clearRun, retryConnection };
}
