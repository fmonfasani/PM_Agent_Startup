#!/usr/bin/env python3
"""
quick_test_post_ollama.py - Test rápido después de configurar Ollama
"""

import asyncio
import sys
import os
from pathlib import Path

# Agregar path
sys.path.append(str(Path(__file__).parent))

async def test_ai_interface():
    """Test básico de AIInterface"""
    print("🧪 Testeando AIInterface...")
    
    try:
        from core.ai_interface import AIInterface
        ai = AIInterface()
        
        # Test de health check
        health = await ai.health_check()
        print(f"🏥 Health check: {health['local']['available']}")
        print(f"📦 Modelos locales: {len(health['local']['models'])}")
        
        for model in health['local']['models']:
            print(f"   • {model}")
        
        # Test de generación simple
        print("\n🤖 Probando generación...")
        response = await ai.generate_response(
            "Responde con una sola palabra: 'funcionando'", 
            max_tokens=10
        )
        print(f"✅ Respuesta: {response}")
        return True
        
    except Exception as e:
        print(f"❌ Error en AIInterface: {e}")
        return False

async def test_simple_project():
    """Test de creación de proyecto simple"""
    print("\n🚀 Testeando creación de proyecto...")
    
    try:
        from core.pm_bot import PMBotEnterprise
        
        pm_bot = PMBotEnterprise()
        
        # Proyecto muy simple para test
        simple_prompt = "Crear página web básica con HTML y CSS"
        
        print(f"📝 Creando proyecto: {simple_prompt}")
        project_id = await pm_bot.create_project(simple_prompt)
        
        print(f"✅ Proyecto creado: {project_id}")
        
        # Obtener estado
        status = await pm_bot.get_project_status(project_id)
        print(f"📊 Estado: {status['status']}")
        print(f"📦 Módulos: {len(status['modules'])}")
        
        return True, project_id
        
    except Exception as e:
        print(f"❌ Error creando proyecto: {e}")
        import traceback
        traceback.print_exc()
        return False, None

async def test_project_execution(project_id):
    """Test de ejecución de proyecto"""
    print(f"\n⚡ Testeando ejecución de proyecto {project_id}...")
    
    try:
        from core.pm_bot import PMBotEnterprise
        
        pm_bot = PMBotEnterprise()
        
        print("🔥 Ejecutando proyecto...")
        success = await pm_bot.execute_project(project_id)
        
        if success:
            print("🎉 ¡Proyecto ejecutado exitosamente!")
            
            # Mostrar estado final
            status = await pm_bot.get_project_status(project_id)
            print(f"📊 Progreso final: {status['progress']:.1f}%")
            
            return True
        else:
            print("❌ Proyecto falló durante ejecución")
            return False
            
    except Exception as e:
        print(f"❌ Error ejecutando proyecto: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Test principal"""
    print("=" * 60)
    print("🧪 PM BOT ENTERPRISE - TEST POST-OLLAMA")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: AIInterface
    if await test_ai_interface():
        tests_passed += 1
        print("✅ Test 1/3: AIInterface PASÓ")
    else:
        print("❌ Test 1/3: AIInterface FALLÓ")
    
    # Test 2: Creación de proyecto
    success, project_id = await test_simple_project()
    if success:
        tests_passed += 1
        print("✅ Test 2/3: Creación de proyecto PASÓ")
        
        # Test 3: Ejecución de proyecto (solo si la creación funcionó)
        if await test_project_execution(project_id):
            tests_passed += 1
            print("✅ Test 3/3: Ejecución de proyecto PASÓ")
        else:
            print("❌ Test 3/3: Ejecución de proyecto FALLÓ")
    else:
        print("❌ Test 2/3: Creación de proyecto FALLÓ")
        print("⏭️ Saltando test de ejecución")
    
    # Resultado final
    print("\n" + "=" * 60)
    print(f"📊 RESULTADO: {tests_passed}/{total_tests} tests pasaron")
    
    if tests_passed == total_tests:
        print("🎉 ¡TODOS LOS TESTS PASARON!")
        print("✅ El sistema PM Bot está completamente funcional")
        print("\n💡 Ahora puedes usar:")
        print("   python run_pm.py --prompt 'Tu proyecto aquí' --auto")
        print("   python run_pm.py --dashboard")
    elif tests_passed >= 1:
        print("⚠️ Tests parcialmente exitosos")
        print("🔧 El sistema básico funciona, pero hay issues en ejecución")
    else:
        print("❌ Todos los tests fallaron")
        print("🔧 Revisa la configuración")
    
    print("=" * 60)
    return tests_passed >= 1

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)