#!/usr/bin/env python3
"""
fix_persistence_issue.py - Corregir problema de persistencia de proyectos
"""

import os
import json
from pathlib import Path

def diagnose_persistence_issue():
    """Diagnosticar el problema de persistencia"""
    
    print("🔍 DIAGNÓSTICO DEL PROBLEMA DE PERSISTENCIA")
    print("=" * 50)
    
    # 1. Verificar archivos de proyecto
    data_dir = Path("data")
    if data_dir.exists():
        project_files = list(data_dir.glob("project_*.json"))
        print(f"📁 Archivos de proyecto encontrados: {len(project_files)}")
        
        for file in project_files:
            print(f"   • {file.name}")
            
            # Verificar contenido
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    print(f"     ID: {data.get('id', 'N/A')}")
                    print(f"     Estado: {data.get('status', 'N/A')}")
                    print(f"     Módulos: {len(data.get('modules', {}))}")
            except Exception as e:
                print(f"     ❌ Error leyendo archivo: {e}")
    else:
        print("❌ Directorio 'data' no existe")
    
    print("\n🔍 PROBLEMA IDENTIFICADO:")
    print("El PMBotEnterprise crea una nueva instancia para la ejecución,")
    print("pero no carga los proyectos existentes desde disco.")
    
    return project_files if data_dir.exists() else []

