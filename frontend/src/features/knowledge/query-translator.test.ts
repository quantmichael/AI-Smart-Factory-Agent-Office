import assert from "node:assert/strict";
import { test } from "node:test";

import { translateKnowledgeQuery } from "./query-translator.ts";

const CASES = [
  ["베어링 외륜 손상의 주요 진동 특징은?", "bearing outer race damage vibration characteristics"],
  ["베어링 내륜 손상의 원인은 무엇인가?", "causes of bearing inner race damage"],
  ["베어링 손상 시 점검해야 할 사항은?", "bearing damage inspection procedure"],
  ["베어링 윤활 부족으로 발생하는 문제는?", "bearing problems caused by inadequate lubrication"],
  ["베어링 진동에서 첨도는 무엇을 의미하는가?", "meaning of kurtosis in bearing vibration"],
] as const;

test("translates the five validated Korean bearing questions deterministically", () => {
  for (const [original, expected] of CASES) {
    const result = translateKnowledgeQuery(original);
    assert.equal(result.original_query, original);
    assert.equal(result.search_query, expected);
    assert.equal(result.method, "RULE_DICTIONARY");
    assert.equal(result.translated, true);
    assert.equal(result.complete, true);
  }
});

test("leaves an English query unchanged", () => {
  const query = "bearing outer race damage vibration characteristics";
  const result = translateKnowledgeQuery(query);
  assert.equal(result.search_query, query);
  assert.equal(result.method, "DIRECT");
  assert.equal(result.translated, false);
  assert.equal(result.complete, true);
});

test("conservatively translates known terms in a mixed-language query", () => {
  const result = translateKnowledgeQuery("SKF 베어링 외륜 vibration");
  assert.equal(result.search_query, "SKF bearing outer race vibration");
  assert.equal(result.language, "mixed");
  assert.equal(result.complete, true);
});

test("preserves unknown Korean instead of inventing a translation", () => {
  const result = translateKnowledgeQuery("베어링 미지현상 원인");
  assert.equal(result.search_query, "bearing 미지현상 causes");
  assert.equal(result.method, "SAFE_FALLBACK");
  assert.equal(result.complete, false);
  assert.deepEqual(result.unmappedKorean, ["미지현상"]);
});

test("returns an explicit empty result for a blank query", () => {
  const result = translateKnowledgeQuery("   ");
  assert.equal(result.search_query, "");
  assert.equal(result.method, "EMPTY");
  assert.equal(result.complete, false);
});
