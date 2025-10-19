"""Recursive descent parser for the pseudocode language.

The goal of this first version is to establish a testable skeleton. The grammar
implementation will be expanded iteratively alongside the test suite.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from . import ast_nodes
from .lexer import Lexer, Token, TokenKind


@dataclass(slots=True)
class ParserConfig:
    """Configuration flags for the parser."""

    enable_strict_mode: bool = False


class ParserError(RuntimeError):
    """Raised when the parser cannot match the incoming tokens."""


class Parser:
    """Consumes tokens and produces an AST."""

    def __init__(self, source: str, config: ParserConfig | None = None) -> None:
        self._tokens: List[Token] = Lexer(source).tokenize()
        self._index: int = 0
        self._previous: Token | None = None
        self._config = config or ParserConfig()

    def parse(self) -> ast_nodes.Program:
        """Parse the entire input and return a Program node."""
        class_definitions: List[ast_nodes.ClassDefinition] = []
        declarations: List[ast_nodes.Declaration] = []
        procedures: List[ast_nodes.Procedure] = []

        while self._match_keyword("class"):
            class_definitions.append(self._parse_class_definition(self._previous_token()))

        self._expect_keyword("begin", "Se esperaba 'begin' al iniciar el programa")
        body = self._parse_statement_block(end_keywords=("end",))
        end_token = self._expect_keyword("end", "Se esperaba 'end' para cerrar el programa")
        self._expect(TokenKind.EOF, "Se esperaban más sentencias? Revisa la estructura general")

        return ast_nodes.Program(
            line=1,
            column=1,
            class_definitions=class_definitions,
            declarations=declarations,
            procedures=procedures,
            body=body,
        )

    def _current(self) -> Token:
        if self._index >= len(self._tokens):
            return self._tokens[-1]
        return self._tokens[self._index]

    def _advance(self) -> Token:
        token = self._current()
        if self._index < len(self._tokens) - 1:
            self._index += 1
        self._previous = token
        return token

    def _expect(self, kind: TokenKind, message: str) -> Token:
        token = self._current()
        if token.kind != kind:
            raise ParserError(f"{message} at {token.line}:{token.column}")
        self._advance()
        return token

    def _previous_token(self) -> Token:
        if self._previous is None:
            raise ParserError("No hay token previo disponible.")
        return self._previous

    # ----------------------------------------------------------------------
    # Top level parsing helpers
    # ----------------------------------------------------------------------

    def _parse_class_definition(self, keyword: Token) -> ast_nodes.ClassDefinition:
        name_token = self._expect_identifier("Se esperaba el nombre de la clase")
        self._expect_symbol("{", "Se esperaba '{' en la definición de clase")
        attributes: List[str] = []
        while not self._check_symbol("}"):
            attr_token = self._expect_identifier("Se esperaba nombre de atributo en la clase")
            attributes.append(attr_token.lexeme)
        self._expect_symbol("}", "Falta '}' para cerrar la definición de clase")
        return ast_nodes.ClassDefinition(line=keyword.line, column=keyword.column, name=name_token.lexeme, attributes=attributes)

    def _parse_statement_block(self, end_keywords: Sequence[str]) -> List[ast_nodes.Statement]:
        statements: List[ast_nodes.Statement] = []
        while not self._check_keywords(end_keywords) and not self._check(TokenKind.EOF):
            statements.append(self._parse_statement())
        return statements

    def _parse_statement(self) -> ast_nodes.Statement:
        token = self._current()
        if token.kind == TokenKind.KEYWORD:
            dispatch = {
                "for": self._parse_for_loop,
                "while": self._parse_while_loop,
                "repeat": self._parse_repeat_until_loop,
                "if": self._parse_if_statement,
                "call": self._parse_call_statement,
                "return": self._parse_return_statement,
            }
            handler = dispatch.get(token.lexeme)
            if handler:
                return handler()
        if token.kind in (TokenKind.IDENTIFIER,):
            return self._parse_assignment()
        raise ParserError(f"No se reconoce la sentencia iniciada en {token.line}:{token.column}")

    # ----------------------------------------------------------------------
    # Statement parsing
    # ----------------------------------------------------------------------

    def _parse_for_loop(self) -> ast_nodes.ForLoop:
        keyword = self._consume_keyword("for")
        iterator_token = self._expect_identifier("Se esperaba el identificador de control del for")
        self._expect_symbol("🡨", "Falta el símbolo de asignación '🡨' en el for")
        start_expr = self._parse_expression()
        self._expect_keyword("to", "Se esperaba 'to' en el for")
        stop_expr = self._parse_expression()
        self._expect_keyword("do", "Se esperaba 'do' en el for")
        body = self._parse_mandatory_block()
        return ast_nodes.ForLoop(
            line=keyword.line,
            column=keyword.column,
            iterator=iterator_token.lexeme,
            start=start_expr,
            stop=stop_expr,
            body=body,
        )

    def _parse_while_loop(self) -> ast_nodes.WhileLoop:
        keyword = self._consume_keyword("while")
        self._expect_symbol("(", "Falta '(' en la condición del while")
        condition = self._parse_expression()
        self._expect_symbol(")", "Falta ')' en la condición del while")
        self._expect_keyword("do", "Se esperaba 'do' en el while")
        body = self._parse_mandatory_block()
        return ast_nodes.WhileLoop(line=keyword.line, column=keyword.column, condition=condition, body=body)

    def _parse_repeat_until_loop(self) -> ast_nodes.RepeatUntilLoop:
        keyword = self._consume_keyword("repeat")
        body = self._parse_statement_block(end_keywords=("until",))
        self._expect_keyword("until", "Falta 'until' al cerrar el repeat")
        self._expect_symbol("(", "Falta '(' en la condición del until")
        condition = self._parse_expression()
        self._expect_symbol(")", "Falta ')' en la condición del until")
        return ast_nodes.RepeatUntilLoop(line=keyword.line, column=keyword.column, body=body, condition=condition)

    def _parse_if_statement(self) -> ast_nodes.IfStatement:
        keyword = self._consume_keyword("if")
        self._expect_symbol("(", "Falta '(' en la condición del if")
        condition = self._parse_expression()
        self._expect_symbol(")", "Falta ')' en la condición del if")
        self._expect_keyword("then", "Se esperaba 'then'")
        then_branch = self._parse_mandatory_block()
        else_branch: List[ast_nodes.Statement] = []
        if self._match_keyword("else"):
            else_branch = self._parse_mandatory_block()
        return ast_nodes.IfStatement(
            line=keyword.line,
            column=keyword.column,
            condition=condition,
            then_branch=then_branch,
            else_branch=else_branch,
        )

    def _parse_call_statement(self) -> ast_nodes.CallStatement:
        keyword = self._consume_keyword("call")
        name_token = self._expect_identifier("Se esperaba el nombre de la subrutina en CALL")
        self._expect_symbol("(", "Falta '(' en la llamada a subrutina")
        arguments: List[ast_nodes.Expression] = []
        if not self._check_symbol(")"):
            arguments.append(self._parse_expression())
            while self._match_symbol(","):
                arguments.append(self._parse_expression())
        self._expect_symbol(")", "Falta ')' al cerrar CALL")
        return ast_nodes.CallStatement(line=keyword.line, column=keyword.column, name=name_token.lexeme, arguments=arguments)

    def _parse_return_statement(self) -> ast_nodes.ReturnStatement:
        keyword = self._consume_keyword("return")
        value: ast_nodes.Expression | None = None
        if not self._check_keyword(("end", "else")) and not self._check(TokenKind.EOF):
            value = self._parse_expression()
        return ast_nodes.ReturnStatement(line=keyword.line, column=keyword.column, value=value)

    def _parse_assignment(self) -> ast_nodes.Assignment:
        target = self._parse_lvalue()
        assign_token = self._expect_symbol("🡨", "Falta el símbolo '🡨' en la asignación")
        value = self._parse_expression()
        return ast_nodes.Assignment(line=assign_token.line, column=assign_token.column, target=target, value=value)

    def _parse_lvalue(self) -> ast_nodes.Expression:
        token = self._expect_identifier("Se esperaba identificador en la asignación")
        expr: ast_nodes.Expression = ast_nodes.Identifier(line=token.line, column=token.column, name=token.lexeme)
        while True:
            if self._match_symbol("["):
                index_expr = self._parse_expression()
                self._expect_symbol("]", "Falta ']' al cerrar acceso a arreglo")
                expr = ast_nodes.ArrayAccess(line=expr.line, column=expr.column, base=expr, index=index_expr)
            elif self._match_symbol("."):
                field_token = self._expect_identifier("Se esperaba nombre de campo después de '.'")
                expr = ast_nodes.FieldAccess(line=expr.line, column=expr.column, base=expr, field_name=field_token.lexeme)
            else:
                break
        return expr

    def _parse_mandatory_block(self) -> List[ast_nodes.Statement]:
        self._expect_keyword("begin", "Se esperaba 'begin' al iniciar bloque")
        statements = self._parse_statement_block(end_keywords=("end",))
        self._expect_keyword("end", "Falta 'end' al cerrar bloque")
        return statements

    # ----------------------------------------------------------------------
    # Expression parsing using precedence climbing
    # ----------------------------------------------------------------------

    def _parse_expression(self) -> ast_nodes.Expression:
        return self._parse_or()

    def _parse_or(self) -> ast_nodes.Expression:
        expr = self._parse_and()
        while self._match_keyword("or"):
            operator = self._previous_token()
            rhs = self._parse_and()
            expr = ast_nodes.BinaryOperation(operator=operator.lexeme, left=expr, right=rhs, line=operator.line, column=operator.column)
        return expr

    def _parse_and(self) -> ast_nodes.Expression:
        expr = self._parse_equality()
        while self._match_keyword("and"):
            operator = self._previous_token()
            rhs = self._parse_equality()
            expr = ast_nodes.BinaryOperation(operator=operator.lexeme, left=expr, right=rhs, line=operator.line, column=operator.column)
        return expr

    def _parse_equality(self) -> ast_nodes.Expression:
        expr = self._parse_comparison()
        while True:
            if self._match_symbol("=") or self._match_symbol("<>"):
                operator = self._previous_token()
                rhs = self._parse_comparison()
                expr = ast_nodes.BinaryOperation(operator=operator.lexeme, left=expr, right=rhs, line=operator.line, column=operator.column)
            else:
                break
        return expr

    def _parse_comparison(self) -> ast_nodes.Expression:
        expr = self._parse_term()
        while True:
            if self._match_symbol("<") or self._match_symbol(">") or self._match_symbol("<=") or self._match_symbol(">="):
                operator = self._previous_token()
                rhs = self._parse_term()
                expr = ast_nodes.BinaryOperation(operator=operator.lexeme, left=expr, right=rhs, line=operator.line, column=operator.column)
            else:
                break
        return expr

    def _parse_term(self) -> ast_nodes.Expression:
        expr = self._parse_factor()
        while True:
            if self._match_symbol("+") or self._match_symbol("-"):
                operator = self._previous_token()
                rhs = self._parse_factor()
                expr = ast_nodes.BinaryOperation(operator=operator.lexeme, left=expr, right=rhs, line=operator.line, column=operator.column)
            else:
                break
        return expr

    def _parse_factor(self) -> ast_nodes.Expression:
        expr = self._parse_unary()
        while True:
            if self._match_symbol("*") or self._match_symbol("/") or self._match_keyword("mod") or self._match_keyword("div"):
                operator = self._previous_token()
                rhs = self._parse_unary()
                lexeme = operator.lexeme
                expr = ast_nodes.BinaryOperation(operator=lexeme, left=expr, right=rhs, line=operator.line, column=operator.column)
            else:
                break
        return expr

    def _parse_unary(self) -> ast_nodes.Expression:
        if self._match_symbol("-") or self._match_symbol("+"):
            operator = self._previous_token()
            operand = self._parse_unary()
            return ast_nodes.UnaryOperation(operator=operator.lexeme, operand=operand, line=operator.line, column=operator.column)
        if self._match_keyword("not"):
            operator = self._previous_token()
            operand = self._parse_unary()
            return ast_nodes.UnaryOperation(operator=operator.lexeme, operand=operand, line=operator.line, column=operator.column)
        return self._parse_primary()

    def _parse_primary(self) -> ast_nodes.Expression:
        token = self._current()
        if token.kind == TokenKind.NUMBER:
            self._advance()
            return ast_nodes.Number(line=token.line, column=token.column, value=int(token.lexeme))
        if token.kind == TokenKind.STRING:
            self._advance()
            return ast_nodes.StringLiteral(line=token.line, column=token.column, value=token.lexeme)
        if token.kind == TokenKind.KEYWORD:
            if token.lexeme == "null":
                self._advance()
                return ast_nodes.NullLiteral(line=token.line, column=token.column)
            if token.lexeme in {"t", "f"}:
                self._advance()
                return ast_nodes.BooleanLiteral(line=token.line, column=token.column, value=(token.lexeme == "t"))
            if token.lexeme == "length":
                return self._parse_length_call()
        if token.kind in (TokenKind.IDENTIFIER,):
            self._advance()
            expr: ast_nodes.Expression = ast_nodes.Identifier(line=token.line, column=token.column, name=token.lexeme)
            expr = self._parse_postfix(expr)
            return expr
        if self._match_symbol("("):
            expr = self._parse_expression()
            self._expect_symbol(")", "Falta ')' en la expresión")
            return expr
        raise ParserError(f"Expresión inválida cerca de {token.line}:{token.column}")

    def _parse_postfix(self, expr: ast_nodes.Expression) -> ast_nodes.Expression:
        while True:
            if self._match_symbol("["):
                index = self._parse_expression()
                self._expect_symbol("]", "Falta ']' en acceso a arreglo")
                expr = ast_nodes.ArrayAccess(line=expr.line, column=expr.column, base=expr, index=index)
            elif self._match_symbol("."):
                field_token = self._expect_identifier("Se esperaba identificador tras '.'")
                expr = ast_nodes.FieldAccess(line=expr.line, column=expr.column, base=expr, field_name=field_token.lexeme)
            elif self._match_symbol(".."):
                right = self._parse_expression()
                expr = ast_nodes.RangeExpression(line=expr.line, column=expr.column, start=expr, end=right)
            else:
                break
        return expr

    def _parse_length_call(self) -> ast_nodes.LengthCall:
        token = self._consume_keyword("length")
        self._expect_symbol("(", "Falta '(' en length()")
        name_token = self._expect_identifier("Se esperaba nombre del arreglo en length()")
        self._expect_symbol(")", "Falta ')' en length()")
        return ast_nodes.LengthCall(line=token.line, column=token.column, array_name=name_token.lexeme)

    # ----------------------------------------------------------------------
    # Token helpers
    # ----------------------------------------------------------------------

    def _match_keyword(self, value: str) -> bool:
        token = self._current()
        if token.kind == TokenKind.KEYWORD and token.lexeme == value:
            self._advance()
            return True
        return False

    def _match_symbol(self, value: str) -> bool:
        token = self._current()
        if token.kind == TokenKind.SYMBOL and token.lexeme == value:
            self._advance()
            return True
        return False

    def _expect_keyword(self, value: str, message: str) -> Token:
        token = self._current()
        if token.kind == TokenKind.KEYWORD and token.lexeme == value:
            self._advance()
            return token
        raise ParserError(f"{message} (token actual: {token.lexeme!r}) en {token.line}:{token.column}")

    def _consume_keyword(self, value: str) -> Token:
        token = self._expect_keyword(value, f"Se esperaba la palabra reservada '{value}'")
        return token

    def _expect_symbol(self, value: str, message: str) -> Token:
        token = self._current()
        if token.kind == TokenKind.SYMBOL and token.lexeme == value:
            self._advance()
            return token
        raise ParserError(f"{message} (token actual: {token.lexeme!r}) en {token.line}:{token.column}")

    def _expect_identifier(self, message: str) -> Token:
        token = self._current()
        if token.kind == TokenKind.IDENTIFIER:
            self._advance()
            return token
        raise ParserError(f"{message} en {token.line}:{token.column}")

    def _check(self, kind: TokenKind) -> bool:
        return self._current().kind == kind

    def _check_symbol(self, value: str) -> bool:
        token = self._current()
        return token.kind == TokenKind.SYMBOL and token.lexeme == value

    def _check_keyword(self, value: Sequence[str]) -> bool:
        token = self._current()
        return token.kind == TokenKind.KEYWORD and token.lexeme in value

    def _check_keywords(self, values: Sequence[str]) -> bool:
        return self._check_keyword(values)


def parse_program(source: str) -> ast_nodes.Program:
    """Convenience wrapper."""
    return Parser(source).parse()