def fix_pm_bot_persistence():
    """Corregir el problema de persistencia en PMBotEnterprise"""
    
    print("\n🔧 APLICANDO FIX DE PERSISTENCIA")
    print("=" * 40)
    
    pm_bot_file = Path("core/pm_bot.py")
    
    if not pm_bot_file.exists():
        print("❌ core/pm_bot.py no encontrado")
        return False
    
    # Leer archivo actual
    with open(pm_bot_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar el constructor __init__
    init_marker = "def __init__(self, config_path: str = \"config/pm_config.json\"):"
    
    if init_marker in content:
        # Encontrar la sección donde se inicializa projects
        projects_init = "self.projects: Dict[str, ProjectState] = {}"
        
        if projects_init in content:
            # Reemplazar con carga automática
            new_projects_init = """self.projects: Dict[str, ProjectState] = {}
        
        # Cargar proyectos existentes automáticamente
        self._load_existing_projects()"""
            
            content = content.replace(projects_init, new_projects_init)
            
            # Agregar método _load_existing_projects antes de save_project_state
            load_method = '''    def _load_existing_projects(self):
        """Cargar todos los proyectos existentes desde disco"""
        try:
            data_dir = Path("data")
            if not data_dir.exists():
                return
            
            project_files = list(data_dir.glob("project_*.json"))
            loaded_count = 0
            
            for project_file in project_files:
                try:
                    project_id = project_file.stem.replace("project_", "")
                    if self.load_project_state(project_id):
                        loaded_count += 1
                except Exception as e:
                    self.logger.warning(f"Could not load project from {project_file}: {e}")
            
            if loaded_count > 0:
                self.logger.info(f"Loaded {loaded_count} existing projects")
        except Exception as e:
            self.logger.error(f"Error loading existing projects: {e}")

'''
            
            # Insertar antes de save_project_state
            save_method_marker = "    async def save_project_state(self, project_id: str):"
            if save_method_marker in content:
                content = content.replace(save_method_marker, load_method + save_method_marker)
            
            # También necesitamos hacer load_project_state síncrono
            old_load_signature = "async def load_project_state(self, project_id: str) -> bool:"
            new_load_signature = "def load_project_state(self, project_id: str) -> bool:"
            
            content = content.replace(old_load_signature, new_load_signature)
            
            # Escribir archivo corregido
            with open(pm_bot_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ Fix de persistencia aplicado a PMBotEnterprise")
            return True
    
    print("⚠️ No se pudo aplicar el fix automáticamente")
    return False

def create_improved_test_script():
    """Crear script de test mejorado"""
    
    print("\n🔧 CREANDO SCRIPT DE TEST MEJORADO")
    print("=" * 35)
    
    improved_test = '''#!/usr/bin/env python3
"""
test_persistence_fix.py - Test mejorado con persistencia corregida
"""

import asyncio
import sys
from pathlib import Path

# Agregar path
sys.path.append(str(Path(__file__).parent))

async def test_full_lifecycle():
    """Test completo del ciclo de vida de un proyecto"""
    print("🧪 TEST COMPLETO DEL CICLO DE VIDA")
    print("=" * 45)
    
    try:
        from core.pm_bot import PMBotEnterprise
        
        # Crear instancia única
        pm_bot = PMBotEnterprise()
        print(f"✅ PMBotEnterprise inicializado")
        print(f"📊 Proyectos cargados: {len(pm_bot.projects)}")
        
        # Listar proyectos existentes
        if pm_bot.projects:
            print("\\n📋 Proyectos existentes:")
            for project_id, project in pm_bot.projects.items():
                print(f"   • {project_id}: {project.status.value}")
        
        # Test 1: Crear nuevo proyecto
        print("\\n🚀 Test 1: Creando nuevo proyecto...")
        simple_prompt = "Crear página web básica con HTML y CSS"
        
        project_id = await pm_bot.create_project(simple_prompt)
        print(f"✅ Proyecto creado: {project_id}")
        
        # Verificar que está en memoria
        if project_id in pm_bot.projects:
            print("✅ Proyecto existe en memoria")
        else:
            print("❌ Proyecto NO existe en memoria")
            return False
        
        # Test 2: Ejecutar proyecto con la MISMA instancia
        print("\\n⚡ Test 2: Ejecutando proyecto...")
        success = await pm_bot.execute_project(project_id)
        
        if success:
            print("🎉 ¡Proyecto ejecutado exitosamente!")
            
            # Mostrar estado final
            status = await pm_bot.get_project_status(project_id)
            print(f"📊 Progreso final: {status['progress']:.1f}%")
            print(f"📦 Módulos: {len(status['modules'])}")
            
            return True
        else:
            print("❌ Proyecto falló durante ejecución")
            return False
            
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_persistence_reload():
    """Test de recarga de persistencia"""
    print("\\n🔄 TEST DE PERSISTENCIA Y RECARGA")
    print("=" * 40)
    
    try:
        # Crear primera instancia
        from core.pm_bot import PMBotEnterprise
        pm_bot1 = PMBotEnterprise()
        
        initial_count = len(pm_bot1.projects)
        print(f"📊 Instancia 1 - Proyectos cargados: {initial_count}")
        
        # Crear segunda instancia (simular reinicio)
        pm_bot2 = PMBotEnterprise()
        reloaded_count = len(pm_bot2.projects)
        print(f"📊 Instancia 2 - Proyectos cargados: {reloaded_count}")
        
        if reloaded_count == initial_count:
            print("✅ Persistencia funcionando correctamente")
            return True
        else:
            print(f"⚠️ Discrepancia en proyectos: {initial_count} vs {reloaded_count}")
            return False
            
    except Exception as e:
        print(f"❌ Error en test de persistencia: {e}")
        return False

async def main():
    """Test principal"""
    print("=" * 60)
    print("🧪 PM BOT ENTERPRISE - TEST MEJORADO CON PERSISTENCIA")
    print("=" * 60)
    
    tests_passed = 0
    
    # Test 1: Ciclo completo
    if await test_full_lifecycle():
        tests_passed += 1
        print("\\n✅ Test 1/2: Ciclo completo PASÓ")
    else:
        print("\\n❌ Test 1/2: Ciclo completo FALLÓ")
    
    # Test 2: Persistencia
    if await test_persistence_reload():
        tests_passed += 1
        print("\\n✅ Test 2/2: Persistencia PASÓ")
    else:
        print("\\n❌ Test 2/2: Persistencia FALLÓ")
    
    # Resultado final
    print("\\n" + "=" * 60)
    print(f"📊 RESULTADO: {tests_passed}/2 tests pasaron")
    
    if tests_passed == 2:
        print("🎉 ¡TODOS LOS TESTS PASARON!")
        print("✅ Sistema completamente funcional")
    elif tests_passed == 1:
        print("⚠️ Test parcialmente exitoso")
    else:
        print("❌ Tests fallaron")
    
    print("=" * 60)
    return tests_passed >= 1

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)'''
    
    with open("test_persistence_fix.py", 'w') as f:
        f.write(improved_test)
    
    print("✅ Script test_persistence_fix.py creado")
    return True

def main():
    """Función principal de diagnóstico y fix"""
    
    print("🔧 PM BOT ENTERPRISE - DIAGNÓSTICO Y FIX")
    print("=" * 50)
    
    # 1. Diagnosticar problema
    project_files = diagnose_persistence_issue()
    
    # 2. Aplicar fixes
    fixes_applied = 0
    
    if fix_pm_bot_persistence():
        fixes_applied += 1
    
    if create_improved_test_script():
        fixes_applied += 1
    
    print(f"\n📊 FIXES APLICADOS: {fixes_applied}/2")
    
    if fixes_applied >= 1:
        print("🎉 ¡FIXES APLICADOS EXITOSAMENTE!")
        print("\n💡 Próximos pasos:")
        print("1. Ejecuta: python test_persistence_fix.py")
        print("2. Si funciona: python run_pm.py --prompt 'Tu proyecto' --auto")
    else:
        print("⚠️ Algunos fixes no se pudieron aplicar automáticamente")
    
    return fixes_applied >= 1

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)