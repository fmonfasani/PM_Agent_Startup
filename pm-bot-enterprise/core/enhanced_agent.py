# core/enhanced_agent.py
"""
Enhanced Agent Interface - Agentes especializados con protocolo MCP
"""

import asyncio
import json
import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging

from .communication_manager import (
    AgentInterface, MCPMessage, MessageType, MessagePriority,
    MCPCommunicationManager
)
from .ai_interface import AIInterface


class AgentStatus(Enum):
    """Estados detallados del agente"""
    INITIALIZING = "initializing"
    IDLE = "idle"
    WORKING = "working"
    COLLABORATING = "collaborating"
    WAITING_RESOURCE = "waiting_resource"
    PAUSED = "paused"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"
    OFFLINE = "offline"


class TaskStatus(Enum):
    """Estados detallados de tareas"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING_DEPENDENCY = "waiting_dependency"
    REVIEW = "review"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentCapability:
    """Capacidad específica del agente"""
    name: str
    level: int  # 1-10
    technologies: List[str]
    description: str


@dataclass
class TaskResult:
    """Resultado detallado de una tarea"""
    task_id: str
    status: TaskStatus
    output: Dict[str, Any]
    quality_score: float
    execution_time_ms: int
    resources_used: List[str]
    errors: List[str] = None
    warnings: List[str] = None


class EnhancedAgent(AgentInterface):
    """Agente especializado mejorado con protocolo MCP"""
    
    def __init__(self, agent_id: str, role: str, specialization: str,
                 capabilities: List[AgentCapability], ai_model: str):
        self.agent_id = agent_id
        self.role = role
        self.specialization = specialization
        self.capabilities = capabilities
        self.ai_model = ai_model
        
        # Estado del agente
        self.status = AgentStatus.INITIALIZING
        self.current_task: Optional[str] = None
        self.active_collaborations: Dict[str, Dict[str, Any]] = {}
        self.task_history: List[TaskResult] = []
        
        # Performance metrics
        self.metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "average_quality_score": 0.0,
            "average_execution_time": 0.0,
            "collaborations_initiated": 0,
            "collaborations_successful": 0,
            "uptime_start": datetime.now(),
            "last_activity": datetime.now()
        }
        
        # Configuración
        self.max_concurrent_tasks = 3
        self.task_timeout = timedelta(hours=2)
        
        # Dependencies
        self.ai_interface = AIInterface()
        self.mcp_manager: Optional[MCPCommunicationManager] = None
        self.logger = logging.getLogger(f'Agent-{agent_id}')
        
        # Internal state
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.resource_locks: List[str] = []
        
        self.logger.info(f"Enhanced agent {agent_id} ({role}) initialized")
    
    async def initialize(self, mcp_manager: MCPCommunicationManager):
        """Inicializar agente con MCP manager"""
        self.mcp_manager = mcp_manager
        self.status = AgentStatus.IDLE
        
        # Registrar en MCP
        mcp_manager.register_agent(self.agent_id, self)
        
        # Anunciar disponibilidad
        await self._announce_availability()
        
        self.logger.info(f"Agent {self.agent_id} initialized and registered with MCP")
    
    async def handle_message(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Manejar mensaje MCP recibido"""
        self.metrics["last_activity"] = datetime.now()
        
        try:
            if message.type == MessageType.TASK_ASSIGNMENT:
                return await self._handle_task_assignment(message)
            elif message.type == MessageType.COLLABORATION_REQUEST:
                return await self._handle_collaboration_request(message)
            elif message.type == MessageType.COLLABORATION_RESPONSE:
                return await self._handle_collaboration_response(message)
            elif message.type == MessageType.RESOURCE_RESPONSE:
                return await self._handle_resource_response(message)
            elif message.type == MessageType.HEALTH_CHECK:
                return await self._handle_health_check(message)
            elif message.type == MessageType.SHUTDOWN:
                return await self._handle_shutdown(message)
            else:
                self.logger.warning(f"Unhandled message type: {message.type}")
                
        except Exception as e:
            self.logger.error(f"Error handling message {message.id}: {e}")
            
            # Enviar mensaje de error
            return MCPMessage(
                id=str(uuid.uuid4()),
                type=MessageType.TASK_FAILURE,
                sender_id=self.agent_id,
                recipient_id=message.sender_id,
                payload={
                    "original_message_id": message.id,
                    "error": str(e),
                    "agent_status": self.status.value
                },
                correlation_id=message.id
            )
        
        return None
    
    async def _handle_task_assignment(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Manejar asignación de tarea"""
        task_data = message.payload
        task_id = task_data.get("task_id", str(uuid.uuid4()))
        
        # Verificar si podemos aceptar la tarea
        if len(self.active_tasks) >= self.max_concurrent_tasks:
            return MCPMessage(
                id=str(uuid.uuid4()),
                type=MessageType.TASK_FAILURE,
                sender_id=self.agent_id,
                recipient_id=message.sender_id,
                payload={
                    "task_id": task_id,
                    "error": "Agent at maximum capacity",
                    "current_load": len(self.active_tasks),
                    "max_capacity": self.max_concurrent_tasks
                },
                correlation_id=message.id
            )
        
        # Aceptar tarea
        self.active_tasks[task_id] = {
            "task_data": task_data,
            "status": TaskStatus.PENDING,
            "assigned_at": datetime.now(),
            "assignor": message.sender_id
        }
        
        self.status = AgentStatus.WORKING
        self.current_task = task_id
        
        # Procesar tarea en background
        asyncio.create_task(self._execute_task(task_id))
        
        # Confirmar aceptación
        return MCPMessage(
            id=str(uuid.uuid4()),
            type=MessageType.STATUS_UPDATE,
            sender_id=self.agent_id,
            recipient_id=message.sender_id,
            payload={
                "task_id": task_id,
                "status": "accepted",
                "estimated_completion": (datetime.now() + timedelta(minutes=30)).isoformat()
            },
            correlation_id=message.id
        )
    
    async def _execute_task(self, task_id: str):
        """Ejecutar tarea asignada"""
        start_time = datetime.now()
        task_info = self.active_tasks[task_id]
        task_data = task_info["task_data"]
        
        try:
            self.logger.info(f"Executing task {task_id}: {task_data.get('description', 'No description')}")
            
            # Actualizar estado
            task_info["status"] = TaskStatus.IN_PROGRESS
            
            # Verificar si necesita colaboración
            collaboration_needed = await self._assess_collaboration_needs(task_data)
            
            if collaboration_needed:
                collaboration_result = await self._initiate_collaboration(task_id, collaboration_needed)
                if not collaboration_result:
                    raise Exception("Required collaboration failed")
            
            # Ejecutar tarea con AI
            result = await self._execute_with_ai(task_data)
            
            # Validar resultado
            quality_score = await self._validate_result(result, task_data)
            
            # Crear resultado de tarea
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            task_result = TaskResult(
                task_id=task_id,
                status=TaskStatus.COMPLETED,
                output=result,
                quality_score=quality_score,
                execution_time_ms=execution_time,
                resources_used=self.resource_locks.copy()
            )
            
            # Actualizar métricas
            self._update_metrics(task_result)
            
            # Notificar completación
            await self._notify_task_completion(task_id, task_result)
            
            self.logger.info(f"Task {task_id} completed successfully (Quality: {quality_score:.2f})")
            
        except Exception as e:
            self.logger.error(f"Task {task_id} failed: {e}")
            
            # Crear resultado de error
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            task_result = TaskResult(
                task_id=task_id,
                status=