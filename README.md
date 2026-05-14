# News Clipper

키워드 기반(Google 검색 연산자 지원) 뉴스 수집 → 스프레드시트 저장 도구.
Google News RSS로 한국어·영어 뉴스를 함께 가져오고, 기간 필터와 신뢰 언론사
화이트리스트를 적용한 뒤 `.xlsx` 또는 Google Sheets에 정리합니다.

두 가지 인터페이스를 제공합니다:
- 🌐 **Web UI (Streamlit)** — 최대 7개 쿼리 동시 검색, 결과 미리보기, xlsx 다운로드
- 💻 **CLI** — 단일 쿼리, 자동화/스케줄링에 적합

> 주 유즈케이스: 매일 `[M&A OR 인수 OR 합병]` 검색을 1일 범위로 돌려 의미 있는
> 헤드라인을 엑셀에 모으는 워크플로 자동화.

## 설치

```powershell
# Python 3.10+ 권장
pip install -r requirements.txt
```

## Web UI (권장)

```powershell
streamlit run app.py
```

브라우저(`http://localhost:8501`)에서:
- **검색어**: 한 줄에 1쿼리, 최대 7줄 (Google 검색 연산자 그대로 통과)
- **지난 N일**: 1~90일 범위
- **파일명**: 기본 `News Clipping_yymmdd.xlsx`, 수정 가능
- **신뢰 언론사**: 줄 단위 입력 (선택)
- **📖 Google 검색 연산자 가이드**: 입력 폼 안에서 접고 펴는 가이드
- **표시할 컬럼**: 결과 테이블 위 멀티셀렉트로 컬럼 토글

"🔍 검색" 클릭 → 결과 테이블에서 링크 클릭 가능 → "📥 다운로드"로 xlsx 저장.
출력 컬럼: `검색 쿼리 | 매칭 키워드 | 제목 | 링크 | 언론사 | 발행일시`.
중복 제거: URL 정규화 + 제목 유사도(≥0.85) 기준.

### 기본 검색어/언론사 사전 설정

`defaults/` 폴더의 두 파일을 직접 편집하면 앱 실행 시 입력창이 자동으로 채워집니다.

- `defaults/queries.txt` — 한 줄에 1쿼리, 최대 7줄
- `defaults/trusted.txt` — 한 줄에 언론사 이름 1개

파일이 없거나 비어 있으면 빈 입력창에 placeholder만 표시됩니다. fork
직후 깨끗한 출발점이 필요하면 같은 폴더의 `*.example` 파일을 참고하거나
`Copy-Item`으로 덮어쓰세요.

## CLI 사용법

기본 (로컬 .xlsx 출력):

```powershell
python news.py --query "M&A OR 인수 OR 합병" --days 1
```

신뢰 언론사 필터 적용:

```powershell
python news.py --query "M&A OR 인수 OR 합병" --days 1 `
  --trusted-sources trusted_sources.txt
```

직접 도메인/이름 리스트 전달:

```powershell
python news.py --query "M&A OR 인수" --days 7 `
  --trusted-sources "한국경제,매일경제,Reuters,Bloomberg"
```

출력 파일명 지정:

```powershell
python news.py --query '"acquisition" OR "merger"' --days 1 `
  --out-path mna_$(Get-Date -Format yyyyMMdd).xlsx
```

## 검색 문법

Google 검색 연산자가 그대로 통과됩니다.

- `사과 OR 바나나 OR 레몬` — 셋 중 하나라도
- `"인공지능 반도체"` — 정확한 구문
- `(M&A OR 합병) "삼성"` — 그룹 + AND(공백)
- `테슬라 -주식` — 제외
- `site:reuters.com merger` — 특정 도메인만

## 출력 컬럼

Web UI (멀티 쿼리, `app.py`):

| 검색 쿼리 | 매칭 키워드 | 제목 | 링크 | 언론사 | 발행일시 |
|----------|------------|------|------|--------|----------|
| `M&A OR 인수` | `M&A, 인수` | "..." | https://... | 한국경제 | Mon, 12 May 2025 ... |

CLI (단일 쿼리, `news.py`) — "검색 쿼리" 컬럼 없이 5개 컬럼.

기사 언어는 보존됩니다(한국어 기사는 한국어, 영어 기사는 영어).

## Google Sheets로 출력 (옵션)

1. [Google Cloud Console](https://console.cloud.google.com/)에서 프로젝트 생성
2. **Google Sheets API** 활성화
3. **서비스 계정** 생성 → JSON 키 다운로드
4. 대상 Sheet를 서비스 계정 이메일과 공유(편집 권한)
5. `.env.example`을 `.env`로 복사하고 JSON 경로 입력:
   ```
   GOOGLE_APPLICATION_CREDENTIALS=C:/path/to/service-account.json
   ```
6. 실행:
   ```powershell
   python news.py --query "M&A OR 인수 OR 합병" --days 1 `
     --output gsheet --sheet-id <YOUR_SHEET_ID>
   ```

Sheet ID는 URL에서 추출: `https://docs.google.com/spreadsheets/d/<SHEET_ID>/edit`

## 자동 실행 (선택)

Windows Task Scheduler 예시 — 매일 오전 8시:

```powershell
schtasks /Create /SC DAILY /TN "NewsClipperMnA" /ST 08:00 `
  /TR "python C:\path\to\news.py --query \"M&A OR 인수 OR 합병\" --days 1 --trusted-sources C:\path\to\trusted_sources.txt"
```

## 보안

- `.env`, 서비스 계정 JSON, `trusted_sources.txt`(CLI 화이트리스트), `*.xlsx`는 `.gitignore`로 제외됨
- 자격증명을 절대 repo에 커밋하지 말 것
- `defaults/queries.txt`, `defaults/trusted.txt`는 기본적으로 commit됩니다.
  본인 설정을 비공개로 두려면 두 파일을 `.gitignore`에 추가하세요.

## 로드맵 (Phase 2+)

- 추가 RSS 소스 결합 (네이버, 다음, 산업별 전문지)
- LLM 기반 주제 적합성 스코어링
- 발행일시 ISO 파싱 및 정렬
