# core/communication_manager.py
"""
MCP Communication Manager - Protocolo de Comunicación Multi-Agente
Maneja toda la comunicación entre agentes y coordinación distribuida
"""

import asyncio
import json
import uuid
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging
from abc import ABC, abstractmethod


class MessageType(Enum):
    """Tipos de mensajes MCP"""
    TASK_ASSIGNMENT = "task_assignment"
    TASK_COMPLETION = "task_completion"
    TASK_FAILURE = "task_failure"
    STATUS_UPDATE = "status_update"
    COLLABORATION_REQUEST = "collaboration_request"
    COLLABORATION_RESPONSE = "collaboration_response"
    RESOURCE_REQUEST = "resource_request"
    RESOURCE_RESPONSE = "resource_response"
    HEALTH_CHECK = "health_check"
    SHUTDOWN = "shutdown"


class MessagePriority(Enum):
    """Prioridades de mensajes"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


@dataclass
class MCPMessage:
    """Mensaje estándar del protocolo MCP"""
    id: str
    type: MessageType
    sender_id: str
    recipient_id: str
    payload: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = None
    ttl: Optional[datetime] = None  # Time to live
    correlation_id: Optional[str] = None  # Para respuestas
    requires_ack: bool = False
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.ttl is None:
            self.ttl = self.timestamp + timedelta(minutes=30)


class AgentInterface(ABC):
    """Interface base para todos los agentes MCP"""
    
    @abstractmethod
    async def handle_message(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Manejar mensaje recibido y retornar respuesta opcional"""
        pass
    
    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """Obtener estado actual del agente"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> bool:
        """Shutdown graceful del agente"""
        pass


class MessageRouter:
    """Router de mensajes para el protocolo MCP"""
    
    def __init__(self):
        self.routes: Dict[str, AgentInterface] = {}
        self.message_history: List[MCPMessage] = []
        self.pending_acks: Dict[str, MCPMessage] = {}
        self.logger = logging.getLogger('MessageRouter')
    
    def register_agent(self, agent_id: str, agent: AgentInterface):
        """Registrar agente en el router"""
        self.routes[agent_id] = agent
        self.logger.info(f"Agent {agent_id} registered in MCP router")
    
    def unregister_agent(self, agent_id: str):
        """Desregistrar agente del router"""
        if agent_id in self.routes:
            del self.routes[agent_id]
            self.logger.info(f"Agent {agent_id} unregistered from MCP router")
    
    async def route_message(self, message: MCPMessage) -> bool:
        """Enrutar mensaje al agente destinatario"""
        
        # Verificar TTL
        if message.ttl and datetime.now() > message.ttl:
            self.logger.warning(f"Message {message.id} expired, dropping")
            return False
        
        # Verificar que el destinatario existe
        if message.recipient_id not in self.routes:
            self.logger.error(f"Recipient {message.recipient_id} not found")
            return False
        
        try:
            # Enviar mensaje al agente
            agent = self.routes[message.recipient_id]
            response = await agent.handle_message(message)
            
            # Manejar respuesta si existe
            if response:
                await self.route_message(response)
            
            # Manejar ACK si es requerido
            if message.requires_ack:
                ack_message = MCPMessage(
                    id=str(uuid.uuid4()),
                    type=MessageType.STATUS_UPDATE,
                    sender_id=message.recipient_id,
                    recipient_id=message.sender_id,
                    payload={"status": "message_received", "original_id": message.id},
                    correlation_id=message.id
                )
                await self.route_message(ack_message)
            
            # Guardar en historial
            self.message_history.append(message)
            self._cleanup_history()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error routing message {message.id}: {e}")
            return False
    
    def _cleanup_history(self, max_history: int = 1000):
        """Limpiar historial de mensajes"""
        if len(self.message_history) > max_history:
            self.message_history = self.message_history[-max_history:]
    
    def get_agent_list(self) -> List[str]:
        """Obtener lista de agentes registrados"""
        return list(self.routes.keys())
    
    async def broadcast_message(self, message: MCPMessage, exclude_sender: bool = True) -> int:
        """Enviar mensaje a todos los agentes"""
        sent_count = 0
        
        for agent_id in self.routes:
            if exclude_sender and agent_id == message.sender_id:
                continue
            
            # Crear copia del mensaje para cada destinatario
            broadcast_msg = MCPMessage(
                id=str(uuid.uuid4()),
                type=message.type,
                sender_id=message.sender_id,
                recipient_id=agent_id,
                payload=message.payload.copy(),
                priority=message.priority
            )
            
            if await self.route_message(broadcast_msg):
                sent_count += 1
        
        return sent_count


class CollaborationProtocol:
    """Protocolo específico para colaboración entre agentes"""
    
    def __init__(self, router: MessageRouter):
        self.router = router
        self.active_collaborations: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger('CollaborationProtocol')
    
    async def request_collaboration(self, requester_id: str, target_id: str, 
                                  task_info: Dict[str, Any]) -> str:
        """Solicitar colaboración entre agentes"""
        
        collaboration_id = str(uuid.uuid4())
        
        # Crear solicitud de colaboración
        request_message = MCPMessage(
            id=str(uuid.uuid4()),
            type=MessageType.COLLABORATION_REQUEST,
            sender_id=requester_id,
            recipient_id=target_id,
            payload={
                "collaboration_id": collaboration_id,
                "task_info": task_info,
                "requester_capabilities": await self._get_agent_capabilities(requester_id)
            },
            requires_ack=True
        )
        
        # Registrar colaboración pendiente
        self.active_collaborations[collaboration_id] = {
            "requester_id": requester_id,
            "target_id": target_id,
            "status": "pending",
            "created_at": datetime.now(),
            "task_info": task_info
        }
        
        # Enviar solicitud
        success = await self.router.route_message(request_message)
        
        if success:
            self.logger.info(f"Collaboration {collaboration_id} requested between {requester_id} and {target_id}")
            return collaboration_id
        else:
            del self.active_collaborations[collaboration_id]
            raise Exception("Failed to send collaboration request")
    
    async def respond_to_collaboration(self, collaboration_id: str, 
                                     responder_id: str, accepted: bool, 
                                     response_data: Dict[str, Any] = None) -> bool:
        """Responder a solicitud de colaboración"""
        
        if collaboration_id not in self.active_collaborations:
            self.logger.error(f"Collaboration {collaboration_id} not found")
            return False
        
        collaboration = self.active_collaborations[collaboration_id]
        requester_id = collaboration["requester_id"]
        
        # Crear respuesta
        response_message = MCPMessage(
            id=str(uuid.uuid4()),
            type=MessageType.COLLABORATION_RESPONSE,
            sender_id=responder_id,
            recipient_id=requester_id,
            payload={
                "collaboration_id": collaboration_id,
                "accepted": accepted,
                "response_data": response_data or {},
                "responder_capabilities": await self._get_agent_capabilities(responder_id)
            },
            correlation_id=collaboration_id
        )
        
        # Actualizar estado de colaboración
        collaboration["status"] = "accepted" if accepted else "rejected"
        collaboration["responded_at"] = datetime.now()
        
        # Enviar respuesta
        success = await self.router.route_message(response_message)
        
        if success:
            self.logger.info(f"Collaboration {collaboration_id} {'accepted' if accepted else 'rejected'}")
        
        return success
    
    async def _get_agent_capabilities(self, agent_id: str) -> Dict[str, Any]:
        """Obtener capacidades de un agente"""
        if agent_id not in self.router.routes:
            return {}
        
        try:
            status = await self.router.routes[agent_id].get_status()
            return status.get("capabilities", {})
        except Exception:
            return {}
    
    def get_active_collaborations(self) -> Dict[str, Dict[str, Any]]:
        """Obtener colaboraciones activas"""
        return self.active_collaborations.copy()


class ResourceManager:
    """Gestor de recursos compartidos entre agentes"""
    
    def __init__(self, router: MessageRouter):
        self.router = router
        self.shared_resources: Dict[str, Any] = {}
        self.resource_locks: Dict[str, str] = {}  # resource_id -> agent_id
        self.resource_queues: Dict[str, List[str]] = {}  # resource_id -> waiting agents
        self.logger = logging.getLogger('ResourceManager')
    
    async def request_resource(self, agent_id: str, resource_id: str, 
                             resource_type: str, timeout_seconds: int = 300) -> bool:
        """Solicitar acceso a recurso compartido"""
        
        # Verificar si el recurso está disponible
        if resource_id not in self.resource_locks:
            # Recurso disponible, asignar inmediatamente
            self.resource_locks[resource_id] = agent_id
            
            # Notificar al agente
            response_message = MCPMessage(
                id=str(uuid.uuid4()),
                type=MessageType.RESOURCE_RESPONSE,
                sender_id="resource_manager",
                recipient_id=agent_id,
                payload={
                    "resource_id": resource_id,
                    "granted": True,
                    "resource_data": self.shared_resources.get(resource_id, {})
                }
            )
            
            await self.router.route_message(response_message)
            self.logger.info(f"Resource {resource_id} granted to {agent_id}")
            return True
        
        else:
            # Recurso ocupado, agregar a cola de espera
            if resource_id not in self.resource_queues:
                self.resource_queues[resource_id] = []
            
            self.resource_queues[resource_id].append(agent_id)
            self.logger.info(f"Resource {resource_id} busy, {agent_id} added to queue")
            
            # TODO: Implementar timeout y notificación cuando se libere
            return False
    
    async def release_resource(self, agent_id: str, resource_id: str) -> bool:
        """Liberar recurso compartido"""
        
        if resource_id not in self.resource_locks:
            return False
        
        if self.resource_locks[resource_id] != agent_id:
            self.logger.warning(f"Agent {agent_id} trying to release resource {resource_id} not owned")
            return False
        
        # Liberar recurso
        del self.resource_locks[resource_id]
        
        # Procesar cola de espera
        if resource_id in self.resource_queues and self.resource_queues[resource_id]:
            next_agent = self.resource_queues[resource_id].pop(0)
            await self.request_resource(next_agent, resource_id, "queued")
        
        self.logger.info(f"Resource {resource_id} released by {agent_id}")
        return True
    
    def add_shared_resource(self, resource_id: str, resource_data: Any):
        """Agregar recurso compartido"""
        self.shared_resources[resource_id] = resource_data
        self.logger.info(f"Shared resource {resource_id} added")


class MCPCommunicationManager:
    """Manager principal del protocolo MCP"""
    
    def __init__(self):
        self.router = MessageRouter()
        self.collaboration = CollaborationProtocol(self.router)
        self.resources = ResourceManager(self.router)
        self.health_monitor = HealthMonitor(self.router)
        self.logger = logging.getLogger('MCPCommunicationManager')
        
        # Métricas
        self.metrics = {
            "messages_sent": 0,
            "messages_received": 0,
            "collaborations_initiated": 0,
            "collaborations_successful": 0,
            "resource_requests": 0,
            "active_agents": 0
        }
    
    async def initialize(self):
        """Inicializar el sistema MCP"""
        self.logger.info("Initializing MCP Communication Manager")
        
        # Iniciar monitoreo de salud
        await self.health_monitor.start_monitoring()
        
        self.logger.info("MCP Communication Manager initialized")
    
    def register_agent(self, agent_id: str, agent: AgentInterface):
        """Registrar agente en el sistema MCP"""
        self.router.register_agent(agent_id, agent)
        self.metrics["active_agents"] += 1
    
    def unregister_agent(self, agent_id: str):
        """Desregistrar agente del sistema MCP"""
        self.router.unregister_agent(agent_id)
        self.metrics["active_agents"] = max(0, self.metrics["active_agents"] - 1)
    
    async def send_message(self, message: MCPMessage) -> bool:
        """Enviar mensaje a través del sistema MCP"""
        success = await self.router.route_message(message)
        if success:
            self.metrics["messages_sent"] += 1
        return success
    
    async def broadcast_status_update(self, sender_id: str, status_data: Dict[str, Any]) -> int:
        """Enviar actualización de estado a todos los agentes"""
        broadcast_message = MCPMessage(
            id=str(uuid.uuid4()),
            type=MessageType.STATUS_UPDATE,
            sender_id=sender_id,
            recipient_id="broadcast",
            payload=status_data
        )
        
        return await self.router.broadcast_message(broadcast_message)
    
    async def request_agent_collaboration(self, requester_id: str, target_id: str, 
                                        task_info: Dict[str, Any]) -> str:
        """Solicitar colaboración entre agentes"""
        collaboration_id = await self.collaboration.request_collaboration(
            requester_id, target_id, task_info
        )
        self.metrics["collaborations_initiated"] += 1
        return collaboration_id
    
    async def shutdown_all_agents(self) -> Dict[str, bool]:
        """Shutdown graceful de todos los agentes"""
        results = {}
        
        for agent_id in self.router.get_agent_list():
            shutdown_message = MCPMessage(
                id=str(uuid.uuid4()),
                type=MessageType.SHUTDOWN,
                sender_id="mcp_manager",
                recipient_id=agent_id,
                payload={"reason": "system_shutdown"},
                priority=MessagePriority.CRITICAL
            )
            
            success = await self.router.route_message(shutdown_message)
            results[agent_id] = success
        
        return results
    
    def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado del sistema MCP"""
        return {
            "active_agents": self.metrics["active_agents"],
            "metrics": self.metrics,
            "active_collaborations": len(self.collaboration.get_active_collaborations()),
            "resource_locks": len(self.resources.resource_locks),
            "message_queue_size": len(self.router.pending_acks)
        }


