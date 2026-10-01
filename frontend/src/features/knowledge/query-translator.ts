export type KnowledgeQueryTranslation = {
  original_query: string;
  search_query: string;
  language: "empty" | "en" | "ko" | "mixed";
  method: "EMPTY" | "DIRECT" | "RULE_DICTIONARY" | "SAFE_FALLBACK";
  translated: boolean;
  complete: boolean;
  unmappedKorean: string[];
};

const HANGUL = /[가-힣]/u;
const LATIN = /[A-Za-z]/u;

/**
 * Validated canonical queries for common bearing questions.
 * These rules translate only concepts present in the original question.
 */
const CANONICAL_QUERY_RULES: Readonly<Record<string, string>> = {
  "베어링 외륜 손상의 주요 진동 특징은": "bearing outer race damage vibration characteristics",
  "베어링 내륜 손상의 원인은 무엇인가": "causes of bearing inner race damage",
  "베어링 손상 시 점검해야 할 사항은": "bearing damage inspection procedure",
  "베어링 윤활 부족으로 발생하는 문제는": "bearing problems caused by inadequate lubrication",
  "베어링 진동에서 첨도는 무엇을 의미하는가": "meaning of kurtosis in bearing vibration",
};

/** Longest phrases must be replaced before their component words. */
export const BEARING_TERM_DICTIONARY: ReadonlyArray<readonly [string, string]> = [
  ["외륜 손상", "outer race damage"],
  ["내륜 손상", "inner race damage"],
  ["진동 특징", "vibration characteristics"],
  ["점검 절차", "inspection procedure"],
  ["윤활 부족", "inadequate lubrication"],
  ["베어링", "bearing"],
  ["외륜", "outer race"],
  ["내륜", "inner race"],
  ["손상", "damage"],
  ["진동", "vibration"],
  ["특징", "characteristics"],
  ["점검", "inspection"],
  ["윤활", "lubrication"],
  ["첨도", "kurtosis"],
  ["고장", "fault"],
  ["원인", "causes"],
];

function normalizedRuleKey(query: string) {
  return query
    .trim()
    .replace(/[?？!！.。]+$/gu, "")
    .replace(/\s+/gu, " ");
}

function uniqueKoreanFragments(query: string) {
  return [...new Set(query.match(/[가-힣]+/gu) ?? [])];
}

export function translateKnowledgeQuery(input: string): KnowledgeQueryTranslation {
  const originalQuery = input.trim().replace(/\s+/gu, " ");
  if (!originalQuery) {
    return {
      original_query: "",
      search_query: "",
      language: "empty",
      method: "EMPTY",
      translated: false,
      complete: false,
      unmappedKorean: [],
    };
  }

  const hasKorean = HANGUL.test(originalQuery);
  const hasLatin = LATIN.test(originalQuery);
  if (!hasKorean) {
    return {
      original_query: originalQuery,
      search_query: originalQuery,
      language: "en",
      method: "DIRECT",
      translated: false,
      complete: true,
      unmappedKorean: [],
    };
  }

  const language = hasLatin ? "mixed" : "ko";
  const canonical = CANONICAL_QUERY_RULES[normalizedRuleKey(originalQuery)];
  if (canonical) {
    return {
      original_query: originalQuery,
      search_query: canonical,
      language,
      method: "RULE_DICTIONARY",
      translated: true,
      complete: true,
      unmappedKorean: [],
    };
  }

  let searchQuery = originalQuery;
  for (const [korean, english] of BEARING_TERM_DICTIONARY) {
    searchQuery = searchQuery.replaceAll(korean, english);
  }
  searchQuery = searchQuery
    .replace(/[?？!！.。]+$/gu, "")
    .replace(/\s+/gu, " ")
    .trim();

  const unmappedKorean = uniqueKoreanFragments(searchQuery);
  const translated = searchQuery !== normalizedRuleKey(originalQuery);
  return {
    original_query: originalQuery,
    search_query: searchQuery,
    language,
    method: unmappedKorean.length ? "SAFE_FALLBACK" : "RULE_DICTIONARY",
    translated,
    complete: unmappedKorean.length === 0,
    unmappedKorean,
  };
}
