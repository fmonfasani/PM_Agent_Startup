#!/usr/bin/env python3
"""
fix_project_errors.py - Script para corregir errores identificados
"""

import os
import json
import shutil
from pathlib import Path

def fix_file_locations():
    """Corregir ubicaciones de archivos"""
    print("🔧 Corrigiendo ubicaciones de archivos...")
    
    # Mover test_fix.py a la raíz si existe en core/
    test_fix_core = Path("core/test_fix.py")
    if test_fix_core.exists():
        shutil.move(str(test_fix_core), "test_fix_updated.py")
        print("✅ Movido core/test_fix.py a test_fix_updated.py")
    
    # Renombrar setup.py a quick_setup.py
    if Path("setup.py").exists() and not Path("quick_setup.py").exists():
        shutil.move("setup.py", "quick_setup.py")
        print("✅ Renombrado setup.py a quick_setup.py")

def fix_core_types():
    """Corregir imports en core/types.py"""
    print("🔧 Corrigiendo core/types.py...")
    
    types_file = Path("core/types.py")
    if types_file.exists():
        with open(types_file, 'r') as f:
            content = f.read()
        
        # Añadir import de datetime si no existe
        if "from datetime import datetime" not in content:
            # Buscar línea de dataclass import
            lines = content.split('\n')
            new_lines = []
            added_datetime = False
            
            for line in lines:
                if line.startswith("from dataclasses import") and not added_datetime:
                    new_lines.append("from datetime import datetime")
                    new_lines.append(line)
                    added_datetime = True
                else:
                    new_lines.append(line)
            
            with open(types_file, 'w') as f:
                f.write('\n'.join(new_lines))
            print("✅ Añadido import datetime a core/types.py")

def fix_run_pm():
    """Corregir imports en run_pm.py"""
    print("🔧 Corrigiendo run_pm.py...")
    
    run_pm_file = Path("run_pm.py")
    if run_pm_file.exists():
        with open(run_pm_file, 'r') as f:
            content = f.read()
        
        # Reemplazar import directo por import con try/catch
        old_import = "from core.pm_bot import PMBotEnterprise"
        new_import = """try:
    from core.pm_bot import PMBotEnterprise
except ImportError as e:
    print(f"❌ Error importing PMBotEnterprise: {e}")
    print("💡 Ejecuta primero: python quick_setup.py")
    sys.exit(1)"""
        
        if old_import in content and "try:" not in content:
            content = content.replace(old_import, new_import)
            
            with open(run_pm_file, 'w') as f:
                f.write(content)
            print("✅ Corregido import en run_pm.py")

def create_missing_template_files():
    """Crear archivos de template faltantes"""
    print("🔧 Creando archivos de template faltantes...")
    
    templates = {
        "templates/qa_agent.json": {
            "name": "qa_specialist",
            "role": "qa",
            "personality": "Meticulous quality assurance specialist",
            "expertise": [
                "Test Automation", "Unit Testing", "Integration Testing",
                "E2E Testing", "Performance Testing", "Security Testing"
            ],
            "tools": ["jest", "cypress", "postman", "k6"],
            "model": "claude-3-5-sonnet",
            "temperature": 0.2,
            "max_tokens": 2000
        },
        
        "templates/deploy_agent.json": {
            "name": "devops_specialist", 
            "role": "devops",
            "personality": "Systematic DevOps engineer focused on automation",
            "expertise": [
                "Docker", "Kubernetes", "CI/CD", "AWS", "Terraform",
                "Monitoring", "Security", "Performance Optimization"
            ],
            "tools": ["docker", "kubectl", "terraform", "aws-cli"],
            "model": "qwen2.5-coder:7b",
            "temperature": 0.1,
            "max_tokens": 2500
        }
    }
    
    for file_path, content in templates.items():
        path = Path(file_path)
        if not path.exists() or path.stat().st_size == 0:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as f:
                json.dump(content, f, indent=2)
            print(f"✅ Creado {file_path}")

