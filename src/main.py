from src.parsing.parser import Parser

def main():
    source = """
begin
    print("Hola Mundo")
end
"""

    #parsear 
    parser = Parser(source)
    program = parser.parse()

    print("Programa parseado:")
    print(program)

if __name__ == "__main__":
    main()



