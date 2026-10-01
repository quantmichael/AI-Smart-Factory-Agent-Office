import { HistoryRunDetail } from "@/components/HistoryRunDetail";

export default async function HistoryRunPage({ params }: { params: Promise<{ runId: string }> }) {
  const { runId } = await params;
  return <HistoryRunDetail runId={runId} />;
}
