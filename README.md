# AI 회의록 요약 & 할 일 추출

회의록 텍스트를 넣으면 AI가 핵심 요약, 주요 결정 사항, 할 일(담당자 / 할 일 / 마감일)을 정리해 주는 Streamlit 웹 앱입니다. 자세한 요구사항은 [PRD.md](PRD.md)를 참고하세요.

> 현재 3단계(UI 디자인)까지 구현되어 있습니다.

## 주요 기능

- `.txt` 업로드 또는 텍스트 붙여넣기로 회의록 입력
- 핵심 요약(3~5줄), 주요 결정 사항, 할 일 표(담당자 / 할 일 / 마감일, 정보 없으면 "미정")
- 분석 결과에 대한 추가 질문 채팅 (원본 회의록 근거로 답변)
- Markdown(전체 결과), CSV(할 일 표) 다운로드
- 파스텔 톤 화면, 오른쪽 위 버튼으로 라이트 / 다크 모드 전환

## 설치

Python 3.10 이상이 필요합니다.

```bash
pip install -r requirements.txt
```

## 환경 변수 설정

`.env.example`을 복사해 `.env`를 만들고 OpenAI API 키를 입력합니다.

```bash
cp .env.example .env
```

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-6.1-sol
```

- `.env`는 Git에 올리지 않습니다 (`.gitignore`에 포함).
- Streamlit Community Cloud에 배포할 때는 **App settings → Secrets**에 같은 키를 입력합니다. 설정은 Secrets → `.env`/환경 변수 순서로 읽습니다.

## 실행

```bash
streamlit run app.py
```

브라우저에서 http://localhost:8501 이 열립니다. 8501 포트를 다른 앱이 쓰고 있으면 `--server.port 8599`처럼 다른 포트를 지정하세요.

## 테스트

API 키 없이 실행됩니다 (OpenAI 클라이언트를 가짜 객체로 대체).

```bash
pytest
```

## 사용 방법

1. **파일 업로드** 탭에서 `.txt` 회의록을 올리거나, **텍스트 붙여넣기** 탭에 내용을 붙여넣습니다.
   - 사이드바에서 샘플 회의록을 골라 **불러오기**를 누르면 붙여넣기 탭에 채워집니다.
2. **분석하기** 버튼을 누릅니다.

### 입력 규칙

- **파일과 붙여넣은 텍스트가 둘 다 있으면 업로드한 파일을 사용합니다.** 화면 아래에 현재 분석 대상이 표시됩니다.
- 샘플을 불러오면 업로드한 파일은 자동으로 해제되어 샘플이 분석 대상이 됩니다.
- `.txt` 파일은 UTF-8로 먼저 읽고, 실패하면 CP949(EUC-KR)로 읽습니다.
- 회의록은 50자 이상, 30,000자 이하여야 합니다.

## 샘플 회의록

| 파일 | 내용 |
|---|---|
| `samples/sample1_product_planning.txt` | IT 스타트업 신규 기능 기획 회의 (명확한 결정·마감일) |
| `samples/sample2_marketing_weekly.txt` | 마케팅팀 주간 회의 (상대적 날짜 표현, 담당자 미정 항목) |
| `samples/sample3_club_event.txt` | 대학 동아리 전시회 준비 회의 (구어체, 보류된 안건) |
