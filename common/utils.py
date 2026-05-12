from unidecode import unidecode


def slugify(value):
    return unidecode(value).lower().replace(' ', '-')
