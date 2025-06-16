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
                status=TaskStatus.FAILED,
                output={"error": str(e)},
                quality_score=0.0,
                execution_time_ms=execution_time,
                resources_used=self.resource_locks.copy(),
                errors=[str(e)]
            )
            
            # Actualizar métricas
            self._update_metrics(task_result)
            
            # Notificar fallo
            await self._notify_task_failure(task_id, task_result)
        
        finally:
            # Limpiar estado
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            
            if self.current_task == task_id:
                self.current_task = None
            
            # Actualizar estado del agente
            if len(self.active_tasks) == 0:
                self.status = AgentStatus.IDLE
    
    async def _assess_collaboration_needs(self, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Evaluar si la tarea requiere colaboración con otros agentes"""
        
        task_type = task_data.get("task_type", "")
        task_description = task_data.get("description", "")
        
        # Patrones que requieren colaboración
        collaboration_patterns = {
            "frontend_backend_integration": {
                "pattern": r"integr|api|endpoint|connect",
                "required_roles": ["backend", "frontend"],
                "collaboration_type": "integration"
            },
            "database_design": {
                "pattern": r"database|db|schema|model",
                "required_roles": ["backend", "data"],
                "collaboration_type": "design_review"
            },
            "security_review": {
                "pattern": r"auth|security|login|password",
                "required_roles": ["security"],
                "collaboration_type": "security_review"
            }
        }
        
        import re
        for collab_name, collab_info in collaboration_patterns.items():
            if re.search(collab_info["pattern"], task_description.lower()):
                # Verificar si necesitamos roles que no tenemos
                needed_roles = set(collab_info["required_roles"])
                if self.role not in needed_roles:
                    return {
                        "type": collab_info["collaboration_type"],
                        "required_roles": list(needed_roles - {self.role}),
                        "reason": f"Task requires {collab_name}"
                    }
        
        return None
    
    async def _initiate_collaboration(self, task_id: str, collaboration_needs: Dict[str, Any]) -> bool:
        """Iniciar colaboración con otros agentes"""
        
        if not self.mcp_manager:
            return False
        
        required_roles = collaboration_needs.get("required_roles", [])
        
        for role in required_roles:
            # Buscar agentes con el rol requerido
            available_agents = [
                agent_id for agent_id, agent in self.mcp_manager.router.routes.items()
                if hasattr(agent, 'role') and agent.role == role
            ]
            
            if available_agents:
                target_agent = available_agents[0]  # Seleccionar el primero disponible
                
                # Solicitar colaboración
                collaboration_id = await self.mcp_manager.request_agent_collaboration(
                    self.agent_id,
                    target_agent,
                    {
                        "task_id": task_id,
                        "collaboration_type": collaboration_needs["type"],
                        "reason": collaboration_needs["reason"]
                    }
                )
                
                if collaboration_id:
                    self.active_collaborations[collaboration_id] = {
                        "task_id": task_id,
                        "partner_agent": target_agent,
                        "type": collaboration_needs["type"],
                        "status": "requested"
                    }
                    
                    return True
        
        return False
    
    async def _execute_with_ai(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar tarea usando AI"""
        
        # Construir prompt especializado
        prompt = self._build_specialized_prompt(task_data)
        
        # Ejecutar con AI
        response = await self.ai_interface.generate_response(
            prompt,
            max_tokens=2000,
            temperature=0.2,
            model=self.ai_model
        )
        
        # Procesar respuesta
        result = self._process_ai_response(response, task_data)
        
        return result
    
    def _build_specialized_prompt(self, task_data: Dict[str, Any]) -> str:
        """Construir prompt especializado para el agente"""
        
        task_type = task_data.get("task_type", "implement")
        description = task_data.get("description", "")
        module_name = task_data.get("module_name", "unknown")
        
        prompt = f"""
You are {self.agent_id}, a highly specialized {self.role} developer.

AGENT PROFILE:
- Role: {self.role}
- Specialization: {self.specialization}
- Capabilities: {', '.join([cap.name for cap in self.capabilities])}
- Technologies: {', '.join([tech for cap in self.capabilities for tech in cap.technologies])}

CURRENT TASK:
- Type: {task_type}
- Module: {module_name}
- Description: {description}

INSTRUCTIONS:
Based on your specialization and the task requirements, provide a complete, production-ready solution.

For implementation tasks:
- Write complete, functional code
- Include proper error handling
- Add comprehensive comments
- Follow best practices for {self.role} development
- Include necessary imports and dependencies

For design tasks:
- Provide detailed technical specifications
- Include architecture diagrams if relevant
- Consider scalability and maintainability
- Address security and performance concerns

For review tasks:
- Identify potential issues and improvements
- Suggest optimizations
- Verify compliance with best practices
- Provide actionable feedback

Begin your response with a brief analysis of the task, then provide your solution.
"""
        
        return prompt
    
    def _process_ai_response(self, response: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar respuesta de AI"""
        
        # Extraer bloques de código
        code_blocks = self._extract_code_blocks(response)
        
        # Extraer archivos mencionados
        files = self._extract_file_references(response)
        
        # Generar estructura del resultado
        result = {
            "raw_response": response,
            "code_blocks": code_blocks,
            "files": files,
            "task_analysis": self._extract_task_analysis(response),
            "recommendations": self._extract_recommendations(response),
            "next_steps": self._extract_next_steps(response)
        }
        
        return result
    
    def _extract_code_blocks(self, text: str) -> List[Dict[str, str]]:
        """Extraer bloques de código del texto"""
        import re
        
        code_blocks = []
        pattern = r'```(\w+)?\s*\n(.*?)\n```'
        matches = re.findall(pattern, text, re.DOTALL)
        
        for i, (language, code) in enumerate(matches):
            code_blocks.append({
                "id": f"code_block_{i+1}",
                "language": language or "text",
                "code": code.strip(),
                "lines": len(code.strip().split('\n'))
            })
        
        return code_blocks
    
    def _extract_file_references(self, text: str) -> List[Dict[str, str]]:
        """Extraer referencias a archivos del texto"""
        import re
        
        files = []
        
        # Patrones para detectar archivos
        file_patterns = [
            r'(\w+\.\w+):?\s*\n',
            r'File:\s*(\S+)',
            r'`([^`]+\.\w+)`'
        ]
        
        for pattern in file_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, str) and '.' in match:
                    files.append({
                        "name": match,
                        "type": match.split('.')[-1],
                        "detected_pattern": pattern
                    })
        
        return files
    
    def _extract_task_analysis(self, text: str) -> str:
        """Extraer análisis de la tarea del texto"""
        lines = text.split('\n')
        analysis_lines = []
        
        in_analysis = False
        for line in lines:
            if any(keyword in line.lower() for keyword in ['analysis', 'approach', 'understanding']):
                in_analysis = True
            elif in_analysis and line.strip() == '':
                break
            elif in_analysis:
                analysis_lines.append(line.strip())
        
        return '\n'.join(analysis_lines) if analysis_lines else "No analysis found"
    
    def _extract_recommendations(self, text: str) -> List[str]:
        """Extraer recomendaciones del texto"""
        import re
        
        recommendations = []
        
        # Buscar patrones de recomendaciones
        rec_patterns = [
            r'recommend[s]?\s*:?\s*(.+?)(?:\n|$)',
            r'suggestion[s]?\s*:?\s*(.+?)(?:\n|$)',
            r'consider\s+(.+?)(?:\n|$)'
        ]
        
        for pattern in rec_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            recommendations.extend(matches)
        
        return [rec.strip() for rec in recommendations if rec.strip()]
    
    def _extract_next_steps(self, text: str) -> List[str]:
        """Extraer próximos pasos del texto"""
        import re
        
        next_steps = []
        
        # Buscar secciones de próximos pasos
        steps_patterns = [
            r'next steps?\s*:?\s*(.+?)(?:\n\n|$)',
            r'todo\s*:?\s*(.+?)(?:\n\n|$)',
            r'follow.?up\s*:?\s*(.+?)(?:\n\n|$)'
        ]
        
        for pattern in steps_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                steps = [step.strip() for step in match.split('\n') if step.strip()]
                next_steps.extend(steps)
        
        return next_steps
    
    async def _validate_result(self, result: Dict[str, Any], task_data: Dict[str, Any]) -> float:
        """Validar calidad del resultado"""
        
        quality_score = 0.0
        
        # Verificar que hay contenido
        if result.get("raw_response") and len(result["raw_response"]) > 50:
            quality_score += 0.2
        
        # Verificar código generado
        code_blocks = result.get("code_blocks", [])
        if code_blocks:
            quality_score += 0.3
            
            # Bonus por código bien formateado
            for block in code_blocks:
                if block.get("language") in ["javascript", "python", "typescript", "java"]:
                    quality_score += 0.1
                if block.get("lines", 0) > 10:
                    quality_score += 0.1
        
        # Verificar análisis de tarea
        if result.get("task_analysis") and len(result["task_analysis"]) > 20:
            quality_score += 0.2
        
        # Verificar recomendaciones
        if result.get("recommendations"):
            quality_score += 0.1
        
        # Verificar próximos pasos
        if result.get("next_steps"):
            quality_score += 0.1
        
        # Normalizar a 0-1
        return min(quality_score, 1.0)
    
    def _update_metrics(self, task_result: TaskResult):
        """Actualizar métricas del agente"""
        
        if task_result.status == TaskStatus.COMPLETED:
            self.metrics["tasks_completed"] += 1
            
            # Actualizar promedio de calidad
            total_tasks = self.metrics["tasks_completed"]
            current_avg = self.metrics["average_quality_score"]
            new_avg = ((current_avg * (total_tasks - 1)) + task_result.quality_score) / total_tasks
            self.metrics["average_quality_score"] = new_avg
            
            # Actualizar tiempo promedio
            current_time_avg = self.metrics["average_execution_time"]
            new_time_avg = ((current_time_avg * (total_tasks - 1)) + task_result.execution_time_ms) / total_tasks
            self.metrics["average_execution_time"] = new_time_avg
            
        elif task_result.status == TaskStatus.FAILED:
            self.metrics["tasks_failed"] += 1
        
        # Agregar a historial
        self.task_history.append(task_result)
        
        # Mantener historial limitado
        if len(self.task_history) > 100:
            self.task_history = self.task_history[-100:]
    
    async def _notify_task_completion(self, task_id: str, task_result: TaskResult):
        """Notificar completación de tarea"""
        
        if not self.mcp_manager:
            return
        
        completion_message = MCPMessage(
            id=str(uuid.uuid4()),
            type=MessageType.TASK_COMPLETION,
            sender_id=self.agent_id,
            recipient_id="orchestrator",  # Enviar al orquestador
            payload={
                "task_id": task_id,
                "result": asdict(task_result),
                "agent_metrics": self.metrics
            }
        )
        
        await self.mcp_manager.send_message(completion_message)
    
    async def _notify_task_failure(self, task_id: str, task_result: TaskResult):
        """Notificar fallo de tarea"""
        
        if not self.mcp_manager:
            return
        
        failure_message = MCPMessage(
            id=str(uuid.uuid4()),
            type=MessageType.TASK_FAILURE,
            sender_id=self.agent_id,
            recipient_id="orchestrator",
            payload={
                "task_id": task_id,
                "result": asdict(task_result),
                "agent_metrics": self.metrics
            }
        )
        
        await self.mcp_manager.send_message(failure_message)
    
    async def _handle_collaboration_request(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Manejar solicitud de colaboración"""
        
        collaboration_id = message.payload.get("collaboration_id")
        collaboration_type = message.payload.get("task_info", {}).get("collaboration_type")
        
        # Evaluar si podemos colaborar
        can_collaborate = self.status == AgentStatus.IDLE
        
        # Responder a la colaboración
        if self.mcp_manager:
            await self.mcp_manager.collaboration.respond_to_collaboration(
                collaboration_id,
                self.agent_id,
                can_collaborate,
                {"capabilities": [cap.name for cap in self.capabilities]}
            )
        
        if can_collaborate:
            self.status = AgentStatus.COLLABORATING
            self.active_collaborations[collaboration_id] = {
                "partner": message.sender_id,
                "type": collaboration_type,
                "status": "active"
            }
        
        return None
    
    async def _handle_collaboration_response(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Manejar respuesta de colaboración"""
        
        collaboration_id = message.payload.get("collaboration_id")
        accepted = message.payload.get("accepted", False)
        
        if collaboration_id in self.active_collaborations:
            if accepted:
                self.active_collaborations[collaboration_id]["status"] = "active"
                self.metrics["collaborations_successful"] += 1
            else:
                del self.active_collaborations[collaboration_id]
        
        return None
    
    async def _handle_resource_response(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Manejar respuesta de recurso"""
        
        resource_id = message.payload.get("resource_id")
        granted = message.payload.get("granted", False)
        
        if granted:
            self.resource_locks.append(resource_id)
            self.logger.info(f"Resource {resource_id} acquired")
        else:
            self.logger.warning(f"Resource {resource_id} denied")
        
        return None
    
    async def _handle_health_check(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Manejar check de salud"""
        
        return MCPMessage(
            id=str(uuid.uuid4()),
            type=MessageType.STATUS_UPDATE,
            sender_id=self.agent_id,
            recipient_id=message.sender_id,
            payload={
                "status": self.status.value,
                "health": "healthy",
                "uptime": (datetime.now() - self.metrics["uptime_start"]).total_seconds(),
                "active_tasks": len(self.active_tasks),
                "metrics": self.metrics
            },
            correlation_id=message.id
        )
    
    async def _handle_shutdown(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Manejar shutdown del agente"""
        
        self.status = AgentStatus.SHUTTING_DOWN
        
        # Cancelar tareas activas
        for task_id in list(self.active_tasks.keys()):
            self.active_tasks[task_id]["status"] = TaskStatus.CANCELLED
        
        # Liberar recursos
        for resource_id in self.resource_locks:
            if self.mcp_manager:
                await self.mcp_manager.resources.release_resource(self.agent_id, resource_id)
        
        self.status = AgentStatus.OFFLINE
        
        return MCPMessage(
            id=str(uuid.uuid4()),
            type=MessageType.STATUS_UPDATE,
            sender_id=self.agent_id,
            recipient_id=message.sender_id,
            payload={
                "status": "shutdown_complete",
                "final_metrics": self.metrics
            },
            correlation_id=message.id
        )
    
    async def _announce_availability(self):
        """Anunciar disponibilidad del agente"""
        
        if not self.mcp_manager:
            return
        
        announcement = MCPMessage(
            id=str(uuid.uuid4()),
            type=MessageType.STATUS_UPDATE,
            sender_id=self.agent_id,
            recipient_id="broadcast",
            payload={
                "event": "agent_available",
                "role": self.role,
                "specialization": self.specialization,
                "capabilities": [asdict(cap) for cap in self.capabilities],
                "status": self.status.value
            }
        )
        
        await self.mcp_manager.broadcast_status_update(
            self.agent_id,
            announcement.payload
        )
    
    async def get_status(self) -> Dict[str, Any]:
        """Obtener estado actual del agente"""
        
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "specialization": self.specialization,
            "status": self.status.value,
            "capabilities": [asdict(cap) for cap in self.capabilities],
            "metrics": self.metrics,
            "active_tasks": len(self.active_tasks),
            "active_collaborations": len(self.active_collaborations),
            "resource_locks": len(self.resource_locks),
            "uptime": (datetime.now() - self.metrics["uptime_start"]).total_seconds()
        }
    
    async def shutdown(self) -> bool:
        """Shutdown graceful del agente"""
        
        try:
            self.status = AgentStatus.SHUTTING_DOWN
            
            # Cancelar tareas pendientes
            for task_id in self.active_tasks:
                self.active_tasks[task_id]["status"] = TaskStatus.CANCELLED
            
            # Limpiar colaboraciones
            self.active_collaborations.clear()
            
            # Liberar recursos
            self.resource_locks.clear()
            
            self.status = AgentStatus.OFFLINE
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
            return False