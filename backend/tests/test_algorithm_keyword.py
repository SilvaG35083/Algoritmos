from parsing.parser import Parser
from parsing import ast_nodes


def test_algorithm_keyword_parses_like_procedure() -> None:
    pseudocode = """ALGORITHM Merge(A, p, q, r)
begin
    declare L[10]
    return 0
end
"""
    program = Parser(pseudocode).parse()
    assert len(program.procedures) == 1
    assert program.procedures[0].name == "merge"
    # ensure declare was tolerated
    assert any(isinstance(stmt, ast_nodes.NoOp) for stmt in program.procedures[0].body)
