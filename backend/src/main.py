from src.parsing.parser import Parser

def main():
    source = """
begin
    x := 5
    print(x + 2)
    print("Resultado: " + x)
end
"""

    #parsear 
    parser = Parser(source)
    program = parser.parse()

    print("Programa parseado:")
    print(program)

if __name__ == "__main__":
    main()



