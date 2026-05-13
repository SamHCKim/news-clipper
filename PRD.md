# PRD: Keyword-based News Aggregator (News Clipper)

> Deep Interview 결과로 생성된 제품 요구사항 문서. M&A 뉴스 일일 트래킹 워크플로의 [수집→정리] 단계 자동화가 주 유즈케이스.

## Metadata
- Final Ambiguity Score: 19% (threshold 20%, PASSED)
- Project Type: Greenfield
- Rounds: 3

## Clarity Breakdown
| Dimension | Score | Weight | Weighted |
|-----------|-------|--------|----------|
| Goal Clarity | 0.90 | 0.40 | 0.36 |
| Constraint Clarity | 0.70 | 0.30 | 0.21 |
| Success Criteria | 0.80 | 0.30 | 0.24 |
| **Total Clarity** | | | **0.81** |
| **Ambiguity** | | | **0.19** |

## Goal
키워드 기반(Google 검색 연산자 — AND/OR/따옴표/괄호 지원)으로 한국·해외 뉴스를 수집하고, 기간(지난 N일) 필터를 적용해 헤드라인+링크 등을 스프레드시트(.xlsx 기본, Google Sheets 옵션)로 저장하는 Python CLI 도구. 주 유즈케이스는 매일 M&A 관련 뉴스를 트래킹해 수동으로 엑셀에 정리하던 워크플로의 [수집 → 정리] 단계를 자동화하는 것.

## Constraints
- 언어/런타임: Python CLI (가장 단순한 MVP 경로)
- 데이터 소스 (MVP): Google News RSS만 사용. 추가 RSS 결합은 Phase 2로 보류. 결과는 URL/제목 기반 중복 제거
- 커버리지: 한국어 + 해외(영어) 뉴스 모두
- 출력: 기본 로컬 `.xlsx`, 옵션으로 Google Sheets(사용자가 자신의 서비스 계정 JSON/OAuth 자격증명 제공)
- 배포: GitHub repo로 공유 가능한 형태 — README에 설치/실행/Google API 인증 가이드 포함
- 개인용, 별도 서버/호스팅 없음
- 인증 키/시크릿은 절대 repo에 포함하지 않음(`.env` 또는 사용자 로컬 경로)

## Non-Goals (MVP 제외)
- 웹 UI / 대시보드
- 스케줄러 내장(cron/Task Scheduler는 사용자가 알아서 호출)
- LLM 기반 자동 주제 적합성 판정 — 사용자가 엑셀에서 수동 검토
- 알림(이메일/슬랙)
- 다중 사용자 / 인증 시스템
- 본문 크롤링/요약 (헤드라인+링크+메타데이터 수준까지만)

## Acceptance Criteria
- [ ] CLI에서 `python news.py --query "M&A OR 인수 OR 합병" --days 1`과 같이 실행 가능
- [ ] Google 검색 연산자(AND, OR, 따옴표 구문, 괄호 그룹) 그대로 통과
- [ ] `--days N` 옵션으로 지난 N일 필터 (1, 7, 30 등 임의값)
- [ ] `--trusted-sources <file|domain-list>` 옵션으로 신뢰 언론사 화이트리스트 필터 (옵션, 미지정 시 전체 결과)
- [ ] 여러 RSS 소스 결합 후 URL/제목 기반 중복 제거
- [ ] 기본 출력: `.xlsx` 파일 (컬럼 순서: 매칭 키워드, 제목, 링크, 언론사, 발행일시)
- [ ] 기사 언어 보존: 한국어 기사는 한국어 그대로, 영어 기사는 영어 그대로 (번역 없음)
- [ ] `--output gsheet --sheet-id <id>` 옵션 사용 시 Google Sheets에 append (사용자 자격증명 사용)
- [ ] 한국어/영어 뉴스 모두 정상 수집·저장
- [ ] README에 설치, 실행 예시(M&A 케이스), Google Sheets 인증 설정 가이드 포함
- [ ] `.env`/자격증명 파일은 `.gitignore`에 포함, repo에 절대 커밋되지 않음
- [ ] M&A 유즈케이스 실제 실행 시 의미 있는 헤드라인 N건 이상 수집 (smoke test)

