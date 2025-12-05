from parsing import ast_nodes
from parsing.parser import Parser


def test_parses_procedures_without_main_block_and_calls_in_expressions() -> None:
    pseudocode = """PROCEDURE SWAP(A, i, j)
begin
    temp := A[i]
    A[i] := A[j]
    A[j] := temp
end

PROCEDURE QUICKSORT(A, p, r)
begin
    if p < r then
    begin
        q := CALL PARTITION(A, p, r)
        CALL QUICKSORT(A, p, q - 1)
        CALL QUICKSORT(A, q + 1, r)
    end
end

PROCEDURE PARTITION(A, p, r)
begin
    x := A[r]
    i := p - 1
    for j := p to r - 1 do
    begin
        if A[j] <= x then
        begin
            i := i + 1
            CALL SWAP(A, i, j)
        end
    end
    CALL SWAP(A, i + 1, r)
    return i + 1
end
"""

    program = Parser(pseudocode).parse()

    assert program.body == []
    assert [proc.name for proc in program.procedures] == ["swap", "quicksort", "partition"]

    quicksort_proc = program.procedures[1]
    assert len(quicksort_proc.body) == 1
    quicksort_if = quicksort_proc.body[0]
    assert isinstance(quicksort_if, ast_nodes.IfStatement)
    assert isinstance(quicksort_if.condition, ast_nodes.BinaryOperation)

    first_then_stmt = quicksort_if.then_branch[0]
    assert isinstance(first_then_stmt, ast_nodes.Assignment)
    assert isinstance(first_then_stmt.value, ast_nodes.CallExpression)
    assert isinstance(first_then_stmt.value.callee, ast_nodes.Identifier)
    assert first_then_stmt.value.callee.name == "partition"
