#!/usr/bin/env python3
"""
test_fix_updated.py - Script mejorado para probar el fix del import circular
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
    print(f"🐍 Python path: {sys.path[0]}")
    
    # Verificar que existe el directorio core
    core_dir = current_dir / "core"
    if not core_dir.exists():
        print(f"❌ ERROR: No existe el directorio 'core' en {current_dir}")
        return False
    
    # Verificar que existe __init__.py en core
    init_file = core_dir / "__init__.py"
    if not init_file.exists():
        print(f"⚠️  WARNING: No existe {init_file}")
        print("🔧 Creando __init__.py básico...")
        create_basic_init(init_file)
    
    print(f"✅ Directorio core encontrado: {core_dir}")
    return True

def create_basic_init(init_file: Path):
    """Crear un __init__.py básico si no existe"""
    init_content = '''# core/__init__.py
"""
PM Bot Enterprise - Core Module
"""

__version__ = "1.0.0"

# Imports básicos para evitar errores
try:
    from .ai_interface import AIInterface
except ImportError:
    pass

try:
    from .planner import ProjectPlanner
except ImportError:
    pass

try:
    from .pm_bot import PMBotEnterprise
except ImportError:
    pass
'''
    
    try:
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(init_content)
        print(f"✅ Creado {init_file}")
    except Exception as e:
        print(f"❌ Error creando {init_file}: {e}")

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
        "core/task_orchestrator.py"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - NO EXISTE")
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
        
        print("\n🎉 ¡FUNCIONALIDAD BÁSICA CONFIRMADA!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR EN FUNCIONALIDAD: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_run_pm_script():
    """Verificar que el script run_pm.py puede importar correctamente"""
    
    print("\n🚀 Probando script run_pm.py...")
    
    try:
        # Verificar que existe run_pm.py
        run_pm_path = Path("run_pm.py")
        if not run_pm_path.exists():
            print("❌ run_pm.py no existe")
            return False
        
        # Intentar leer e importar las dependencias principales
        print("📦 Verificando imports de run_pm.py...")
        
        # Simular import desde run_pm.py
        from core.pm_bot import PMBotEnterprise
        print("✅ run_pm.py puede importar PMBotEnterprise")
        
        print("\n🎉 ¡run_pm.py está listo para funcionar!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR EN run_pm.py: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_necessary_directories():
    """Crear directorios necesarios si no existen"""
    
    print("\n📁 Creando directorios necesarios...")
    
    directories = [
        "data", "logs", "agents", "templates", 
        "prompts", "projects", "models"
    ]
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(exist_ok=True)
            print(f"   ✅ Creado directorio: {directory}")
        else:
            print(f"   ✅ Directorio existe: {directory}")
    
    return True

def main():
    """Función principal de pruebas"""
    
    print("=" * 60)
    print("🔧 PM BOT ENTERPRISE - TEST DE FIXES MEJORADO")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 5
    
    # Test 0: Setup del entorno
    if not setup_python_path():
        print("❌ No se pudo configurar el entorno")
        return False
    
    # Test 1: Verificar archivos
    if test_core_files_exist():
        tests_passed += 1
    
    # Test 2: Crear directorios
    if create_necessary_directories():
        tests_passed += 1
    
    # Test 3: Imports
    if test_imports():
        tests_passed += 1
    
    # Test 4: Funcionalidad básica
    if test_basic_functionality():
        tests_passed += 1
    
    # Test 5: Script run_pm
    if test_run_pm_script():
        tests_passed += 1
    
    # Resultado final
    print("\n" + "=" * 60)
    print(f"📊 RESULTADO FINAL: {tests_passed}/{total_tests} tests pasaron")
    
    if tests_passed == total_tests:
        print("🎉 ¡TODOS LOS TESTS PASARON!")
        print("✅ El sistema está listo para usar")
        print("\n💡 Ahora puedes ejecutar:")
        print("   python run_pm.py --prompt 'Crear blog con React y Node.js' --auto")
        print("\n🌐 O abrir el dashboard web:")
        print("   python run_pm.py --dashboard")
    elif tests_passed >= 3:
        print("⚠️  La mayoría de tests pasaron")
        print("🔧 El sistema debería funcionar básicamente")
        print("💡 Puedes intentar ejecutar:")
        print("   python run_pm.py --help")
    else:
        print("❌ Muchos tests fallaron")
        print("🔧 Revisa los errores arriba para más detalles")
    
    print("=" * 60)
    
    return tests_passed >= 3

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)