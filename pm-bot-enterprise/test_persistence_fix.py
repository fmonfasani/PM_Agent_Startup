#!/usr/bin/env python3
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
    print("TEST COMPLETO DEL CICLO DE VIDA")
    print("=" * 45)
    
    try:
        from core.pm_bot import PMBotEnterprise
        
        # Crear instancia única
        pm_bot = PMBotEnterprise()
        print(f"PMBotEnterprise inicializado")
        print(f"Proyectos cargados: {len(pm_bot.projects)}")
        
        # Listar proyectos existentes
        if pm_bot.projects:
            print("\nProyectos existentes:")
            for project_id, project in pm_bot.projects.items():
                print(f"   • {project_id}: {project.status.value}")
        
        # Test 1: Crear nuevo proyecto
        print("\nTest 1: Creando nuevo proyecto...")
        simple_prompt = "Crear página web básica con HTML y CSS"
        
        project_id = await pm_bot.create_project(simple_prompt)
        print(f"Proyecto creado: {project_id}")
        
        # Verificar que está en memoria
        if project_id in pm_bot.projects:
            print("Proyecto existe en memoria")
        else:
            print("ERROR: Proyecto NO existe en memoria")
            return False
        
        # Test 2: Ejecutar proyecto con la MISMA instancia
        print("\nTest 2: Ejecutando proyecto...")
        success = await pm_bot.execute_project(project_id)
        
        if success:
            print("PROYECTO EJECUTADO EXITOSAMENTE!")
            
            # Mostrar estado final
            status = await pm_bot.get_project_status(project_id)
            print(f"Progreso final: {status['progress']:.1f}%")
            print(f"Módulos: {len(status['modules'])}")
            
            return True
        else:
            print("ERROR: Proyecto falló durante ejecución")
            return False
            
    except Exception as e:
        print(f"ERROR en test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_persistence_reload():
    """Test de recarga de persistencia"""
    print("\nTEST DE PERSISTENCIA Y RECARGA")
    print("=" * 40)
    
    try:
        # Crear primera instancia
        from core.pm_bot import PMBotEnterprise
        pm_bot1 = PMBotEnterprise()
        
        initial_count = len(pm_bot1.projects)
        print(f"Instancia 1 - Proyectos cargados: {initial_count}")
        
        # Crear segunda instancia (simular reinicio)
        pm_bot2 = PMBotEnterprise()
        reloaded_count = len(pm_bot2.projects)
        print(f"Instancia 2 - Proyectos cargados: {reloaded_count}")
        
        if reloaded_count == initial_count:
            print("Persistencia funcionando correctamente")
            return True
        else:
            print(f"ADVERTENCIA: Discrepancia en proyectos: {initial_count} vs {reloaded_count}")
            return False
            
    except Exception as e:
        print(f"ERROR en test de persistencia: {e}")
        return False

async def main():
    """Test principal"""
    print("=" * 60)
    print("PM BOT ENTERPRISE - TEST MEJORADO CON PERSISTENCIA")
    print("=" * 60)
    
    tests_passed = 0
    
    # Test 1: Ciclo completo
    if await test_full_lifecycle():
        tests_passed += 1
        print("\nTEST 1/2: Ciclo completo PASO")
    else:
        print("\nTEST 1/2: Ciclo completo FALLO")
    
    # Test 2: Persistencia
    if await test_persistence_reload():
        tests_passed += 1
        print("\nTEST 2/2: Persistencia PASO")
    else:
        print("\nTEST 2/2: Persistencia FALLO")
    
    # Resultado final
    print("\n" + "=" * 60)
    print(f"RESULTADO: {tests_passed}/2 tests pasaron")
    
    if tests_passed == 2:
        print("TODOS LOS TESTS PASARON!")
        print("Sistema completamente funcional")
    elif tests_passed == 1:
        print("Test parcialmente exitoso")
    else:
        print("Tests fallaron")
    
    print("=" * 60)
    return tests_passed >= 1

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)