# core/pm_bot.py
"""
PM Bot Enterprise - Project Manager Core
Lógica central del sistema de gestión de proyectos con agentes IA
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from .planner import ProjectPlanner, ModuleSpec
from .agent_spawner import AgentSpawner
from .module_manager import ModuleManager
from .task_orchestrator import TaskOrchestrator



class ProjectStatus(Enum):
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class ProjectConfig:
    name: str
    description: str
    complexity: int  # 1-10
    timeline: str
    budget: str
    requirements: List[str]
    tech_stack: List[str]
    team_size: int
    compliance: List[str] = None


@dataclass
class ProjectState:
    id: str
    config: ProjectConfig
    status: ProjectStatus
    modules: Dict[str, Any]
    agents: Dict[str, Any]
    progress: float
    start_time: datetime
    estimated_completion: datetime
    actual_completion: Optional[datetime] = None
    metrics: Dict[str, Any] = None


class PMBotEnterprise:
    """
    Project Manager Bot Enterprise
    Sistema central que coordina todos los componentes del PM Bot
    """
    
    def __init__(self, config_path: str = "config/pm_config.json"):
        self.config_path = config_path
        self.projects: Dict[str, ProjectState] = {}
        self.active_project: Optional[str] = None
        
        # Componentes del sistema
        self.planner = ProjectPlanner()
        self.agent_spawner = AgentSpawner()
        self.module_manager = ModuleManager()
        self.orchestrator = TaskOrchestrator()
        
        # Estado del sistema
        self.system_metrics = {
            "projects_created": 0,
            "projects_completed": 0,
            "agents_spawned": 0,
            "modules_generated": 0,
            "success_rate": 0.0,
            "average_completion_time": 0.0
        }
        
        self.setup_logging()
        self.load_configuration()
    
    def setup_logging(self):
        """Configurar sistema de logging"""
        os.makedirs("logs", exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/pm_bot.log'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('PMBotEnterprise')
        self.logger.info("PM Bot Enterprise initialized")
    
    def load_configuration(self):
        """Cargar configuración del sistema"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = self.get_default_config()
                self.save_configuration()
            
            self.logger.info("Configuration loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            self.config = self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Configuración por defecto del sistema"""
        return {
            "max_concurrent_projects": 5,
            "default_team_size": 6,
            "supported_tech_stacks": [
                "MERN", "MEAN", "Django+React", "FastAPI+Vue", 
                "Next.js", "Laravel+Vue", "Rails+React"
            ],
            "agent_types": [
                "backend", "frontend", "fullstack", "qa", 
                "devops", "security", "data", "mobile"
            ],
            "deployment_targets": [
                "AWS", "Azure", "GCP", "Vercel", "Netlify", "DigitalOcean"
            ],
            "ai_models": {
                "primary": "deepseek-r1:14b",
                "fallback": ["claude-3-5-sonnet", "gpt-4o"],
                "local_models": ["deepseek-r1:14b", "qwen2.5-coder:7b", "llama3.2:latest"]
            }
        }
    
    def save_configuration(self):
        """Guardar configuración actual"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    async def create_project(self, prompt: str, **kwargs) -> str:
        """
        Crear nuevo proyecto desde prompt del usuario
        
        Args:
            prompt: Descripción del proyecto del usuario
            **kwargs: Parámetros adicionales (budget, timeline, etc.)
        
        Returns:
            project_id: ID único del proyecto creado
        """
        project_id = f"project_{int(datetime.now().timestamp())}"
        
        self.logger.info(f"Creating project {project_id}: {prompt[:100]}...")
        
        try:
            # 1. Analizar prompt y generar configuración
            project_config = await self.planner.analyze_prompt(prompt, **kwargs)
            
            # 2. Crear estado inicial del proyecto
            project_state = ProjectState(
                id=project_id,
                config=project_config,
                status=ProjectStatus.PLANNING,
                modules={},
                agents={},
                progress=0.0,
                start_time=datetime.now(),
                estimated_completion=self.planner.estimate_completion_time(project_config),
                metrics={}
            )
            
            # 3. Generar módulos del proyecto
            modules = await self.planner.generate_modules(project_config)
            project_state.modules = modules
            
            # 4. Registrar proyecto
            self.projects[project_id] = project_state
            self.active_project = project_id
            
            # 5. Actualizar métricas
            self.system_metrics["projects_created"] += 1
            self.system_metrics["modules_generated"] += len(modules)
            
            # 6. Persistir estado
            await self.save_project_state(project_id)
            
            self.logger.info(f"Project {project_id} created with {len(modules)} modules")
            
            return project_id
            
        except Exception as e:
            self.logger.error(f"Error creating project: {e}")
            raise
    
    async def execute_project(self, project_id: str) -> bool:
        """
        Ejecutar proyecto completo
        
        Args:
            project_id: ID del proyecto a ejecutar
            
        Returns:
            success: True si el proyecto se completó exitosamente
        """
        if project_id not in self.projects:
            raise ValueError(f"Project {project_id} not found")
        
        project = self.projects[project_id]
        project.status = ProjectStatus.IN_PROGRESS
        
        self.logger.info(f"Executing project {project_id}")
        
        try:
            # 1. Generar agentes para cada módulo
            for module_name, module_config in project.modules.items():
                agents = await self.agent_spawner.spawn_agents_for_module(
                    module_name, module_config, project.config
                )
                project.agents[module_name] = agents
                self.system_metrics["agents_spawned"] += len(agents)
            
            # 2. Ejecutar módulos en paralelo (respetando dependencias)
            execution_plan = self.module_manager.create_execution_plan(project.modules)
            
            for phase in execution_plan:
                # Ejecutar módulos de esta fase en paralelo
                tasks = []
                for module_name in phase:
                    task = self.orchestrator.execute_module(
                        project_id, module_name, project.agents[module_name]
                    )
                    tasks.append(task)
                
                # Esperar a que todos los módulos de la fase terminen
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Verificar resultados
                for i, result in enumerate(results):
                    module_name = phase[i]
                    if isinstance(result, Exception):
                        self.logger.error(f"Module {module_name} failed: {result}")
                        project.status = ProjectStatus.FAILED
                        return False
                    else:
                        self.logger.info(f"Module {module_name} completed successfully")
                
                # Actualizar progreso
                completed_modules = sum(1 for module in project.modules.values() 
                                     if module.get('status') == 'completed')
                project.progress = (completed_modules / len(project.modules)) * 100
                
                await self.save_project_state(project_id)
            
            # 3. Ejecutar testing global y deployment
            await self.orchestrator.execute_global_qa(project_id)
            await self.orchestrator.execute_deployment(project_id)
            
            # 4. Finalizar proyecto
            project.status = ProjectStatus.COMPLETED
            project.actual_completion = datetime.now()
            project.progress = 100.0
            
            # 5. Actualizar métricas del sistema
            self.system_metrics["projects_completed"] += 1
            completion_time = (project.actual_completion - project.start_time).total_seconds()
            self._update_average_completion_time(completion_time)
            self._update_success_rate()
            
            await self.save_project_state(project_id)
            
            self.logger.info(f"Project {project_id} completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing project {project_id}: {e}")
            project.status = ProjectStatus.FAILED
            await self.save_project_state(project_id)
            return False
    
    async def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Obtener estado actual del proyecto"""
        if project_id not in self.projects:
            raise ValueError(f"Project {project_id} not found")
        
        project = self.projects[project_id]
        
        # Obtener métricas en tiempo real
        real_time_metrics = await self.orchestrator.get_project_metrics(project_id)
        
        return {
            "id": project.id,
            "name": project.config.name,
            "status": project.status.value,
            "progress": project.progress,
            "modules": {
                name: {
                    "status": module.get("status", "pending"),
                    "progress": module.get("progress", 0),
                    "agents": len(project.agents.get(name, []))
                }
                for name, module in project.modules.items()
            },
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
    
    async def list_projects(self, status_filter: Optional[ProjectStatus] = None) -> List[Dict[str, Any]]:
        """Listar todos los proyectos con filtro opcional por estado"""
        projects = []
        
        for project_id, project in self.projects.items():
            if status_filter is None or project.status == status_filter:
                project_summary = {
                    "id": project.id,
                    "name": project.config.name,
                    "status": project.status.value,
                    "progress": project.progress,
                    "modules_count": len(project.modules),
                    "agents_count": sum(len(agents) for agents in project.agents.values()),
                    "start_time": project.start_time.isoformat(),
                    "complexity": project.config.complexity
                }
                projects.append(project_summary)
        
        return sorted(projects, key=lambda x: x["start_time"], reverse=True)
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Obtener métricas del sistema"""
        return {
            **self.system_metrics,
            "active_projects": len([p for p in self.projects.values() 
                                  if p.status == ProjectStatus.IN_PROGRESS]),
            "total_projects": len(self.projects),
            "system_uptime": self._get_system_uptime(),
            "memory_usage": self._get_memory_usage(),
            "agent_utilization": self.orchestrator.get_agent_utilization()
        }
    
    async def pause_project(self, project_id: str) -> bool:
        """Pausar proyecto en ejecución"""
        if project_id not in self.projects:
            return False
        
        project = self.projects[project_id]
        if project.status != ProjectStatus.IN_PROGRESS:
            return False
        
        project.status = ProjectStatus.PAUSED
        await self.orchestrator.pause_project_execution(project_id)
        await self.save_project_state(project_id)
        
        self.logger.info(f"Project {project_id} paused")
        return True
    
    async def resume_project(self, project_id: str) -> bool:
        """Reanudar proyecto pausado"""
        if project_id not in self.projects:
            return False
        
        project = self.projects[project_id]
        if project.status != ProjectStatus.PAUSED:
            return False
        
        project.status = ProjectStatus.IN_PROGRESS
        await self.orchestrator.resume_project_execution(project_id)
        await self.save_project_state(project_id)
        
        self.logger.info(f"Project {project_id} resumed")
        return True
    
    async def save_project_state(self, project_id: str):
        """Persistir estado del proyecto"""
        if project_id not in self.projects:
            return
        
        os.makedirs("data", exist_ok=True)
        project_file = f"data/project_{project_id}.json"
        
        project = self.projects[project_id]
        project_data = {
            "id": project.id,
            "config": asdict(project.config),
            "status": project.status.value,
            "modules": {name: asdict(module) for name, module in project.modules.items()},  # ← FIX AQUÍ
            "agents": project.agents,
            "progress": project.progress,
            "start_time": project.start_time.isoformat(),
            "estimated_completion": project.estimated_completion.isoformat(),
            "actual_completion": project.actual_completion.isoformat() 
                                if project.actual_completion else None,
            "metrics": project.metrics
        }
        
        with open(project_file, 'w') as f:
            json.dump(project_data, f, indent=2)
    
    async def load_project_state(self, project_id: str) -> bool:
        """Cargar estado del proyecto desde disco"""
        project_file = f"data/project_{project_id}.json"
        
        if not os.path.exists(project_file):
            return False
        
        try:
            with open(project_file, 'r') as f:
                project_data = json.load(f)
            
            config = ProjectConfig(**project_data["config"])

            modules = {}
            for name, module_data in project_data["modules"].items():
                modules[name] = ModuleSpec(**module_data)
            
            project = ProjectState(
                id=project_data["id"],
                config=config,
                status=ProjectStatus(project_data["status"]),
                modules=modules, 
                agents=project_data["agents"],
                progress=project_data["progress"],
                start_time=datetime.fromisoformat(project_data["start_time"]),
                estimated_completion=datetime.fromisoformat(project_data["estimated_completion"]),
                actual_completion=datetime.fromisoformat(project_data["actual_completion"]) 
                                if project_data["actual_completion"] else None,
                metrics=project_data.get("metrics", {})
            )
            
            self.projects[project_id] = project
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading project {project_id}: {e}")
            return False
    
    def _update_average_completion_time(self, completion_time: float):
        """Actualizar tiempo promedio de finalización"""
        completed = self.system_metrics["projects_completed"]
        if completed == 1:
            self.system_metrics["average_completion_time"] = completion_time
        else:
            current_avg = self.system_metrics["average_completion_time"]
            new_avg = ((current_avg * (completed - 1)) + completion_time) / completed
            self.system_metrics["average_completion_time"] = new_avg
    
    def _update_success_rate(self):
        """Actualizar tasa de éxito"""
        total = self.system_metrics["projects_created"]
        completed = self.system_metrics["projects_completed"]
        
        if total > 0:
            self.system_metrics["success_rate"] = (completed / total) * 100
    
    def _get_system_uptime(self) -> float:
        """Obtener tiempo de actividad del sistema en horas"""
        # Implementar lógica de uptime
        return 0.0
    
    def _get_memory_usage(self) -> Dict[str, Any]:
        """Obtener uso de memoria del sistema"""
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "rss": memory_info.rss / 1024 / 1024,  # MB
            "vms": memory_info.vms / 1024 / 1024,  # MB
            "percent": process.memory_percent()
        }


# Ejemplo de uso
async def main():
    """Ejemplo de uso del PM Bot Enterprise"""
    pm_bot = PMBotEnterprise()
    
    # Crear proyecto desde prompt
    project_id = await pm_bot.create_project(
        "Crear marketplace de productos artesanales con pagos Stripe, "
        "chat en tiempo real, reviews de productos, panel admin y app móvil",
        budget="startup",
        timeline="3 months",
        team_size=8
    )
    
    print(f"Proyecto creado: {project_id}")
    
    # Ejecutar proyecto
    success = await pm_bot.execute_project(project_id)
    
    if success:
        print("Proyecto completado exitosamente!")
        
        # Obtener estado final
        status = await pm_bot.get_project_status(project_id)
        print(f"Estado final: {status}")
        
        # Métricas del sistema
        metrics = pm_bot.get_system_metrics()
        print(f"Métricas del sistema: {metrics}")
    else:
        print("El proyecto falló durante la ejecución")


if __name__ == "__main__":
    asyncio.run(main())