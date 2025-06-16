# core/enhanced_agent_spawner.py
"""
Enhanced Agent Spawner con Smart Routing
Integra el router inteligente para optimizar selección de agentes
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from .agent_spawner import AgentSpawner, AgentConfig, AgentTask
from .smart_agent_router import SmartAgentRouter, create_smart_router
from .planner import ModuleSpec

class EnhancedAgentSpawner(AgentSpawner):
    """AgentSpawner mejorado con selección inteligente de modelos"""
    
    def __init__(self):
        super().__init__()
        self.smart_router = create_smart_router()
        self.budget_preference = "balanced"  # Configurable
        self.cost_tracking = {}
        
    def set_budget_preference(self, preference: str):
        """
        Configurar preferencia de presupuesto
        Options: "cost_optimized", "balanced", "quality_first"
        """
        if preference in ["cost_optimized", "balanced", "quality_first"]:
            self.budget_preference = preference
            self.logger.info(f"Budget preference set to: {preference}")
        else:
            self.logger.warning(f"Invalid budget preference: {preference}")
    
    async def spawn_agents_for_module(self, module_name: str, module_spec: ModuleSpec, 
                                    project_config: 'ProjectConfig') -> List[AgentConfig]:
        """
        Crear agentes para módulo usando selección inteligente
        """
        self.logger.info(f"Spawning intelligent agents for module: {module_name}")
        
        # Ajustar preferencia de presupuesto según configuración del proyecto
        budget_pref = self._determine_budget_preference(project_config)
        
        # Obtener recomendaciones del smart router
        module_dict = {
            "type": module_spec.type,
            "description": module_spec.description,
            "complexity": module_spec.complexity,
            "tech_stack": module_spec.tech_stack
        }
        
        recommendations = self.smart_router.recommend_agent_for_module(
            module_dict, budget_pref
        )
        
        agents = []
        
        # Crear agentes basado en roles necesarios
        for role in module_spec.agents_needed:
            agent = await self._create_intelligent_agent(
                role, module_name, module_spec, project_config, recommendations
            )
            agents.append(agent)
            self.active_agents[agent.id] = agent
        
        # Guardar configuración y métricas
        await self._save_agents_config(module_name, agents)
        await self._track_cost_metrics(module_name, agents, recommendations)
        
        self.logger.info(f"Created {len(agents)} intelligent agents for module {module_name}")
        return agents
    
    def _determine_budget_preference(self, project_config: 'ProjectConfig') -> str:
        """Determinar preferencia de presupuesto basado en configuración del proyecto"""
        
        budget = getattr(project_config, 'budget', 'medium').lower()
        complexity = getattr(project_config, 'complexity', 5)
        
        # Lógica de decisión
        if budget == "startup" or budget == "low":
            return "cost_optimized"
        elif budget == "enterprise" or budget == "high":
            return "quality_first"
        elif complexity >= 8:
            return "quality_first"  # Proyectos muy complejos necesitan calidad
        elif complexity <= 3:
            return "cost_optimized"  # Proyectos simples pueden usar modelos locales
        else:
            return "balanced"
    
    async def _create_intelligent_agent(self, role: str, module_name: str, 
                                      module_spec: ModuleSpec, project_config: 'ProjectConfig',
                                      recommendations: Dict[str, Dict]) -> AgentConfig:
        """Crear agente con modelo seleccionado inteligentemente"""
        
        agent_id = f"{module_name}_{role}_{int(datetime.now().timestamp())}"
        
        # Obtener template base
        template = self.agent_templates.get(role, self.agent_templates['backend'])
        
        # Determinar mejor modelo para este rol y módulo
        task_description = f"{role} development for {module_spec.description}"
        
        selected_model, expected_quality, reasoning = self.smart_router.select_optimal_agent(
            task_description, self._determine_budget_preference(project_config)
        )
        
        # Ajustar parámetros según el modelo seleccionado
        model_params = self._get_model_parameters(selected_model)
        
        # Generar especialización específica usando el modelo seleccionado
        specialization = await self._generate_intelligent_specialization(
            role, module_spec, project_config, selected_model
        )
        
        # Crear configuración del agente
        agent = AgentConfig(
            id=agent_id,
            name=f"{role.title()} Specialist - {module_name}",
            role=role,
            specialization=specialization,
            model=selected_model,
            temperature=model_params['temperature'],
            max_tokens=model_params['max_tokens'],
            personality=template['personality'],
            expertise=template['expertise'].copy(),
            tools=template['tools'].copy(),
            status="idle"
        )
        
        # Agregar metadata de selección inteligente
        agent.expertise.append(f"Selected for: {reasoning}")
        agent.expertise.append(f"Expected quality: {expected_quality:.2f}")
        
        # Personalizar expertise para el módulo específico
        await self._customize_agent_expertise(agent, module_spec, project_config)
        
        self.logger.info(f"Created intelligent agent {agent_id}: {selected_model} - {reasoning}")
        
        return agent
    
    def _get_model_parameters(self, model_name: str) -> Dict[str, Any]:
        """Obtener parámetros optimizados para cada modelo"""
        
        model_configs = {
            "deepseek-r1:14b": {
                "temperature": 0.2,
                "max_tokens": 2500,
                "top_p": 0.9
            },
            "llama3.2:latest": {
                "temperature": 0.3,
                "max_tokens": 2000,
                "top_p": 0.85
            },
            "qwen2.5-coder:7b": {
                "temperature": 0.1,
                "max_tokens": 2200,
                "top_p": 0.9
            },
            "claude-3-5-sonnet": {
                "temperature": 0.4,
                "max_tokens": 2000,
                "top_p": 0.9
            },
            "gpt-4o": {
                "temperature": 0.3,
                "max_tokens": 2000,
                "top_p": 0.85
            }
        }
        
        return model_configs.get(model_name, {
            "temperature": 0.3,
            "max_tokens": 2000,
            "top_p": 0.9
        })
    
    async def _generate_intelligent_specialization(self, role: str, module_spec: ModuleSpec, 
                                                 project_config: 'ProjectConfig', 
                                                 selected_model: str) -> str:
        """Generar especialización optimizada para el modelo seleccionado"""
        
        # Crear prompt optimizado según el modelo
        if "deepseek" in selected_model.lower():
            prompt_style = "technical and algorithmic"
        elif "llama" in selected_model.lower():
            prompt_style = "clear and structured"
        elif "qwen" in selected_model.lower():
            prompt_style = "practical and implementation-focused"
        elif "claude" in selected_model.lower():
            prompt_style = "analytical and creative"
        elif "gpt" in selected_model.lower():
            prompt_style = "versatile and adaptive"
        else:
            prompt_style = "standard"
        
        ai_prompt = f"""
        As a {role} specialist using {selected_model}, define your specialization for this module.
        
        Module: {module_spec.name}
        Description: {module_spec.description}
        Technologies: {', '.join(module_spec.tech_stack)}
        Complexity: {module_spec.complexity}/10
        
        Project: {project_config.description}
        Style: {prompt_style}
        
        In 2-3 sentences, define your specific focus and approach for this module.
        Emphasize what makes you uniquely suited for this task with {selected_model}.
        """
        
        try:
            from .ai_interface import AIInterface
            ai = AIInterface()
            
            specialization = await ai.generate_response(
                ai_prompt, max_tokens=200, temperature=0.3, model=selected_model
            )
            return specialization.strip()
        except Exception as e:
            self.logger.warning(f"Could not generate intelligent specialization: {e}")
            return f"Specialized {role} developer for {module_spec.name} using {selected_model}"
    
    async def assign_intelligent_task(self, task_description: str, module_name: str) -> Optional[str]:
        """Asignar tarea al agente más apropiado basado en análisis inteligente"""
        
        # Analizar la tarea
        best_model, expected_quality, reasoning = self.smart_router.select_optimal_agent(
            task_description, self.budget_preference
        )
        
        # Buscar agente activo con ese modelo
        suitable_agents = [
            agent_id for agent_id, agent in self.active_agents.items()
            if agent.model == best_model and agent.status == "idle"
        ]
        
        if not suitable_agents:
            # Buscar agente alternativo
            suitable_agents = [
                agent_id for agent_id, agent in self.active_agents.items()
                if agent.status == "idle"
            ]
            
            if suitable_agents:
                self.logger.warning(f"Optimal model {best_model} not available, using alternative")
        
        if suitable_agents:
            selected_agent_id = suitable_agents[0]
            
            # Crear tarea
            task = AgentTask(
                id=f"task_{int(datetime.now().timestamp())}",
                agent_id=selected_agent_id,
                module_name=module_name,
                task_type="intelligent_assignment",
                description=task_description,
                priority=5,
                dependencies=[],
                created_at=datetime.now()
            )
            
            # Asignar tarea
            success = await self.assign_task_to_agent(selected_agent_id, task)
            
            if success:
                self.logger.info(f"Intelligent task assignment: {selected_agent_id} - {reasoning}")
                return selected_agent_id
        
        self.logger.error(f"No suitable agent available for task: {task_description}")
        return None
    
    async def _track_cost_metrics(self, module_name: str, agents: List[AgentConfig], 
                                recommendations: Dict[str, Dict]):
        """Rastrear métricas de costo y selección"""
        
        module_costs = {
            "module_name": module_name,
            "agents": [],
            "total_estimated_cost": 0.0,
            "cost_breakdown": {},
            "selection_reasoning": {}
        }
        
        for agent in agents:
            # Estimar tokens por agente (basado en complejidad)
            estimated_tokens = self._estimate_agent_tokens(agent, recommendations)
            
            # Calcular costo estimado
            cost_info = self.smart_router.get_cost_estimate(agent.model, estimated_tokens)
            
            agent_info = {
                "agent_id": agent.id,
                "role": agent.role,
                "model": agent.model,
                "estimated_tokens": estimated_tokens,
                "estimated_cost": cost_info.get("estimated_cost_usd", 0.0),
                "is_local": cost_info.get("is_local", False)
            }
            
            module_costs["agents"].append(agent_info)
            module_costs["total_estimated_cost"] += agent_info["estimated_cost"]
            
            # Breakdown por modelo
            model = agent.model
            if model not in module_costs["cost_breakdown"]:
                module_costs["cost_breakdown"][model] = 0.0
            module_costs["cost_breakdown"][model] += agent_info["estimated_cost"]
        
        # Guardar métricas
        self.cost_tracking[module_name] = module_costs
        
        # Log resumen de costos
        self.logger.info(f"Module {module_name} cost estimate: ${module_costs['total_estimated_cost']:.4f}")
        
        for model, cost in module_costs["cost_breakdown"].items():
            if cost == 0.0:
                self.logger.info(f"  {model}: FREE (local)")
            else:
                self.logger.info(f"  {model}: ${cost:.4f}")
    
    def _estimate_agent_tokens(self, agent: AgentConfig, recommendations: Dict[str, Dict]) -> int:
        """Estimar tokens que usará un agente basado en su rol y complejidad"""
        
        base_tokens = {
            "backend": 3000,
            "frontend": 2500,
            "fullstack": 4000,
            "qa": 2000,
            "devops": 2200,
            "mobile": 3500,
            "security": 2800,
            "data": 3200
        }
        
        # Token base según rol
        tokens = base_tokens.get(agent.role, 2500)
        
        # Multiplicador según complejidad (extraído de specialization)
        if "complex" in agent.specialization.lower():
            tokens *= 1.5
        elif "simple" in agent.specialization.lower():
            tokens *= 0.7
        
        # Multiplicador según modelo (algunos generan respuestas más largas)
        if "claude" in agent.model:
            tokens *= 1.3  # Claude tiende a ser más verboso
        elif "deepseek" in agent.model:
            tokens *= 1.2  # DeepSeek es detallado en código
        elif "llama" in agent.model:
            tokens *= 0.9   # Llama es más conciso
        
        return int(tokens)
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Obtener resumen de costos de todos los módulos"""
        
        total_cost = 0.0
        total_local_usage = 0
        total_cloud_usage = 0
        model_usage = {}
        
        for module_name, module_costs in self.cost_tracking.items():
            total_cost += module_costs["total_estimated_cost"]
            
            for agent_info in module_costs["agents"]:
                if agent_info["is_local"]:
                    total_local_usage += 1
                else:
                    total_cloud_usage += 1
                
                model = agent_info["model"]
                if model not in model_usage:
                    model_usage[model] = {"count": 0, "cost": 0.0}
                
                model_usage[model]["count"] += 1
                model_usage[model]["cost"] += agent_info["estimated_cost"]
        
        return {
            "total_estimated_cost_usd": total_cost,
            "total_agents": total_local_usage + total_cloud_usage,
            "local_agents": total_local_usage,
            "cloud_agents": total_cloud_usage,
            "cost_savings_local": f"{(total_local_usage / (total_local_usage + total_cloud_usage) * 100):.1f}%" if (total_local_usage + total_cloud_usage) > 0 else "0%",
            "model_breakdown": model_usage,
            "modules": self.cost_tracking
        }
    
    def optimize_existing_agents(self, rebalance_budget: str = None) -> Dict[str, Any]:
        """Optimizar agentes existentes cambiando modelos si es beneficioso"""
        
        if rebalance_budget:
            self.set_budget_preference(rebalance_budget)
        
        optimization_results = {
            "changes_made": 0,
            "cost_savings": 0.0,
            "quality_changes": {},
            "recommendations": []
        }
        
        for agent_id, agent in self.active_agents.items():
            if agent.status != "idle":
                continue  # Solo optimizar agentes inactivos
            
            # Analizar si hay un modelo mejor para este agente
            task_desc = f"{agent.role} development using current specialization: {agent.specialization}"
            
            optimal_model, optimal_quality, reasoning = self.smart_router.select_optimal_agent(
                task_desc, self.budget_preference
            )
            
            if optimal_model != agent.model:
                # Calcular impacto del cambio
                current_cost = self.smart_router.get_cost_estimate(agent.model, 2500)
                new_cost = self.smart_router.get_cost_estimate(optimal_model, 2500)
                
                cost_change = new_cost["estimated_cost_usd"] - current_cost["estimated_cost_usd"]
                
                recommendation = {
                    "agent_id": agent_id,
                    "current_model": agent.model,
                    "recommended_model": optimal_model,
                    "cost_change": cost_change,
                    "reasoning": reasoning,
                    "auto_apply": cost_change <= 0  # Solo aplicar automáticamente si reduce costo
                }
                
                optimization_results["recommendations"].append(recommendation)
                
                # Aplicar cambio automáticamente si reduce costo
                if cost_change <= 0:
                    agent.model = optimal_model
                    agent.expertise.append(f"Optimized to: {optimal_model}")
                    
                    optimization_results["changes_made"] += 1
                    optimization_results["cost_savings"] += abs(cost_change)
                    
                    self.logger.info(f"Optimized agent {agent_id}: {agent.model} -> {optimal_model} (saves ${abs(cost_change):.4f})")
        
        return optimization_results
    
    async def create_dynamic_agent(self, task_description: str, module_name: str) -> AgentConfig:
        """Crear agente dinámicamente para una tarea específica"""
        
        # Analizar tarea para determinar rol y modelo óptimo
        task_type, complexity = self.smart_router.analyze_task_type(task_description)
        
        # Mapear tipo de tarea a rol
        task_to_role = {
            "backend_development": "backend",
            "frontend_development": "frontend",
            "algorithm_implementation": "backend",
            "devops": "devops",
            "testing": "qa",
            "ui_design": "frontend",
            "security_analysis": "security",
            "documentation": "qa"
        }
        
        role = task_to_role.get(task_type, "fullstack")
        
        # Seleccionar modelo óptimo
        optimal_model, expected_quality, reasoning = self.smart_router.select_optimal_agent(
            task_description, self.budget_preference
        )
        
        # Crear agente dinámico
        agent_id = f"dynamic_{task_type}_{int(datetime.now().timestamp())}"
        
        template = self.agent_templates.get(role, self.agent_templates['backend'])
        model_params = self._get_model_parameters(optimal_model)
        
        agent = AgentConfig(
            id=agent_id,
            name=f"Dynamic {role.title()} - {task_type}",
            role=role,
            specialization=f"Dynamic agent for: {task_description[:100]}...",
            model=optimal_model,
            temperature=model_params['temperature'],
            max_tokens=model_params['max_tokens'],
            personality=f"Dynamic {template['personality']}",
            expertise=template['expertise'] + [f"Task-specific: {task_type}"],
            tools=template['tools'],
            status="idle"
        )
        
        # Registrar agente
        self.active_agents[agent_id] = agent
        
        self.logger.info(f"Created dynamic agent {agent_id}: {optimal_model} for {task_type}")
        
        return agent

    def get_intelligent_metrics(self) -> Dict[str, Any]:
        """Obtener métricas de selección inteligente"""
        
        model_distribution = {}
        role_model_mapping = {}
        quality_scores = []
        
        for agent in self.active_agents.values():
            # Distribución de modelos
            if agent.model not in model_distribution:
                model_distribution[agent.model] = 0
            model_distribution[agent.model] += 1
            
            # Mapeo rol-modelo
            if agent.role not in role_model_mapping:
                role_model_mapping[agent.role] = {}
            if agent.model not in role_model_mapping[agent.role]:
                role_model_mapping[agent.role][agent.model] = 0
            role_model_mapping[agent.role][agent.model] += 1
            
            # Extraer quality score si está en expertise
            for expertise in agent.expertise:
                if "Expected quality:" in expertise:
                    try:
                        quality = float(expertise.split("Expected quality:")[1].strip())
                        quality_scores.append(quality)
                    except:
                        pass
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        cost_summary = self.get_cost_summary()
        
        return {
            "intelligent_selection": {
                "total_agents": len(self.active_agents),
                "model_distribution": model_distribution,
                "role_model_mapping": role_model_mapping,
                "average_expected_quality": avg_quality,
                "budget_preference": self.budget_preference
            },
            "cost_optimization": cost_summary,
            "local_vs_cloud": {
                "local_percentage": f"{(cost_summary['local_agents'] / cost_summary['total_agents'] * 100):.1f}%" if cost_summary['total_agents'] > 0 else "0%",
                "estimated_savings": f"${cost_summary['total_estimated_cost_usd']:.4f} would cost with premium models"
            }
        }

# Función para integrar con el sistema existente
def upgrade_agent_spawner(existing_spawner: AgentSpawner) -> EnhancedAgentSpawner:
    """Upgrade del AgentSpawner existente al EnhancedAgentSpawner"""
    
    enhanced = EnhancedAgentSpawner()
    
    # Migrar agentes existentes
    enhanced.active_agents = existing_spawner.active_agents.copy()
    enhanced.agent_tasks = existing_spawner.agent_tasks.copy()
    enhanced.agent_templates = existing_spawner.agent_templates.copy()
    
    return enhanced