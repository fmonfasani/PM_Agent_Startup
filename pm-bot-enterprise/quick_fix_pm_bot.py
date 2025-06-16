#!/usr/bin/env python3
"""
quick_fix_pm_bot.py - Fix rápido para corregir errores en PMBotEnterprise
"""

import os
from pathlib import Path

def fix_pm_bot_errors():
    """Corregir errores en core/pm_bot.py"""
    
    print("🔧 Corrigiendo errores en PMBotEnterprise...")
    
    pm_bot_file = Path("core/pm_bot.py")
    
    if not pm_bot_file.exists():
        print("❌ core/pm_bot.py no encontrado")
        return False
    
    # Leer archivo
    with open(pm_bot_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix 1: Agregar import de Path si no existe
    if "from pathlib import Path" not in content:
        # Buscar línea de imports
        import_line = "from datetime import datetime"
        if import_line in content:
            content = content.replace(import_line, import_line + "\nfrom pathlib import Path")
            print("✅ Agregado import de Path")
    
    # Fix 2: Mover _load_existing_projects después de setup_logging
    old_load_call = """        # Cargar proyectos existentes automáticamente
        self._load_existing_projects()"""
    
    new_load_call = """        # Cargar proyectos existentes automáticamente (después de logging)
        try:
            self._load_existing_projects()
        except Exception as e:
            print(f"Warning: Could not load existing projects: {e}")"""
    
    if old_load_call in content:
        content = content.replace(old_load_call, new_load_call)
        print("✅ Corregido llamada a _load_existing_projects")
    
    # Fix 3: Mejorar el método _load_existing_projects
    old_method = """    def _load_existing_projects(self):
        \"\"\"Cargar todos los proyectos existentes desde disco\"\"\"
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
            self.logger.error(f"Error loading existing projects: {e}")"""
    
    new_method = """    def _load_existing_projects(self):
        \"\"\"Cargar todos los proyectos existentes desde disco\"\"\"
        try:
            from pathlib import Path
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
                    if hasattr(self, 'logger'):
                        self.logger.warning(f"Could not load project from {project_file}: {e}")
                    else:
                        print(f"Warning: Could not load project from {project_file}: {e}")
            
            if loaded_count > 0:
                if hasattr(self, 'logger'):
                    self.logger.info(f"Loaded {loaded_count} existing projects")
                else:
                    print(f"Info: Loaded {loaded_count} existing projects")
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Error loading existing projects: {e}")
            else:
                print(f"Error loading existing projects: {e}")"""
    
    if old_method in content:
        content = content.replace(old_method, new_method)
        print("✅ Mejorado método _load_existing_projects")
    
    # Escribir archivo corregido
    with open(pm_bot_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Todos los fixes aplicados a core/pm_bot.py")
    return True

def main():
    """Aplicar fix rápido"""
    print("🔧 PM BOT ENTERPRISE - FIX RÁPIDO")
    print("=" * 40)
    
    if fix_pm_bot_errors():
        print("\n🎉 ¡Fix aplicado exitosamente!")
        print("\n💡 Ahora ejecuta:")
        print("   python test_persistence_fix.py")
    else:
        print("\n❌ No se pudo aplicar el fix")
    
    return True

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)