#!/usr/bin/env python3
"""
check_ollama.py - Script para verificar y configurar Ollama
"""

import subprocess
import json
import sys
import requests
import time

def check_ollama_running():
    """Verificar si Ollama está ejecutándose"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def start_ollama():
    """Intentar iniciar Ollama"""
    try:
        if sys.platform == "win32":
            subprocess.Popen(["ollama", "serve"], shell=True)
        else:
            subprocess.Popen(["ollama", "serve"])
        
        print("🔄 Iniciando Ollama...")
        time.sleep(5)
        return check_ollama_running()
    except:
        return False

def check_models():
    """Verificar modelos disponibles"""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = response.json()
            return [model['name'] for model in models.get('models', [])]
        return []
    except:
        return []

def pull_model(model_name):
    """Descargar modelo si no existe"""
    try:
        print(f"📥 Descargando modelo {model_name}...")
        result = subprocess.run(
            ["ollama", "pull", model_name], 
            capture_output=True, text=True
        )
        return result.returncode == 0
    except:
        return False

def main():
    print("🔍 Verificando configuración de Ollama...")
    
    # 1. Verificar si Ollama está corriendo
    if not check_ollama_running():
        print("❌ Ollama no está ejecutándose")
        if start_ollama():
            print("✅ Ollama iniciado correctamente")
        else:
            print("❌ No se pudo iniciar Ollama")
            print("💡 Instala Ollama desde: https://ollama.ai")
            return False
    else:
        print("✅ Ollama está ejecutándose")
    
    # 2. Verificar modelos
    models = check_models()
    print(f"📦 Modelos disponibles: {len(models)}")
    
    required_models = [
        "llama3.2:latest",
        "qwen2.5-coder:7b"
    ]
    
    # 3. Descargar modelos necesarios
    for model in required_models:
        if not any(model in m for m in models):
            print(f"⬇️ Descargando {model}...")
            if pull_model(model):
                print(f"✅ {model} descargado")
            else:
                print(f"❌ Error descargando {model}")
        else:
            print(f"✅ {model} ya disponible")
    
    # 4. Verificar final
    final_models = check_models()
    print(f"\n📋 Modelos finales disponibles: {len(final_models)}")
    for model in final_models:
        print(f"   • {model}")
    
    return len(final_models) > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)