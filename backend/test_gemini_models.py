"""Script para verificar modelos disponibles de Gemini."""

import os
import sys
from pathlib import Path

# Cargar variables de entorno desde .env si existe
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"✅ Cargado archivo .env desde: {env_path}")
    else:
        print(f"⚠️ Archivo .env no encontrado en: {env_path}")
        print("   Intentando cargar desde variables de entorno del sistema...")
except ImportError:
    print("⚠️ python-dotenv no está instalado. Solo se cargarán variables de entorno del sistema.")
    print("   Instala con: pip install python-dotenv")

try:
    import google.generativeai as genai
except ImportError:
    print("❌ google-generativeai no está instalado. Instala con: pip install google-generativeai")
    sys.exit(1)

# Cargar API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("\n❌ GEMINI_API_KEY no está configurada.")
    print("\nOpciones:")
    print("1. Agrega GEMINI_API_KEY=tu-key-aqui en el archivo backend/.env")
    print("2. O configura la variable de entorno:")
    print("   Windows PowerShell: $env:GEMINI_API_KEY='tu-key-aqui'")
    print("   Windows CMD: set GEMINI_API_KEY=tu-key-aqui")
    print("   Linux/macOS: export GEMINI_API_KEY='tu-key-aqui'")
    sys.exit(1)

print(f"✅ API Key encontrada (primeros 10 caracteres: {api_key[:10]}...)\n")

genai.configure(api_key=api_key)

print("🔍 Buscando modelos disponibles de Gemini...\n")

try:
    models = genai.list_models()
    
    available_models = []
    for model in models:
        if 'generateContent' in model.supported_generation_methods:
            available_models.append(model.name)
            print(f"✅ {model.name}")
            if model.display_name:
                print(f"   Display: {model.display_name}")
            print()
    
    if not available_models:
        print("❌ No se encontraron modelos con soporte para generateContent")
    else:
        print(f"\n📋 Modelos disponibles ({len(available_models)}):")
        for model in available_models:
            # Extraer solo el nombre del modelo (sin la ruta completa)
            model_name = model.split('/')[-1] if '/' in model else model
            print(f"   - {model_name}")
        
        print("\n💡 Sugerencia: Usa uno de estos nombres en GEMINI_MODEL:")
        print("   Ejemplo: GEMINI_MODEL=gemini-1.5-flash")
        
except Exception as e:
    print(f"❌ Error al listar modelos: {e}")
    print("\n💡 Intenta usar estos modelos comunes:")
    print("   - gemini-1.5-flash")
    print("   - gemini-1.5-pro")
    print("   - gemini-pro")

