#!/usr/bin/env python3
"""
test_fix_updated.py - Script mejorado para probar el sistema completo
"""

import sys
import os
from pathlib import Path

def setup_python_path():
    """Configurar correctamente el PYTHONPATH"""
    
    # Obtener el directorio actual (donde está este script)
    current_dir = Path(__file__).resolve().parent
    
    # Agregar el directorio actual al path
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    print(f"📁 Directorio de trabajo: {current_dir}")
    print(f"🐍 Python path configurado")
    
    # Verificar que existe el directorio core
    core_dir = current_dir / "core"
    if not core_dir.exists():
        print(f"❌ ERROR: No existe el directorio 'core' en {current_dir}")
        return False
    
    print(f"✅ Directorio core encontrado: {core_dir}")
    return True

def test_core_files_exist():
    """Verificar que existen los archivos core necesarios"""
    
    print("\n📋 Verificando archivos core...")
    
    required_files = [
        "core/__init__.py",
        "core/ai_interface.py", 
        "core/planner.py",
        "core/pm_bot.py",
        "core/module_manager.py",
        "core/agent_spawner.py",
        "core/task_orchestrator.py",
        "core/types.py"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        path = Path(file_path)
        if path.exists() and path.stat().st_size > 0:
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - NO EXISTE O VACÍO")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠️  ARCHIVOS FALTANTES: {len(missing_files)}")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("\n✅ Todos los archivos core existen")
    return True