class HealthMonitor:
    """Monitor de salud para agentes MCP"""
    
    def __init__(self, router: MessageRouter):
        self.router = router
        self.health_status: Dict[str, Dict[str, Any]] = {}
        self.monitoring_active = False
        self.logger = logging.getLogger('HealthMonitor')
    
    async def start_monitoring(self, interval_seconds: int = 30):
        """Iniciar monitoreo de salud"""
        self.monitoring_active = True
        
        async def monitor_loop():
            while self.monitoring_active:
                await self.check_all_agents_health()
                await asyncio.sleep(interval_seconds)
        
        # Ejecutar en background
        asyncio.create_task(monitor_loop())
        self.logger.info("Health monitoring started")
    
    async def check_all_agents_health(self):
        """Verificar salud de todos los agentes"""
        for agent_id in self.router.get_agent_list():
            await self.check_agent_health(agent_id)
    
    async def check_agent_health(self, agent_id: str) -> Dict[str, Any]:
        """Verificar salud de un agente específico"""
        try:
            # Enviar ping de salud
            health_message = MCPMessage(
                id=str(uuid.uuid4()),
                type=MessageType.HEALTH_CHECK,
                sender_id="health_monitor",
                recipient_id=agent_id,
                payload={"timestamp": datetime.now().isoformat()},
                ttl=datetime.now() + timedelta(seconds=10)
            )
            
            # TODO: Implementar respuesta de health check
            # Por ahora, asumir que si el agente está registrado, está saludable
            
            health_status = {
                "status": "healthy",
                "last_check": datetime.now(),
                "response_time_ms": 0  # TODO: Medir tiempo real de respuesta
            }
            
            self.health_status[agent_id] = health_status
            return health_status
            
        except Exception as e:
            self.logger.error(f"Health check failed for agent {agent_id}: {e}")
            
            health_status = {
                "status": "unhealthy",
                "last_check": datetime.now(),
                "error": str(e)
            }
            
            self.health_status[agent_id] = health_status
            return health_status
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Obtener salud general del sistema"""
        if not self.health_status:
            return {"status": "unknown", "healthy_agents": 0, "total_agents": 0}
        
        healthy_count = sum(1 for status in self.health_status.values() 
                          if status.get("status") == "healthy")
        total_count = len(self.health_status)
        
        overall_status = "healthy" if healthy_count == total_count else "degraded"
        if healthy_count == 0:
            overall_status = "critical"
        
        return {
            "status": overall_status,
            "healthy_agents": healthy_count,
            "total_agents": total_count,
            "health_percentage": (healthy_count / total_count) * 100 if total_count > 0 else 0
        }