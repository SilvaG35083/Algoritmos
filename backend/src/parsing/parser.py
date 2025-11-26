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
        algorithm_name: str = ""

        # Parsear definiciones de clases
        while self._match_keyword("class"):
            class_definitions.append(self._parse_class_definition(self._previous_token()))

        # Parsear palabra clave "algoritmo" seguida del nombre (opcional)
        if self._match_keyword("algoritmo"):
            name_token = self._expect_identifier("Se esperaba el nombre del algoritmo después de 'algoritmo'")
            algorithm_name = name_token.lexeme
            
            # Los algoritmos pueden tener parámetros: Algoritmo QUICKSORT(A, p, r)
            # Consumimos los parámetros opcionales (no los guardamos, solo los parseamos)
            if self._match_symbol("("):
                # Parsear parámetros (si los hay)
                if not self._check_symbol(")"):
                    # Hay al menos un parámetro
                    self._parse_parameter()  # Parsear primer parámetro
                    while self._match_symbol(","):
                        self._parse_parameter()  # Parsear parámetros adicionales
                self._expect_symbol(")", "Falta ')' después de los parámetros del algoritmo")

        # Parsear definiciones de procedimientos (antes del begin principal)
        # Los procedimientos pueden tener la forma: "Procedimiento nombre(parametros) begin ... end"
        # O simplemente: nombre(parametros) begin ... end
        # IMPORTANTE: Los procedimientos pueden estar ANTES o DESPUÉS del algoritmo principal
        # Primero parseamos los que están antes del begin principal
        while not self._check_keyword(("begin",)) and not self._check(TokenKind.EOF):
            if self._match_keyword("procedimiento"):
                # Formato: Procedimiento NOMBRE(parametros) begin ... end
                name_token = self._expect_identifier("Se esperaba el nombre del procedimiento después de 'Procedimiento'")
                self._expect_symbol("(", "Se esperaba '(' después del nombre del procedimiento")
                
                parameters: List[ast_nodes.Parameter] = []
                if not self._check_symbol(")"):
                    # Parsear primer parámetro
                    param = self._parse_parameter()
                    parameters.append(param)
                    # Parsear parámetros adicionales
                    while self._match_symbol(","):
                        param = self._parse_parameter()
                        parameters.append(param)
                
                self._expect_symbol(")", "Se esperaba ')' para cerrar los parámetros")
                body = self._parse_mandatory_block()
                
                proc = ast_nodes.Procedure(
                    line=name_token.line,
                    column=name_token.column,
                    name=name_token.lexeme,
                    parameters=parameters,
                    body=body,
                )
                procedures.append(proc)
            elif self._current().kind == TokenKind.IDENTIFIER:
                # Verificar si es un procedimiento (tiene paréntesis después)
                saved_index = self._index
                name_token = self._current()
                self._advance()
                if self._check_symbol("("):
                    # Es un procedimiento sin palabra clave "Procedimiento"
                    self._index = saved_index  # Restaurar para parsear correctamente
                    proc = self._parse_procedure()
                    procedures.append(proc)
                else:
                    # No es un procedimiento, podría ser el nombre del algoritmo
                    # Pero si ya tenemos un nombre de algoritmo, esto es un error
                    if algorithm_name:
                        # Ya tenemos nombre, esto no debería pasar
                        self._index = saved_index
                        break
                    else:
                        # Podría ser el nombre del algoritmo, pero necesitamos verificar
                        # Si no hay "algoritmo" antes, esto podría ser un error
                        self._index = saved_index
                        break
            else:
                break

        # Si no encontramos nombre antes, verificar si hay un identificador seguido de begin
        # Puede ser: NOMBRE begin ... o NOMBRE(parametros) begin ...
        if not algorithm_name and self._current().kind == TokenKind.IDENTIFIER:
            saved_index = self._index
            name_token = self._current()
            self._advance()
            
            # Verificar si tiene parámetros
            if self._match_symbol("("):
                # Tiene parámetros, consumirlos
                if not self._check_symbol(")"):
                    self._parse_parameter()
                    while self._match_symbol(","):
                        self._parse_parameter()
                self._expect_symbol(")", "Falta ')' después de los parámetros del algoritmo")
            
            # Ahora verificar si sigue 'begin'
            if self._check_keyword(("begin",)):
                algorithm_name = name_token.lexeme
            else:
                # No era el nombre del algoritmo, restaurar
                self._index = saved_index

        self._expect_keyword("begin", "Se esperaba 'begin' al iniciar el programa")
        
        # Parsear declaraciones locales (arreglos, objetos, variables) al inicio del bloque
        while self._check_keyword(("new",)) or (
            self._current().kind == TokenKind.IDENTIFIER and self._check_ahead_for_array_declaration()
        ):
            if self._match_keyword("new"):
                # Formato: new Array(tamaño) o new Array[n]
                decl = self._parse_new_array_declaration()
                declarations.append(decl)
            elif self._current().kind == TokenKind.IDENTIFIER:
                # Podría ser una declaración de arreglo: nombreArreglo[tamaño]
                saved_index = self._index
                name_token = self._current()
                self._advance()
                if self._check_symbol("["):
                    # Es una declaración de arreglo
                    self._index = saved_index
                    decl = self._parse_array_declaration()
                    declarations.append(decl)
                else:
                    # No es declaración, continuar con el cuerpo
                    self._index = saved_index
                    break
            else:
                break
        
        body = self._parse_statement_block(end_keywords=("end",))
        end_token = self._expect_keyword("end", "Se esperaba 'end' para cerrar el programa")
        
        # Después del algoritmo principal, pueden venir procedimientos adicionales
        # Parsear procedimientos que vienen después del algoritmo principal
        while not self._check(TokenKind.EOF):
            if self._match_keyword("procedimiento"):
                # Formato: Procedimiento NOMBRE(parametros) begin ... end
                name_token = self._expect_identifier("Se esperaba el nombre del procedimiento después de 'Procedimiento'")
                self._expect_symbol("(", "Se esperaba '(' después del nombre del procedimiento")
                
                parameters: List[ast_nodes.Parameter] = []
                if not self._check_symbol(")"):
                    # Parsear primer parámetro
                    param = self._parse_parameter()
                    parameters.append(param)
                    # Parsear parámetros adicionales
                    while self._match_symbol(","):
                        param = self._parse_parameter()
                        parameters.append(param)
                
                self._expect_symbol(")", "Se esperaba ')' para cerrar los parámetros")
                proc_body = self._parse_mandatory_block()
                
                proc = ast_nodes.Procedure(
                    line=name_token.line,
                    column=name_token.column,
                    name=name_token.lexeme,
                    parameters=parameters,
                    body=proc_body,
                )
                procedures.append(proc)
            elif self._current().kind == TokenKind.IDENTIFIER:
                # Verificar si es un procedimiento (tiene paréntesis después)
                saved_index = self._index
                name_token = self._current()
                self._advance()
                if self._check_symbol("("):
                    # Es un procedimiento sin palabra clave "Procedimiento"
                    self._index = saved_index  # Restaurar para parsear correctamente
                    proc = self._parse_procedure()
                    procedures.append(proc)
                else:
                    # No es un procedimiento, terminar
                    self._index = saved_index
                    break
            else:
                break
        
        self._expect(TokenKind.EOF, "Se esperaban más sentencias? Revisa la estructura general")

        return ast_nodes.Program(
            line=1,
            column=1,
            name=algorithm_name,
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

    def _parse_procedure(self) -> ast_nodes.Procedure:
        """Parsea una definición de procedimiento/subrutina."""
        name_token = self._expect_identifier("Se esperaba el nombre del procedimiento")
        self._expect_symbol("(", "Se esperaba '(' después del nombre del procedimiento")
        
        parameters: List[ast_nodes.Parameter] = []
        if not self._check_symbol(")"):
            # Parsear primer parámetro
            param = self._parse_parameter()
            parameters.append(param)
            # Parsear parámetros adicionales
            while self._match_symbol(","):
                param = self._parse_parameter()
                parameters.append(param)
        
        self._expect_symbol(")", "Se esperaba ')' para cerrar los parámetros")
        body = self._parse_mandatory_block()
        
        return ast_nodes.Procedure(
            line=name_token.line,
            column=name_token.column,
            name=name_token.lexeme,
            parameters=parameters,
            body=body,
        )

    def _parse_parameter(self) -> ast_nodes.Parameter:
        """Parsea un parámetro de procedimiento.
        
        Formatos soportados:
        - nombre_arreglo[n]..[m] (arreglo multidimensional)
        - Clase nombre_objeto (objeto)
        - nombre (variable simple)
        """
        # Verificar si es un objeto (Clase nombre)
        if self._match_keyword("class"):
            class_name = self._expect_identifier("Se esperaba nombre de clase").lexeme
            param_name = self._expect_identifier("Se esperaba nombre del parámetro objeto").lexeme
            return ast_nodes.Parameter(
                line=self._current().line,
                column=self._current().column,
                name=param_name,
                datatype=class_name,
            )
        
        # Verificar si es un arreglo
        param_name_token = self._expect_identifier("Se esperaba nombre del parámetro")
        param_name = param_name_token.lexeme
        
        # Verificar si tiene corchetes (arreglo)
        if self._match_symbol("["):
            # Es un arreglo, parsear dimensiones
            dimensions = []
            while self._match_symbol("["):
                # El contenido entre corchetes es opcional
                if not self._check_symbol("]"):
                    # Hay un tamaño especificado, lo ignoramos por ahora
                    self._parse_expression()
                self._expect_symbol("]", "Falta ']' en dimensión de arreglo")
                dimensions.append(None)  # Por ahora no guardamos el tamaño
            
            return ast_nodes.Parameter(
                line=param_name_token.line,
                column=param_name_token.column,
                name=param_name,
                datatype="array",
            )
        
        # Variable simple
        return ast_nodes.Parameter(
            line=param_name_token.line,
            column=param_name_token.column,
            name=param_name,
            datatype=None,
        )

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
                "print": self._parse_print_statement,
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
        self._expect_symbol("🡨", "Falta el símbolo de asignación '🡨' en el for")
        start_expr = self._parse_expression()
        self._expect_keyword("to", "Se esperaba 'to' en el for")
        stop_expr = self._parse_expression()
        self._expect_keyword("do", "Se esperaba 'do' en el for")
        body = self._parse_loop_body("for")
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
        # Paréntesis opcionales para mayor flexibilidad
        has_paren = self._match_symbol("(")
        condition = self._parse_expression()
        if has_paren:
            self._expect_symbol(")", "Falta ')' en la condición del while")
        self._expect_keyword("do", "Se esperaba 'do' en el while")
        body = self._parse_loop_body("while")
        return ast_nodes.WhileLoop(line=keyword.line, column=keyword.column, condition=condition, body=body)

    def _parse_repeat_until_loop(self) -> ast_nodes.RepeatUntilLoop:
        keyword = self._consume_keyword("repeat")
        body = self._parse_statement_block(end_keywords=("until",))
        self._expect_keyword("until", "Falta 'until' al cerrar el repeat")
        # Paréntesis opcionales
        has_paren = self._match_symbol("(")
        condition = self._parse_expression()
        if has_paren:
            self._expect_symbol(")", "Falta ')' en la condición del until")
        return ast_nodes.RepeatUntilLoop(line=keyword.line, column=keyword.column, body=body, condition=condition)

    def _parse_if_statement(self) -> ast_nodes.IfStatement:
        keyword = self._consume_keyword("if")
        # Paréntesis opcionales para mayor flexibilidad
        has_paren = self._match_symbol("(")
        condition = self._parse_expression()
        if has_paren:
            self._expect_symbol(")", "Falta ')' en la condición del if")
        self._expect_keyword("then", "Se esperaba 'then'")
        if self._match_keyword("begin"):
            then_branch = self._parse_statement_block(end_keywords=("end",))
            self._expect_keyword("end", "Falta 'end' al cerrar el bloque del if")
        else:
            then_branch = self._parse_inline_statements(stop_keywords=("else", "end"))

        else_branch: List[ast_nodes.Statement] = []
        if self._match_keyword("else"):
            if self._check_keyword(("if",)):
                else_branch = [self._parse_if_statement()]
            elif self._match_keyword("begin"):
                else_branch = self._parse_statement_block(end_keywords=("end",))
                self._expect_keyword("end", "Falta 'end' al cerrar el bloque del else")
            else:
                else_branch = self._parse_inline_statements(stop_keywords=("end",))

        return ast_nodes.IfStatement(
            line=keyword.line,
            column=keyword.column,
            condition=condition,
            then_branch=then_branch,
            else_branch=else_branch,
        )

    def _parse_call_statement(self) -> ast_nodes.CallStatement:
        keyword, name_token, arguments = self._parse_call_invocation()
        return ast_nodes.CallStatement(line=keyword.line, column=keyword.column, name=name_token.lexeme, arguments=arguments)

    def _parse_call_expression(self) -> ast_nodes.Expression:
        keyword, name_token, arguments = self._parse_call_invocation()
        return ast_nodes.CallExpression(line=keyword.line, column=keyword.column, name=name_token.lexeme, arguments=arguments)

    def _parse_call_invocation(self):
        keyword = self._consume_keyword("call")
        name_token = self._expect_identifier("Se esperaba el nombre de la subrutina en CALL")
        self._expect_symbol("(", "Falta '(' en la llamada a subrutina")
        arguments: List[ast_nodes.Expression] = []
        if not self._check_symbol(")"):
            arguments.append(self._parse_expression())
            while self._match_symbol(","):
                arguments.append(self._parse_expression())
        self._expect_symbol(")", "Falta ')' al cerrar CALL")
        return keyword, name_token, arguments

    def _parse_return_statement(self) -> ast_nodes.ReturnStatement:
        keyword = self._consume_keyword("return")
        value: ast_nodes.Expression | None = None
        if not self._check_keyword(("end", "else")) and not self._check(TokenKind.EOF):
            value = self._parse_expression()
        return ast_nodes.ReturnStatement(line=keyword.line, column=keyword.column, value=value)

    def _parse_assignment(self) -> ast_nodes.Assignment:
        target = self._parse_lvalue()
        assign_token = self._expect_symbol_any(["🡨", ":="], "Falta el símbolo '🡨' o ':=' en la asignación")
        # El parseo de "new Array" se maneja en _parse_primary, así que simplemente parseamos la expresión
        value = self._parse_expression()
        return ast_nodes.Assignment(line=assign_token.line, column=assign_token.column, target=target, value=value)

    def _parse_lvalue(self) -> ast_nodes.Expression:
        token = self._expect_identifier("Se esperaba identificador en la asignación")
        expr: ast_nodes.Expression = ast_nodes.Identifier(line=token.line, column=token.column, name=token.lexeme)
        while True:
            if self._match_symbol("["):
                indexes: List[ast_nodes.Expression] = []
                indexes.append(self._parse_expression())
                while self._match_symbol(","):
                    indexes.append(self._parse_expression())
                self._expect_symbol("]", "Falta ']' al cerrar acceso a arreglo")
                for index_expr in indexes:
                    expr = ast_nodes.ArrayAccess(
                        line=expr.line,
                        column=expr.column,
                        base=expr,
                        index=index_expr,
                    )
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

    def _parse_inline_statements(self, stop_keywords: Sequence[str]) -> List[ast_nodes.Statement]:
        statements: List[ast_nodes.Statement] = []
        while not self._check_keyword(stop_keywords) and not self._check(TokenKind.EOF):
            statements.append(self._parse_statement())
        return statements

    def _parse_loop_body(self, loop_name: str) -> List[ast_nodes.Statement]:
        if self._match_keyword("begin"):
            body = self._parse_statement_block(end_keywords=("end",))
            self._expect_keyword("end", f"Falta 'end' al cerrar el {loop_name}")
            return body
        inline_body = self._parse_inline_statements(stop_keywords=("end",))
        self._expect_keyword("end", f"Falta 'end' al cerrar el {loop_name}")
        return inline_body

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
            matched = False
            op_lexeme = None
            op_token = None
            
            # Intentar todos los operadores de comparación
            if self._match_symbol("<"):
                op_token = self._previous_token()
                op_lexeme = "<"
                matched = True
            elif self._match_symbol(">"):
                op_token = self._previous_token()
                op_lexeme = ">"
                matched = True
            elif self._match_symbol("<="):
                op_token = self._previous_token()
                op_lexeme = "<="
                matched = True
            elif self._match_symbol(">="):
                op_token = self._previous_token()
                op_lexeme = ">="
                matched = True
            elif self._match_symbol("≤"):
                op_token = self._previous_token()
                op_lexeme = "<="  # Normalizar a <=
                matched = True
            elif self._match_symbol("≥"):
                op_token = self._previous_token()
                op_lexeme = ">="  # Normalizar a >=
                matched = True
            
            if matched and op_token:
                rhs = self._parse_term()
                expr = ast_nodes.BinaryOperation(operator=op_lexeme, left=expr, right=rhs, line=op_token.line, column=op_token.column)
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
            expr = ast_nodes.Number(line=token.line, column=token.column, value=int(token.lexeme))
            return self._parse_postfix(expr)
        if token.kind == TokenKind.STRING:
            self._advance()
            expr = ast_nodes.StringLiteral(line=token.line, column=token.column, value=token.lexeme)
            return self._parse_postfix(expr)
        if token.kind == TokenKind.KEYWORD:
            if token.lexeme == "null":
                self._advance()
                return ast_nodes.NullLiteral(line=token.line, column=token.column)
            if token.lexeme in {"t", "f"}:
                self._advance()
                return ast_nodes.BooleanLiteral(line=token.line, column=token.column, value=(token.lexeme == "t"))
            if token.lexeme == "length":
                return self._parse_length_call()
            if token.lexeme == "new":
                # Soporte para "new Array(tamaño)" o "new Array[n]"
                return self._parse_new_array_expression()
            if token.lexeme == "call":
                return self._parse_call_expression()
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
    
    def _parse_new_array_expression(self) -> ast_nodes.ArrayCreation:
        """Parsea 'new Array(tamaño)' o 'new Array[n]' como expresión."""
        self._consume_keyword("new")
        self._expect_keyword("array", "Se esperaba 'Array' después de 'new'")
        
        # Verificar formato: Array(tamaño) o Array[n]
        if self._match_symbol("("):
            size_expr = self._parse_expression()
            self._expect_symbol(")", "Falta ')' en new Array(tamaño)")
        elif self._match_symbol("["):
            size_expr = self._parse_expression()
            self._expect_symbol("]", "Falta ']' en new Array[n]")
        else:
            raise ParserError("Se esperaba '(' o '[' después de 'Array'")
        
        return ast_nodes.ArrayCreation(
            line=self._current().line,
            column=self._current().column,
            size=size_expr,
        )

    def _parse_postfix(self, expr: ast_nodes.Expression) -> ast_nodes.Expression:
        while True:
            if self._match_symbol("["):
                indexes: List[ast_nodes.Expression] = []
                indexes.append(self._parse_expression())
                while self._match_symbol(","):
                    indexes.append(self._parse_expression())
                self._expect_symbol("]", "Falta ']' en acceso a arreglo")

                for index_expr in indexes:
                    expr = ast_nodes.ArrayAccess(
                        line=expr.line,
                        column=expr.column,
                        base=expr,
                        index=index_expr,
                    )
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

    def _check_ahead_for_array_declaration(self) -> bool:
        """Verifica si el identificador actual parece ser declaración de arreglo (nombre[...])."""
        if self._index + 1 >= len(self._tokens):
            return False
        next_token = self._tokens[self._index + 1]
        return next_token.kind == TokenKind.SYMBOL and next_token.lexeme == "["

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
