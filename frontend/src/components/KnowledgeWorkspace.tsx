"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

import { AppHeader } from "@/components/AppHeader";
import {
  translateKnowledgeQuery,
  type KnowledgeQueryTranslation,
} from "@/features/knowledge/query-translator";
import {
  fetchKnowledgeDocument,
  fetchKnowledgeDocuments,
  fetchKnowledgeSummary,
  searchKnowledge,
  type KnowledgeDocument,
  type KnowledgeDocumentDetail,
  type KnowledgeSearchResult,
  type KnowledgeSummary,
} from "@/lib/api";

const TYPE_LABEL: Record<string, string> = {
  dataset_overview: "데이터셋 안내",
  damage_fact_sheet: "손상 정보",
  experiment_description: "시험 설명",
  publication: "연구 논문",
  measurement_log: "측정 기록",
  vibration_diagnostic_guide: "진동 진단 가이드",
  failure_analysis_guide: "고장 분석 가이드",
};

const PURPOSES = [
  { value: "DIAGNOSTIC_EVIDENCE", label: "진단 근거" },
  { value: "INSPECTION_ACTION", label: "점검·조치" },
  { value: "DATASET_EVIDENCE", label: "데이터셋 근거" },
];

function sourceClass(document: KnowledgeDocument) {
  return document.publisher.toLowerCase().includes("skf") ? "source-skf" : "source-paderborn";
}

function SourceBadge({ document }: { document: KnowledgeDocument }) {
  return <span className={`knowledge-source ${sourceClass(document)}`}>{document.publisher.toLowerCase().includes("skf") ? "SKF" : "PADERBORN"}</span>;
}

