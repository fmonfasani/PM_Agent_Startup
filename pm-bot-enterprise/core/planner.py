# core/planner.py
"""
Project Planner - Analiza prompts del usuario y genera arquitectura modular
"""

import json
import re
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
import logging

from .ai_interface import AIInterface


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
        self.logger = logging.getLogger('ProjectPlanner')
        
        # Patrones para identificar funcionalidades
        self.feature_patterns = {
            'auth': [
                r'autenticaci[óo]n', r'login', r'registro', r'sign[- ]?up',
                r'usuarios?', r'user management', r'auth', r'jwt'
            ],
            'payments': [
                r'pagos?', r'payment', r'stripe', r'paypal', r'billing',
                r'suscripci[óo]n', r'subscription', r'checkout', r'facturaci[óo]n'
            ],
            'chat': [
                r'chat', r'mensajer[íi]a', r'messaging', r'tiempo real',
                r'real[- ]?time', r'websocket', r'socket\.io'
            ],
            'ecommerce': [
                r'tienda', r'shop', r'cart', r'carrito', r'productos?',
                r'catalog', r'inventory', r'marketplace', r'e-commerce',
                r'vendedores?', r'sellers?'
            ],
            'admin': [
                r'admin', r'dashboard', r'panel', r'backoffice',
                r'administraci[óo]n', r'management', r'cms'
            ],
            'api': [
                r'api', r'rest', r'graphql', r'endpoint', r'microservic',
                r'backend', r'servidor'
            ],
            'mobile': [
                r'app m[óo]vil', r'mobile app', r'react native',
                r'flutter', r'ios', r'android', r'móvil'
            ],
            'web': [
                r'web', r'frontend', r'react', r'vue', r'angular',
                r'interfaz', r'ui', r'ux', r'next\.js'
            ],
            'database': [
                r'base de datos', r'database', r'db', r'postgresql',
                r'mongodb', r'mysql', r'redis'
            ],
            'analytics': [
                r'analytics', r'metricas', r'reportes?', r'dashboard',
                r'estadisticas', r'tracking', r'kpi'
            ],
            'notifications': [
                r'notificaciones', r'notifications', r'email',
                r'push notifications', r'alerts', r'alertas'
            ],
            'search': [
                r'búsqueda', r'search', r'filtros?', r'elasticsearch',
                r'algolia', r'buscar'
            ],
            'reviews': [
                r'reviews', r'reseñas', r'comentarios', r'ratings',
                r'calificaciones', r'feedback', r'valoraciones'
            ],
            'social': [
                r'social', r'seguir', r'follow', r'likes', r'shares',
                r'red social', r'perfiles', r'friends'
            ],
            'file_upload': [
                r'upload', r'subir archivos', r'files', r'images',
                r'documentos', r'multimedia'
            ],
            'reports': [
                r'reportes?', r'reports?', r'informes?', r'export',
                r'pdf', r'excel', r'csv'
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
            'social': ['social_features'],
            'file_upload': ['file_upload_module'],
            'reports': ['reporting_module']
        }

        # Plantillas de módulos estándar (movidas aquí para evitar imports circulares)
        self.module_templates = self._initialize_module_templates()
    
    def _initialize_module_templates(self) -> Dict[str, Dict[str, Any]]:
        """Inicializar plantillas de módulos predefinidos"""
        return {
            'auth_module': {
                'name': 'auth_module',
                'type': 'backend',
                'description': 'Authentication and user management system with JWT',
                'dependencies': [],
                'agents_needed': ['backend'],
                'complexity': 4,
                'estimated_hours': 25,
                'tech_stack': ['JWT', 'bcrypt', 'passport', 'express-validator'],
                'apis_needed': ['auth', 'users', 'sessions'],
                'database_entities': ['users', 'sessions', 'roles', 'permissions']
            },
            
            'payments_module': {
                'name': 'payments_module',
                'type': 'backend',
                'description': 'Payment processing with Stripe integration and subscription management',
                'dependencies': ['auth_module'],
                'agents_needed': ['backend'],
                'complexity': 6,
                'estimated_hours': 30,
                'tech_stack': ['Stripe API', 'Webhooks', 'PayPal SDK'],
                'apis_needed': ['payments', 'subscriptions', 'invoices', 'refunds'],
                'database_entities': ['payments', 'subscriptions', 'customers', 'invoices']
            },
            
            'chat_module': {
                'name': 'chat_module',
                'type': 'fullstack',
                'description': 'Real-time chat system with WebSocket and message history',
                'dependencies': ['auth_module'],
                'agents_needed': ['backend', 'frontend'],
                'complexity': 7,
                'estimated_hours': 35,
                'tech_stack': ['Socket.io', 'Redis', 'MongoDB'],
                'apis_needed': ['messages', 'conversations', 'notifications'],
                'database_entities': ['messages', 'conversations', 'participants']
            },
            
            'product_catalog': {
                'name': 'product_catalog',
                'type': 'fullstack',
                'description': 'Product catalog with search, filtering and inventory management',
                'dependencies': ['auth_module'],
                'agents_needed': ['backend', 'frontend'],
                'complexity': 5,
                'estimated_hours': 28,
                'tech_stack': ['Elasticsearch', 'Redis', 'Image Processing'],
                'apis_needed': ['products', 'categories', 'inventory', 'search'],
                'database_entities': ['products', 'categories', 'inventory', 'product_images']
            },
            
            'shopping_cart': {
                'name': 'shopping_cart',
                'type': 'fullstack',
                'description': 'Shopping cart and checkout process',
                'dependencies': ['auth_module', 'product_catalog'],
                'agents_needed': ['backend', 'frontend'],
                'complexity': 4,
                'estimated_hours': 22,
                'tech_stack': ['Session Management', 'Redis'],
                'apis_needed': ['cart', 'checkout', 'orders'],
                'database_entities': ['carts', 'cart_items', 'orders', 'order_items']
            },
            
            'admin_dashboard': {
                'name': 'admin_dashboard',
                'type': 'frontend',
                'description': 'Administrative dashboard with analytics and management tools',
                'dependencies': ['auth_module'],
                'agents_needed': ['frontend'],
                'complexity': 5,
                'estimated_hours': 28,
                'tech_stack': ['React Admin', 'Charts.js', 'Material-UI'],
                'apis_needed': ['admin', 'analytics', 'reports', 'users_management'],
                'database_entities': []
            },
            
            'mobile_app': {
                'name': 'mobile_app',
                'type': 'mobile',
                'description': 'Mobile application for iOS and Android with offline support',
                'dependencies': ['core_backend'],
                'agents_needed': ['mobile'],
                'complexity': 8,
                'estimated_hours': 45,
                'tech_stack': ['React Native', 'Expo', 'AsyncStorage'],
                'apis_needed': ['mobile_auth', 'mobile_api', 'push_notifications'],
                'database_entities': []
            },
            
            'analytics_module': {
                'name': 'analytics_module',
                'type': 'backend',
                'description': 'Analytics and metrics collection system',
                'dependencies': ['auth_module'],
                'agents_needed': ['backend', 'data'],
                'complexity': 6,
                'estimated_hours': 32,
                'tech_stack': ['InfluxDB', 'Grafana', 'Apache Kafka'],
                'apis_needed': ['analytics', 'metrics', 'reports'],
                'database_entities': ['events', 'metrics', 'user_analytics']
            },
            
            'notification_system': {
                'name': 'notification_system',
                'type': 'backend',
                'description': 'Multi-channel notification system (email, push, SMS)',
                'dependencies': ['auth_module'],
                'agents_needed': ['backend'],
                'complexity': 5,
                'estimated_hours': 25,
                'tech_stack': ['SendGrid', 'FCM', 'Twilio', 'Redis Queue'],
                'apis_needed': ['notifications', 'templates', 'delivery_status'],
                'database_entities': ['notifications', 'notification_templates', 'delivery_logs']
            }
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
        
        # 7. Usar AI para enriquecer el análisis
        enriched_analysis = await self._enrich_with_ai_analysis(
            prompt, features, complexity, tech_stack
        )
        
        # 8. Extraer requisitos de performance y escalabilidad
        performance_requirements = self._extract_performance_requirements(prompt)
        
        # Importar ProjectConfig aquí para evitar imports circulares
        try:
            from .pm_bot import ProjectConfig
        except ImportError:
            # Definir ProjectConfig localmente si no está disponible
            @dataclass
            class ProjectConfig:
                name: str
                description: str
                complexity: int
                timeline: str
                budget: str
                requirements: List[str]
                tech_stack: List[str]
                team_size: int
                compliance: List[str] = None
        
        return ProjectConfig(
            name=project_name,
            description=prompt,
            complexity=complexity,
            timeline=timeline,
            budget=kwargs.get('budget', 'medium'),
            requirements=enriched_analysis.get('requirements', features),
            tech_stack=tech_stack,
            team_size=team_size,
            compliance=compliance or []
        )

    # Resto de los métodos permanecen igual...
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
            r'video|streaming|multimedia': 2,
            r'geolocation|maps|gps': 1,
            r'oauth|sso|single sign[- ]?on': 1,
            r'multi[- ]?language|i18n|internationalization': 1,
            r'offline|sync|synchronization': 2
        }
        
        prompt_lower = prompt.lower()
        for pattern, weight in complexity_indicators.items():
            if re.search(pattern, prompt_lower):
                base_complexity += weight
        
        # Ajustar por palabras clave de escala
        scale_indicators = {
            r'enterprise|corporativo': 2,
            r'startup|pequeño|simple': -1,
            r'escalable|scale|millones': 2,
            r'high[- ]?performance|alta performance': 1
        }
        
        for pattern, weight in scale_indicators.items():
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
            default_stack['mobile'] = 'React Native + Expo'
        
        if 'payments' in features:
            default_stack['payments'] = 'Stripe + PayPal'
        
        if 'analytics' in features:
            default_stack['analytics'] = 'Analytics.js + Grafana'
        
        if 'search' in features:
            default_stack['search'] = 'Elasticsearch'
        
        if 'file_upload' in features:
            default_stack['storage'] = 'AWS S3 + Multer'
        
        # Detectar preferencias de tecnología en el prompt
        tech_preferences = self._detect_tech_preferences(prompt)
        if tech_preferences:
            default_stack.update(tech_preferences)
        
        # Usar AI para refinar tech stack
        ai_recommendations = await self._get_ai_tech_recommendations(prompt, features)
        if ai_recommendations:
            default_stack.update(ai_recommendations)
        
        return [f"{k}: {v}" for k, v in default_stack.items()]
    
    def _detect_tech_preferences(self, prompt: str) -> Dict[str, str]:
        """Detectar preferencias tecnológicas específicas en el prompt"""
        preferences = {}
        prompt_lower = prompt.lower()
        
        # Backend frameworks
        if re.search(r'django|python', prompt_lower):
            preferences['backend'] = 'Python + Django/FastAPI'
        elif re.search(r'laravel|php', prompt_lower):
            preferences['backend'] = 'PHP + Laravel'
        elif re.search(r'rails|ruby', prompt_lower):
            preferences['backend'] = 'Ruby on Rails'
        elif re.search(r'spring|java', prompt_lower):
            preferences['backend'] = 'Java + Spring Boot'
        
        # Frontend frameworks
        if re.search(r'vue\.?js?', prompt_lower):
            preferences['frontend'] = 'Vue.js + TypeScript'
        elif re.search(r'angular', prompt_lower):
            preferences['frontend'] = 'Angular + TypeScript'
        elif re.search(r'next\.?js?', prompt_lower):
            preferences['frontend'] = 'Next.js + TypeScript'
        
        # Databases
        if re.search(r'mongodb|mongo', prompt_lower):
            preferences['database'] = 'MongoDB'
        elif re.search(r'mysql', prompt_lower):
            preferences['database'] = 'MySQL'
        elif re.search(r'firebase', prompt_lower):
            preferences['database'] = 'Firebase Firestore'
        
        # Cloud providers
        if re.search(r'aws|amazon', prompt_lower):
            preferences['cloud'] = 'AWS'
        elif re.search(r'azure|microsoft', prompt_lower):
            preferences['cloud'] = 'Azure'
        elif re.search(r'gcp|google cloud', prompt_lower):
            preferences['cloud'] = 'Google Cloud'
        elif re.search(r'vercel', prompt_lower):
            preferences['deployment'] = 'Vercel'
        
        return preferences
    
    def _extract_compliance_requirements(self, prompt: str) -> List[str]:
        """Extraer requisitos de compliance del prompt"""
        compliance_patterns = {
            'GDPR': r'gdpr|privacidad|privacy|protección de datos',
            'PCI DSS': r'pci|pagos|tarjetas|credit card',
            'HIPAA': r'hipaa|salud|health|medical',
            'SOX': r'sox|sarbanes|financial reporting',
            'ISO 27001': r'iso.*27001|seguridad de la información',
            'SOC 2': r'soc.*2|auditoria|audit',
            'CCPA': r'ccpa|california privacy'
        }
        
        prompt_lower = prompt.lower()
        detected_compliance = []
        
        for standard, pattern in compliance_patterns.items():
            if re.search(pattern, prompt_lower):
                detected_compliance.append(standard)
        
        return detected_compliance
    
    def _extract_performance_requirements(self, prompt: str) -> Dict[str, Any]:
        """Extraer requisitos de performance del prompt"""
        prompt_lower = prompt.lower()
        requirements = {}
        
        # Detectar requisitos de carga
        if re.search(r'millones?\s+de\s+usuarios|million users', prompt_lower):
            requirements['concurrent_users'] = 1000000
        elif re.search(r'miles?\s+de\s+usuarios|thousand users', prompt_lower):
            requirements['concurrent_users'] = 1000
        
        # Detectar requisitos de velocidad
        if re.search(r'tiempo\s+real|real[- ]?time', prompt_lower):
            requirements['real_time'] = True
        
        if re.search(r'alta\s+performance|high[- ]?performance', prompt_lower):
            requirements['high_performance'] = True
        
        # Detectar requisitos de disponibilidad
        if re.search(r'24/7|alta\s+disponibilidad|high\s+availability', prompt_lower):
            requirements['high_availability'] = True
        
        return requirements
    
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
            - Evita palabras genéricas como "app", "system", "platform"
            
            Ejemplos de buenos nombres:
            - ecommerce-marketplace
            - fintech-dashboard
            - chat-platform
            - analytics-engine
            
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
                "security_requirements": ["requerimientos de seguridad"],
                "scalability_factors": ["factores de escalabilidad"]
            }}
            
            Sé específico y técnico. Responde solo con el JSON válido.
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
            "risks": ["Technical complexity", "Integration challenges", "Timeline pressure"],
            "architecture_recommendations": ["Microservices", "API-first", "Database optimization"],
            "performance_considerations": ["Caching strategy", "Database optimization", "CDN implementation"],
            "security_requirements": ["Authentication", "Data encryption", "Input validation"],
            "scalability_factors": ["Horizontal scaling", "Load balancing", "Database sharding"]
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
                "search": "tecnología recomendada si aplica",
                "monitoring": "tecnología recomendada",
                "testing": "tecnología recomendada"
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
        
        # 6. Optimizar módulos basado en complejidad
        self._optimize_modules_by_complexity(all_modules, project_config.complexity)
        
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
            apis_needed=['auth', 'users', 'health'],
            database_entities=['users', 'sessions']
        )
        
        # Solo agregar frontend si no es exclusivamente API
        if not self._is_api_only_project(project_config):
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
    
    def _is_api_only_project(self, project_config: 'ProjectConfig') -> bool:
        """Determinar si el proyecto es solo API"""
        description_lower = project_config.description.lower()
        return bool(re.search(r'api\s+only|solo\s+api|microservic.*api|headless', description_lower))
    
    async def _generate_feature_modules(self, project_config: 'ProjectConfig') -> Dict[str, ModuleSpec]:
        """Generar módulos específicos basados en features detectadas"""
        feature_modules = {}
        
        # Mapear requirements a módulos usando templates
        feature_modules.update(self._pattern_based_modules(project_config))
        
        return feature_modules
    
    def _pattern_based_modules(self, project_config: 'ProjectConfig') -> Dict[str, ModuleSpec]:
        """Generar módulos basado en patterns detectados"""
        modules = {}
        
        for requirement in project_config.requirements:
            if requirement in self.feature_to_modules:
                for module_template_name in self.feature_to_modules[requirement]:
                    if module_template_name in self.module_templates:
                        template = self.module_templates[module_template_name]
                        modules[module_template_name] = ModuleSpec(
                            name=template['name'],
                            type=template['type'],
                            description=template['description'],
                            dependencies=template['dependencies'].copy(),
                            agents_needed=template['agents_needed'].copy(),
                            complexity=template['complexity'],
                            estimated_hours=template['estimated_hours'],
                            tech_stack=template['tech_stack'].copy(),
                            apis_needed=template['apis_needed'].copy(),
                            database_entities=template['database_entities'].copy()
                        )
        
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
            tech_stack=['Jest', 'Cypress', 'Postman', 'K6'],
            apis_needed=[],
            database_entities=[]
        )
        
        # Deployment si la complejidad lo justifica
        if project_config.complexity >= 4:
            infra_modules['deployment'] = ModuleSpec(
                name='deployment',
                type='deploy',
                description='Deployment and DevOps configuration with CI/CD',
                dependencies=['global_qa'],
                agents_needed=['devops'],
                complexity=2,
                estimated_hours=8 + (project_config.complexity // 2),
                tech_stack=['Docker', 'GitHub Actions', 'AWS/Azure/GCP'],
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
                    if other_module.type in ['backend', 'frontend', 'fullstack', 'mobile']:
                        if other_name not in module.dependencies:
                            module.dependencies.append(other_name)
            
            # Deployment depends on QA
            if module.type == 'deploy':
                for other_name, other_module in modules.items():
                    if other_module.type == 'qa':
                        if other_name not in module.dependencies:
                            module.dependencies.append(other_name)
    
    def _optimize_modules_by_complexity(self, modules: Dict[str, ModuleSpec], project_complexity: int):
        """Optimizar módulos basado en la complejidad del proyecto"""
        # Para proyectos simples, combinar módulos relacionados
        if project_complexity <= 3:
            self._merge_simple_modules(modules)
        
        # Ajustar estimaciones de horas basado en complejidad del proyecto
        complexity_multiplier = 0.8 + (project_complexity / 10) * 0.4  # 0.8 - 1.2
        
        for module in modules.values():
            module.estimated_hours = int(module.estimated_hours * complexity_multiplier)
    
    def _merge_simple_modules(self, modules: Dict[str, ModuleSpec]):
        """Combinar módulos para proyectos simples"""
        # Ejemplo: combinar auth con core_backend para proyectos simples
        if 'auth_module' in modules and 'core_backend' in modules:
            core_backend = modules['core_backend']
            auth_module = modules['auth_module']
            
            # Merge auth functionality into core_backend
            core_backend.description += " with integrated authentication"
            core_backend.apis_needed.extend(auth_module.apis_needed)
            core_backend.database_entities.extend(auth_module.database_entities)
            core_backend.tech_stack.extend(auth_module.tech_stack)
            core_backend.estimated_hours += auth_module.estimated_hours // 2
            
            # Remove separate auth module
            del modules['auth_module']
    
    def _extract_backend_tech(self, tech_stack: List[str]) -> List[str]:
        """Extraer tecnologías de backend del tech stack"""
        backend_techs = []
        for tech in tech_stack:
            if any(keyword in tech.lower() for keyword in ['node', 'express', 'python', 'django', 'fastapi', 'spring', 'laravel']):
                backend_techs.append(tech)
        return backend_techs or ['Node.js + Express']
    
    def _extract_frontend_tech(self, tech_stack: List[str]) -> List[str]:
        """Extraer tecnologías de frontend del tech stack"""
        frontend_techs = []
        for tech in tech_stack:
            if any(keyword in tech.lower() for keyword in ['react', 'vue', 'angular', 'next', 'nuxt']):
                frontend_techs.append(tech)
        return frontend_techs or ['React + TypeScript']
    
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