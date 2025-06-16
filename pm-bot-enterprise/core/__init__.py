# core/__init__.py
"""
PM Bot Enterprise Core Package
"""

from .pm_bot import PMBotEnterprise, ProjectConfig, ProjectStatus, ProjectState
from .planner import ProjectPlanner, ModuleSpec
from .agent_spawner import AgentSpawner, AgentConfig, AgentTask
from .module_manager import ModuleManager, ModuleStatus, ModuleState
from .task_orchestrator import TaskOrchestrator, ExecutionPlan
from .ai_interface import AIInterface
from .communication_manager import MCPCommunicationManager, MCPMessage, MessageType
from .enhanced_agent import EnhancedAgent, AgentCapability, TaskResult

__version__ = "1.0.0"
__author__ = "PM Bot Enterprise Team"

__all__ = [
    # Main classes
    "PMBotEnterprise",
    "ProjectPlanner", 
    "AgentSpawner",
    "ModuleManager",
    "TaskOrchestrator",
    "AIInterface",
    "MCPCommunicationManager",
    "EnhancedAgent",
    
    # Data classes
    "ProjectConfig",
    "ProjectState", 
    "ModuleSpec",
    "ModuleState",
    "AgentConfig",
    "AgentTask",
    "AgentCapability",
    "TaskResult",
    "ExecutionPlan",
    "MCPMessage",
    
    # Enums
    "ProjectStatus",
    "ModuleStatus", 
    "MessageType"
]

# Verificar dependencias críticas al importar
def check_dependencies():
    """Verificar que las dependencias críticas estén disponibles"""
    missing_deps = []
    
    try:
        import asyncio
    except ImportError:
        missing_deps.append("asyncio")
    
    try:
        import aiohttp
    except ImportError:
        missing_deps.append("aiohttp")
    
    try:
        import json
    except ImportError:
        missing_deps.append("json")
    
    if missing_deps:
        raise ImportError(f"Missing critical dependencies: {', '.join(missing_deps)}")

# Ejecutar verificación al importar
check_dependencies()

# Configuración por defecto
DEFAULT_CONFIG = {
    "max_concurrent_projects": 5,
    "default_team_size": 6,
    "ai_models": {
        "primary": "deepseek-r1:14b",
        "fallback": ["claude-3-5-sonnet", "gpt-4o"]
    }
}