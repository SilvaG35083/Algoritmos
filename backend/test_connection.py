import os
from dotenv import load_dotenv, find_dotenv
import google.generativeai as genai
import asyncio

async def test():
    print("--- INICIANDO DIAGNÓSTICO ---")
    
    # 1. Buscar .env
    env_file = find_dotenv()
    if env_file:
        print(f"✅ Archivo .env encontrado en: {env_file}")
        load_dotenv(env_file)
    else:
        print("❌ NO se encontró el archivo .env")
        return

    # 2. Verificar API Key
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ La variable GEMINI_API_KEY está vacía o no existe.")
        return
    else:
        # Mostramos solo los últimos 4 caracteres por seguridad
        print(f"✅ API Key detectada: ...{api_key[-4:]}")

    # 3. Probar Conexión
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        print("📡 Enviando 'Hola' a Gemini...")
        
        response = await model.generate_content_async("Responde solo con la palabra: FUNCIONA")
        print(f"🎉 RESPUESTA RECIBIDA: {response.text}")
        
    except Exception as e:
        print(f"❌ ERROR CONECTANDO A GOOGLE: {e}")

if __name__ == "__main__":
    asyncio.run(test())