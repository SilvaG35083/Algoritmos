# ⚠️ IMPORTANTE: Configuración de API Keys

## 🔒 Seguridad

**NUNCA** pongas tu API key directamente en archivos de código o documentación que se suban a Git.

## 📝 Cómo configurar tu API key de OpenAI

### Opción 1: Archivo .env (Recomendado)

1. **Crea un archivo `.env` en la carpeta `backend/`**:
   ```bash
   cd backend
   touch .env  # En Windows: type nul > .env
   ```

2. **Abre el archivo `.env` y agrega tu API key**:
   ```env
   OPENAI_API_KEY=sk-proj-tu-api-key-real-aqui
   OPENAI_MODEL=gpt-4o-mini
   LLM_PROVIDER=openai
   ```

3. **El archivo `.env` ya está en `.gitignore`**, así que no se subirá al repositorio.

### Opción 2: Variables de entorno del sistema

#### Windows (PowerShell):
```powershell
$env:OPENAI_API_KEY="sk-proj-tu-api-key-aqui"
$env:OPENAI_MODEL="gpt-4o-mini"
$env:LLM_PROVIDER="openai"
```

#### Windows (CMD):
```cmd
set OPENAI_API_KEY=sk-proj-tu-api-key-aqui
set OPENAI_MODEL=gpt-4o-mini
set LLM_PROVIDER=openai
```

#### Windows (Permanente):
1. Busca "Variables de entorno" en el menú de inicio
2. Click en "Variables de entorno"
3. En "Variables de usuario", click en "Nueva"
4. Nombre: `OPENAI_API_KEY`
5. Valor: `sk-proj-tu-api-key-aqui`
6. Click en "Aceptar"

#### Linux/macOS:
```bash
export OPENAI_API_KEY="sk-proj-tu-api-key-aqui"
export OPENAI_MODEL="gpt-4o-mini"
export LLM_PROVIDER="openai"
```

Para hacerlo permanente en Linux/macOS, agrega las líneas a `~/.bashrc` o `~/.zshrc`.

### Opción 3: Cargar desde .env automáticamente

Si usas `python-dotenv`, puedes cargar el archivo `.env` automáticamente:

```bash
pip install python-dotenv
```

Luego en tu código Python:
```python
from dotenv import load_dotenv
load_dotenv()  # Carga variables desde .env
```

## ✅ Verificar que funciona

Después de configurar, verifica que la variable esté disponible:

**Windows (PowerShell):**
```powershell
echo $env:OPENAI_API_KEY
```

**Windows (CMD):**
```cmd
echo %OPENAI_API_KEY%
```

**Linux/macOS:**
```bash
echo $OPENAI_API_KEY
```

## 🚨 Si ya pusiste tu API key en un archivo

Si accidentalmente pusiste tu API key en un archivo que se subió a Git:

1. **Revoca la API key inmediatamente** en https://platform.openai.com/api-keys
2. **Genera una nueva API key**
3. **Configúrala usando uno de los métodos arriba**
4. **Elimina la key del archivo** y haz commit

## 📚 Más información

Ver `LLM_SETUP.md` para más detalles sobre configuración y troubleshooting.
