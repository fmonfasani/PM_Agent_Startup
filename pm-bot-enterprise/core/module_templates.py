# core/module_templates.py
"""
Templates para diferentes tipos de módulos
"""

from typing import Dict, Any, List # Make sure List is imported
from .types import ModuleSpec # <-- CHANGE THIS LINE: Import ModuleSpec from core.types


class ModuleTemplates:
    """Plantillas reutilizables para módulos comunes"""

    def __init__(self):
        self.templates = {
            'auth_module': {
                'name': 'auth_module',
                'type': 'backend',
                'description': 'Authentication and user management system',
                'dependencies': [],
                'agents_needed': ['backend'],
                'complexity': 4,
                'estimated_hours': 25,
                'tech_stack': ['JWT', 'bcrypt', 'passport'],
                'apis_needed': ['auth', 'users', 'sessions'],
                'database_entities': ['users', 'sessions', 'roles']
            },

            'payments_module': {
                'name': 'payments_module',
                'type': 'backend',
                'description': 'Payment processing with Stripe integration',
                'dependencies': ['auth_module'],
                'agents_needed': ['backend'],
                'complexity': 6,
                'estimated_hours': 30,
                'tech_stack': ['Stripe API', 'Webhooks'],
                'apis_needed': ['payments', 'subscriptions', 'invoices'],
                'database_entities': ['payments', 'subscriptions', 'customers']
            },

            'chat_module': {
                'name': 'chat_module',
                'type': 'fullstack',
                'description': 'Real-time chat system with WebSocket',
                'dependencies': ['auth_module'],
                'agents_needed': ['backend', 'frontend'],
                'complexity': 7,
                'estimated_hours': 35,
                'tech_stack': ['Socket.io', 'Redis'],
                'apis_needed': ['messages', 'conversations', 'notifications'],
                'database_entities': ['messages', 'conversations', 'participants']
            },

            'admin_dashboard': {
                'name': 'admin_dashboard',
                'type': 'frontend',
                'description': 'Administrative dashboard with analytics',
                'dependencies': ['auth_module'],
                'agents_needed': ['frontend'],
                'complexity': 5,
                'estimated_hours': 28,
                'tech_stack': ['React Admin', 'Charts.js'],
                'apis_needed': ['admin', 'analytics', 'reports'],
                'database_entities': []
            },

            'mobile_app': {
                'name': 'mobile_app',
                'type': 'mobile',
                'description': 'Mobile application for iOS and Android',
                'dependencies': ['core_backend'],
                'agents_needed': ['mobile'],
                'complexity': 8,
                'estimated_hours': 45,
                'tech_stack': ['React Native', 'Expo'],
                'apis_needed': ['mobile_auth', 'mobile_api'],
                'database_entities': []
            }
        }

    def get_module_template(self, template_name: str) -> ModuleSpec:
        """Obtener template de módulo por nombre"""

        if template_name not in self.templates:
            return None

        template = self.templates[template_name]

        return ModuleSpec(
            name=template['name'],
            type=template['type'],
            description=template['description'],
            dependencies=template['dependencies'],
            agents_needed=template['agents_needed'],
            complexity=template['complexity'],
            estimated_hours=template['estimated_hours'],
            tech_stack=template['tech_stack'],
            apis_needed=template['apis_needed'],
            database_entities=template['database_entities']
        )

    def list_available_templates(self) -> List[str]:
        """Listar templates disponibles"""
        return list(self.templates.keys())

    def create_custom_template(self, name: str, template_data: Dict[str, Any]):
        """Crear template personalizado"""
        # Fix the trailing comma and variables:
        self.templates[name] = template_data