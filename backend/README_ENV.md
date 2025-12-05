# IMPORTANTE: Configuración de API keys

## Seguridad
- **Nunca** subas tus keys a Git.
- Guarda las claves en `.env` (ya está en `.gitignore`) o como variables de entorno.

## Ejemplo de `.env` (backend/.env)
```env
# OpenAI (chat/analyze)
OPENAI_API_KEY=sk-proj-tu-api-key
OPENAI_MODEL=gpt-4o-mini

# Gemini (chat/analyze/simulate)
GEMINI_API_KEY=tu-api-key-gemini
GEMINI_MODEL=gemini-2.5-flash

# Proveedor por defecto para chat/analyze
LLM_PROVIDER=openai
```

## Variables en el sistema
### Windows (PowerShell)
```powershell
$env:OPENAI_API_KEY="sk-proj-tu-api-key"
$env:OPENAI_MODEL="gpt-4o-mini"
$env:GEMINI_API_KEY="tu-api-key-gemini"
$env:GEMINI_MODEL="gemini-2.5-flash"
$env:LLM_PROVIDER="openai"
```

### Windows (CMD)
```cmd
set OPENAI_API_KEY=sk-proj-tu-api-key
set OPENAI_MODEL=gpt-4o-mini
set GEMINI_API_KEY=tu-api-key-gemini
set GEMINI_MODEL=gemini-2.5-flash
set LLM_PROVIDER=openai
```

### Linux/macOS
```bash
export OPENAI_API_KEY="sk-proj-tu-api-key"
export OPENAI_MODEL="gpt-4o-mini"
export GEMINI_API_KEY="tu-api-key-gemini"
export GEMINI_MODEL="gemini-2.5-flash"
export LLM_PROVIDER="openai"
```
Para hacerlo permanente agrega las líneas a `~/.bashrc` o `~/.zshrc`.

## Verificar
```powershell
echo $env:OPENAI_API_KEY
echo $env:GEMINI_API_KEY
```
o
```bash
echo $OPENAI_API_KEY
echo $GEMINI_API_KEY
```

## Si publicaste tu key por error
1) Revoca la key (OpenAI/Gemini). 2) Genera una nueva. 3) Guarda solo en `.env` o variables. 4) Quita la key del repo y haz commit.

Más detalles en `LLM_SETUP.md` y `GEMINI_SETUP.md`.
