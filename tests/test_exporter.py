import csv
import io
from datetime import datetime

from core import exporter
from core.llm import normalize
from tests.fakes import SAMPLE_ANALYSIS

ANALYSIS = normalize(SAMPLE_ANALYSIS)
WHEN = datetime(2026, 11, 17, 14, 30)


def test_to_markdown_has_all_sections():
    md = exporter.to_markdown(ANALYSIS, WHEN)
    assert "생성 일시: 2026-11-17 14:30" in md
    for heading in ("## 1. 회의 핵심 요약", "## 2. 주요 결정 사항", "## 3. 할 일 (Action Items)"):
        assert heading in md
    assert "| 담당자 | 할 일 | 마감일 |" in md
    assert "| 정하늘 | QA 테스트 케이스 작성 | 미정 |" in md


def test_to_markdown_escapes_pipes_and_newlines():
    md = exporter.to_markdown({"action_items": [{"owner": "A|B", "task": "줄\n바꿈", "due_date": "미정"}]}, WHEN)
    assert "| A\\|B | 줄 바꿈 | 미정 |" in md


def test_to_markdown_empty_sections():
    md = exporter.to_markdown({"summary": [], "decisions": [], "action_items": []}, WHEN)
    assert exporter.NO_DECISIONS in md and exporter.NO_ACTION_ITEMS in md


def test_to_csv_has_bom_three_columns_and_korean():
    data = exporter.to_csv(ANALYSIS)
    assert data.startswith(b"\xef\xbb\xbf")
    rows = list(csv.reader(io.StringIO(data.decode("utf-8-sig"))))
    assert rows[0] == ["담당자", "할 일", "마감일"]
    assert len(rows) == 1 + len(ANALYSIS["action_items"])
    assert all(len(r) == 3 for r in rows)
    assert rows[3] == ["미정", "공유용 이미지 생성 방식 조사", "미정"]


def test_to_csv_quotes_commas():
    rows = list(csv.reader(io.StringIO(exporter.to_csv({"action_items": [{"owner": "김", "task": "A, B 정리", "due_date": "미정"}]}).decode("utf-8-sig"))))
    assert rows[1] == ["김", "A, B 정리", "미정"]


def test_to_csv_neutralizes_formula_cells():
    """회의록에서 온 '=...' 같은 값이 Excel에서 수식으로 실행되지 않아야 한다."""
    data = exporter.to_csv(
        {"action_items": [{"owner": "=1+1", "task": '=HYPERLINK("http://x","클릭")', "due_date": "@SUM(A1)"},
                          {"owner": "김민수", "task": "-10% 할인 검토", "due_date": "2026-11-20"}]}
    )
    rows = list(csv.reader(io.StringIO(data.decode("utf-8-sig"))))
    assert rows[1] == ["'=1+1", "'=HYPERLINK(\"http://x\",\"클릭\")", "'@SUM(A1)"]
    assert rows[2] == ["김민수", "'-10% 할인 검토", "2026-11-20"]


def test_to_csv_empty_has_header_only():
    assert exporter.to_csv({"action_items": []}).decode("utf-8-sig").strip() == "담당자,할 일,마감일"
