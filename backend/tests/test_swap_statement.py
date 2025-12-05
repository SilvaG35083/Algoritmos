from parsing.parser import Parser
from parsing import ast_nodes


def test_swap_statement_parses_as_call() -> None:
    code = """begin
    swap A[i] with A[j]
end"""
    program = Parser(code).parse()
    assert len(program.body) == 1
    stmt = program.body[0]
    assert isinstance(stmt, ast_nodes.CallStatement)
    assert stmt.name == "swap"
    assert len(stmt.arguments) == 2
