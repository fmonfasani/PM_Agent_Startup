# core/__init__.py
"""
PM Bot Enterprise - Core Module
Sistema de gestión de proyectos con IA
"""

__version__ = "1.0.0"

# Imports principales ordenados para evitar dependencias circulares
try:
    # Primero los módulos sin dependencias
    from .ai_interface import AIInterface
    
    # Luego los que dependen de ai_interface
    from .planner import ProjectPlanner, ModuleSpec
    
    # Después los módulos principales
    from .pm_bot import PMBotEnterprise, ProjectConfig, ProjectStatus, ProjectState
    from .module_manager import ModuleManager
    from .agent_spawner import AgentSpawner
    from .task_orchestrator import TaskOrchestrator
    
    # Finalmente los módulos de comunicación
    from .communication_manager import MCPCommunicationManager
    from .enhanced_agent import EnhancedAgent
    
    __all__ = [
        'AIInterface',
        'ProjectPlanner', 
        'ModuleSpec',
        'PMBotEnterprise',
        'ProjectConfig',
        'ProjectStatus', 
        'ProjectState',
        'ModuleManager',
        'AgentSpawner',
        'TaskOrchestrator',
        'MCPCommunicationManager',
        'EnhancedAgent'
    ]
    
    print("✅ Core module loaded successfully")
    
except ImportError as e:
    print(f"⚠️  Warning: Some core modules could not be imported: {e}")
    # Import solo los módulos que funcionan
    __all__ = []
    
    try:
        from .ai_interface import AIInterface
        __all__.append('AIInterface')
    except ImportError:
        pass
    
    try:
        from .planner import ProjectPlanner
        __all__.append('ProjectPlanner')
    except ImportError:
        pass
    
    try:
        from .pm_bot import PMBotEnterprise
        __all__.append('PMBotEnterprise')
    except ImportError:
        pass