export function KnowledgeWorkspace() {
  const [summary, setSummary] = useState<KnowledgeSummary>();
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [detail, setDetail] = useState<KnowledgeDocumentDetail>();
  const [chunkPage, setChunkPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string>();
  const [question, setQuestion] = useState("베어링 외륜 손상의 주요 진동 특징은?");
  const [topK, setTopK] = useState(5);
  const [purpose, setPurpose] = useState("DIAGNOSTIC_EVIDENCE");
  const [searchResult, setSearchResult] = useState<KnowledgeSearchResult>();
  const [submittedQuery, setSubmittedQuery] = useState<KnowledgeQueryTranslation>();
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string>();

  const loadCatalog = useCallback(async () => {
    setLoading(true); setError(undefined);
    try {
      const [nextSummary, nextDocuments] = await Promise.all([
        fetchKnowledgeSummary(),
        fetchKnowledgeDocuments(),
      ]);
      setSummary(nextSummary);
      setDocuments(nextDocuments);
      setSelectedId((current) => current && nextDocuments.some((item) => item.document_id === current) ? current : (nextDocuments[0]?.document_id ?? ""));
    } catch (nextError: unknown) {
      setError(nextError instanceof Error ? nextError.message : "기술지식을 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadDetail = useCallback(async () => {
    if (!selectedId) { setDetail(undefined); return; }
    setDetailLoading(true); setDetailError(undefined);
    try {
      setDetail(await fetchKnowledgeDocument(selectedId, chunkPage));
    } catch (nextError: unknown) {
      setDetailError(nextError instanceof Error ? nextError.message : "문서 상세정보를 불러오지 못했습니다.");
    } finally {
      setDetailLoading(false);
    }
  }, [chunkPage, selectedId]);

  useEffect(() => { void loadCatalog(); }, [loadCatalog]);
  useEffect(() => { void loadDetail(); }, [loadDetail]);

  const selectDocument = (documentId: string) => {
    setSelectedId(documentId); setChunkPage(1);
  };

  const submitSearch = async (event: FormEvent) => {
    event.preventDefault();
    const translatedQuery = translateKnowledgeQuery(question);
    if (!translatedQuery.search_query) return;
    setSearching(true); setSearchError(undefined); setSearchResult(undefined);
    setSubmittedQuery(translatedQuery);
    try {
      setSearchResult(await searchKnowledge(translatedQuery.search_query, topK, purpose));
    } catch (nextError: unknown) {
      setSearchError(nextError instanceof Error ? nextError.message : "검색을 실행하지 못했습니다.");
    } finally {
      setSearching(false);
    }
  };

  return (
    <main className="app-shell knowledge-shell">
      <AppHeader active="knowledge" status={<div className="system-health"><span className={`connection-dot ${summary?.status === "READY" ? "online" : "offline"}`} /><div><strong>읽기 전용 지식 조회</strong><small>KNOWLEDGE BASE</small></div></div>} />
      <section className="knowledge-hero"><div><span className="kicker">기술문서 · KNOWLEDGE TRANSPARENCY</span><h1>기술지식</h1><p>AI 진단에 사용되는 기술문서와 검색 근거를 확인합니다.</p></div>{summary && <div className="knowledge-ready"><span className="connection-dot online" /><div><small>COLLECTION ACCESS</small><strong>조회 가능</strong></div></div>}</section>

      {loading && <section className="knowledge-feedback surface" aria-live="polite">Knowledge Base를 확인하는 중…</section>}
      {!loading && error && <section className="knowledge-feedback knowledge-error surface" role="alert"><strong>기술지식을 불러오지 못했습니다.</strong><p>{error}</p><button type="button" onClick={() => void loadCatalog()}>다시 시도</button></section>}
      {!loading && !error && summary && <>
        <section className="knowledge-summary" aria-label="Knowledge Base 요약">
          <article className="surface"><span>기술문서</span><strong>{summary.document_count}</strong><small>색인된 문서</small></article>
          <article className="surface"><span>검색 단위</span><strong>{summary.chunk_count}</strong><small>CHUNKS</small></article>
          <article className="surface"><span>Vector DB</span><strong>{summary.vector_store}</strong><small>{summary.collection}</small></article>
          <article className="surface"><span>Knowledge Pack</span><strong>{summary.knowledge_pack}</strong><small>MANIFEST v{summary.knowledge_version}</small></article>
          <article className="surface"><span>Embedding</span><strong>{summary.embedding_dimension}차원</strong><small>{summary.embedding_method}</small></article>
        </section>

        <section className="knowledge-layout">
          <div className="knowledge-documents surface">
            <div className="knowledge-panel-heading"><div><span className="kicker">DOCUMENT CATALOG</span><h2>기술문서 목록</h2></div><span className="count-badge">{documents.length}개</span></div>
            {documents.length === 0 ? <div className="knowledge-empty">색인된 기술문서가 없습니다.</div> : <div className="knowledge-document-list">{documents.map((document) => <button className={selectedId === document.document_id ? "selected" : ""} key={document.document_id} onClick={() => selectDocument(document.document_id)} type="button"><div><SourceBadge document={document} /><span>{TYPE_LABEL[document.document_type] ?? document.document_type}</span></div><strong>{document.title}</strong><small>{document.publisher}</small><footer><span>{document.chunk_count} Chunks</span><span>v{document.version}</span></footer></button>)}</div>}
          </div>

          <div className="knowledge-detail surface">
            <div className="knowledge-panel-heading"><div><span className="kicker">INDEXED CONTENT</span><h2>문서 상세 및 Chunk</h2></div></div>
            {detailLoading && <div className="knowledge-empty" aria-live="polite">문서 내용을 불러오는 중…</div>}
            {!detailLoading && detailError && <div className="knowledge-inline-error" role="alert"><p>{detailError}</p><button type="button" onClick={() => void loadDetail()}>다시 시도</button></div>}
            {!detailLoading && !detailError && detail && <>
              <article className="knowledge-document-meta">
                <div><SourceBadge document={detail.document} /><span className="knowledge-type">{TYPE_LABEL[detail.document.document_type] ?? detail.document.document_type}</span></div>
                <h3>{detail.document.title}</h3>
                <dl><div><dt>Publisher</dt><dd>{detail.document.publisher}</dd></div><div><dt>Version</dt><dd>{detail.document.version}</dd></div><div><dt>License</dt><dd>{detail.document.license || detail.document.license_status}</dd></div><div><dt>색인 페이지</dt><dd>{detail.document.indexed_pages.length ? `${detail.document.indexed_pages.length}개` : "페이지 정보 없음"}</dd></div></dl>
                {detail.document.official_url && <a href={detail.document.official_url} target="_blank" rel="noreferrer">공식 출처 열기 ↗</a>}
              </article>
              <div className="knowledge-chunk-heading"><strong>색인 Chunk</strong><span>{detail.chunks.total}개 중 {detail.chunks.items.length}개 표시</span></div>
              <div className="knowledge-chunks">{detail.chunks.items.map((chunk) => <details key={chunk.chunk_id}><summary><span>{chunk.chunk_id}</span><b>{chunk.page ? `p.${chunk.page}` : "페이지 없음"}{chunk.section ? ` · ${chunk.section}` : ""}</b></summary><p>{chunk.content}</p></details>)}</div>
              {detail.chunks.total_pages > 1 && <nav className="knowledge-pagination" aria-label="Chunk 페이지"><button disabled={chunkPage <= 1} type="button" onClick={() => setChunkPage((value) => value - 1)}>이전</button><span>{chunkPage} / {detail.chunks.total_pages}</span><button disabled={chunkPage >= detail.chunks.total_pages} type="button" onClick={() => setChunkPage((value) => value + 1)}>다음</button></nav>}
            </>}
          </div>
        </section>

        <section className="knowledge-search surface">
          <div className="knowledge-panel-heading"><div><span className="kicker">LIVE RETRIEVAL TEST</span><h2>RAG 검색 테스트</h2><p>현재 Agent가 사용하는 동일한 검색 API로 근거 Chunk를 확인합니다.</p></div></div>
          <form onSubmit={submitSearch}><label><span>질문</span><input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="기술문서에서 확인할 질문을 입력하세요" /></label><label><span>검색 목적</span><select value={purpose} onChange={(event) => setPurpose(event.target.value)}>{PURPOSES.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label><label><span>Top-K</span><select value={topK} onChange={(event) => setTopK(Number(event.target.value))}>{[3, 5, 10].map((value) => <option key={value} value={value}>{value}</option>)}</select></label><button disabled={searching || !question.trim()} type="submit">{searching ? "검색 중…" : "근거 검색"}</button></form>
          <p className="knowledge-score-note">검색 점수는 1 − cosine distance 기반의 상대적 유사도 순위이며, 정확도·신뢰도·정답 확률을 의미하지 않습니다. 검색 결과는 Knowledge Base 안의 유사 Chunk이며 질문의 정답을 보장하지 않습니다.</p>
          {searchError && <div className="knowledge-inline-error" role="alert"><p>{searchError}</p><button type="button" onClick={() => setSearchError(undefined)}>닫기</button></div>}
          {searchResult && submittedQuery && (submittedQuery.translated || !submittedQuery.complete) && <div className="knowledge-query-trace" aria-label="검색 Query 변환 정보"><div><span>사용자 질문</span><strong>{submittedQuery.original_query}</strong></div>{submittedQuery.translated && <div><span>검색에 사용된 영문 Query</span><strong>{searchResult.query.query_text}</strong></div>}{!submittedQuery.complete && <p>사전에 없는 한국어 표현({submittedQuery.unmappedKorean.join(", ")})은 의미를 추측하지 않고 원문으로 유지했습니다. 검색 결과의 관련성이 낮을 수 있습니다.</p>}</div>}
          {searchResult && searchResult.evidence.length === 0 && <div className="knowledge-empty">검색된 근거가 없습니다. 질문이나 검색 목적을 바꿔 보세요.</div>}
          {searchResult && searchResult.evidence.length > 0 && <div className="knowledge-results">{searchResult.evidence.map((evidence, index) => <article key={evidence.evidence_id}><header><span className="knowledge-rank">#{index + 1}</span><div><strong>{evidence.title}</strong><small>{evidence.publisher} · {evidence.page ? `p.${evidence.page}` : "페이지 없음"}{evidence.section ? ` · ${evidence.section}` : ""}</small></div><b>{evidence.retrieval_score?.toFixed(4) ?? "—"}</b></header><p>{evidence.content}</p><footer><span>{evidence.chunk_id}</span>{evidence.official_url && <a href={evidence.official_url} target="_blank" rel="noreferrer">출처 ↗</a>}</footer></article>)}</div>}
        </section>
      </>}
    </main>
  );
}
