# core/planner.py
"""
Project Planner - Analiza prompts del usuario y genera arquitectura modular
"""

import json
import re
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import logging

from .ai_interface import AIInterface
from .module_templates import ModuleTemplates


@dataclass
class ModuleSpec:
    name: str
    type: str  # backend, frontend, fullstack, qa, deploy
    description: str
    dependencies: List[str]
    agents_needed: List[str]
    complexity: int  # 1-10
    estimated_hours: int
    tech_stack: List[str]
    apis_needed: List[str]
    database_entities: List[str]


class ProjectPlanner:
    """
    Planificador de proyectos que analiza prompts y genera arquitectura modular
    """
    
    def __init__(self):
        self.ai = AIInterface()
        self.templates = ModuleTemplates()
        self.logger = logging.getLogger('ProjectPlanner')
        
        # Patrones para identificar funcionalidades
        self.feature_patterns = {
            'auth': [
                r'autenticaci[óo]n', r'login', r'registro', r'sign[- ]?up',
                r'usuarios?', r'user management', r'auth', r'jwt'
            ],
            'payments': [
                r'pagos?', r'payment', r'stripe', r'paypal', r'billing',
                r'suscripci[óo]n', r'subscription', r'checkout'
            ],
            'chat': [
                r'chat', r'mensajer[íi]a', r'messaging', r'tiempo real',
                r'real[- ]?time', r'websocket', r'socket\.io'
            ],
            'ecommerce': [
                r'tienda', r'shop', r'cart', r'carrito', r'productos?',
                r'catalog', r'inventory', r'marketplace'
            ],
            'admin': [
                r'admin', r'dashboard', r'panel', r'backoffice',
                r'administraci[óo]n', r'management'
            ],
            'api': [
                r'api', r'rest', r'graphql', r'endpoint', r'microservic',
                r'backend', r'servidor'
            ],
            'mobile': [
                r'app m[óo]vil', r'mobile app', r'react native',
                r'flutter', r'ios', r'android'
            ],
            'web': [
                r'web', r'frontend', r'react', r'vue', r'angular',
                r'interfaz', r'ui', r'ux'
            ],
            'database': [
                r'base de datos', r'database', r'db', r'postgresql',
                r'mongodb', r'mysql', r'redis'
            ],
            'analytics': [
                r'analytics', r'metricas', r'reportes?', r'dashboard',
                r'estadisticas', r'tracking'
            ],
            'notifications': [
                r'notificaciones', r'notifications', r'email',
                r'push notifications', r'alerts'
            ],
            'search': [
                r'búsqueda', r'search', r'filtros?', r'elasticsearch',
                r'algolia'
            ],
            'reviews': [
                r'reviews', r'reseñas', r'comentarios', r'ratings',
                r'calificaciones', r'feedback'
            ],
            'social': [
                r'social', r'seguir', r'follow', r'likes', r'shares',
                r'red social', r'perfiles'
            ]
        }
        
        # Mapeo de funcionalidades a módulos
        self.feature_to_modules = {
            'auth': ['auth_module'],
            'payments': ['payments_module'],
            'chat': ['chat_module'],
            'ecommerce': ['product_catalog', 'shopping_cart', 'order_management'],
            'admin': ['admin_dashboard'],
            'mobile': ['mobile_app'],
            'analytics': ['analytics_module'],
            'notifications': ['notification_system'],
            'search': ['search_module'],
            'reviews': ['review_system'],
            'social': ['social_features']
        }
    
    async def analyze_prompt(self, prompt: str, **kwargs) -> 'ProjectConfig':
        """
        Analizar prompt del usuario y generar configuración del proyecto
        
        Args:
            prompt: Descripción del proyecto del usuario
            **kwargs: Parámetros adicionales (budget, timeline, etc.)
            
        Returns:
            ProjectConfig: Configuración del proyecto generada
        """
        self.logger.info(f"Analyzing prompt: {prompt[:100]}...")
        
        # 1. Extraer funcionalidades principales
        features = self._extract_features(prompt)
        self.logger.info(f"Detected features: {features}")
        
        # 2. Determinar complejidad del proyecto
        complexity = self._calculate_complexity(prompt, features)
        
        # 3. Estimar timeline y equipo
        timeline = kwargs.get('timeline', self._estimate_timeline(complexity))
        team_size = kwargs.get('team_size', self._estimate_team_size(complexity))
        
        # 4. Determinar tech stack
        tech_stack = await self._determine_tech_stack(prompt, features)
        
        # 5. Identificar requisitos de compliance
        compliance = self._extract_compliance_requirements(prompt)
        
        # 6. Generar nombre del proyecto
        project_name = await self._generate_project_name(prompt)
        
        # Usar AI para enriquecer el análisis
        enriched_analysis = await self._enrich_with_ai_analysis(
            prompt, features, complexity, tech_stack
        )
        
        from .pm_bot import ProjectConfig
        return ProjectConfig(
            name=project_name,
            description=prompt,
            complexity=complexity,
            timeline=timeline,
            budget=kwargs.get('budget', 'medium'),
            requirements=enriched_analysis.get('requirements', features),
            tech_stack=tech_stack,
            team_size=team_size,
            compliance=compliance
        )
    
    def _extract_features(self, prompt: str) -> List[str]:
        """Extraer funcionalidades del prompt usando patrones regex"""
        prompt_lower = prompt.lower()
        detected_features = []
        
        for feature, patterns in self.feature_patterns.items():
            for pattern in patterns:
                if re.search(pattern, prompt_lower):
                    detected_features.append(feature)
                    break
        
        # Eliminar duplicados manteniendo orden
        return list(dict.fromkeys(detected_features))
    
    def _calculate_complexity(self, prompt: str, features: List[str]) -> int:
        """Calcular complejidad del proyecto (1-10)"""
        base_complexity = len(features)
        
        # Factores que aumentan complejidad
        complexity_indicators = {
            r'tiempo real|real[- ]?time|websocket': 2,
            r'machine learning|ml|ai|inteligencia artificial': 3,
            r'microservic|distributed|scalab': 2,
            r'multi[- ]?tenant|enterprise': 2,
            r'compliance|gdpr|hipaa|pci': 1,
            r'mobile|ios|android': 1,
            r'payment|stripe|paypal': 1,
            r'analytic|reporting|dashboard': 1,
            r'blockchain|crypto': 3,
            r'video|streaming|multimedia': 2
        }
        
        prompt_lower = prompt.lower()
        for pattern, weight in complexity_indicators.items():
            if re.search(pattern, prompt_lower):
                base_complexity += weight
        
        # Normalizar a escala 1-10
        return min(max(base_complexity, 1), 10)
    
    def _estimate_timeline(self, complexity: int) -> str:
        """Estimar timeline basado en complejidad"""
        timeline_map = {
            1: "1-2 weeks",
            2: "2-3 weeks", 
            3: "3-4 weeks",
            4: "1-2 months",
            5: "2-3 months",
            6: "3-4 months",
            7: "4-6 months",
            8: "6-8 months",
            9: "8-12 months",
            10: "12+ months"
        }
        return timeline_map.get(complexity, "3-6 months")
    
    def _estimate_team_size(self, complexity: int) -> int:
        """Estimar tamaño del equipo basado en complejidad"""
        if complexity <= 2:
            return 2  # 1 fullstack + 1 QA
        elif complexity <= 4:
            return 4  # 2 dev + 1 frontend + 1 QA
        elif complexity <= 6:
            return 6  # 2 backend + 2 frontend + 1 DevOps + 1 QA
        elif complexity <= 8:
            return 8  # 3 backend + 2 frontend + 1 DevOps + 1 mobile + 1 QA
        else:
            return 10  # Equipo completo
    
    async def _determine_tech_stack(self, prompt: str, features: List[str]) -> List[str]:
        """Determinar tech stack óptimo basado en requerimientos"""
        
        # Stack por defecto moderno
        default_stack = {
            'backend': 'Node.js + Express',
            'frontend': 'React + TypeScript',
            'database': 'PostgreSQL',
            'cache': 'Redis',
            'deployment': 'Docker + AWS'
        }
        
        # Ajustes basados en features detectadas
        if 'chat' in features or 'tiempo real' in prompt.lower():
            default_stack['realtime'] = 'Socket.io'
        
        if 'mobile' in features:
            default_stack['mobile'] = 'React Native'
        
        if 'payments' in features:
            default_stack['payments'] = 'Stripe'
        
        if 'analytics' in features:
            default_stack['analytics'] = 'Analytics.js'
        
        # Usar AI para refinar tech stack
        ai_recommendations = await self._get_ai_tech_recommendations(prompt, features)
        if ai_recommendations:
            default_stack.update(ai_recommendations)
        
        return [f"{k}: {v}" for k, v in default_stack.items()]
    
    def _extract_compliance_requirements(self, prompt: str) -> List[str]:
        """Extraer requisitos de compliance del prompt"""
        compliance_patterns = {
            'GDPR': r'gdpr|privacidad|privacy|protección de datos',
            'PCI DSS': r'pci|pagos|tarjetas|credit card',
            'HIPAA': r'hipaa|salud|health|medical',
            'SOX': r'sox|sarbanes|financial reporting',
            'ISO 27001': r'iso.*27001|seguridad de la información',
            'SOC 2': r'soc.*2|auditoria|audit'
        }
        
        prompt_lower = prompt.lower()
        detected_compliance = []
        
        for standard, pattern in compliance_patterns.items():
            if re.search(pattern, prompt_lower):
                detected_compliance.append(standard)
        
        return detected_compliance
    
    async def _generate_project_name(self, prompt: str) -> str:
        """Generar nombre del proyecto usando AI"""
        try:
            ai_prompt = f"""
            Basándote en esta descripción de proyecto, genera un nombre técnico conciso para el proyecto:
            
            "{prompt}"
            
            Requisitos:
            - Máximo 3 palabras
            - En inglés
            - Descriptivo pero técnico
            - Sin espacios (usar guiones o camelCase)
            
            Responde solo con el nombre del proyecto.
            """
            
            response = await self.ai.generate_response(ai_prompt, max_tokens=50)
            name = response.strip().replace(' ', '-').lower()
            
            # Sanitizar nombre
            name = re.sub(r'[^a-z0-9\-_]', '', name)
            
            return name or "enterprise-project"
            
        except Exception as e:
            self.logger.warning(f"Could not generate project name: {e}")
            return "enterprise-project"
    
    async def _enrich_with_ai_analysis(self, prompt: str, features: List[str], 
                                     complexity: int, tech_stack: List[str]) -> Dict[str, Any]:
        """Enriquecer análisis usando AI"""
        try:
            ai_prompt = f"""
            Analiza este proyecto y proporciona un análisis técnico detallado:
            
            Descripción: {prompt}
            Features detectadas: {', '.join(features)}
            Complejidad: {complexity}/10
            Tech stack: {', '.join(tech_stack)}
            
            Proporciona en formato JSON:
            {{
                "requirements": ["lista de requerimientos técnicos específicos"],
                "risks": ["principales riesgos técnicos"],
                "architecture_recommendations": ["recomendaciones de arquitectura"],
                "performance_considerations": ["consideraciones de performance"],
                "security_requirements": ["requerimientos de seguridad"]
            }}
            
            Responde solo con el JSON válido.
            """
            
            response = await self.ai.generate_response(ai_prompt, max_tokens=1000)
            
            # Intentar parsear JSON
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # Extraer JSON del response si está envuelto en texto
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                
        except Exception as e:
            self.logger.warning(f"AI enrichment failed: {e}")
        
        # Fallback analysis
        return {
            "requirements": features,
            "risks": ["Technical complexity", "Integration challenges"],
            "architecture_recommendations": ["Microservices", "API-first"],
            "performance_considerations": ["Caching", "Database optimization"],
            "security_requirements": ["Authentication", "Data encryption"]
        }
    
    async def _get_ai_tech_recommendations(self, prompt: str, features: List[str]) -> Dict[str, str]:
        """Obtener recomendaciones de tech stack usando AI"""
        try:
            ai_prompt = f"""
            Para este proyecto, recomienda el tech stack más apropiado:
            
            Proyecto: {prompt}
            Features: {', '.join(features)}
            
            Responde en JSON con estas categorías:
            {{
                "backend": "tecnología recomendada",
                "frontend": "tecnología recomendada", 
                "database": "tecnología recomendada",
                "cache": "tecnología recomendada si aplica",
                "queue": "tecnología recomendada si aplica",
                "search": "tecnología recomendada si aplica"
            }}
            
            Solo tecnologías existentes y populares. Responde solo JSON.
            """
            
            response = await self.ai.generate_response(ai_prompt, max_tokens=300)
            
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                    
        except Exception as e:
            self.logger.warning(f"AI tech recommendations failed: {e}")
        
        return {}
    
    async def generate_modules(self, project_config: 'ProjectConfig') -> Dict[str, ModuleSpec]:
        """
        Generar módulos específicos para el proyecto
        
        Args:
            project_config: Configuración del proyecto
            
        Returns:
            Dict[str, ModuleSpec]: Diccionario de módulos generados
        """
        self.logger.info(f"Generating modules for project: {project_config.name}")
        
        # 1. Identificar módulos base requeridos
        base_modules = self._identify_base_modules(project_config)
        
        # 2. Generar módulos específicos por feature
        feature_modules = await self._generate_feature_modules(project_config)
        
        # 3. Agregar módulos de infraestructura
        infra_modules = self._generate_infrastructure_modules(project_config)
        
        # 4. Combinar todos los módulos
        all_modules = {**base_modules, **feature_modules, **infra_modules}
        
        # 5. Calcular dependencias entre módulos
        self._calculate_module_dependencies(all_modules)
        
        self.logger.info(f"Generated {len(all_modules)} modules")
        
        return all_modules
    
    def _identify_base_modules(self, project_config: 'ProjectConfig') -> Dict[str, ModuleSpec]:
        """Identificar módulos base requeridos para cualquier proyecto"""
        base_modules = {}
        
        # Siempre incluir core modules
        base_modules['core_backend'] = ModuleSpec(
            name='core_backend',
            type='backend',
            description='Core backend API with authentication and base functionality',
            dependencies=[],
            agents_needed=['backend'],
            complexity=project_config.complexity // 2,
            estimated_hours=20 + (project_config.complexity * 2),
            tech_stack=self._extract_backend_tech(project_config.tech_stack),
            apis_needed=['auth', 'users'],
            database_entities=['users', 'sessions']
        )
        
        base_modules['core_frontend'] = ModuleSpec(
            name='core_frontend',
            type='frontend',
            description='Core frontend application with routing and base components',
            dependencies=['core_backend'],
            agents_needed=['frontend'],
            complexity=project_config.complexity // 2,
            estimated_hours=15 + (project_config.complexity * 2),
            tech_stack=self._extract_frontend_tech(project_config.tech_stack),
            apis_needed=['auth', 'users'],
            database_entities=[]
        )
        
        return base_modules
    
    async def _generate_feature_modules(self, project_config: 'ProjectConfig') -> Dict[str, ModuleSpec]:
        """Generar módulos específicos basados en features detectadas"""
        feature_modules = {}
        
        # Mapear requirements a módulos usando AI
        ai_modules = await self._ai_generate_modules(project_config)
        
        if ai_modules:
            feature_modules.update(ai_modules)
        else:
            # Fallback: generar módulos basados en patterns
            feature_modules.update(self._pattern_based_modules(project_config))
        
        return feature_modules
    
    async def _ai_generate_modules(self, project_config: 'ProjectConfig') -> Dict[str, ModuleSpec]:
        """Generar módulos usando AI"""
        try:
            ai_prompt = f"""
            Para este proyecto, descompón la funcionalidad en módulos técnicos específicos:
            
            Proyecto: {project_config.name}
            Descripción: {project_config.description}
            Complejidad: {project_config.complexity}/10
            Requirements: {', '.join(project_config.requirements)}
            
            Genera módulos en este formato JSON:
            {{
                "module_name": {{
                    "name": "module_name",
                    "type": "backend|frontend|fullstack",
                    "description": "descripción técnica específica",
                    "apis_needed": ["lista de APIs que este módulo necesita"],
                    "database_entities": ["entidades de base de datos necesarias"],
                    "estimated_hours": número_entero,
                    "complexity": 1-10
                }}
            }}
            
            Enfócate en módulos técnicos específicos, no genéricos.
            Responde solo JSON válido.
            """
            
            response = await self.ai.generate_response(ai_prompt, max_tokens=1500)
            
            try:
                modules_data = json.loads(response)
                modules = {}
                
                for module_name, module_data in modules_data.items():
                    modules[module_name] = ModuleSpec(
                        name=module_data['name'],
                        type=module_data['type'],
                        description=module_data['description'],
                        dependencies=self._infer_dependencies(module_data, modules_data),
                        agents_needed=self._determine_agents_needed(module_data['type']),
                        complexity=module_data.get('complexity', 5),
                        estimated_hours=module_data.get('estimated_hours', 20),
                        tech_stack=self._extract_tech_for_module(module_data['type'], project_config.tech_stack),
                        apis_needed=module_data.get('apis_needed', []),
                        database_entities=module_data.get('database_entities', [])
                    )
                
                return modules
                
            except json.JSONDecodeError:
                self.logger.warning("Could not parse AI-generated modules JSON")
                
        except Exception as e:
            self.logger.warning(f"AI module generation failed: {e}")
        
        return {}
    
    def _pattern_based_modules(self, project_config: 'ProjectConfig') -> Dict[str, ModuleSpec]:
        """Generar módulos basado en patterns detectados"""
        modules = {}
        
        for requirement in project_config.requirements:
            if requirement in self.feature_to_modules:
                for module_template in self.feature_to_modules[requirement]:
                    module_spec = self.templates.get_module_template(module_template)
                    if module_spec:
                        modules[module_template] = module_spec
        
        return modules
    
    def _generate_infrastructure_modules(self, project_config: 'ProjectConfig') -> Dict[str, ModuleSpec]:
        """Generar módulos de infraestructura y deployment"""
        infra_modules = {}
        
        # Siempre incluir QA global
        infra_modules['global_qa'] = ModuleSpec(
            name='global_qa',
            type='qa',
            description='Global testing and quality assurance for the entire project',
            dependencies=list(project_config.requirements),  # Depende de todos los módulos
            agents_needed=['qa'],
            complexity=3,
            estimated_hours=10 + project_config.complexity,
            tech_stack=['Jest', 'Cypress', 'Postman'],
            apis_needed=[],
            database_entities=[]
        )
        
        # Deployment si la complejidad lo justifica
        if project_config.complexity >= 4:
            infra_modules['deployment'] = ModuleSpec(
                name='deployment',
                type='deploy',
                description='Deployment and DevOps configuration',
                dependencies=['global_qa'],
                agents_needed=['devops'],
                complexity=2,
                estimated_hours=8 + (project_config.complexity // 2),
                tech_stack=['Docker', 'AWS', 'GitHub Actions'],
                apis_needed=[],
                database_entities=[]
            )
        
        return infra_modules
    
    def _calculate_module_dependencies(self, modules: Dict[str, ModuleSpec]):
        """Calcular y actualizar dependencias entre módulos"""
        for module_name, module in modules.items():
            # Frontend modules depend on backend modules
            if module.type == 'frontend':
                for other_name, other_module in modules.items():
                    if (other_module.type == 'backend' and 
                        any(api in other_module.apis_needed for api in module.apis_needed)):
                        if other_name not in module.dependencies:
                            module.dependencies.append(other_name)
            
            # QA depends on all feature modules
            if module.type == 'qa':
                for other_name, other_module in modules.items():
                    if other_module.type in ['backend', 'frontend', 'fullstack']:
                        if other_name not in module.dependencies:
                            module.dependencies.append(other_name)
            
            # Deployment depends on QA
            if module.type == 'deploy':
                for other_name, other_module in modules.items():
                    if other_module.type == 'qa':
                        if other_name not in module.dependencies:
                            module.dependencies.append(other_name)
    
    def _infer_dependencies(self, module_data: Dict, all_modules: Dict) -> List[str]:
        """Inferir dependencias de un módulo basado en APIs que necesita"""
        dependencies = []
        
        for other_name, other_data in all_modules.items():
            if (other_data.get('type') == 'backend' and 
                any(api in other_data.get('apis_needed', []) 
                    for api in module_data.get('apis_needed', []))):
                dependencies.append(other_name)
        
        return dependencies
    
    def _determine_agents_needed(self, module_type: str) -> List[str]:
        """Determinar agentes necesarios basado en tipo de módulo"""
        agent_mapping = {
            'backend': ['backend'],
            'frontend': ['frontend'],
            'fullstack': ['fullstack'],
            'mobile': ['mobile'],
            'qa': ['qa'],
            'deploy': ['devops'],
            'data': ['data'],
            'security': ['security']
        }
        
        return agent_mapping.get(module_type, ['backend'])
    
    def _extract_backend_tech(self, tech_stack: List[str]) -> List[str]:
        """Extraer tecnologías de backend del tech stack"""
        backend_techs = []
        for tech in tech_stack:
            if any(keyword in tech.lower() for keyword in ['node', 'express', 'python', 'django', 'fastapi']):
                backend_techs.append(tech)
        return backend_techs or ['Node.js + Express']
    
    def _extract_frontend_tech(self, tech_stack: List[str]) -> List[str]:
        """Extraer tecnologías de frontend del tech stack"""
        frontend_techs = []
        for tech in tech_stack:
            if any(keyword in tech.lower() for keyword in ['react', 'vue', 'angular', 'next']):
                frontend_techs.append(tech)
        return frontend_techs or ['React + TypeScript']
    
    def _extract_tech_for_module(self, module_type: str, tech_stack: List[str]) -> List[str]:
        """Extraer tecnologías relevantes para un tipo de módulo"""
        if module_type == 'backend':
            return self._extract_backend_tech(tech_stack)
        elif module_type == 'frontend':
            return self._extract_frontend_tech(tech_stack)
        else:
            return tech_stack
    
    def estimate_completion_time(self, project_config: 'ProjectConfig') -> datetime:
        """Estimar tiempo de finalización del proyecto"""
        base_hours = 40  # Horas base
        complexity_hours = project_config.complexity * 10
        
        total_hours = base_hours + complexity_hours
        
        # Asumir 6 horas productivas por día por desarrollador
        daily_hours = 6 * project_config.team_size
        days_needed = total_hours / daily_hours
        
        # Agregar buffer del 20%
        days_with_buffer = days_needed * 1.2
        
        return datetime.now() + timedelta(days=days_with_buffer)


# core/ai_interface.py
"""
Interface para comunicación con modelos de IA (local y cloud)
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, Optional
import logging


class AIInterface:
    """Interface unificada para modelos de IA locales y cloud"""
    
    def __init__(self):
        self.logger = logging.getLogger('AIInterface')
        self.ollama_host = "http://localhost:11434"
        self.preferred_model = "deepseek-r1:14b"
        
    async def generate_response(self, prompt: str, max_tokens: int = 1000, 
                              temperature: float = 0.3) -> str:
        """Generar respuesta usando el
            '