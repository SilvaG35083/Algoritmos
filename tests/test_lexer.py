from src.parsing.lexer import lex  # si el archivo se llama lexer.py y está en el mismo directorio

source_code = '''
begin
    x := 10
    if x >= 5 then
        ► este es un comentario
        y := "hola"
    end
end
'''

for token in lex(source_code):
    print(token)
