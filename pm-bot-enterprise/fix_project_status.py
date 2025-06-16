#!/usr/bin/env python3
"""
fix_project_status.py - Corregir el método get_project_status
"""

from pathlib import Path

def fix_get_project_status():
    """Corregir el método get_project_status en pm_bot.py"""
    
    pm_bot_file = Path("core/pm_bot.py")
    if not pm_bot_file.exists():
        print("❌ core/pm_bot.py no encontrado")
        return False
    
    # Leer archivo
    with open(pm_bot_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar y corregir la línea problemática
    old_line = '"status": module.get("status", "pending"),'
    new_line = '"status": getattr(module, "status", "pending") if hasattr(module, "status") else "pending",'
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        
        # También corregir otras líneas similares en el mismo método
        fixes = [
            ('"progress": module.get("progress", 0),', 
             '"progress": getattr(module, "progress", 0) if hasattr(module, "progress") else 0,'),
            ('"agents": len(project.agents.get(name, []))', 
             '"agents": len(project.agents.get(name, []))'),
        ]
        
        for old, new in fixes:
            if old in content:
                content = content.replace(old, new)
        
        # Buscar el método get_project_status completo y reemplazarlo
        method_start = 'async def get_project_status(self, project_id: str) -> Dict[str, Any]:'
        if method_start in content:
            # Encontrar el inicio del método
            start_pos = content.find(method_start)
            
            # Encontrar el final del método (próximo 'async def' o 'def')
            search_pos = start_pos + len(method_start)
            next_method_pos = content.find('\n    async def', search_pos)
            if next_method_pos == -1:
                next_method_pos = content.find('\n    def ', search_pos)
            if next_method_pos == -1:
                next_method_pos = len(content)
            
            # Reemplazar el método completo
            new_method = '''async def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Obtener estado actual del proyecto"""
        if project_id not in self.projects:
            raise ValueError(f"Project {project_id} not found")
        
        project = self.projects[project_id]
        
        # Obtener métricas en tiempo real
        try:
            real_time_metrics = await self.orchestrator.get_project_metrics(project_id)
        except Exception as e:
            self.logger.warning(f"Could not get real-time metrics: {e}")
            real_time_metrics = {}
        
        # Procesar módulos de manera segura
        modules_status = {}
        for name, module in project.modules.items():
            if hasattr(module, 'status'):
                # Es un objeto con atributos
                modules_status[name] = {
                    "status": getattr(module, 'status', 'pending'),
                    "progress": getattr(module, 'progress', 0),
                    "agents": len(project.agents.get(name, []))
                }
            elif isinstance(module, dict):
                # Es un diccionario
                modules_status[name] = {
                    "status": module.get("status", "pending"),
                    "progress": module.get("progress", 0),
                    "agents": len(project.agents.get(name, []))
                }
            else:
                # Fallback
                modules_status[name] = {
                    "status": "unknown",
                    "progress": 0,
                    "agents": len(project.agents.get(name, []))
                }
        
        return {
            "id": project.id,
            "name": project.config.name,
            "status": project.status.value,
            "progress": project.progress,
            "modules": modules_status,
            "timeline": {
                "start_time": project.start_time.isoformat(),
                "estimated_completion": project.estimated_completion.isoformat(),
                "actual_completion": project.actual_completion.isoformat() 
                                   if project.actual_completion else None
            },
            "metrics": real_time_metrics,
            "team": {
                "total_agents": sum(len(agents) for agents in project.agents.values()),
                "active_agents": real_time_metrics.get("active_agents", 0)
            }
        }

    '''
            
            before = content[:start_pos]
            after = content[next_method_pos:]
            
            content = before + new_method + after
        
        # Escribir archivo modificado
        with open(pm_bot_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Fix de get_project_status aplicado")
        return True
    else:
        print("⚠️ Línea problemática no encontrada, posiblemente ya corregida")
        return True

def main():
    """Aplicar fix"""
    print("🔧 Corrigiendo get_project_status...")
    success = fix_get_project_status()
    
    if success:
        print("🎉 ¡Fix aplicado exitosamente!")
        print("\n💡 Ahora ejecuta:")
        print("   python quick_test_post_ollama.py")
    else:
        print("❌ No se pudo aplicar el fix")
    
    return success

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)