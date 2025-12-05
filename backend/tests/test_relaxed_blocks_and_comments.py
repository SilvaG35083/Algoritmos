from parsing.parser import Parser
from parsing import ast_nodes


def test_mergesort_without_begin_blocks_and_comments() -> None:
    pseudocode = """► MergeSort con if sin begin
MERGESORT(A, p, r)
begin
    if p < r then
      q 🡨 (p + r) / 2
      CALL MERGESORT(A, p, q)
      CALL MERGESORT(A, q + 1, r)
      CALL MERGE(A, p, q, r)
    end
end

MERGE(A, p, q, r)
begin
    ► bloque sin begin
    if p < r then
      i 🡨 p
    end
    ► let ... línea ignorada
    let L[1..n1+1] and R[1..n2+1] be new arrays
    return 0
end
"""
    program = Parser(pseudocode).parse()
    assert len(program.procedures) == 2
    mergesort = program.procedures[0]
    assert isinstance(mergesort.body[0], ast_nodes.IfStatement)
    merge = program.procedures[1]
    assert any(isinstance(stmt, ast_nodes.NoOp) for stmt in merge.body)
