# core/module_manager.py
"""
Module Manager - Gestiona estados, dependencias y ciclo de vida de módulos
"""

import json
import os
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from .planner import ModuleSpec


class ModuleStatus(Enum):
    """Estados de módulos"""
    PLANNED = "planned"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    WAITING_DEPENDENCY = "waiting_dependency"
    TESTING = "testing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ModuleState:
    """Estado completo de un módulo"""
    name: str
    spec: ModuleSpec
    status: ModuleStatus
    progress: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    assigned_agents: List[str] = None
    deliverables: Dict[str, Any] = None
    dependencies_met: List[str] = None
    blockers: List[str] = None
    metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.assigned_agents is None:
            self.assigned_agents = []
        if self.deliverables is None:
            self.deliverables = {}
        if self.dependencies_met is None:
            self.dependencies_met = []
        if self.blockers is None:
            self.blockers = []
        if self.metrics is None:
            self.metrics = {}


class ModuleManager:
    """
    Gestor completo de módulos que controla estados, dependencias y ejecución
    """
    
    def __init__(self):
        self.logger = logging.getLogger('ModuleManager')
        self.modules_file = "data/modules_state.json"
        self.modules: Dict[str, ModuleState] = {}
        
        # Configuración
        self.dependency_timeout = timedelta(hours=2)
        self.module_timeout = timedelta(hours=6)
        
        # Estado interno
        self.execution_order: List[List[str]] = []
        self.critical_path: List[str] = []
        
        self.load_modules_state()
    
    def load_modules_state(self):
        """Cargar estado de módulos desde archivo"""
        try:
            if os.path.exists(self.modules_file):
                with open(self.modules_file, 'r') as f:
                    data = json.load(f)
                
                # Reconstruir objetos ModuleState
                for module_name, module_data in data.items():
                    spec_data = module_data.pop('spec')
                    spec = ModuleSpec(**spec_data)
                    
                    # Convertir fechas
                    if module_data.get('start_time'):
                        module_data['start_time'] = datetime.fromisoformat(module_data['start_time'])
                    if module_data.get('end_time'):
                        module_data['end_time'] = datetime.fromisoformat(module_data['end_time'])
                    
                    module_data['status'] = ModuleStatus(module_data['status'])
                    module_state = ModuleState(spec=spec, **module_data)
                    self.modules[module_name] = module_state
                    
                self.logger.info(f"Loaded {len(self.modules)} modules from state file")
            else:
                self.modules = {}
                
        except Exception as e:
            self.logger.error(f"Error loading modules state: {e}")
            self.modules = {}
    
    def save_modules_state(self):
        """Guardar estado de módulos"""
        try:
            os.makedirs(os.path.dirname(self.modules_file), exist_ok=True)
            
            # Serializar módulos
            data = {}
            for name, module_state in self.modules.items():
                module_dict = asdict(module_state)
                
                # Convertir enums y fechas a strings
                module_dict['status'] = module_state.status.value
                if module_state.start_time:
                    module_dict['start_time'] = module_state.start_time.isoformat()
                if module_state.end_time:
                    module_dict['end_time'] = module_state.end_time.isoformat()
                
                data[name] = module_dict
            
            with open(self.modules_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Error saving modules state: {e}")
    
    def register_modules(self, modules_specs: Dict[str, ModuleSpec]):
        """Registrar módulos del proyecto"""
        
        for name, spec in modules_specs.items():
            if name not in self.modules:
                module_state = ModuleState(
                    name=name,
                    spec=spec,
                    status=ModuleStatus.PLANNED
                )
                self.modules[name] = module_state
            else:
                # Actualizar spec si ya existe
                self.modules[name].spec = spec
        
        # Calcular orden de ejecución y ruta crítica
        self._calculate_execution_plan()
        
        self.save_modules_state()
        self.logger.info(f"Registered {len(modules_specs)} modules")
    
    def create_execution_plan(self, modules_specs: Dict[str, ModuleSpec] = None) -> List[List[str]]:
        """
        Crear plan de ejecución respetando dependencias
        
        Args:
            modules_specs: Especificaciones de módulos (opcional, usa registrados si no se provee)
            
        Returns:
            Lista de fases, cada fase contiene módulos que pueden ejecutarse en paralelo
        """
        
        if modules_specs:
            self.register_modules(modules_specs)
        
        return self.execution_order
    
    def _calculate_execution_plan(self):
        """Calcular plan de ejecución usando ordenamiento topológico"""
        
        # Crear grafo de dependencias
        module_deps = {}
        for name, module_state in self.modules.items():
            module_deps[name] = module_state.spec.dependencies
        
        # Ordenamiento topológico con detección de ciclos
        phases = []
        remaining_modules = set(module_deps.keys())
        completed_modules = set()
        iteration = 0
        max_iterations = len(module_deps) + 1
        
        while remaining_modules and iteration < max_iterations:
            iteration += 1
            
            # Encontrar módulos sin dependencias pendientes
            ready_modules = []
            for module in remaining_modules:
                dependencies = module_deps[module]
                # Filtrar dependencias que existen en nuestro proyecto
                valid_deps = [dep for dep in dependencies if dep in module_deps]
                
                if all(dep in completed_modules for dep in valid_deps):
                    ready_modules.append(module)
            
            if not ready_modules:
                # Posible ciclo de dependencias - identificar y romper
                self.logger.warning("Possible dependency cycle detected")
                cycle_breaker = self._break_dependency_cycle(remaining_modules, module_deps, completed_modules)
                if cycle_breaker:
                    ready_modules = [cycle_breaker]
                else:
                    # Último recurso - tomar cualquier módulo restante
                    ready_modules = [next(iter(remaining_modules))]
            
            # Agregar fase con módulos listos
            if ready_modules:
                phases.append(ready_modules)
                
                # Actualizar conjuntos
                for module in ready_modules:
                    remaining_modules.remove(module)
                    completed_modules.add(module)
                    
                    # Marcar módulo como listo
                    if module in self.modules:
                        self._check_and_update_status(module)
        
        self.execution_order = phases
        self._calculate_critical_path()
        
        self.logger.info(f"Execution plan created with {len(phases)} phases")
        return phases
    
    def _break_dependency_cycle(self, remaining_modules: set, module_deps: Dict, completed_modules: set) -> Optional[str]:
        """Intentar romper ciclo de dependencias eligiendo el módulo más apropiado"""
        
        # Estrategia: elegir el módulo con menos dependencias pendientes
        best_candidate = None
        min_pending_deps = float('inf')
        
        for module in remaining_modules:
            dependencies = module_deps[module]
            valid_deps = [dep for dep in dependencies if dep in module_deps]
            pending_deps = [dep for dep in valid_deps if dep not in completed_modules]
            
            if len(pending_deps) < min_pending_deps:
                min_pending_deps = len(pending_deps)
                best_candidate = module
        
        if best_candidate:
            self.logger.info(f"Breaking cycle by selecting module: {best_candidate}")
            
            # Marcar dependencias como bloqueadas temporalmente
            if best_candidate in self.modules:
                pending_deps = [dep for dep in module_deps[best_candidate] 
                              if dep in module_deps and dep not in completed_modules]
                self.modules[best_candidate].blockers.extend(pending_deps)
        
        return best_candidate
    
    def _calculate_critical_path(self):
        """Calcular ruta crítica del proyecto"""
        
        # Algoritmo simplificado: la cadena más larga de dependencias
        def get_longest_path(module_name: str, visited: set = None) -> List[str]:
            if visited is None:
                visited = set()
            
            if module_name in visited or module_name not in self.modules:
                return []
            
            visited.add(module_name)
            module_spec = self.modules[module_name].spec
            
            # Encontrar el camino más largo a través de las dependencias
            max_path = [module_name]
            for dep in module_spec.dependencies:
                if dep in self.modules:
                    dep_path = get_longest_path(dep, visited.copy())
                    if len(dep_path) + 1 > len(max_path):
                        max_path = [module_name] + dep_path
            
            return max_path
        
        # Encontrar la ruta crítica más larga
        longest_path = []
        for module_name in self.modules.keys():
            path = get_longest_path(module_name)
            if len(path) > len(longest_path):
                longest_path = path
        
        self.critical_path = longest_path
        self.logger.info(f"Critical path identified: {' -> '.join(longest_path)}")
    
    def get_critical_path(self) -> List[str]:
        """Obtener ruta crítica del proyecto"""
        return self.critical_path.copy()
    
    def get_next_ready_modules(self) -> List[str]:
        """Obtener módulos listos para ejecutar"""
        
        ready_modules = []
        for name, module_state in self.modules.items():
            if module_state.status == ModuleStatus.READY:
                ready_modules.append(name)
        
        return ready_modules
    
    def start_module_execution(self, module_name: str, assigned_agents: List[str]) -> bool:
        """Iniciar ejecución de un módulo"""
        
        if module_name not in self.modules:
            self.logger.error(f"Module {module_name} not found")
            return False
        
        module_state = self.modules[module_name]
        
        # Verificar que el módulo está listo
        if module_state.status != ModuleStatus.READY:
            self.logger.warning(f"Module {module_name} not ready for execution (status: {module_state.status})")
            return False
        
        # Verificar dependencias
        if not self._check_dependencies_met(module_name):
            module_state.status = ModuleStatus.WAITING_DEPENDENCY
            self.save_modules_state()
            return False
        
        # Iniciar ejecución
        module_state.status = ModuleStatus.IN_PROGRESS
        module_state.start_time = datetime.now()
        module_state.assigned_agents = assigned_agents
        module_state.progress = 0.0
        
        self.save_modules_state()
        self.logger.info(f"Started execution of module {module_name} with agents: {assigned_agents}")
        return True
    
    def update_module_progress(self, module_name: str, progress: float, 
                             deliverables: Dict[str, Any] = None, 
                             metrics: Dict[str, Any] = None):
        """Actualizar progreso de un módulo"""
        
        if module_name not in self.modules:
            self.logger.error(f"Module {module_name} not found")
            return
        
        module_state = self.modules[module_name]
        module_state.progress = max(0.0, min(100.0, progress))
        
        if deliverables:
            module_state.deliverables.update(deliverables)
        
        if metrics:
            module_state.metrics.update(metrics)
        
        # Verificar si el módulo está completo
        if progress >= 100.0 and module_state.status == ModuleStatus.IN_PROGRESS:
            self._complete_module(module_name)
        
        self.save_modules_state()
        self.logger.info(f"Module {module_name} progress updated to {progress:.1f}%")
    
    def _complete_module(self, module_name: str):
        """Marcar módulo como completado"""
        
        module_state = self.modules[module_name]
        module_state.status = ModuleStatus.COMPLETED
        module_state.end_time = datetime.now()
        module_state.progress = 100.0
        
        # Verificar qué módulos se desbloquean
        self._check_and_unlock_dependent_modules(module_name)
        
        self.logger.info(f"Module {module_name} completed successfully")
    
    def fail_module(self, module_name: str, error: str):
        """Marcar módulo como fallido"""
        
        if module_name not in self.modules:
            return
        
        module_state = self.modules[module_name]
        module_state.status = ModuleStatus.FAILED
        module_state.end_time = datetime.now()
        module_state.metrics["error"] = error
        
        # Identificar módulos que se ven afectados
        affected_modules = self._get_dependent_modules(module_name)
        for affected in affected_modules:
            if self.modules[affected].status in [ModuleStatus.PLANNED, ModuleStatus.READY]:
                self.modules[affected].blockers.append(f"dependency_failed:{module_name}")
        
        self.save_modules_state()
        self.logger.error(f"Module {module_name} failed: {error}")
    
    def pause_module(self, module_name: str):
        """Pausar ejecución de un módulo"""
        
        if module_name not in self.modules:
            return
        
        module_state = self.modules[module_name]
        if module_state.status == ModuleStatus.IN_PROGRESS:
            # Guardar estado antes de pausar
            module_state.metrics["paused_at"] = datetime.now().isoformat()
            module_state.metrics["paused_progress"] = module_state.progress
        
        self.save_modules_state()
        self.logger.info(f"Module {module_name} paused")
    
    def resume_module(self, module_name: str):
        """Reanudar ejecución de un módulo"""
        
        if module_name not in self.modules:
            return
        
        module_state = self.modules[module_name]
        
        # Restaurar progreso si estaba pausado
        if "paused_progress" in module_state.metrics:
            module_state.progress = module_state.metrics["paused_progress"]
            del module_state.metrics["paused_progress"]
            del module_state.metrics["paused_at"]
        
        module_state.status = ModuleStatus.IN_PROGRESS
        
        self.save_modules_state()
        self.logger.info(f"Module {module_name} resumed")
    
    def _check_dependencies_met(self, module_name: str) -> bool:
        """Verificar si todas las dependencias de un módulo están satisfechas"""
        
        if module_name not in self.modules:
            return False
        
        module_spec = self.modules[module_name].spec
        
        for dep in module_spec.dependencies:
            if dep in self.modules:
                dep_status = self.modules[dep].status
                if dep_status != ModuleStatus.COMPLETED:
                    return False
            # Si la dependencia no está en nuestros módulos, la ignoramos
            # (puede ser una dependencia externa)
        
        return True
    
    def _check_and_update_status(self, module_name: str):
        """Verificar y actualizar estado de un módulo"""
        
        if module_name not in self.modules:
            return
        
        module_state = self.modules[module_name]
        
        # Si está planificado, verificar si puede pasar a listo
        if module_state.status == ModuleStatus.PLANNED:
            if self._check_dependencies_met(module_name):
                module_state.status = ModuleStatus.READY
                module_state.dependencies_met = module_state.spec.dependencies.copy()
        
        # Si está esperando dependencias, verificar de nuevo
        elif module_state.status == ModuleStatus.WAITING_DEPENDENCY:
            if self._check_dependencies_met(module_name):
                module_state.status = ModuleStatus.READY
    
    def _check_and_unlock_dependent_modules(self, completed_module: str):
        """Verificar y desbloquear módulos que dependían del módulo completado"""
        
        for name, module_state in self.modules.items():
            if completed_module in module_state.spec.dependencies:
                self._check_and_update_status(name)
    
    def _get_dependent_modules(self, module_name: str) -> List[str]:
        """Obtener módulos que dependen del módulo dado"""
        
        dependents = []
        for name, module_state in self.modules.items():
            if module_name in module_state.spec.dependencies:
                dependents.append(name)
        
        return dependents
    
    def get_module_status(self, module_name: str) -> Dict[str, Any]:
        """Obtener estado detallado de un módulo"""
        
        if module_name not in self.modules:
            return {"error": "Module not found"}
        
        module_state = self.modules[module_name]
        
        status_dict = asdict(module_state)
        status_dict['status'] = module_state.status.value
        
        # Agregar información adicional
        status_dict['dependencies_status'] = {}
        for dep in module_state.spec.dependencies:
            if dep in self.modules:
                status_dict['dependencies_status'][dep] = self.modules[dep].status.value
            else:
                status_dict['dependencies_status'][dep] = "external"
        
        status_dict['dependents'] = self._get_dependent_modules(module_name)
        status_dict['is_critical_path'] = module_name in self.critical_path
        
        # Calcular tiempo estimado restante
        if module_state.status == ModuleStatus.IN_PROGRESS and module_state.start_time:
            elapsed = datetime.now() - module_state.start_time
            if module_state.progress > 0:
                total_estimated = elapsed.total_seconds() * (100.0 / module_state.progress)
                remaining = total_estimated - elapsed.total_seconds()
                status_dict['estimated_remaining_seconds'] = max(0, remaining)
        
        return status_dict
    
    def get_all_modules_status(self) -> Dict[str, Dict[str, Any]]:
        """Obtener estado de todos los módulos"""
        
        all_status = {}
        for module_name in self.modules:
            all_status[module_name] = self.get_module_status(module_name)
        
        return all_status
    
    def get_project_summary(self) -> Dict[str, Any]:
        """Obtener resumen del proyecto"""
        
        total_modules = len(self.modules)
        if total_modules == 0:
            return {"error": "No modules registered"}
        
        # Contar módulos por estado
        status_counts = {}
        for status in ModuleStatus:
            status_counts[status.value] = 0
        
        total_progress = 0.0
        total_estimated_hours = 0
        completed_hours = 0
        
        for module_state in self.modules.values():
            status_counts[module_state.status.value] += 1
            total_progress += module_state.progress
            total_estimated_hours += module_state.spec.estimated_hours
            
            if module_state.status == ModuleStatus.COMPLETED:
                completed_hours += module_state.spec.estimated_hours
        
        overall_progress = total_progress / total_modules if total_modules > 0 else 0
        
        # Calcular tiempos
        project_start = min((m.start_time for m in self.modules.values() if m.start_time), default=None)
        project_end = max((m.end_time for m in self.modules.values() if m.end_time), default=None)
        
        return {
            "total_modules": total_modules,
            "status_breakdown": status_counts,
            "overall_progress": overall_progress,
            "estimated_total_hours": total_estimated_hours,
            "completed_hours": completed_hours,
            "project_start": project_start.isoformat() if project_start else None,
            "project_end": project_end.isoformat() if project_end else None,
            "critical_path": self.critical_path,
            "execution_phases": len(self.execution_order),
            "ready_modules": len([m for m in self.modules.values() if m.status == ModuleStatus.READY]),
            "blocked_modules": len([m for m in self.modules.values() if m.blockers])
        }
    
    def validate_dependencies(self, modules_specs: Dict[str, ModuleSpec] = None) -> List[str]:
        """Validar que todas las dependencias existen y no hay ciclos"""
        
        if modules_specs is None:
            modules_specs = {name: state.spec for name, state in self.modules.items()}
        
        errors = []
        module_names = set(modules_specs.keys())
        
        # Verificar dependencias inexistentes
        for name, spec in modules_specs.items():
            for dep in spec.dependencies:
                if dep not in module_names:
                    errors.append(f"Module '{name}' depends on non-existent module '{dep}'")
        
        # Detectar ciclos usando DFS
        def has_cycle(node: str, visited: set, rec_stack: set) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            if node in modules_specs:
                for dep in modules_specs[node].dependencies:
                    if dep in modules_specs:
                        if dep not in visited:
                            if has_cycle(dep, visited, rec_stack):
                                return True
                        elif dep in rec_stack:
                            return True
            
            rec_stack.remove(node)
            return False
        
        visited = set()
        for module in module_names:
            if module not in visited:
                if has_cycle(module, visited, set()):
                    errors.append(f"Dependency cycle detected involving module '{module}'")
        
        return errors
    
    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """Obtener grafo de dependencias"""
        
        graph = {}
        for name, module_state in self.modules.items():
            graph[name] = module_state.spec.dependencies.copy()
        
        return graph
    
    def get_modules_by_status(self, status: ModuleStatus) -> List[str]:
        """Obtener módulos por estado específico"""
        
        return [name for name, module_state in self.modules.items() 
                if module_state.status == status]
    
    def reset_module(self, module_name: str):
        """Reset un módulo a estado inicial"""
        
        if module_name not in self.modules:
            return
        
        module_state = self.modules[module_name]
        module_state.status = ModuleStatus.PLANNED
        module_state.progress = 0.0
        module_state.start_time = None
        module_state.end_time = None
        module_state.assigned_agents = []
        module_state.deliverables = {}
        module_state.dependencies_met = []
        module_state.blockers = []
        module_state.metrics = {}
        
        # Verificar si puede pasar a ready
        self._check_and_update_status(module_name)
        
        self.save_modules_state()
        self.logger.info(f"Module {module_name} reset to initial state")
    
    def cleanup_completed_modules(self, days_old: int = 30):
        """Limpiar módulos completados antiguos"""
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        modules_to_archive = []
        
        for name, module_state in self.modules.items():
            if (module_state.status == ModuleStatus.COMPLETED and 
                module_state.end_time and 
                module_state.end_time < cutoff_date):
                modules_to_archive.append(name)
        
        # Archivar módulos (podrías mover a archivo separado)
        for module_name in modules_to_archive:
            self.logger.info(f"Archiving old completed module: {module_name}")
            # En una implementación real, moverías a un archivo de archivo
            # Por ahora solo los dejamos
        
        return len(modules_to_archive)
    