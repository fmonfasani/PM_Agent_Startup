# core/planner.py
"""
Project Planner - Analiza prompts del usuario y genera arquitectura modular
"""

import json
import re
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
import logging

from .ai_interface import AIInterface
from .types import ModuleSpec # <-- Importación corregida para ModuleSpec
# from .pm_bot import ProjectConfig # Comentar/Descomentar según dónde ProjectConfig esté definido.
                                  # Si ProjectConfig está en pm_bot.py y pm_bot.py importa planner.py,
                                  # entonces esta importación debería ser manejada con un try-except
                                  # o moviendo ProjectConfig a types.py también.
                                  # Por ahora, dejo el try-except en analyze_prompt.


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
                r'web', r'frontend', r'react', 'vue', 'angular',
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

        # Plantillas de módulos estándar
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
                'apis_needed': ['analytics', 'metrics', 'user_analytics'],
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

        # Importar ProjectConfig si no está disponible
        try:
            from .pm_bot import ProjectConfig
        except ImportError:
            # Definir ProjectConfig localmente si no está disponible,
            # o idealmente, mover ProjectConfig a core/types.py también
            # si es una clase que otros módulos deben importar.
            from dataclasses import dataclass # Asegurarse de importar dataclass si se usa aquí
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
        """Extraer requisitos de performance del prompt usando AI o regex
           (Esta es la parte del código que faltaba en tu input anterior)
        """
        requirements = {}
        prompt_lower = prompt.lower()

        # Latencia
        latency_match = re.search(r'(baja latencia|respuesta rápida|menos de \d+ms)', prompt_lower)
        if latency_match:
            requirements['latency'] = 'low'
            if 'menos de' in latency_match.group(0):
                ms_match = re.search(r'menos de (\d+)ms', latency_match.group(0))
                if ms_match:
                    requirements['latency_ms'] = int(ms_match.group(1))

        # Escalabilidad
        scalability_match = re.search(r'(escalable|alta concurrencia|miles de usuarios|millones de usuarios)', prompt_lower)
        if scalability_match:
            requirements['scalability'] = 'high'
            if 'miles de usuarios' in scalability_match.group(0):
                requirements['concurrent_users'] = 'thousands'
            elif 'millones de usuarios' in scalability_match.group(0):
                requirements['concurrent_users'] = 'millions'

        # Disponibilidad
        availability_match = re.search(r'(alta disponibilidad|99\.?\d*% uptime|siempre disponible)', prompt_lower)
        if availability_match:
            requirements['availability'] = 'high'
            if '% uptime' in availability_match.group(0):
                uptime_match = re.search(r'(\d+\.?\d*)% uptime', availability_match.group(0))
                if uptime_match:
                    requirements['uptime_percentage'] = float(uptime_match.group(1))

        # Redundancia/Resiliencia
        resilience_match = re.search(r'(tolerancia a fallos|redundancia|resiliente)', prompt_lower)
        if resilience_match:
            requirements['resilience'] = True

        return requirements

    async def _get_ai_tech_recommendations(self, prompt: str, features: List[str]) -> Dict[str, str]:
        """
        Obtener recomendaciones de tech stack adicionales de la AI.
        """
        system_message = (
            "Eres un arquitecto de software experto. Analiza la descripción del proyecto "
            "y las funcionalidades detectadas. Proporciona recomendaciones específicas de "
            "tecnología (frameworks, bases de datos, herramientas específicas) en formato JSON, "
            "sin explicaciones adicionales. Si no tienes una recomendación fuerte para una categoría, omítela."
            "Las categorías deben ser: 'backend', 'frontend', 'database', 'cache', 'deployment', 'realtime', 'mobile', 'payments', 'analytics', 'search', 'storage'."
            "Ejemplo de formato JSON: {'backend': 'Spring Boot', 'frontend': 'Angular', 'database': 'MongoDB'}"
        )
        user_message = (
            f"Descripción del proyecto: {prompt}\n"
            f"Funcionalidades detectadas: {', '.join(features)}\n"
            "Dame tus recomendaciones de stack tecnológico en formato JSON."
        )

        try:
            raw_response = await self.ai.generate_response(system_message + "\n" + user_message, max_tokens=500, temperature=0.7)
            self.logger.debug(f"AI raw tech stack response: {raw_response}")
            # Intenta limpiar la respuesta para asegurarte de que sea un JSON válido
            json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                recommendations = json.loads(json_str)
                # Asegurarse de que las claves y valores sean strings
                return {k.lower(): str(v) for k, v in recommendations.items()}
            else:
                self.logger.warning(f"AI did not return valid JSON for tech stack: {raw_response}")
                return {}
        except Exception as e:
            self.logger.error(f"Error getting AI tech recommendations: {e}")
            return {}

    async def _enrich_with_ai_analysis(self, prompt: str, features: List[str], complexity: int, tech_stack: List[str]) -> Dict[str, Any]:
        """
        Usar AI para enriquecer el análisis del proyecto.
        """
        system_message = (
            "Eres un planificador de proyectos experimentado. Analiza la descripción del proyecto, "
            "las funcionalidades detectadas, la complejidad y el stack tecnológico preliminar. "
            "Proporciona un análisis enriquecido en formato JSON, sin explicaciones adicionales. "
            "Incluye 'requirements' (lista de requisitos detallados), 'potential_challenges' (lista de desafíos), "
            "'suggested_improvements' (lista de mejoras opcionales). "
            "Ejemplo de JSON: {'requirements': ['Auth', 'Payments'], 'potential_challenges': ['Scalability'], 'suggested_improvements': ['Analytics']}"
        )
        user_message = (
            f"Descripción del proyecto: {prompt}\n"
            f"Funcionalidades detectadas: {', '.join(features)}\n"
            f"Complejidad calculada: {complexity}/10\n"
            f"Tech Stack preliminar: {', '.join(tech_stack)}\n"
            "Genera un análisis enriquecido del proyecto en formato JSON."
        )

        try:
            raw_response = await self.ai.generate_response(system_message + "\n" + user_message, max_tokens=1000, temperature=0.6)
            self.logger.debug(f"AI raw enrichment response: {raw_response}")
            json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                enriched_data = json.loads(json_str)
                # Asegurarse de que las listas sean listas de strings
                return {k: [str(item) for item in v] if isinstance(v, list) else v for k, v in enriched_data.items()}
            else:
                self.logger.warning(f"AI did not return valid JSON for enrichment: {raw_response}")
                return {}
        except Exception as e:
            self.logger.error(f"Error enriching with AI analysis: {e}")
            return {}

    async def _generate_project_name(self, prompt: str) -> str:
        """
        Generar un nombre de proyecto conciso usando AI.
        """
        system_message = (
            "Eres un generador de nombres de proyectos creativo. Basado en la descripción, "
            "propón un nombre de proyecto conciso (2-5 palabras). Sin explicaciones, solo el nombre."
        )
        user_message = f"Descripción del proyecto: {prompt}\nNombre propuesto:"

        try:
            name = await self.ai.generate_response(system_message + "\n" + user_message, max_tokens=20, temperature=0.8)
            # Limpiar la respuesta de la AI
            return name.strip().replace('"', '').replace("'", "").replace('.', '').split('\n')[0]
        except Exception as e:
            self.logger.error(f"Error generating project name with AI: {e}")
            return "Untitled Project"

    async def plan_project(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Método principal para planificar un proyecto basado en un prompt.
        """
        project_config = await self.analyze_prompt(prompt, **kwargs)
        # Aquí podrías añadir lógica para generar los módulos basados en project_config
        # Por ahora, solo devolvemos la configuración general del proyecto.
        return project_config.__dict__ # Convertir dataclass a diccionario para fácil manejo

# Ejemplo de uso (solo para pruebas, no para ejecución en producción)
async def main():
    planner = ProjectPlanner()
    prompt = "Necesito una aplicación web y móvil de comercio electrónico con autenticación de usuarios, sistema de pagos con Stripe y chat en tiempo real. También un panel de administración para ver métricas y gestionar pedidos. Quiero que sea escalable para millones de usuarios."
    
    # Simular _get_ai_tech_recommendations y _enrich_with_ai_analysis si no hay AI real conectada
    # Para la demostración, las funciones AI están simuladas si AIInterface no es real.
    # Necesitarías una implementación real de AIInterface para que esto funcione.

    try:
        project_plan = await planner.plan_project(prompt)
        print(json.dumps(project_plan, indent=4))
    except Exception as e:
        print(f"Error durante la planificación: {e}")

if __name__ == "__main__":
    # Configurar logging básico para ver mensajes
    logging.basicConfig(level=logging.INFO)
    # Importar ModuleSpec antes de ProjectPlanner para evitar NameError en pruebas directas
    # from core.types import ModuleSpec # Esto ya se hace en el archivo si se ejecuta normalmente
    asyncio.run(main())