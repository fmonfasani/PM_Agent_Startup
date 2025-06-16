# core/agent_spawner.py
"""
Agent Spawner - Crea y gestiona agentes especializados para cada módulo
"""

import json
import os
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

from .ai_interface import AIInterface
from .planner import ModuleSpec


@dataclass
class AgentConfig:
    id: str
    name: str
    role: str  # backend, frontend, fullstack, qa, devops, etc.
    specialization: str
    model: str
    temperature: float
    max_tokens: int
    personality: str
    expertise: List[str]
    tools: List[str]
    status: str = "idle"  # idle, working, completed, error


@dataclass
class AgentTask:
    id: str
    agent_id: str
    module_name: str
    task_type: str  # design, implement, test, review
    description: str
    priority: int  # 1-10
    dependencies: List[str]
    status: str = "pending"  # pending, in_progress, completed, failed
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AgentSpawner:
    """
    Generador de agentes especializados que crea equipos dinámicos
    para cada módulo del proyecto
    """
    
    def __init__(self):
        self.ai = AIInterface()
        self.logger = logging.getLogger('AgentSpawner')
        
        # Registro de agentes activos
        self.active_agents: Dict[str, AgentConfig] = {}
        self.agent_tasks: Dict[str, List[AgentTask]] = {}
        
        # Templates de agentes especializados
        self.agent_templates = self._load_agent_templates()
        
        # Configuración de modelos por especialización
        self.model_preferences = {
            'backend': ['deepseek-r1:14b', 'qwen2.5-coder:7b'],
            'frontend': ['claude-3-5-sonnet', 'gpt-4o'],
            'fullstack': ['deepseek-r1:14b', 'claude-3-5-sonnet'],
            'mobile': ['gpt-4o', 'claude-3-5-sonnet'],
            'devops': ['qwen2.5-coder:7b', 'deepseek-r1:7b'],
            'qa': ['claude-3-5-sonnet', 'deepseek-r1:14b'],
            'security': ['claude-3-5-sonnet', 'deepseek-r1:14b'],
            'data': ['deepseek-r1:14b', 'claude-3-5-sonnet']
        }
    
    def _load_agent_templates(self) -> Dict[str, Dict[str, Any]]:
        """Cargar templates de agentes desde archivos de configuración"""
        
        templates = {
            'backend': {
                'personality': 'Expert backend developer focused on scalable architecture, API design, and database optimization. Methodical and security-conscious.',
                'expertise': [
                    'Node.js/Express', 'Python/FastAPI', 'PostgreSQL', 'Redis',
                    'RESTful APIs', 'GraphQL', 'Microservices', 'Docker',
                    'JWT Authentication', 'Database Design', 'Performance Optimization'
                ],
                'tools': ['npm', 'pip', 'docker', 'postgres', 'redis-cli'],
                'temperature': 0.2,
                'max_tokens': 2500
            },
            
            'frontend': {
                'personality': 'Creative frontend developer specializing in modern web technologies and exceptional user experiences. Detail-oriented with strong design sense.',
                'expertise': [
                    'React/TypeScript', 'Vue.js', 'Next.js', 'Tailwind CSS',
                    'State Management', 'Responsive Design', 'Accessibility',
                    'Performance Optimization', 'Testing', 'Web Components'
                ],
                'tools': ['npm', 'webpack', 'vite', 'cypress', 'jest'],
                'temperature': 0.4,
                'max_tokens': 2000
            },
            
            'fullstack': {
                'personality': 'Versatile fullstack developer with expertise across the entire development stack. Bridge between frontend and backend teams.',
                'expertise': [
                    'Full-Stack JavaScript', 'MERN/MEAN Stack', 'API Integration',
                    'Database Design', 'DevOps Basics', 'Testing Strategies',
                    'System Architecture', 'Performance Optimization'
                ],
                'tools': ['npm', 'docker', 'postgres', 'cypress', 'jest'],
                'temperature': 0.3,
                'max_tokens': 2200
            },
            
            'mobile': {
                'personality': 'Mobile development specialist creating cross-platform applications with native performance and user experience.',
                'expertise': [
                    'React Native', 'Flutter', 'Expo', 'Mobile UI/UX',
                    'App Store Deployment', 'Push Notifications',
                    'Offline Storage', 'Performance Optimization'
                ],
                'tools': ['expo', 'react-native', 'adb', 'xcode'],
                'temperature': 0.3,
                'max_tokens': 2000
            },
            
            'devops': {
                'personality': 'DevOps engineer focused on automation, reliability, and scalable infrastructure. Systematic approach to deployment and monitoring.',
                'expertise': [
                    'Docker/Kubernetes', 'CI/CD Pipelines', 'AWS/Azure/GCP',
                    'Infrastructure as Code', 'Monitoring', 'Security',
                    'Performance Tuning', 'Backup Strategies'
                ],
                'tools': ['docker', 'kubectl', 'terraform', 'aws-cli', 'helm'],
                'temperature': 0.1,
                'max_tokens': 2000
            },
            
            'qa': {
                'personality': 'Quality assurance specialist ensuring robust, bug-free applications through comprehensive testing strategies.',
                'expertise': [
                    'Test Automation', 'Unit Testing', 'Integration Testing',
                    'E2E Testing', 'Performance Testing', 'Security Testing',
                    'Test Planning', 'Bug Tracking', 'Quality Metrics'
                ],
                'tools': ['jest', 'cypress', 'selenium', 'postman', 'jmeter'],
                'temperature': 0.2,
                'max_tokens': 1800
            },
            
            'security': {
                'personality': 'Security specialist focused on identifying vulnerabilities and implementing robust security measures.',
                'expertise': [
                    'Security Auditing', 'Penetration Testing', 'OWASP Guidelines',
                    'Authentication/Authorization', 'Data Encryption',
                    'Compliance', 'Threat Modeling', 'Security Architecture'
                ],
                'tools': ['burp-suite', 'nmap', 'owasp-zap', 'sqlmap'],
                'temperature': 0.1,
                'max_tokens': 2000
            },
            
            'data': {
                'personality': 'Data engineer specializing in data pipelines, analytics, and machine learning integration.',
                'expertise': [
                    'Data Pipelines', 'ETL/ELT', 'SQL Optimization',
                    'Data Warehousing', 'Analytics', 'ML Integration',
                    'Big Data Technologies', 'Data Visualization'
                ],
                'tools': ['python', 'sql', 'spark', 'airflow', 'tableau'],
                'temperature': 0.3,
                'max_tokens': 2200
            }
        }
        
        return templates
    
    async def spawn_agents_for_module(self, module_name: str, module_spec: ModuleSpec, 
                                    project_config: 'ProjectConfig') -> List[AgentConfig]:
        """
        Crear agentes especializados para un módulo específico
        
        Args:
            module_name: Nombre del módulo
            module_spec: Especificación del módulo
            project_config: Configuración del proyecto
            
        Returns:
            List[AgentConfig]: Lista de agentes creados
        """
        
        self.logger.info(f"Spawning agents for module: {module_name}")
        
        agents = []
        
        # Crear agentes basados en roles necesarios
        for role in module_spec.agents_needed:
            agent = await self._create_specialized_agent(
                role, module_name, module_spec, project_config
            )
            agents.append(agent)
            self.active_agents[agent.id] = agent
        
        # Guardar configuración de agentes
        await self._save_agents_config(module_name, agents)
        
        self.logger.info(f"Created {len(agents)} agents for module {module_name}")
        
        return agents
    
    async def _create_specialized_agent(self, role: str, module_name: str, 
                                      module_spec: ModuleSpec, project_config: 'ProjectConfig') -> AgentConfig:
        """Crear agente especializado para un rol específico"""
        
        agent_id = f"{module_name}_{role}_{int(datetime.now().timestamp())}"
        
        # Obtener template base para el rol
        template = self.agent_templates.get(role, self.agent_templates['backend'])
        
        # Seleccionar mejor modelo para este rol
        preferred_models = self.model_preferences.get(role, ['deepseek-r1:14b'])
        available_models = await self.ai.get_available_models()
        
        selected_model = None
        for model in preferred_models:
            if model in available_models:
                selected_model = model
                break
        
        if not selected_model:
            selected_model = available_models[0] if available_models else 'deepseek-r1:14b'
        
        # Generar especialización específica para el módulo
        specialization = await self._generate_module_specialization(
            role, module_spec, project_config
        )
        
        # Crear configuración del agente
        agent = AgentConfig(
            id=agent_id,
            name=f"{role.title()} Specialist - {module_name}",
            role=role,
            specialization=specialization,
            model=selected_model,
            temperature=template['temperature'],
            max_tokens=template['max_tokens'],
            personality=template['personality'],
            expertise=template['expertise'].copy(),
            tools=template['tools'].copy(),
            status="idle"
        )
        
        # Personalizar expertise para el módulo específico
        await self._customize_agent_expertise(agent, module_spec, project_config)
        
        return agent
    
    async def _generate_module_specialization(self, role: str, module_spec: ModuleSpec, 
                                            project_config: 'ProjectConfig') -> str:
        """Generar especialización específica del agente para el módulo"""
        
        ai_prompt = f"""
        Eres un {role} specialist que trabajará en un módulo específico. 
        
        Módulo: {module_spec.name}
        Descripción: {module_spec.description}
        Tecnologías: {', '.join(module_spec.tech_stack)}
        APIs necesarias: {', '.join(module_spec.apis_needed)}
        Entidades DB: {', '.join(module_spec.database_entities)}
        
        Proyecto general: {project_config.description}
        Complejidad: {project_config.complexity}/10
        
        Define tu especialización específica para este módulo en 2-3 líneas:
        - ¿En qué aspectos técnicos te enfocarás?
        - ¿Qué patrones/arquitecturas aplicarás?
        - ¿Cuáles son tus prioridades principales?
        
        Responde en primera persona como el especialista.
        """
        
        try:
            specialization = await self.ai.generate_response(
                ai_prompt, max_tokens=200, temperature=0.3
            )
            return specialization.strip()
        except Exception as e:
            self.logger.warning(f"Could not generate specialization: {e}")
            return f"Specialized {role} developer for {module_spec.name} module"
    
    async def _customize_agent_expertise(self, agent: AgentConfig, module_spec: ModuleSpec, 
                                       project_config: 'ProjectConfig'):
        """Personalizar expertise del agente para el módulo específico"""
        
        # Agregar tecnologías específicas del módulo
        for tech in module_spec.tech_stack:
            if tech not in agent.expertise:
                agent.expertise.append(tech)
        
        # Agregar expertise basada en APIs necesarias
        api_expertise_map = {
            'auth': 'Authentication & Authorization',
            'payments': 'Payment Processing & Stripe Integration',
            'chat': 'Real-time Communication & WebSockets',
            'analytics': 'Analytics & Reporting',
            'search': 'Search & Indexing'
        }
        
        for api in module_spec.apis_needed:
            if api in api_expertise_map:
                expertise = api_expertise_map[api]
                if expertise not in agent.expertise:
                    agent.expertise.append(expertise)
        
        # Agregar expertise de compliance si es necesario
        if project_config.compliance:
            for compliance in project_config.compliance:
                compliance_expertise = f"{compliance} Compliance"
                if compliance_expertise not in agent.expertise:
                    agent.expertise.append(compliance_expertise)
    
    async def assign_task_to_agent(self, agent_id: str, task: AgentTask) -> bool:
        """Asignar tarea a un agente específico"""
        
        if agent_id not in self.active_agents:
            self.logger.error(f"Agent {agent_id} not found")
            return False
        
        agent = self.active_agents[agent_id]
        
        if agent.status != "idle":
            self.logger.warning(f"Agent {agent_id} is not idle (status: {agent.status})")
            return False
        
        # Actualizar estado del agente
        agent.status = "working"
        
        # Registrar tarea
        if agent_id not in self.agent_tasks:
            self.agent_tasks[agent_id] = []
        
        task.status = "in_progress"
        task.started_at = datetime.now()
        self.agent_tasks[agent_id].append(task)
        
        self.logger.info(f"Assigned task {task.id} to agent {agent_id}")
        
        return True
    
    async def execute_agent_task(self, agent_id: str, task: AgentTask) -> Dict[str, Any]:
        """Ejecutar tarea específica del agente"""
        
        if agent_id not in self.active_agents:
            raise ValueError(f"Agent {agent_id} not found")
        
        agent = self.active_agents[agent_id]
        
        self.logger.info(f"Agent {agent.name} executing task: {task.description}")
        
        try:
            # Construir prompt especializado para el agente
            prompt = self._build_agent_prompt(agent, task)
            
            # Ejecutar tarea con el modelo del agente
            result = await self.ai.generate_response(
                prompt, 
                max_tokens=agent.max_tokens,
                temperature=agent.temperature,
                model=agent.model
            )
            
            # Procesar resultado
            processed_result = await self._process_agent_result(agent, task, result)
            
            # Actualizar estado de la tarea
            task.status = "completed"
            task.completed_at = datetime.now()
            task.result = processed_result
            
            # Actualizar estado del agente
            agent.status = "idle"
            
            self.logger.info(f"Agent {agent.name} completed task {task.id}")
            
            return processed_result
            
        except Exception as e:
            # Manejar error
            task.status = "failed"
            task.error = str(e)
            task.completed_at = datetime.now()
            agent.status = "error"
            
            self.logger.error(f"Agent {agent.name} failed task {task.id}: {e}")
            
            raise
    
    def _build_agent_prompt(self, agent: AgentConfig, task: AgentTask) -> str:
        """Construir prompt especializado para el agente"""
        
        prompt = f"""
You are {agent.name}, a highly skilled {agent.role} developer.

AGENT PROFILE:
- Role: {agent.role}
- Specialization: {agent.specialization}
- Personality: {agent.personality}
- Expertise: {', '.join(agent.expertise)}
- Available Tools: {', '.join(agent.tools)}

CURRENT TASK:
- Module: {task.module_name}
- Task Type: {task.task_type}
- Description: {task.description}
- Priority: {task.priority}/10

INSTRUCTIONS:
Based on your expertise and the task requirements, provide a detailed, production-ready solution.

For code generation tasks:
- Write complete, functional code
- Include proper error handling
- Add comprehensive comments
- Follow best practices for {agent.role} development
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
    
    async def _process_agent_result(self, agent: AgentConfig, task: AgentTask, 
                                  raw_result: str) -> Dict[str, Any]:
        """Procesar resultado del agente para extraer información estructurada"""
        
        # Análisis básico del resultado
        result = {
            "agent_id": agent.id,
            "agent_role": agent.role,
            "task_id": task.id,
            "raw_output": raw_result,
            "analysis": {},
            "deliverables": {},
            "next_steps": [],
            "quality_score": 0.0
        }
        
        # Extraer código si existe
        code_blocks = self._extract_code_blocks(raw_result)
        if code_blocks:
            result["deliverables"]["code"] = code_blocks
        
        # Extraer archivos generados
        files = self._extract_file_structure(raw_result)
        if files:
            result["deliverables"]["files"] = files
        
        # Calcular puntuación de calidad básica
        result["quality_score"] = self._calculate_quality_score(raw_result, task.task_type)
        
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
    
    def _extract_file_structure(self, text: str) -> List[Dict[str, str]]:
        """Extraer estructura de archivos del texto"""
        files = []
        
        # Buscar patrones comunes de nombres de archivos
        import re
        file_patterns = [
            r'(\w+\.\w+):?\s*\n',  # filename.ext:
            r'File:\s*(\S+)',       # File: filename
            r'`([^`]+\.\w+)`'       # `filename.ext`
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
    
    def _calculate_quality_score(self, result: str, task_type: str) -> float:
        """Calcular puntuación de calidad del resultado"""
        score = 0.0
        
        # Factores de calidad básicos
        if len(result) > 100:
            score += 0.2  # Respuesta sustancial
        
        if "```" in result:
            score += 0.3  # Incluye código
        
        if any(word in result.lower() for word in ['error', 'exception', 'try', 'catch']):
            score += 0.2  # Manejo de errores
        
        if any(word in result.lower() for word in ['test', 'spec', 'describe']):
            score += 0.1  # Incluye testing
        
        if task_type == 'implement' and 'import' in result:
            score += 0.2  # Imports apropiados
        
        # Normalizar a 0-1
        return min(score, 1.0)
    
    async def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Obtener estado actual de un agente"""
        if agent_id not in self.active_agents:
            return {"error": "Agent not found"}
        
        agent = self.active_agents[agent_id]
        tasks = self.agent_tasks.get(agent_id, [])
        
        return {
            "agent": asdict(agent),
            "tasks": {
                "total": len(tasks),
                "pending": len([t for t in tasks if t.status == "pending"]),
                "in_progress": len([t for t in tasks if t.status == "in_progress"]),
                "completed": len([t for t in tasks if t.status == "completed"]),
                "failed": len([t for t in tasks if t.status == "failed"])
            },
            "performance": {
                "success_rate": self._calculate_agent_success_rate(agent_id),
                "average_task_time": self._calculate_average_task_time(agent_id)
            }
        }
    
    def _calculate_agent_success_rate(self, agent_id: str) -> float:
        """Calcular tasa de éxito del agente"""
        tasks = self.agent_tasks.get(agent_id, [])
        if not tasks:
            return 0.0
        
        completed_tasks = [t for t in tasks if t.status in ["completed", "failed"]]
        if not completed_tasks:
            return 0.0
        
        successful_tasks = [t for t in completed_tasks if t.status == "completed"]
        return len(successful_tasks) / len(completed_tasks)
    
    def _calculate_average_task_time(self, agent_id: str) -> float:
        """Calcular tiempo promedio de tareas del agente"""
        tasks = self.agent_tasks.get(agent_id, [])
        completed_tasks = [t for t in tasks if t.status == "completed" and t.started_at and t.completed_at]
        
        if not completed_tasks:
            return 0.0
        
        total_time = sum(
            (task.completed_at - task.started_at).total_seconds() 
            for task in completed_tasks
        )
        
        return total_time / len(completed_tasks)
    
    async def _save_agents_config(self, module_name: str, agents: List[AgentConfig]):
        """Guardar configuración de agentes para un módulo"""
        os.makedirs("agents", exist_ok=True)
        
        config_file = f"agents/{module_name}_agents.json"
        agents_data = [asdict(agent) for agent in agents]
        
        with open(config_file, 'w') as f:
            json.dump(agents_data, f, indent=2, default=str)
    
    async def load_agents_config(self, module_name: str) -> List[AgentConfig]:
        """Cargar configuración de agentes desde archivo"""
        config_file = f"agents/{module_name}_agents.json"
        
        if not os.path.exists(config_file):
            return []
        
        try:
            with open(config_file, 'r') as f:
                agents_data = json.load(f)
            
            agents = []
            for agent_data in agents_data:
                agent = AgentConfig(**agent_data)
                agents.append(agent)
                self.active_agents[agent.id] = agent
            
            return agents
            
        except Exception as e:
            self.logger.error(f"Error loading agents config: {e}")
            return []
    
    def get_all_agents(self) -> Dict[str, AgentConfig]:
        """Obtener todos los agentes activos"""
        return self.active_agents.copy()
    
    def get_agents_by_role(self, role: str) -> List[AgentConfig]:
        """Obtener agentes por rol específico"""
        return [agent for agent in self.active_agents.values() if agent.role == role]
    
    async def terminate_agent(self, agent_id: str) -> bool:
        """Terminar y limpiar un agente"""
        if agent_id not in self.active_agents:
            return False
        
        # Cancelar tareas pendientes
        if agent_id in self.agent_tasks:
            for task in self.agent_tasks[agent_id]:
                if task.status == "in_progress":
                    task.status = "cancelled"
                    task.completed_at = datetime.now()
        
        # Remover agente
        del self.active_agents[agent_id]
        
        self.logger.info(f"Agent {agent_id} terminated")
        return True
    
    async def get_agent_utilization(self) -> Dict[str, Any]:
        """Obtener métricas de utilización de agentes"""
        total_agents = len(self.active_agents)
        
        if total_agents == 0:
            return {"utilization": 0.0, "agents": {}}
        
        working_agents = len([a for a in self.active_agents.values() if a.status == "working"])
        idle_agents = len([a for a in self.active_agents.values() if a.status == "idle"])
        error_agents = len([a for a in self.active_agents.values() if a.status == "error"])
        
        utilization = working_agents / total_agents
        
        return {
            "utilization": utilization,
            "total_agents": total_agents,
            "working": working_agents,
            "idle": idle_agents,
            "error": error_agents,
            "by_role": self._get_utilization_by_role()
        }
    
    def _get_utilization_by_role(self) -> Dict[str, Dict[str, int]]:
        """Obtener utilización por rol"""
        role_stats = {}
        
        for agent in self.active_agents.values():
            if agent.role not in role_stats:
                role_stats[agent.role] = {"total": 0, "working": 0, "idle": 0, "error": 0}
            
            role_stats[agent.role]["total"] += 1
            role_stats[agent.role][agent.status] += 1
        
        return role_stats