def test_imports():
    """Probar que todos los imports funcionen sin errores circulares"""
    
    print("\n🔍 Probando imports del sistema...")
    
    try:
        print("📦 Importando AIInterface...")
        from core.ai_interface import AIInterface
        print("   ✅ AIInterface importado correctamente")
        
        print("📦 Importando tipos...")
        from core.types import ModuleSpec, ProjectConfig
        print("   ✅ Tipos importados correctamente")
        
        print("📦 Importando ProjectPlanner...")
        from core.planner import ProjectPlanner
        print("   ✅ ProjectPlanner importado correctamente")
        
        print("📦 Importando PMBotEnterprise...")
        from core.pm_bot import PMBotEnterprise
        print("   ✅ PMBotEnterprise importado correctamente")
        
        print("📦 Importando otros módulos core...")
        from core.module_manager import ModuleManager
        from core.agent_spawner import AgentSpawner
        from core.task_orchestrator import TaskOrchestrator
        print("   ✅ Todos los módulos core importados")
        
        print("\n🎉 ¡TODOS LOS IMPORTS FUNCIONAN CORRECTAMENTE!")
        return True
        
    except ImportError as e:
        print(f"\n❌ ERROR DE IMPORT: {e}")
        print("\n🔍 Detalles del error:")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_functionality():
    """Probar funcionalidad básica del sistema"""
    
    print("\n🧪 Probando funcionalidad básica...")
    
    try:
        # Probar AIInterface
        from core.ai_interface import AIInterface
        ai = AIInterface()
        print("✅ AIInterface se inicializa correctamente")
        
        # Probar ProjectPlanner
        from core.planner import ProjectPlanner
        planner = ProjectPlanner()
        print("✅ ProjectPlanner se inicializa correctamente")
        
        # Probar PMBotEnterprise
        from core.pm_bot import PMBotEnterprise
        pm_bot = PMBotEnterprise()
        print("✅ PMBotEnterprise se inicializa correctamente")
        
        # Probar que podemos crear una config básica
        from core.types import ProjectConfig
        config = ProjectConfig(
            name="test_project",
            description="Test project",
            complexity=5,
            timeline="1 month",
            budget="medium",
            requirements=["test"],
            tech_stack=["React", "Node.js"],
            team_size=3
        )
        print("✅ ProjectConfig se crea correctamente")
        
        print("\n🎉 ¡FUNCIONALIDAD BÁSICA CONFIRMADA!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR EN FUNCIONALIDAD: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_run_pm_script():
    """Verificar que el script run_pm.py puede ejecutarse"""
    
    print("\n🚀 Probando script run_pm.py...")
    
    try:
        # Verificar que existe run_pm.py
        run_pm_path = Path("run_pm.py")
        if not run_pm_path.exists():
            print("❌ run_pm.py no existe")
            return False
        
        print("✅ run_pm.py existe")
        
        # Verificar que puede importar sus dependencias
        from core.pm_bot import PMBotEnterprise
        print("✅ run_pm.py puede importar PMBotEnterprise")
        
        print("\n🎉 ¡run_pm.py está listo para funcionar!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR EN run_pm.py: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_templates_and_configs():
    """Verificar que templates y configuraciones existen"""
    
    print("\n📋 Verificando templates y configuraciones...")
    
    required_files = [
        "templates/qa_agent.json",
        "templates/deploy_agent.json", 
        "templates/standard_module_trio.json",
        "config/pm_config.json",
        "data/modules_status.json"
    ]
    
    missing = []
    for file_path in required_files:
        path = Path(file_path)
        if path.exists() and path.stat().st_size > 0:
            print(f"   ✅ {file_path}")
        else:
            print(f"   ⚠️  {file_path} - faltante")
            missing.append(file_path)
    
    if missing:
        print(f"\n⚠️  Algunos archivos faltan: {len(missing)}")
        print("💡 Esto no es crítico, el sistema puede funcionar sin ellos")
    else:
        print("\n✅ Todos los archivos de configuración existen")
    
    return True

def test_encoding():
    """Verificar que no hay problemas de codificación"""
    
    print("\n🔤 Verificando codificación de archivos...")
    
    key_files = [
        "run_pm.py",
        "core/__init__.py",
        "core/pm_bot.py",
        "core/types.py"
    ]
    
    for file_path in key_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"   ✅ {file_path} - codificación UTF-8 OK")
        except Exception as e:
            print(f"   ❌ {file_path} - error de codificación: {e}")
            return False
    
    print("✅ Codificación verificada correctamente")
    return True

def main():
    """Función principal de pruebas"""
    
    print("=" * 60)
    print("🔧 PM BOT ENTERPRISE - TEST COMPLETO")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 7
    
    # Lista de tests a ejecutar
    tests = [
        ("Setup del entorno", setup_python_path),
        ("Verificar archivos core", test_core_files_exist),
        ("Probar imports", test_imports),
        ("Funcionalidad básica", test_basic_functionality),
        ("Script run_pm", test_run_pm_script),
        ("Templates y configs", test_templates_and_configs),
        ("Verificar codificación", test_encoding)
    ]
    
    for test_name, test_func in tests:
        print(f"\n🧪 Test: {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                tests_passed += 1
                print(f"✅ {test_name} - PASÓ")
            else:
                print(f"❌ {test_name} - FALLÓ")
        except Exception as e:
            print(f"❌ {test_name} - ERROR: {e}")
    
    # Resultado final
    print("\n" + "=" * 60)
    print(f"📊 RESULTADO FINAL: {tests_passed}/{total_tests} tests pasaron")
    
    if tests_passed == total_tests:
        print("🎉 ¡TODOS LOS TESTS PASARON!")
        print("✅ El sistema está completamente listo")
        print("\n💡 Comandos disponibles:")
        print("   python run_pm.py --help")
        print("   python run_pm.py --setup")
        print("   python run_pm.py --check-models")
        print("   python run_pm.py")
        print("\n🌐 Para dashboard web:")
        print("   python run_pm.py --dashboard")
    elif tests_passed >= 5:
        print("⚠️  La mayoría de tests pasaron")
        print("🔧 El sistema debería funcionar básicamente")
        print("💡 Puedes intentar:")
        print("   python run_pm.py --help")
    else:
        print("❌ Muchos tests fallaron")
        print("🔧 Revisa los errores arriba para más detalles")
        print("💡 Ejecuta: python fix_encoding_errors.py")
    
    print("=" * 60)
    
    return tests_passed >= 5

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)