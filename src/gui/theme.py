_dark: bool = False


def configure(dark: bool) -> None:
    global _dark
    _dark = dark


def is_dark() -> bool:
    return _dark


def bg() -> str:
    return "#1A1A18" if _dark else "#F9F8F6"


def surface() -> str:
    return "#222220" if _dark else "#F0EFE9"


def border() -> str:
    return "#333331" if _dark else "#E4E3DF"


def text() -> str:
    return "#E8E7E4" if _dark else "#1A1A18"


def muted() -> str:
    return "#8A8A86" if _dark else "#6B6B66"


def content_bg() -> str:
    return "#252523" if _dark else "#FFFFFF"
