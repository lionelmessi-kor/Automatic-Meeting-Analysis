import pytest

from core.textfile import MSG_DECODE, MSG_NOT_TEXT, decode_text_file
from pathlib import Path

SAMPLES = sorted((Path(__file__).resolve().parent.parent / "samples").glob("*.txt"))
TEXT = "회의록 한글 테스트\n참석자: 김민수\t박지훈\r\n"


def test_reads_utf8_with_and_without_bom():
    assert decode_text_file(TEXT.encode("utf-8")) == TEXT
    assert decode_text_file(b"\xef\xbb\xbf" + TEXT.encode("utf-8")) == TEXT


def test_falls_back_to_cp949():
    assert decode_text_file(TEXT.encode("cp949")) == TEXT


def test_empty_file_is_text():
    assert decode_text_file(b"") == ""


@pytest.mark.parametrize("path", SAMPLES, ids=lambda p: p.name)
def test_samples_are_text_in_both_encodings(path):
    text = path.read_text(encoding="utf-8")
    assert decode_text_file(text.encode("utf-8")) == text
    assert decode_text_file(text.encode("cp949")) == text


@pytest.mark.parametrize(
    "data",
    [
        bytes.fromhex("89504e470d0a1a0a0000000d49484452") + b"\x00" * 32,  # PNG
        b"PK\x03\x04\x14\x00\x06\x00" + b"word/document.xml" * 4,  # .docx (ZIP)
        b"%PDF-1.7\n" + bytes(range(1, 32)) * 4,  # 제어 문자가 많은 바이너리
    ],
    ids=["png", "docx", "control-chars"],
)
def test_binary_files_are_rejected(data):
    with pytest.raises(ValueError) as info:
        decode_text_file(data)
    assert str(info.value) == MSG_NOT_TEXT


def test_utf16_file_is_rejected_not_garbled():
    """UTF-16은 NUL 바이트를 포함하므로 깨진 글자로 읽히지 않고 오류가 나야 한다."""
    with pytest.raises(ValueError):
        decode_text_file(TEXT.encode("utf-16"))


def test_undecodable_text_gives_decode_message():
    with pytest.raises(ValueError) as info:
        decode_text_file(b"\xff\xfe\xfd hello")
    assert str(info.value) in (MSG_DECODE, MSG_NOT_TEXT)
