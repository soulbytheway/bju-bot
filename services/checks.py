MAX_TEXT_LENGTH = 300
def is_valid_text_input(text: str | None) -> bool:
    if text is None:
        return False
    return len(text.strip()) > 0

def clean_and_truncate(text: str, max_length: int = MAX_TEXT_LENGTH) -> str:
    return text.strip()[:max_length]