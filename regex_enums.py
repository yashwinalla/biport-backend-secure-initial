from enum import Enum


class Regex(Enum):
    STRIP_SQUARE_BRACKETS = "[]$"
    SQUARE_BRACKETS = "[]"
    DOT = "."
    COLON = ":"
    TAB_REPLACE = "#tab"
    UNDER_SCORE = "_"
    EMPTY = ""
    COMMA = ","
    HYPHEN = "-"
    SEMI_COLON = ";"
    BETWEEN_SQUARE_BRACKETS = r'\[.*?\]'
    BETWEEN_SQUARE_BRACKETS_FOLLOWED_BY_DOT = r'\[.*?\]\.'
    COLUMNS_IN_WS = r'\[(?!federated\.)[^\]]+\]'
    LIST_IN_LIST_FOLLOWED = r'\[[^\]]+\]'
    STARTS_WITH_COLON_IN_LIST = r'^\[[^:]+:[^:]+:[^\]]+\]$'