## Assumptions Exposed & Resolved
| Assumption | Challenge | Resolution |
|------------|-----------|------------|
| Google News를 직접 검색 | 공식 API 없음 — RSS로 우회 가능한가? | Google News RSS 사용 (검색 연산자 그대로 통과, when:Nd로 기간 필터) |
| 단일 소스로 충분 | 커버리지 부족 위험 | 다중 RSS 결합 + 중복 제거로 결정 |
| Google Sheets는 복잡 | 사용자가 자신의 자격증명 제공하면 GitHub 공유 가능 | 양쪽 지원, 기본 xlsx, Sheets는 opt-in |
| 도구가 신뢰도/주제 판정 | MVP 스코프 폭증 + 결정권 사용자에게 | 화이트리스트만 도구가, 주제 적합성은 수동 |

## Technical Context (Greenfield)
- 권장 스택: Python 3.10+, `feedparser` (RSS), `openpyxl` (xlsx), `gspread`+`google-auth` (Google Sheets, 옵션), `python-dotenv`
- Google News RSS URL 패턴: `https://news.google.com/rss/search?q={query}+when:{N}d&hl=ko&gl=KR&ceid=KR:ko` (한국) + `hl=en-US&gl=US&ceid=US:en` (영어) — 두 로케일 병렬 호출. 각 로케일 결과는 원문 언어 그대로 저장(번역/변환 없음).
- 중복 제거 키: 정규화된 URL (쿼리스트링/트래킹 파라미터 제거) → 제목 정규화 fuzzy match는 phase 2

## Ontology (Key Entities)
| Entity | Type | Fields | Relationships |
|--------|------|--------|---------------|
| NewsItem | core domain | title, link, source, published_at, matched_keywords | belongs to one fetch run |
| KeywordQuery | core domain | raw_string (Google syntax) | applied to many Sources |
| DateRange | supporting | days (int) | filter on fetch |
| SourceFilter | supporting | whitelist_domains[] | optional filter on NewsItem |
| OutputTarget | supporting | type (xlsx/gsheet), path_or_id | receives NewsItem[] |

## Ontology Convergence
| Round | Entity Count | New | Changed | Stable | Stability Ratio |
|-------|-------------|-----|---------|--------|----------------|
| 1 | 4 | 4 | - | - | N/A |
| 2 | 5 | 1 (OutputTarget) | 0 | 4 | 80% |
| 3 | 5 | 0 | 0 | 5 | 100% ✅ |

## Interview Transcript
<details>
<summary>Full Q&A (3 rounds)</summary>

### Round 1 — Goal Clarity (data source)
**Q:** 뉴스 데이터를 어디에서 가져올지?
**A:** 여러 소스 결합해서 커버리지 최대화 + 중복 제거, 해외 뉴스 커버, Google RSS 충분할 듯 + 추가 RSS 있으면 알아서.
**Ambiguity:** 57%

### Round 2 — Constraints (runtime + output)
**Q:** 실행 방식과 결과 저장 위치?
**A:** Google Sheets가 API 인증만 유저에게 맡기면 GitHub repo로 배포 가능한 경우 그렇게, 아니면 로컬 xlsx.
**Resolution:** 양쪽 지원, 기본 xlsx, Sheets는 사용자 자격증명 제공 시 opt-in.
**Ambiguity:** 34%

### Round 3 — Success Criteria (filtering scope)
**Q:** 신뢰 언론사 / M&A 주제 적합성 필터링은 어디까지 자동화?
**A:** Default는 전부 모아서 던져주되, filter처럼 신뢰 언론사 설정 옵션 추가.
**Ambiguity:** 19% ✅
</details>
