import unicodedata


def remove_vietnamese_accents(text: str) -> str:
    if not text:
        return ''

    nfd = unicodedata.normalize('NFD', text)
    ascii_text = ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')
    return ascii_text.replace('đ', 'd').replace('Đ', 'D')