def create_missing_data_files():
    """Crear archivos de data faltantes"""
    print("🔧 Creando archivos de data faltantes...")
    
    data_files = {
        "data/modules_status.json": {},
        "agents/auth_agents.json": [],
        "agents/cart_agents.json": [],
        "agents/profile_agents.json": [],
        "models/ollama_models.json": {
            "available_models": [],
            "last_update": "2024-01-01T00:00:00"
        }
    }
    
    for file_path, content in data_files.items():
        path = Path(file_path)
        if not path.exists() or path.stat().st_size == 0:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as f:
                json.dump(content, f, indent=2)
            print(f"✅ Creado {file_path}")

def fix_core_init():
    """Corregir core/__init__.py para evitar imports circulares"""
    print("🔧 Corrigiendo core/__init__.py...")
    
    init_file = Path("core/__init__.py")
    if init_file.exists():
        # Crear versión mejorada sin imports circulares
        init_content = '''# core/__init__.py
"""
PM Bot Enterprise - Core Module
"""

__version__ = "1.0.0"

# Import solo lo esencial para evitar circulares
try:
    from .ai_interface import AIInterface
    from .planner import ProjectPlanner, ModuleSpec  
    from .pm_bot import PMBotEnterprise, ProjectConfig, ProjectStatus
    
    __all__ = [
        'AIInterface',
        'ProjectPlanner',
        'ModuleSpec', 
        'PMBotEnterprise',
        'ProjectConfig',
        'ProjectStatus'
    ]
    
except ImportError as e:
    print(f"⚠️ Warning importing core modules: {e}")
    __all__ = []
'''
        
        with open(init_file, 'w') as f:
            f.write(init_content)
        print("✅ Corregido core/__init__.py")

def validate_fixes():
    """Validar que las correcciones funcionan"""
    print("🔍 Validando correcciones...")
    
    # Verificar archivos clave
    key_files = [
        "core/__init__.py",
        "core/types.py", 
        "core/pm_bot.py",
        "core/planner.py",
        "run_pm.py",
        "templates/qa_agent.json",
        "templates/deploy_agent.json"
    ]
    
    missing = []
    for file_path in key_files:
        if not Path(file_path).exists():
            missing.append(file_path)
    
    if missing:
        print(f"❌ Archivos faltantes: {missing}")
        return False
    
    print("✅ Todos los archivos clave existen")
    
    # Intentar import básico
    try:
        import sys
        sys.path.append('.')
        from core.ai_interface import AIInterface
        print("✅ Import de AIInterface funciona")
        return True
    except Exception as e:
        print(f"❌ Error en import: {e}")
        return False

def main():
    """Función principal de corrección"""
    print("=" * 60)
    print("🛠️  PM BOT ENTERPRISE - CORRECCIÓN DE ERRORES")
    print("=" * 60)
    
    fixes = [
        ("Corrigiendo ubicaciones de archivos", fix_file_locations),
        ("Corrigiendo core/types.py", fix_core_types),
        ("Corrigiendo run_pm.py", fix_run_pm),
        ("Creando templates faltantes", create_missing_template_files),
        ("Creando archivos de data", create_missing_data_files),
        ("Corrigiendo core/__init__.py", fix_core_init),
        ("Validando correcciones", validate_fixes)
    ]
    
    success_count = 0
    
    for name, fix_func in fixes:
        print(f"\n🔧 {name}...")
        try:
            if fix_func():
                success_count += 1
                print(f"✅ {name} - Completado")
            else:
                print(f"⚠️ {name} - Completado con advertencias")
                success_count += 0.5
        except Exception as e:
            print(f"❌ {name} - Error: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 CORRECCIONES: {success_count}/{len(fixes)} exitosas")
    
    if success_count >= len(fixes) * 0.8:
        print("🎉 ¡ERRORES CORREGIDOS!")
        print("\n💡 Próximos pasos:")
        print("1. python test_fix_updated.py")
        print("2. python run_pm.py --setup")
        print("3. python run_pm.py --check-models")
    else:
        print("⚠️ Algunas correcciones fallaron")
        print("🔧 Revisa los errores arriba")
    
    print("=" * 60)
    
    return success_count >= len(fixes) * 0.8

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)