# core/ai_interface.py
"""
Interface para comunicación con modelos de IA (local y cloud)
"""

import asyncio
import aiohttp
import json
import os
from typing import Dict, Any, Optional, List
import logging


class AIInterface:
    """Interface unificada para modelos de IA locales y cloud"""
    
    def __init__(self):
        self.logger = logging.getLogger('AIInterface')
        self.ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        self.preferred_model = os.getenv('DEEPSEEK_MODEL', 'deepseek-r1:14b')
        
        # Configuración de modelos disponibles
        self.local_models = [
            'deepseek-r1:14b', 'deepseek-r1:7b',
            'qwen2.5-coder:7b', 'llama3.2:latest'
        ]
        
        # Fallbacks cloud (si están configurados)
        self.cloud_fallbacks = []
        if os.getenv('ANTHROPIC_API_KEY'):
            self.cloud_fallbacks.append('claude')
        if os.getenv('OPENAI_API_KEY'):
            self.cloud_fallbacks.append('gpt')
        
    async def generate_response(self, prompt: str, max_tokens: int = 1000, 
                              temperature: float = 0.3, model: str = None) -> str:
        """Generar respuesta usando el mejor modelo disponible"""
        
        selected_model = model or self.preferred_model
        
        try:
            # Intentar primero con modelo local
            return await self._generate_local(prompt, selected_model, max_tokens, temperature)
            
        except Exception as e:
            self.logger.warning(f"Local model {selected_model} failed: {e}")
            
            # Intentar con otros modelos locales
            for fallback_model in self.local_models:
                if fallback_model != selected_model:
                    try:
                        return await self._generate_local(prompt, fallback_model, max_tokens, temperature)
                    except Exception:
                        continue
            
            # Como último recurso, usar cloud si está disponible
            if self.cloud_fallbacks:
                self.logger.info("Falling back to cloud model")
                return await self._generate_cloud(prompt, max_tokens, temperature)
            
            raise Exception("No AI models available")
    
    async def _generate_local(self, prompt: str, model: str, max_tokens: int, temperature: float) -> str:
        """Generar respuesta usando Ollama local"""
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "top_p": 0.9
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.ollama_host}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                
                if response.status != 200:
                    raise Exception(f"Ollama API error: {response.status}")
                
                result = await response.json()
                return result.get('response', '').strip()
    
    async def _generate_cloud(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generar respuesta usando API cloud como fallback"""
        
        if 'claude' in self.cloud_fallbacks:
            return await self._generate_claude(prompt, max_tokens, temperature)
        elif 'gpt' in self.cloud_fallbacks:
            return await self._generate_openai(prompt, max_tokens, temperature)
        else:
            raise Exception("No cloud fallbacks configured")
    
    async def _generate_claude(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generar usando Claude API"""
        try:
            from anthropic import AsyncAnthropic
            
            client = AsyncAnthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
            
            response = await client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            raise Exception(f"Claude API error: {e}")
    
    async def _generate_openai(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generar usando OpenAI API"""
        try:
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            response = await client.chat.completions.create(
                model="gpt-4o",
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"OpenAI API error: {e}")
    
    async def get_available_models(self) -> List[str]:
        """Obtener lista de modelos disponibles"""
        available = []
        
        # Verificar modelos locales
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_host}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        local_models = [model['name'] for model in data.get('models', [])]
                        available.extend(local_models)
        except Exception:
            pass
        
        # Agregar modelos cloud si están configurados
        available.extend(self.cloud_fallbacks)
        
        return available
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificar estado de los modelos AI"""
        status = {
            "local": {"available": False, "models": []},
            "cloud": {"available": False, "services": []}
        }
        
        # Verificar Ollama local
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.ollama_host}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        status["local"]["available"] = True
                        status["local"]["models"] = [m['name'] for m in data.get('models', [])]
        except Exception as e:
            status["local"]["error"] = str(e)
        
        # Verificar servicios cloud
        status["cloud"]["services"] = self.cloud_fallbacks
        status["cloud"]["available"] = len(self.cloud_fallbacks) > 0
        
        return status


# core/module_templates.py
"""
Templates para diferentes tipos de módulos
"""

from typing import Dict, Any
from .planner import ModuleSpec


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
        self.templates[name] = template_data