"""Definitions of AST nodes for the pseudocode language."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence


@dataclass(slots=True)
class Node:
    """Base class for all AST nodes."""

    line: int
    column: int

    def children(self) -> Sequence["Node"]:
        """Return child nodes for traversals."""
        return ()


@dataclass(slots=True)
class Program(Node):
    """Programa principal con cuerpo y definiciones auxiliares."""

    class_definitions: List["ClassDefinition"] = field(default_factory=list)
    declarations: List["Declaration"] = field(default_factory=list)
    procedures: List["Procedure"] = field(default_factory=list)
    body: List["Statement"] = field(default_factory=list)

    def children(self) -> Sequence["Node"]:
        return [*self.class_definitions, *self.declarations, *self.procedures, *self.body]



@dataclass(slots=True)
class Declaration(Node):
    """Declaración genérica de variables."""

    name: str

@dataclass(slots=True)
class VariableDeclaration(Declaration):
    datatype: str | None = None


@dataclass(slots=True)
class ArrayDeclaration(Declaration):
    size_expression: "Expression | None" = None


@dataclass(slots=True)
class ObjectDeclaration(Declaration):
    class_name: str = ""


@dataclass(slots=True)
class ClassDefinition(Node):
    """Representa la definición de una clase simple (atributos listados)."""

    name: str
    attributes: List[str] = field(default_factory=list)


@dataclass(slots=True)
class Procedure(Node):
    """Definición de una subrutina."""

    name: str
    parameters: List["Parameter"] = field(default_factory=list)
    body: List["Statement"] = field(default_factory=list)

    def children(self) -> Sequence["Node"]:
        return [*self.parameters, *self.body]


@dataclass(slots=True)
class Parameter(Node):
    name: str
    datatype: str | None = None


@dataclass(slots=True)
class Statement(Node):
    pass


@dataclass(slots=True)
class Assignment(Statement):
    target: "Expression"
    value: "Expression"

    def children(self) -> Sequence["Node"]:
        return [self.target, self.value]

@dataclass(slots=True)
class PrintStatement(Statement):
    expression: "Expression"

    def children(self) -> Sequence["Node"]:
        return [self.expression]

@dataclass(slots=True)
class ForLoop(Statement):
    iterator: str
    start: "Expression"
    stop: "Expression"
    body: List[Statement] = field(default_factory=list)

    def children(self) -> Sequence["Node"]:
        return [self.start, self.stop, *self.body]


@dataclass(slots=True)
class WhileLoop(Statement):
    condition: "Expression"
    body: List[Statement] = field(default_factory=list)

    def children(self) -> Sequence["Node"]:
        return [self.condition, *self.body]


@dataclass(slots=True)
class RepeatUntilLoop(Statement):
    body: List[Statement] = field(default_factory=list)
    condition: "Expression" | None = None

    def children(self) -> Sequence["Node"]:
        result: List[Node] = [*self.body]
        if self.condition:
            result.append(self.condition)
        return result


@dataclass(slots=True)
class IfStatement(Statement):
    condition: "Expression"
    then_branch: List[Statement] = field(default_factory=list)
    else_branch: List[Statement] = field(default_factory=list)

    def children(self) -> Sequence["Node"]:
        return [self.condition, *self.then_branch, *self.else_branch]


@dataclass(slots=True)
class CallStatement(Statement):
    name: str
    arguments: List["Expression"] = field(default_factory=list)

    def children(self) -> Sequence["Node"]:
        return list(self.arguments)


@dataclass(slots=True)
class ReturnStatement(Statement):
    value: "Expression | None" = None

    def children(self) -> Sequence["Node"]:
        return [self.value] if self.value else []


@dataclass(slots=True)
class Expression(Node):
    pass


@dataclass(slots=True)
class CallExpression(Expression):
    callee: Expression
    arguments: List[Expression] = field(default_factory=list)

    def children(self) -> Sequence["Node"]:
        return [self.callee, *self.arguments]


@dataclass(slots=True)
class Identifier(Expression):
    name: str


@dataclass(slots=True)
class Number(Expression):
    value: int


@dataclass(slots=True)
class BooleanLiteral(Expression):
    value: bool


@dataclass(slots=True)
class NullLiteral(Expression):
    pass


@dataclass(slots=True)
class StringLiteral(Expression):
    value: str


@dataclass(slots=True)
class BinaryOperation(Expression):
    operator: str
    left: Expression
    right: Expression

    def children(self) -> Sequence["Node"]:
        return [self.left, self.right]


@dataclass(slots=True)
class UnaryOperation(Expression):
    operator: str
    operand: Expression

    def children(self) -> Sequence["Node"]:
        return [self.operand]


@dataclass(slots=True)
class ArrayAccess(Expression):
    base: Expression
    index: Expression

    def children(self) -> Sequence["Node"]:
        return [self.base, self.index]


@dataclass(slots=True)
class FieldAccess(Expression):
    base: Expression
    field_name: str

    def children(self) -> Sequence["Node"]:
        return [self.base]


@dataclass(slots=True)
class LengthCall(Expression):
    array_name: str


@dataclass(slots=True)
class RangeExpression(Expression):
    start: Expression
    end: Expression

    def children(self) -> Sequence["Node"]:
        return [self.start, self.end]


AstNode = Node


def iter_statements(program: Program) -> Sequence[Statement]:
    """Helper that returns all statements in the program."""
    return program.body
