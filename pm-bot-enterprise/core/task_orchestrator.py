# core/task_orchestrator.py
"""
Task Orchestrator - Coordina la ejecución de tareas entre módulos y agentes
"""

import asyncio
import json
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import logging

from .agent_spawner import AgentSpawner, AgentTask, AgentConfig
from .module_manager import ModuleManager


@dataclass
class ExecutionPlan:
    project_id: str
    phases: List[List[str]]  # Lista de fases, cada fase contiene módulos que pueden ejecutarse en paralelo
    dependencies: Dict[str, List[str]]
    estimated_duration: timedelta
    critical_path: List[str]


class TaskOrchestrator:
    """
    Orquestador de tareas que coordina la ejecución de módulos y agentes
    """
    
    def __init__(self):
        self.agent_spawner = AgentSpawner()
        self.module_manager = ModuleManager()
        self.logger = logging.getLogger('TaskOrchestrator')
        
        # Estado de ejecución
        self.active_executions: Dict[str, Dict[str, Any]] = {}
        self.execution_metrics: Dict[str, Dict[str, Any]] = {}
        
        # Cola de tareas
        self.task_queue: List[AgentTask] = []
        self.running_tasks: Dict[str, AgentTask] = {}
        
        # Configuración
        self.max_concurrent_tasks = 10
        self.task_timeout = timedelta(hours=2)
    
    async def execute_module(self, project_id: str, module_name: str, 
                           agents: List[AgentConfig]) -> Dict[str, Any]:
        """
        Ejecutar un módulo completo con sus agentes asignados
        
        Args:
            project_id: ID del proyecto
            module_name: Nombre del módulo
            agents: Lista de agentes asignados al módulo
            
        Returns:
            Dict con resultados de la ejecución
        """
        
        execution_id = f"{project_id}_{module_name}_{int(datetime.now().timestamp())}"
        
        self.logger.info(f"Starting module execution: {module_name} (ID: {execution_id})")
        
        # Inicializar estado de ejecución
        execution_state = {
            "id": execution_id,
            "project_id": project_id,
            "module_name": module_name,
            "status": "running",
            "start_time": datetime.now(),
            "agents": [agent.id for agent in agents],
            "tasks": [],
            "progress": 0.0,
            "results": {}
        }
        
        self.active_executions[execution_id] = execution_state
        
        try:
            # Crear plan de ejecución para el módulo
            task_plan = await self._create_module_task_plan(module_name, agents)
            execution_state["tasks"] = [task.id for task in task_plan]
            
            # Ejecutar tareas según el plan
            results = await self._execute_task_plan(task_plan, execution_state)
            
            # Procesar resultados finales
            final_result = await self._process_module_results(module_name, results)
            
            execution_state["status"] = "completed"
            execution_state["end_time"] = datetime.now()
            execution_state["results"] = final_result
            execution_state["progress"] = 100.0
            
            self.logger.info(f"Module {module_name} completed successfully")
            
            return final_result
            
        except Exception as e:
            execution_state["status"] = "failed"
            execution_state["end_time"] = datetime.now()
            execution_state["error"] = str(e)
            
            self.logger.error(f"Module {module_name} execution failed: {e}")
            raise
        
        finally:
            # Limpiar estado de ejecución
            if execution_id in self.active_executions:
                self._archive_execution(execution_id)
    
    async def _create_module_task_plan(self, module_name: str, 
                                     agents: List[AgentConfig]) -> List[AgentTask]:
        """Crear plan de tareas para un módulo"""
        
        task_plan = []
        
        # Definir secuencia estándar de tareas por tipo de módulo
        task_sequences = {
            'backend': [
                ('design', 'Design API structure and database schema'),
                ('implement', 'Implement core functionality and endpoints'),
                ('test', 'Create and run unit tests'),
                ('review', 'Code review and optimization')
            ],
            'frontend': [
                ('design', 'Design component structure and user flows'),
                ('implement', 'Implement UI components and state management'),
                ('test', 'Create and run component tests'),
                ('review', 'UI/UX review and optimization')
            ],
            'fullstack': [
                ('design', 'Design full-stack architecture'),
                ('implement_backend', 'Implement backend functionality'),
                ('implement_frontend', 'Implement frontend components'),
                ('integrate', 'Integrate frontend with backend'),
                ('test', 'End-to-end testing'),
                ('review', 'Full-stack review')
            ],
            'mobile': [
                ('design', 'Design mobile app architecture and UI'),
                ('implement', 'Implement mobile app features'),
                ('test', 'Mobile app testing on devices'),
                ('review', 'App store readiness review')
            ],
            'qa': [
                ('plan', 'Create comprehensive test plan'),
                ('implement', 'Implement automated tests'),
                ('execute', 'Execute test suites'),
                ('report', 'Generate test reports and recommendations')
            ],
            'deploy': [
                ('plan', 'Plan deployment strategy'),
                ('configure', 'Configure infrastructure and CI/CD'),
                ('deploy', 'Deploy to staging and production'),
                ('monitor', 'Setup monitoring and alerts')
            ]
        }
        
        # Determinar tipo de módulo basado en agentes
        module_type = self._determine_module_type(agents)
        sequence = task_sequences.get(module_type, task_sequences['backend'])
        
        # Crear tareas específicas
        for i, (task_type, description) in enumerate(sequence):
            task = AgentTask(
                id=f"{module_name}_{task_type}_{int(datetime.now().timestamp())}_{i}",
                agent_id="",  # Se asignará después
                module_name=module_name,
                task_type=task_type,
                description=f"{module_name}: {description}",
                priority=10 - i,  # Tareas tempranas tienen mayor prioridad
                dependencies=[],
                created_at=datetime.now()
            )
            
            # Asignar agente más apropiado para la tarea
            assigned_agent = self._assign_agent_to_task(task, agents)
            if assigned_agent:
                task.agent_id = assigned_agent.id
                task_plan.append(task)
        
        # Configurar dependencias entre tareas
        self._configure_task_dependencies(task_plan)
        
        return task_plan
    
    def _determine_module_type(self, agents: List[AgentConfig]) -> str:
        """Determinar tipo de módulo basado en roles de agentes"""
        roles = [agent.role for agent in agents]
        
        if 'qa' in roles:
            return 'qa'
        elif 'devops' in roles:
            return 'deploy'
        elif 'mobile' in roles:
            return 'mobile'
        elif 'fullstack' in roles:
            return 'fullstack'
        elif 'frontend' in roles and 'backend' in roles:
            return 'fullstack'
        elif 'frontend' in roles:
            return 'frontend'
        else:
            return 'backend'
    
    def _assign_agent_to_task(self, task: AgentTask, agents: List[AgentConfig]) -> Optional[AgentConfig]:
        """Asignar el agente más apropiado para una tarea"""
        
        # Mapeo de tipos de tarea a roles preferidos
        task_role_mapping = {
            'design': ['backend', 'frontend', 'fullstack'],
            'implement': ['backend', 'frontend', 'fullstack'],
            'implement_backend': ['backend', 'fullstack'],
            'implement_frontend': ['frontend', 'fullstack'],
            'integrate': ['fullstack', 'backend'],
            'test': ['qa', 'backend', 'frontend'],
            'review': ['backend', 'frontend', 'fullstack'],
            'plan': ['qa', 'devops'],
            'configure': ['devops'],
            'deploy': ['devops'],
            'monitor': ['devops'],
            'execute': ['qa'],
            'report': ['qa']
        }
        
        preferred_roles = task_role_mapping.get(task.task_type, ['backend'])
        
        # Buscar agente con rol preferido
        for role in preferred_roles:
            for agent in agents:
                if agent.role == role and agent.status == "idle":
                    return agent
        
        # Fallback: cualquier agente disponible
        for agent in agents:
            if agent.status == "idle":
                return agent
        
        return None
    
    def _configure_task_dependencies(self, tasks: List[AgentTask]):
        """Configurar dependencias entre tareas del módulo"""
        
        # Crear mapeo de tipos de tarea a tareas
        task_by_type = {task.task_type: task for task in tasks}
        
        # Configurar dependencias estándar
        dependency_rules = {
            'implement': ['design'],
            'implement_backend': ['design'],
            'implement_frontend': ['design'],
            'integrate': ['implement_backend', 'implement_frontend'],
            'test': ['implement', 'implement_backend', 'implement_frontend', 'integrate'],
            'review': ['test'],
            'configure': ['plan'],
            'deploy': ['configure'],
            'monitor': ['deploy'],
            'execute': ['implement'],
            'report': ['execute']
        }
        
        for task in tasks:
            dependencies = dependency_rules.get(task.task_type, [])
            for dep_type in dependencies:
                if dep_type in task_by_type:
                    task.dependencies.append(task_by_type[dep_type].id)
    
    async def _execute_task_plan(self, tasks: List[AgentTask], 
                               execution_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Ejecutar plan de tareas respetando dependencias"""
        
        results = []
        completed_tasks = set()
        
        while len(completed_tasks) < len(tasks):
            # Encontrar tareas listas para ejecutar
            ready_tasks = [
                task for task in tasks 
                if (task.id not in completed_tasks and 
                    all(dep_id in completed_tasks for dep_id in task.dependencies))
            ]
            
            if not ready_tasks:
                # Verificar si hay deadlock
                remaining_tasks = [t for t in tasks if t.id not in completed_tasks]
                if remaining_tasks:
                    self.logger.error(f"Potential deadlock detected with tasks: {[t.id for t in remaining_tasks]}")
                break
            
            # Ejecutar tareas listas en paralelo (limitado por concurrencia)
            batch_size = min(len(ready_tasks), self.max_concurrent_tasks)
            batch_tasks = ready_tasks[:batch_size]
            
            # Crear corrutinas para ejecución paralela
            task_coroutines = [
                self._execute_single_task(task, execution_state)
                for task in batch_tasks
            ]
            
            # Ejecutar batch y esperar resultados
            batch_results = await asyncio.gather(*task_coroutines, return_exceptions=True)
            
            # Procesar resultados del batch
            for i, result in enumerate(batch_results):
                task = batch_tasks[i]
                
                if isinstance(result, Exception):
                    self.logger.error(f"Task {task.id} failed: {result}")
                    task.status = "failed"
                    task.error = str(result)
                else:
                    task.status = "completed"
                    task.result = result
                    results.append(result)
                
                completed_tasks.add(task.id)
            
            # Actualizar progreso
            progress = (len(completed_tasks) / len(tasks)) * 100
            execution_state["progress"] = progress
            
            self.logger.info(f"Module progress: {progress:.1f}% ({len(completed_tasks)}/{len(tasks)} tasks)")
        
        return results
    
    async def _execute_single_task(self, task: AgentTask, 
                                 execution_state: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar una tarea individual"""
        
        self.logger.info(f"Executing task: {task.description}")
        
        try:
            # Asignar tarea al agente
            success = await self.agent_spawner.assign_task_to_agent(task.agent_id, task)
            
            if not success:
                raise Exception(f"Could not assign task to agent {task.agent_id}")
            
            # Ejecutar tarea
            result = await self.agent_spawner.execute_agent_task(task.agent_id, task)
            
            # Validar resultado
            if not result or result.get("quality_score", 0) < 0.3:
                self.logger.warning(f"Task {task.id} produced low quality result")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
            raise
    
    async def _process_module_results(self, module_name: str, 
                                    results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Procesar y consolidar resultados del módulo"""
        
        # Consolidar todos los entregables
        all_deliverables = {}
        all_code = []
        all_files = []
        
        for result in results:
            deliverables = result.get("deliverables", {})
            
            if "code" in deliverables:
                all_code.extend(deliverables["code"])
            
            if "files" in deliverables:
                all_files.extend(deliverables["files"])
            
            # Agregar otros entregables
            for key, value in deliverables.items():
                if key not in ["code", "files"]:
                    if key not in all_deliverables:
                        all_deliverables[key] = []
                    all_deliverables[key].append(value)
        
        # Generar estructura de archivos del módulo
        file_structure = await self._generate_module_file_structure(
            module_name, all_code, all_files
        )
        
        # Calcular métricas del módulo
        metrics = self._calculate_module_metrics(results)
        
        return {
            "module_name": module_name,
            "status": "completed",
            "deliverables": all_deliverables,
            "code_blocks": all_code,
            "files": all_files,
            "file_structure": file_structure,
            "metrics": metrics,
            "summary": self._generate_module_summary(module_name, results)
        }
    
    async def _generate_module_file_structure(self, module_name: str, 
                                            code_blocks: List[Dict], 
                                            files: List[Dict]) -> Dict[str, Any]:
        """Generar estructura de archivos para el módulo"""
        
        # Crear estructura base
        structure = {
            "root": f"./{module_name}/",
            "directories": [],
            "files": []
        }
        
        # Mapear bloques de código a archivos
        for i, code_block in enumerate(code_blocks):
            language = code_block.get("language", "text")
            
            # Determinar extensión de archivo
            extension_map = {
                "javascript": "js",
                "typescript": "ts",
                "python": "py",
                "html": "html",
                "css": "css",
                "json": "json",
                "yaml": "yml",
                "sql": "sql"
            }
            
            extension = extension_map.get(language, "txt")
            filename = f"{module_name}_{i+1}.{extension}"
            
            structure["files"].append({
                "name": filename,
                "path": f"{structure['root']}{filename}",
                "type": language,
                "size": len(code_block.get("code", "")),
                "content": code_block.get("code", "")
            })
        
        # Agregar archivos detectados
        for file_info in files:
            if file_info.get("name"):
                structure["files"].append({
                    "name": file_info["name"],
                    "path": f"{structure['root']}{file_info['name']}",
                    "type": file_info.get("type", "unknown"),
                    "detected": True
                })
        
        return structure
    
    def _calculate_module_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcular métricas del módulo"""
        
        if not results:
            return {}
        
        # Métricas básicas
        total_tasks = len(results)
        successful_tasks = len([r for r in results if r.get("quality_score", 0) > 0.5])
        
        # Puntuación de calidad promedio
        quality_scores = [r.get("quality_score", 0) for r in results]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Líneas de código generadas
        total_code_lines = 0
        for result in results:
            code_blocks = result.get("deliverables", {}).get("code", [])
            for block in code_blocks:
                total_code_lines += block.get("lines", 0)
        
        return {
            "total_tasks": total_tasks,
            "successful_tasks": successful_tasks,
            "success_rate": successful_tasks / total_tasks if total_tasks > 0 else 0,
            "average_quality_score": avg_quality,
            "total_code_lines": total_code_lines,
            "deliverables_count": sum(len(r.get("deliverables", {})) for r in results)
        }
    
    def _generate_module_summary(self, module_name: str, 
                               results: List[Dict[str, Any]]) -> str:
        """Generar resumen del módulo"""
        
        metrics = self._calculate_module_metrics(results)
        
        summary = f"""
Module: {module_name}
Status: Completed Successfully
Tasks Executed: {metrics.get('total_tasks', 0)}
Success Rate: {metrics.get('success_rate', 0):.1%}
Quality Score: {metrics.get('average_quality_score', 0):.2f}/1.0
Code Generated: {metrics.get('total_code_lines', 0)} lines
Deliverables: {metrics.get('deliverables_count', 0)} items

The {module_name} module has been successfully implemented with all required functionality.
        """.strip()
        
        return summary
    
    # Métodos para QA y Deployment globales
    
    async def execute_global_qa(self, project_id: str) -> Dict[str, Any]:
        """Ejecutar testing y QA global del proyecto"""
        
        self.logger.info(f"Starting global QA for project {project_id}")
        
        # Crear agente de QA global
        qa_agents = await self.agent_spawner.spawn_agents_for_module(
            "global_qa", 
            self._get_qa_module_spec(),
            self._get_project_config(project_id)
        )
        
        # Ejecutar QA global
        qa_result = await self.execute_module(project_id, "global_qa", qa_agents)
        
        return qa_result
    
    async def execute_deployment(self, project_id: str) -> Dict[str, Any]:
        """Ejecutar deployment del proyecto"""
        
        self.logger.info(f"Starting deployment for project {project_id}")
        
        # Crear agente de deployment
        deploy_agents = await self.agent_spawner.spawn_agents_for_module(
            "deployment",
            self._get_deploy_module_spec(),
            self._get_project_config(project_id)
        )
        
        # Ejecutar deployment
        deploy_result = await self.execute_module(project_id, "deployment", deploy_agents)
        
        return deploy_result
    
    def _get_qa_module_spec(self):
        """Obtener especificación del módulo de QA"""
        from .planner import ModuleSpec
        
        return ModuleSpec(
            name="global_qa",
            type="qa",
            description="Global testing and quality assurance",
            dependencies=[],
            agents_needed=["qa"],
            complexity=3,
            estimated_hours=15,
            tech_stack=["Jest", "Cypress", "Postman"],
            apis_needed=[],
            database_entities=[]
        )
    
    def _get_deploy_module_spec(self):
        """Obtener especificación del módulo de deployment"""
        from .planner import ModuleSpec
        
        return ModuleSpec(
            name="deployment",
            type="deploy",
            description="Project deployment and DevOps setup",
            dependencies=[],
            agents_needed=["devops"],
            complexity=2,
            estimated_hours=10,
            tech_stack=["Docker", "AWS", "GitHub Actions"],
            apis_needed=[],
            database_entities=[]
        )
    
    def _get_project_config(self, project_id: str):
        """Obtener configuración del proyecto (mock)"""
        from .pm_bot import ProjectConfig
        
        return ProjectConfig(
            name=f"project_{project_id}",
            description="Enterprise project",
            complexity=5,
            timeline="3 months",
            budget="medium",
            requirements=[],
            tech_stack=["Node.js", "React", "PostgreSQL"],
            team_size=6
        )
    
    # Métodos de control y monitoreo
    
    async def pause_project_execution(self, project_id: str):
        """Pausar ejecución del proyecto"""
        executions = [
            exec_id for exec_id, execution in self.active_executions.items()
            if execution["project_id"] == project_id
        ]
        
        for exec_id in executions:
            self.active_executions[exec_id]["status"] = "paused"
        
        self.logger.info(f"Paused {len(executions)} executions for project {project_id}")
    
    async def resume_project_execution(self, project_id: str):
        """Reanudar ejecución del proyecto"""
        executions = [
            exec_id for exec_id, execution in self.active_executions.items()
            if execution["project_id"] == project_id and execution["status"] == "paused"
        ]
        
        for exec_id in executions:
            self.active_executions[exec_id]["status"] = "running"
        
        self.logger.info(f"Resumed {len(executions)} executions for project {project_id}")
    
    async def get_project_metrics(self, project_id: str) -> Dict[str, Any]:
        """Obtener métricas en tiempo real del proyecto"""
        
        # Buscar ejecuciones del proyecto
        project_executions = [
            execution for execution in self.active_executions.values()
            if execution["project_id"] == project_id
        ]
        
        if not project_executions:
            return {"error": "No active executions found for project"}
        
        # Calcular métricas agregadas
        total_modules = len(project_executions)
        completed_modules = len([e for e in project_executions if e["status"] == "completed"])
        failed_modules = len([e for e in project_executions if e["status"] == "failed"])
        
        # Progreso promedio
        total_progress = sum(e.get("progress", 0) for e in project_executions)
        avg_progress = total_progress / total_modules if total_modules > 0 else 0
        
        # Agentes activos
        all_agents = set()
        for execution in project_executions:
            all_agents.update(execution.get("agents", []))
        
        active_agents = len([
            agent_id for agent_id in all_agents
            if self.agent_spawner.active_agents.get(agent_id, {}).get("status") == "working"
        ])
        
        return {
            "project_id": project_id,
            "total_modules": total_modules,
            "completed_modules": completed_modules,
            "failed_modules": failed_modules,
            "in_progress_modules": total_modules - completed_modules - failed_modules,
            "overall_progress": avg_progress,
            "active_agents": active_agents,
            "total_agents": len(all_agents),
            "execution_details": [
                {
                    "module": e["module_name"],
                    "status": e["status"],
                    "progress": e.get("progress", 0),
                    "start_time": e["start_time"].isoformat() if e.get("start_time") else None
                }
                for e in project_executions
            ]
        }
    
    def get_agent_utilization(self) -> Dict[str, Any]:
        """Obtener utilización de agentes del orquestador"""
        return self.agent_spawner.get_agent_utilization()
    
    def _archive_execution(self, execution_id: str):
        """Archivar ejecución completada"""
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            
            # Guardar métricas
            self.execution_metrics[execution_id] = {
                "module_name": execution["module_name"],
                "project_id": execution["project_id"],
                "status": execution["status"],
                "duration": (execution.get("end_time", datetime.now()) - execution["start_time"]).total_seconds(),
                "progress": execution.get("progress", 0),
                "tasks_count": len(execution.get("tasks", []))
            }
            
            # Remover de ejecuciones activas
            del self.active_executions[execution_id]
    
    def get_execution_history(self, project_id: str = None) -> List[Dict[str, Any]]:
        """Obtener historial de ejecuciones"""
        history = list(self.execution_metrics.values())
        
        if project_id:
            history = [h for h in history if h["project_id"] == project_id]
        
        return sorted(history, key=lambda x: x.get("duration", 0), reverse=True)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de performance del orquestador"""
        all_executions = list(self.execution_metrics.values())
        
        if not all_executions:
            return {"message": "No execution history available"}
        
        successful_executions = [e for e in all_executions if e["status"] == "completed"]
        failed_executions = [e for e in all_executions if e["status"] == "failed"]
        
        avg_duration = sum(e["duration"] for e in successful_executions) / len(successful_executions) if successful_executions else 0
        
        return {
            "total_executions": len(all_executions),
            "successful_executions": len(successful_executions),
            "failed_executions": len(failed_executions),
            "success_rate": len(successful_executions) / len(all_executions) if all_executions else 0,
            "average_duration_seconds": avg_duration,
            "active_executions": len(self.active_executions),
            "agent_utilization": self.get_agent_utilization()
        }


# core/module_manager.py
"""
Module Manager - Gestiona estados y dependencias de módulos
"""

import json
import os
from typing import Dict, List, Any
from datetime import datetime
import logging


class ModuleManager:
    """
    Gestor de módulos que controla estados y dependencias
    """
    
    def __init__(self):
        self.logger = logging.getLogger('ModuleManager')
        self.modules_status_file = "data/modules_status.json"
        self.modules_status: Dict[str, Dict[str, Any]] = {}
        
        self.load_modules_status()
    
    def load_modules_status(self):
        """Cargar estado de módulos desde archivo"""
        try:
            if os.path.exists(self.modules_status_file):
                with open(self.modules_status_file, 'r') as f:
                    self.modules_status = json.load(f)
            else:
                self.modules_status = {}
        except Exception as e:
            self.logger.error(f"Error loading modules status: {e}")
            self.modules_status = {}
    
    def save_modules_status(self):
        """Guardar estado de módulos"""
        try:
            os.makedirs(os.path.dirname(self.modules_status_file), exist_ok=True)
            with open(self.modules_status_file, 'w') as f:
                json.dump(self.modules_status, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error saving modules status: {e}")
    
    def create_execution_plan(self, modules: Dict[str, Any]) -> List[List[str]]:
        """
        Crear plan de ejecución respetando dependencias
        
        Args:
            modules: Diccionario de módulos con sus dependencias
            
        Returns:
            Lista de fases, cada fase contiene módulos que pueden ejecutarse en paralelo
        """
        
        # Convertir módulos a formato simple para análisis de dependencias
        module_deps = {}
        for name, module in modules.items():
            if hasattr(module, 'dependencies'):
                module_deps[name] = module.dependencies
            else:
                module_deps[name] = module.get('dependencies', [])
        
        # Algoritmo de ordenamiento topológico
        phases = []
        remaining_modules = set(module_deps.keys())
        completed_modules = set()
        
        while remaining_modules:
            # Encontrar módulos sin dependencias pendientes
            ready_modules = []
            for module in remaining_modules:
                dependencies = module_deps[module]
                if all(dep in completed_modules for dep in dependencies if dep in module_deps):
                    ready_modules.append(module)
            
            if not ready_modules:
                # Posible ciclo de dependencias - romper eligiendo uno arbitrariamente
                self.logger.warning("Possible dependency cycle detected, breaking with arbitrary choice")
                ready_modules = [next(iter(remaining_modules))]
            
            # Agregar fase con módulos listos
            phases.append(ready_modules)
            
            # Actualizar conjuntos
            for module in ready_modules:
                remaining_modules.remove(module)
                completed_modules.add(module)
        
        self.logger.info(f"Created execution plan with {len(phases)} phases")
        return phases
    
    def update_module_status(self, module_name: str, status: str, **kwargs):
        """Actualizar estado de un módulo"""
        
        if module_name not in self.modules_status:
            self.modules_status[module_name] = {}
        
        self.modules_status[module_name].update({
            "status": status,
            "updated_at": datetime.now().isoformat(),
            **kwargs
        })
        
        self.save_modules_status()
        self.logger.info(f"Module {module_name} status updated to: {status}")
    
    def get_module_status(self, module_name: str) -> Dict[str, Any]:
        """Obtener estado de un módulo"""
        return self.modules_status.get(module_name, {"status": "unknown"})
    
    def get_all_modules_status(self) -> Dict[str, Dict[str, Any]]:
        """Obtener estado de todos los módulos"""
        return self.modules_status.copy()
    
    def validate_dependencies(self, modules: Dict[str, Any]) -> List[str]:
        """Validar que todas las dependencias existen"""
        
        errors = []
        module_names = set(modules.keys())
        
        for name, module in modules.items():
            dependencies = getattr(module, 'dependencies', [])
            for dep in dependencies:
                if dep not in module_names:
                    errors.append(f"Module '{name}' depends on non-existent module '{dep}'")
        
        return errors
    
    def get_dependency_graph(self, modules: Dict[str, Any]) -> Dict[str, List[str]]:
        """Obtener grafo de dependencias"""
        
        graph = {}
        for name, module in modules.items():
            dependencies = getattr(module, 'dependencies', [])
            graph[name] = dependencies
        
        return graph
    
    def calculate_critical_path(self, modules: Dict[str, Any]) -> List[str]:
        """Calcular ruta crítica del proyecto"""
        
        # Simplificado: la ruta más larga en términos de dependencias
        graph = self.get_dependency_graph(modules)
        
        def get_longest_path(node, visited=None):
            if visited is None:
                visited = set()
            
            if node in visited:
                return []
            
            visited.add(node)
            max_path = [node]
            
            dependencies = graph.get(node, [])
            for dep in dependencies:
                if dep in graph:
                    dep_path = get_longest_path(dep, visited.copy())
                    if len(dep_path) + 1 > len(max_path):
                        max_path = [node] + dep_path
            
            return max_path
        
        # Encontrar la ruta más larga
        longest_path = []
        for module in graph.keys():
            path = get_longest_path(module)
            if len(path) > len(longest_path):
                longest_path = path
        
        return longest_path