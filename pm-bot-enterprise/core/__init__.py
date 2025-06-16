# core/__init__.py
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
    
    print("Core module loaded successfully")
    
except ImportError as e:
    print(f"Warning importing core modules: {e}")
    __all__ = []
