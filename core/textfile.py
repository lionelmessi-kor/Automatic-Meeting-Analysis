"""업로드한 회의록 파일을 텍스트로 읽는다."""

from __future__ import annotations

import unicodedata

MSG_NOT_TEXT = "텍스트 파일이 아닌 것 같아요. 회의록 내용이 담긴 .txt 파일을 올려 주세요."
MSG_DECODE = "파일을 읽을 수 없습니다. UTF-8 형식의 .txt 파일인지 확인해주세요."

# 일반 텍스트에도 들어 있을 수 있는 제어 문자 (줄바꿈, 탭, 페이지 나눔)
_ALLOWED_CONTROLS = {"\n", "\r", "\t", "\f"}
# 제어 문자가 이 비율을 넘으면 텍스트가 아니라고 본다
_MAX_CONTROL_RATIO = 0.01


def _looks_binary(text: str) -> bool:
    if not text:
        return False
    controls = sum(
        1 for ch in text if ch not in _ALLOWED_CONTROLS and unicodedata.category(ch) == "Cc"
    )
    return controls / len(text) > _MAX_CONTROL_RATIO


def decode_text_file(data: bytes) -> str:
    """UTF-8(BOM 포함)을 먼저 시도하고, 실패하면 CP949로 읽는다.

    확장자만 .txt인 바이너리 파일(이미지, 문서 파일 등)은 CP949로 억지로 읽혀 깨진 글자가 되므로,
    NUL 바이트가 있거나 제어 문자가 많으면 텍스트가 아니라고 보고 ValueError를 던진다.
    """
    if b"\x00" in data:
        raise ValueError(MSG_NOT_TEXT)
    for encoding in ("utf-8-sig", "cp949"):
        try:
            text = data.decode(encoding)
        except UnicodeDecodeError:
            continue
        if _looks_binary(text):
            raise ValueError(MSG_NOT_TEXT)
        return text
    raise ValueError(MSG_DECODE)
