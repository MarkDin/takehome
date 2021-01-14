import re

SNAKE_PATTERN_RE = re.compile('_([a-zA-Z0-9])')
CAMEL_TO_SNAKE_FIRST_RE = re.compile('(.)([A-Z][a-z]+)')
CAMEL_TO_SNAKE_RE = re.compile('([a-z0-9])([A-Z])')


def snake_to_camel(key):
    return SNAKE_PATTERN_RE.sub(lambda m: m.group(1).upper(), key)


def camel_to_snake(key):
    tmp = CAMEL_TO_SNAKE_FIRST_RE.sub(r'\1_\2', key)
    return CAMEL_TO_SNAKE_RE.sub(r'\1_\2', tmp).lower()
