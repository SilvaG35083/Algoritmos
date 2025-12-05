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


ASSIGNMENT_SYMBOLS = ("胑哩", ":=", "🡨", "←", "<-", "=")


class Parser:
    """Consumes tokens and produces an AST."""

    def __init__(self, source: str, config: ParserConfig | None = None) -> None:
        self._tokens: List[Token] = Lexer(source).tokenize()
        self._index: int = 0
        self._previous: Token | None = None
        self._config = config or ParserConfig()

    def parse(self) -> ast_nodes.Program:
            # 🔍 Depuración: ver todos los tokens que el parser recibió
        print("\nTOKENS RECONOCIDOS POR EL LEXER:")
        print([ (t.kind, t.lexeme) for t in self._tokens ])
        print()  # línea vacía para claridad

        """Parse the entire input and return a Program node."""
        class_definitions: List[ast_nodes.ClassDefinition] = []
        declarations: List[ast_nodes.Declaration] = []
        procedures: List[ast_nodes.Procedure] = []

        while self._match_keyword("class"):
            class_definitions.append(self._parse_class_definition(self._previous_token()))

        # Permitir definiciones de subrutinas en toplevel antes del bloque principal
        while self._is_procedure_definition():
            procedures.append(self._parse_procedure())

        # Si el archivo contiene solo subrutinas (sin un programa begin..end),
        # devolvemos el Programa con las subrutinas y cuerpo vacío.
        if self._check(TokenKind.EOF) and procedures:
            return ast_nodes.Program(
                line=1,
                column=1,
                class_definitions=class_definitions,
                declarations=declarations,
                procedures=procedures,
                body=[],
            )

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

    def _is_procedure_definition(self) -> bool:
        token = self._current()
        next_tok = self._peek(1)
        # Formato con palabra clave: PROCEDURE/FUNCTION/ALGORITHM nombre(...)
        if token.kind == TokenKind.KEYWORD and token.lexeme in {"procedure", "function", "algorithm"}:
            return (
                next_tok.kind == TokenKind.IDENTIFIER
                and self._peek(2).kind == TokenKind.SYMBOL
                and self._peek(2).lexeme == "("
            )
        # Formato sencillo: nombre(...)
        return token.kind == TokenKind.IDENTIFIER and next_tok.kind == TokenKind.SYMBOL and next_tok.lexeme == "("

    def _parse_procedure(self) -> ast_nodes.Procedure:
        proc_keyword: Token | None = None
        if self._match_keyword("procedure") or self._match_keyword("function") or self._match_keyword("algorithm"):
            proc_keyword = self._previous_token()
        name_token = self._expect_identifier("Se esperaba el nombre de la subrutina")
        # Lista de parámetros entre paréntesis
        self._expect_symbol("(", "Falta '(' tras el nombre de la subrutina")
        parameters: List[ast_nodes.Parameter] = []
        if not self._check_symbol(")"):
            # Cada parámetro puede ser un identificador, opcionalmente seguido
            # de una anotación de arreglo como `A[n]` o un rango `A[n]..[m]`.
            def _read_parameter() -> ast_nodes.Parameter:
                token = self._expect_identifier("Se esperaba nombre de parámetro en la subrutina")
                datatype: str | None = None
                # Soportar anotación de arreglo entre corchetes, ej. A[n] o A[n]..[m]
                if self._match_symbol("["):
                    parts: List[str] = ["["]
                    # recoger lexemas hasta ']' (no intentamos re-parsing de expresiones aquí)
                    while not self._check_symbol("]") and not self._check(TokenKind.EOF):
                        parts.append(self._current().lexeme)
                        self._advance()
                    self._expect_symbol("]", "Falta ']' en anotación de parámetro")
                    parts.append("]")
                    # Soportar '..' seguido de otra anotación entre corchetes
                    if self._match_symbol(".."):
                        parts.append("..")
                        if self._match_symbol("["):
                            while not self._check_symbol("]") and not self._check(TokenKind.EOF):
                                parts.append(self._current().lexeme)
                                self._advance()
                            self._expect_symbol("]", "Falta ']' en anotación de parámetro")
                            parts.append("]")
                        else:
                            # Dejar que el mensaje de error estándar aparezca
                            raise ParserError("Falta '[' después de '..' en anotación de parámetro")
                    datatype = "".join(parts)
                return ast_nodes.Parameter(line=token.line, column=token.column, name=token.lexeme, datatype=datatype)

            parameters.append(_read_parameter())
            while self._match_symbol(","):
                parameters.append(_read_parameter())
        self._expect_symbol(")", "Falta ')' al cerrar la lista de parámetros")
        # Opcional: RETURNS <tipo> se ignora
        if self._match_keyword("returns"):
            if self._check(TokenKind.IDENTIFIER) or self._check(TokenKind.KEYWORD):
                self._advance()
        # Cuerpo obligatorio usando begin...end
        body = self._parse_mandatory_block()
        anchor = proc_keyword or name_token
        return ast_nodes.Procedure(line=anchor.line, column=anchor.column, name=name_token.lexeme, parameters=parameters, body=body)

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
                "swap": self._parse_swap_statement,
                "let": self._parse_let_statement,
                "declare": self._parse_declare_statement,
                "return": self._parse_return_statement,
                "print": self._parse_print_statement,
            }
            handler = dispatch.get(token.lexeme)
            if handler:
                return handler()
        
        if token.kind in (TokenKind.IDENTIFIER,):
            if token.lexeme == "swap":
                return self._parse_swap_statement()
            return self._parse_assignment()
            
        raise ParserError(f"No se reconoce la sentencia iniciada en {token.line}:{token.column}")

    # ----------------------------------------------------------------------
    # Statement parsing
    # ----------------------------------------------------------------------
    def _parse_print_statement(self) -> ast_nodes.PrintStatement:
        print_token = self._expect_keyword("print", "Se esperaba 'print'")
        
        # Permitir con o sin paréntesis
        if self._match_symbol("("):
            expr = self._parse_expression()
            self._expect_symbol(")", "Falta el símbolo ')' en la llamada a print")
        else:
            expr = self._parse_expression()

        return ast_nodes.PrintStatement(
            line=print_token.line,
            column=print_token.column,
            expression=expr
        )


    def _parse_for_loop(self) -> ast_nodes.ForLoop:
        keyword = self._consume_keyword("for")
        iterator_token = self._expect_identifier("Se esperaba el identificador de control del for")
        # Aceptar símbolos de asignación comunes (🡨, <-, :=, =)
        self._expect_symbol_any(ASSIGNMENT_SYMBOLS, "Falta un símbolo de asignación en el for")
        start_expr = self._parse_expression()
        self._expect_keyword("to", "Se esperaba 'to' en el for")
        stop_expr = self._parse_expression()
        self._expect_keyword("do", "Se esperaba 'do' en el for")
        body, _ = self._parse_relaxed_block(end_keywords=("end",), consume_end=True)
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
        if self._match_symbol("("):
            condition = self._parse_expression()
            self._expect_symbol(")", "Falta ')' en la condición del while")
        else:
            condition = self._parse_expression()
        self._expect_keyword("do", "Se esperaba 'do' en el while")
        body, _ = self._parse_relaxed_block(end_keywords=("end",), consume_end=True)
        return ast_nodes.WhileLoop(line=keyword.line, column=keyword.column, condition=condition, body=body)

    def _parse_repeat_until_loop(self) -> ast_nodes.RepeatUntilLoop:
        keyword = self._consume_keyword("repeat")
        body = self._parse_statement_block(end_keywords=("until",))
        self._expect_keyword("until", "Falta 'until' al cerrar el repeat")
        if self._match_symbol("("):
            condition = self._parse_expression()
            self._expect_symbol(")", "Falta ')' en la condición del until")
        else:
            condition = self._parse_expression()
        return ast_nodes.RepeatUntilLoop(line=keyword.line, column=keyword.column, body=body, condition=condition)

    def _parse_if_statement(self) -> ast_nodes.IfStatement:
        keyword = self._consume_keyword("if")
        if self._match_symbol("("):
            condition = self._parse_expression()
            self._expect_symbol(")", "Falta ')' en la condición del if")
        else:
            condition = self._parse_expression()
        self._expect_keyword("then", "Se esperaba 'then'")
        then_branch, used_begin = self._parse_relaxed_block(end_keywords=("else", "end"), consume_end=False)
        else_branch: List[ast_nodes.Statement] = []
        if self._match_keyword("else"):
            else_branch, _ = self._parse_relaxed_block(end_keywords=("end",), consume_end=True)
        else:
            # Si no hay else, consumir el 'end' de cierre si existe
            if not used_begin:
                self._match_keyword("end")
        return ast_nodes.IfStatement(
            line=keyword.line,
            column=keyword.column,
            condition=condition,
            then_branch=then_branch,
            else_branch=else_branch,
        )

    def _parse_call_statement(self) -> ast_nodes.CallStatement:
        call_expr = self._parse_call_expression()
        callee_name = call_expr.callee.name if isinstance(call_expr.callee, ast_nodes.Identifier) else str(call_expr.callee)
        return ast_nodes.CallStatement(line=call_expr.line, column=call_expr.column, name=callee_name, arguments=call_expr.arguments)

    def _parse_swap_statement(self) -> ast_nodes.CallStatement:
        token = self._current()
        if token.kind == TokenKind.KEYWORD and token.lexeme == "swap":
            self._advance()
        elif token.kind == TokenKind.IDENTIFIER and token.lexeme == "swap":
            self._advance()
        else:
            raise ParserError(f"Se esperaba 'swap' en {token.line}:{token.column}")

        first = self._parse_expression()
        self._expect_keyword("with", "Falta la palabra 'with' en swap")
        second = self._parse_expression()
        return ast_nodes.CallStatement(line=token.line, column=token.column, name="swap", arguments=[first, second])

    def _parse_let_statement(self) -> ast_nodes.Statement:
        """Ignora líneas tipo 'let ...' comunes en salidas de LLM."""
        start_line = self._current().line
        self._advance()
        while not self._check(TokenKind.EOF) and self._current().line == start_line:
            self._advance()
        return ast_nodes.NoOp(line=start_line, column=1)

    def _parse_declare_statement(self) -> ast_nodes.Statement:
        """Ignora declaraciones sueltas (declare X[n])."""
        start_line = self._current().line
        self._advance()
        while not self._check(TokenKind.EOF) and self._current().line == start_line:
            self._advance()
        return ast_nodes.NoOp(line=start_line, column=1)

    def _parse_call_expression(self) -> ast_nodes.CallExpression:
        keyword = self._consume_keyword("call")
        name_token = self._expect_identifier("Se esperaba el nombre de la subrutina en CALL")
        self._expect_symbol("(", "Falta '(' en la llamada a subrutina")
        arguments: List[ast_nodes.Expression] = []
        if not self._check_symbol(")"):
            arguments.append(self._parse_expression())
            while self._match_symbol(","):
                arguments.append(self._parse_expression())
        self._expect_symbol(")", "Falta ')' al cerrar CALL")
        callee = ast_nodes.Identifier(line=name_token.line, column=name_token.column, name=name_token.lexeme)
        return ast_nodes.CallExpression(line=keyword.line, column=keyword.column, callee=callee, arguments=arguments)

    def _parse_return_statement(self) -> ast_nodes.ReturnStatement:
        keyword = self._consume_keyword("return")
        value: ast_nodes.Expression | None = None
        if not self._check_keyword(("end", "else")) and not self._check(TokenKind.EOF):
            value = self._parse_expression()
        return ast_nodes.ReturnStatement(line=keyword.line, column=keyword.column, value=value)

    def _parse_assignment(self) -> ast_nodes.Assignment:
        target = self._parse_lvalue()
        assign_token = self._expect_symbol_any(ASSIGNMENT_SYMBOLS, "Falta un símbolo de asignación válido")
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

    def _parse_relaxed_block(self, end_keywords: Sequence[str], consume_end: bool = True) -> tuple[List[ast_nodes.Statement], bool]:
        """Permite bloques con o sin 'begin'. Devuelve (statements, uso_de_begin).
        
        Si consume_end es True y el bloque implícito termina con 'end', lo consume.
        """
        if self._match_keyword("begin"):
            statements = self._parse_statement_block(end_keywords=("end",))
            self._expect_keyword("end", "Falta 'end' al cerrar bloque")
            return statements, True
        # Modo laxo: consumir sentencias hasta encontrar palabra de cierre
        statements: List[ast_nodes.Statement] = []
        while not self._check_keywords(end_keywords) and not self._check(TokenKind.EOF):
            statements.append(self._parse_statement())
        if consume_end:
            self._match_keyword("end")
        return statements, False

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
            if token.lexeme in {"t", "f", "true", "false"}:
                self._advance()
                return ast_nodes.BooleanLiteral(line=token.line, column=token.column, value=(token.lexeme in {"t", "true"}))
            if token.lexeme == "length":
                return self._parse_length_call()
            if token.lexeme == "call":
                return self._parse_call_expression()
        if token.kind in (TokenKind.IDENTIFIER,):
            # Tolerar descripciones de estructuras como "array of size n" o "empty list"
            if token.lexeme in {"array", "list", "empty"}:
                start = token
                self._advance()
                # Consumir palabras descriptivas comunes
                while True:
                    t = self._current()
                    if t.kind in {TokenKind.KEYWORD, TokenKind.IDENTIFIER} and t.lexeme in {"of", "size", "integer", "boolean", "list", "empty"}:
                        self._advance()
                        continue
                    if t.kind == TokenKind.SYMBOL and t.lexeme not in {",", ")", "end", "then", "do"}:
                        self._advance()
                        continue
                    break
                return ast_nodes.NullLiteral(line=start.line, column=start.column)
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
            elif self._match_symbol("("):
                args: List[ast_nodes.Expression] = []
                if not self._check_symbol(")"):
                    args.append(self._parse_expression())
                    while self._match_symbol(","):
                        args.append(self._parse_expression())
                self._expect_symbol(")", "Falta ')' en la llamada a función")
                expr = ast_nodes.CallExpression(line=expr.line, column=expr.column, callee=expr, arguments=args)
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
        
    def _expect_symbol_any(self, values, message):
        token = self._current()
        if token.kind == TokenKind.SYMBOL and token.lexeme in values:
            self._advance()
            return token
        raise ParserError(f"{message} (token actual: {token.lexeme!r}) en {token.line}:{token.column}")



    def _expect_identifier(self, message: str) -> Token:
        token = self._current()
        if token.kind == TokenKind.IDENTIFIER:
            self._advance()
            return token
        raise ParserError(f"{message} en {token.line}:{token.column}")

    def _peek(self, offset: int) -> Token:
        idx = self._index + offset
        if idx < 0:
            idx = 0
        if idx >= len(self._tokens):
            return self._tokens[-1]
        return self._tokens[idx]

    def _check(self, kind: TokenKind) -> bool:
        return self._current().kind == kind

    def _check_symbol(self, value: str) -> bool:
        token = self._current()
        return token.kind == TokenKind.SYMBOL and token.lexeme == value

    def _check_keyword(self, values: Sequence[str]) -> bool:
        token = self._current()
        return token.kind == TokenKind.KEYWORD and token.lexeme in values

    def _check_keywords(self, values: Sequence[str]) -> bool:
        return self._check_keyword(values)


def parse_program(source: str) -> ast_nodes.Program:
    """Convenience wrapper."""
    return Parser(source).parse()
