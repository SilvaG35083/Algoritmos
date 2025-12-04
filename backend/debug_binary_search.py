"""Debug script to understand why best case detection is not working."""

from parsing.parser import Parser
from analysis.complexity_engine import ComplexityEngine
from parsing import ast_nodes

code = """
busquedaBinaria(A[n], valor)      
begin
    inicio ← 0
    fin ← n - 1
    encontro ← 0
    while (inicio ≤ fin and encontro = 0) do
    begin
        medio ← (inicio + fin) div 2
        if (A[medio] = valor) then
        begin
            encontro ← 1
        end
        else
        begin
            if (A[medio] > valor) then
            begin
                fin ← medio - 1
            end
            else
            begin
                inicio ← medio + 1
            end
        end
    end
    return encontro
end
"""

def debug_condition(node, indent=0):
    """Debug helper to print AST structure."""
    prefix = "  " * indent
    if node is None:
        print(f"{prefix}None")
        return
    
    node_type = type(node).__name__
    print(f"{prefix}{node_type}", end="")
    
    if isinstance(node, ast_nodes.BinaryOperation):
        print(f" [operator={node.operator}]")
        print(f"{prefix}  left:")
        debug_condition(node.left, indent + 2)
        print(f"{prefix}  right:")
        debug_condition(node.right, indent + 2)
    elif isinstance(node, ast_nodes.Identifier):
        print(f" [name={node.name}]")
    elif isinstance(node, ast_nodes.Number):
        print(f" [value={node.value}]")
    else:
        print()

def main():
    parser = Parser()
    ast = parser.parse(code)
    
    print("=" * 60)
    print("DEBUG: AST Structure")
    print("=" * 60)
    
    # Find the while loop
    if ast.procedures:
        proc = ast.procedures[0]
        print(f"\nProcedure: {proc.name}")
        print(f"Number of statements: {len(proc.body)}")
        
        for i, stmt in enumerate(proc.body):
            print(f"\nStatement {i}: {type(stmt).__name__}")
            if isinstance(stmt, ast_nodes.WhileLoop):
                print("\n  WHILE LOOP CONDITION:")
                debug_condition(stmt.condition, indent=2)
                
                print(f"\n  Body has {len(stmt.body)} statements")
                
                # Test the engine methods
                engine = ComplexityEngine()
                print("\n" + "=" * 60)
                print("Testing detection methods:")
                print("=" * 60)
                
                has_flag = engine._condition_has_exit_flag(stmt.condition)
                print(f"  _condition_has_exit_flag: {has_flag}")
                
                can_set = engine._body_can_set_exit_flag(stmt.body, stmt.condition)
                print(f"  _body_can_set_exit_flag: {can_set}")
                
                has_early_exit = engine._has_early_exit_condition(stmt)
                print(f"  _has_early_exit_condition: {has_early_exit}")
    
    print("\n" + "=" * 60)
    print("Full Analysis:")
    print("=" * 60)
    engine = ComplexityEngine()
    result = engine.analyze(ast)
    
    print(f"Mejor caso:    {result.best_case}")
    print(f"Peor caso:     {result.worst_case}")
    print(f"Caso promedio: {result.average_case}")

if __name__ == "__main__":
    main()
