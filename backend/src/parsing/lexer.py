"""Tokenization utilities for the project pseudocode language."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterable, Iterator, List, Sequence


class TokenKind(Enum):
    """Kinds of lexical tokens supported by the parser."""

    IDENTIFIER = auto()
    NUMBER = auto()
    KEYWORD = auto()
    SYMBOL = auto()
    STRING = auto()
    COMMENT = auto()
    WHITESPACE = auto()
    EOF = auto()


RESERVED_WORDS: Sequence[str] = (
    "algoritmo",
    "procedimiento",
    "begin",
    "end",
    "for",
    "to",
    "while",
    "repeat",
    "until",
    "if",
    "then",
    "else",
    "do",
    "and",
    "or",
    "not",
    "call",
    "length",
    "null",
    "class",
    "mod",
    "div",
    "return",
    "print",
    "t",
    "f",
    "new",
    "array",
)


@dataclass(frozen=True)
class Token:
    """Lightweight token representation."""

    kind: TokenKind
    lexeme: str
    line: int
    column: int

    def __repr__(self) -> str:
        return f"Token({self.kind.name}, {self.lexeme!r}, {self.line}:{self.column})"


class LexerError(RuntimeError):
    """Raised when the lexer finds an unexpected character."""


class Lexer:
    """Streaming lexer that yields tokens one by one.

    The implementation is deliberately simple at this stage. It prioritizes
    readability and testability over raw performance. The class can be
    extended with additional token kinds as new grammar features appear.
    """

    def __init__(self, source: str) -> None:
        self._source = source
        self._length = len(source)

    def tokenize(self) -> List[Token]:
        """Tokenize the entire input eagerly."""
        return list(self.iter_tokens())

    def iter_tokens(self) -> Iterator[Token]:
        """Yield tokens lazily until EOF."""
        line = 1
        column = 1
        idx = 0
        while idx < self._length:
            current = self._source[idx]
            if current in " \t\r":
                idx, column = self._consume_whitespace(idx, column)
                continue
            if current == "∞":
                yield Token(TokenKind.IDENTIFIER, "infinito", line, column)
                idx += 1
                column += 1
                continue
            if current == "\n":
                line += 1
                column = 1
                idx += 1
                continue
            if current == "►":
                idx, line, column = self._consume_comment(idx, line, column)
                continue
            if current == ".":
                next_char = self._peek(idx + 1)
                if next_char == ".":
                    yield Token(TokenKind.SYMBOL, "..", line, column)
                    idx += 2
                    column += 2
                    continue
            if current.isalpha():
                token, idx, column = self._consume_identifier(idx, line, column)
                yield token
                continue
            if current.isdigit():
                token, idx, column = self._consume_number(idx, line, column)
                yield token
                continue
            if current == '"':
                token, idx, column, line = self._consume_string(idx, line, column)
                yield token
                continue
            multi_symbol = self._consume_multi_symbol(idx)
            if multi_symbol:
                lexeme, advance = multi_symbol
                token = Token(TokenKind.SYMBOL, lexeme, line, column)
                yield token
                idx += advance
                column += advance
                continue
            token = Token(TokenKind.SYMBOL, current, line, column)
            yield token
            idx += 1
            column += 1

        yield Token(TokenKind.EOF, "", line, column)

    def _consume_whitespace(self, idx: int, column: int) -> tuple[int, int]:
        while idx < self._length and self._source[idx] in " \t":
            idx += 1
            column += 1
        return idx, column

    def _consume_identifier(self, idx: int, line: int, column: int) -> tuple[Token, int, int]:
        start = idx
        while idx < self._length and (self._source[idx].isalnum() or self._source[idx] == "_"):
            idx += 1
        lexeme = self._source[start:idx].lower()
        kind = TokenKind.KEYWORD if lexeme in RESERVED_WORDS else TokenKind.IDENTIFIER
        token = Token(kind, lexeme, line, column)
        column += idx - start
        return token, idx, column

    def _consume_number(self, idx: int, line: int, column: int) -> tuple[Token, int, int]:
        start = idx
        while idx < self._length and self._source[idx].isdigit():
            idx += 1
        lexeme = self._source[start:idx]
        token = Token(TokenKind.NUMBER, lexeme, line, column)
        column += idx - start
        return token, idx, column

    def _consume_string(self, idx: int, line: int, column: int) -> tuple[Token, int, int, int]:
        start_column = column
        idx += 1
        column += 1
        start = idx
        while idx < self._length and self._source[idx] != '"':
            if self._source[idx] == "\n":
                line += 1
                column = 1
            else:
                column += 1
            idx += 1
        if idx >= self._length:
            raise LexerError(f"Unterminated string literal at line {line}")
        lexeme = self._source[start:idx]
        idx += 1
        column += 1
        token = Token(TokenKind.STRING, lexeme, line, start_column)
        return token, idx, column, line

    def _consume_comment(self, idx: int, line: int, column: int) -> tuple[int, int, int]:
        while idx < self._length and self._source[idx] != "\n":
            idx += 1
            column += 1
        return idx, line, column

    def _consume_multi_symbol(self, idx: int) -> tuple[str, int] | None:
        current = self._source[idx]
        next_char = self._peek(idx + 1)
        lexeme = None
        if current == "<" and next_char == "=":
            lexeme = "<="
        elif current == ">" and next_char == "=":
            lexeme = ">="
        elif current == "<" and next_char == ">":
            lexeme = "<>"
        elif current == ":" and next_char == "=":
            lexeme = ":="
        elif current == "≤":
            lexeme = "≤"  # Mantener el símbolo original
            next_char = ""
        elif current == "≥":
            lexeme = "≥"  # Mantener el símbolo original
            next_char = ""
        elif current == "≠":
            lexeme = "<>"
            next_char = ""
        elif current == "🡨":
            lexeme = "🡨"
            next_char = ""
        elif current == "↨":
            lexeme = "🡨"  # Normalizar ↨ a 🡨
            next_char = ""
        elif current == "(":
            lexeme = "("
            next_char = ""
        elif current == ")":
            lexeme = ")"
            next_char = ""
        if lexeme is not None:
            advance = 2 if len(lexeme) == 2 and current in {"<", ">", ":"} else 1
            return lexeme, advance
        return None

    def _peek(self, idx: int) -> str:
        if idx < self._length:
            return self._source[idx]
        return ""


def lex(source: str) -> Iterable[Token]:
    """Convenience helper for quick prototyping."""
    return Lexer(source).iter_tokens()
