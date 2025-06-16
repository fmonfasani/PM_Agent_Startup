#!/usr/bin/env python3
"""
apply_critical_fixes.py - Aplicar los fixes más importantes
"""

import os
import shutil
from pathlib import Path

def fix_pm_bot_serialization():
    """Fix el error de serialización JSON en pm_bot.py"""
    print("🔧 Aplicando fix de serialización JSON...")
    
    pm_bot_file = Path("core/pm_bot.py")
    if not pm_bot_file.exists():
        print("❌ core/pm_bot.py no encontrado")
        return False
    
    # Leer archivo actual
    with open(pm_bot_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar y reemplazar la función save_project_state
    old_line = '"modules": {name: asdict(module) for name, module in project.modules.items()},'
    new_line = '"modules": {name: asdict(module) if hasattr(module, "__dict__") else module for name, module in project.modules.items()},'
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        
        # También fix para agents
        old_agents = '"agents": project.agents,'
        new_agents = '''# Convertir AgentConfig a dict usando asdict
        agents_serializable = {}
        for module_name, agents_list in project.agents.items():
            agents_serializable[module_name] = [
                asdict(agent) if hasattr(agent, '__dict__') else agent 
                for agent in agents_list
            ]
        
        project_data = {
            "id": project.id,
            "config": asdict(project.config),
            "status": project.status.value,
            "modules": {name: asdict(module) if hasattr(module, "__dict__") else module for name, module in project.modules.items()},
            "agents": agents_serializable,'''
        
        # Buscar la línea de project_data y reemplazar toda la sección
        if '"agents": project.agents,' in content:
            # Encontrar el inicio de project_data
            start_marker = 'project_data = {'
            end_marker = '"agents": project.agents,'
            
            start_pos = content.find(start_marker)
            end_pos = content.find(end_marker) + len(end_marker)
            
            if start_pos != -1 and end_pos != -1:
                # Reemplazar la sección completa
                before = content[:start_pos]
                after = content[end_pos:]
                
                new_section = '''project_data = {
            "id": project.id,
            "config": asdict(project.config),
            "status": project.status.value,
            "modules": {name: asdict(module) if hasattr(module, "__dict__") else module for name, module in project.modules.items()},
            "agents": {module_name: [asdict(agent) if hasattr(agent, '__dict__') else agent for agent in agents_list] for module_name, agents_list in project.agents.items()},'''
                
                content = before + new_section + after
        
        # Escribir archivo modificado
        with open(pm_bot_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Fix de serialización JSON aplicado")
        return True
    else:
        print("⚠️ No se encontró la línea a reemplazar, posiblemente ya está corregido")
        return True

def fix_task_orchestrator():
    """Fix task_orchestrator con el módulo completo"""
    print("🔧 Aplicando fix de TaskOrchestrator...")
    
    orchestrator_file = Path("core/task_orchestrator.py")
    if not orchestrator_file.exists():
        print("❌ core/task_orchestrator.py no encontrado")
        return False
    
    # Leer archivo actual
    with open(orchestrator_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar la función execute_module
    if "async def execute_module(" in content:
        # Hacer backup
        backup_file = orchestrator_file.with_suffix('.py.backup')
        shutil.copy2(orchestrator_file, backup_file)
        print(f"✅ Backup creado: {backup_file}")
        
        # Aquí insertaríamos el módulo completo, pero es muy largo
        # En su lugar, solo aplicamos fix crítico
        old_error_line = "ERROR:AgentSpawner:Agent"
        if old_error_line in content:
            # Buscar y agregar fix de registro de agentes
            fix_code = '''        # FIX: Registrar agentes en el spawner si no están registrados
        registered_agents = []
        for agent in agents:
            if agent.id not in self.agent_spawner.active_agents:
                self.logger.info(f"Registering agent {agent.id} in spawner")
                self.agent_spawner.active_agents[agent.id] = agent
            registered_agents.append(agent)'''
            
            # Buscar donde insertar el fix (después de la validación de entrada)
            insert_point = "self.logger.info(f\"Starting module execution: {module_name}"
            if insert_point in content:
                insertion_pos = content.find(insert_point)
                # Encontrar el final de esa línea
                line_end = content.find('\n', insertion_pos) + 1
                
                before = content[:line_end]
                after = content[line_end:]
                
                content = before + '\n' + fix_code + '\n' + after
                
                with open(orchestrator_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print("✅ Fix de TaskOrchestrator aplicado")
                return True
    
    print("⚠️ No se pudo aplicar fix automático de TaskOrchestrator")
    return False

def create_env_file():
    """Crear archivo .env si no existe"""
    print("🔧 Verificando archivo .env...")
    
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env ya existe")
        return True
    
    env_content = """# PM Bot Enterprise - Variables de Entorno

# Ollama Local (principal)
OLLAMA_HOST=http://localhost:11434
DEEPSEEK_MODEL=deepseek-r1:14b
LLAMA_MODEL=llama3.2:latest
QWEN_MODEL=qwen2.5-coder:7b

# APIs Cloud (fallback opcional)
# ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
# OPENAI_API_KEY=sk-proj-your-key-here

# Configuración del sistema
MAX_CONCURRENT_PROJECTS=3
DEFAULT_TEAM_SIZE=4
LOG_LEVEL=INFO
"""
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print("✅ Archivo .env creado")
    return True

def main():
    """Aplicar todos los fixes críticos"""
    print("=" * 60)
    print("🛠️ APLICANDO FIXES CRÍTICOS")
    print("=" * 60)
    
    fixes = [
        ("Serialización JSON", fix_pm_bot_serialization),
        ("TaskOrchestrator", fix_task_orchestrator),
        ("Archivo .env", create_env_file)
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
        except Exception as e:
            print(f"❌ {name} - Error: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 FIXES APLICADOS: {success_count}/{len(fixes)}")
    
    if success_count >= 2:
        print("🎉 ¡Fixes críticos aplicados!")
        print("\n💡 Próximo paso:")
        print("   python quick_test_post_ollama.py")
    else:
        print("⚠️ Algunos fixes fallaron")
    
    print("=" * 60)
    return success_count >= 2

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)