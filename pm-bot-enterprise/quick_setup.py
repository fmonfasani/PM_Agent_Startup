#!/usr/bin/env python3
"""
quick_setup.py - Setup rápido del entorno PM Bot Enterprise
"""

import os
import sys
from pathlib import Path
import json

def create_core_init():
    """Crear __init__.py correcto para el módulo core"""
    
    core_dir = Path("core")
    if not core_dir.exists():
        print("❌ ERROR: Directorio 'core' no existe")
        return False
    
    init_file = core_dir / "__init__.py"
    
    init_content = '''# core/__init__.py
"""
PM Bot Enterprise - Core Module
Sistema de gestión de proyectos con IA
"""

__version__ = "1.0.0"

# Imports principales ordenados para evitar dependencias circulares
try:
    # Primero los módulos sin dependencias
    from .ai_interface import AIInterface
    
    # Luego los que dependen de ai_interface
    from .planner import ProjectPlanner, ModuleSpec
    
    # Después los módulos principales
    from .pm_bot import PMBotEnterprise, ProjectConfig, ProjectStatus, ProjectState
    from .module_manager import ModuleManager
    from .agent_spawner import AgentSpawner
    from .task_orchestrator import TaskOrchestrator
    
    # Finalmente los módulos de comunicación
    from .communication_manager import MCPCommunicationManager
    from .enhanced_agent import EnhancedAgent
    
    __all__ = [
        'AIInterface',
        'ProjectPlanner', 
        'ModuleSpec',
        'PMBotEnterprise',
        'ProjectConfig',
        'ProjectStatus', 
        'ProjectState',
        'ModuleManager',
        'AgentSpawner',
        'TaskOrchestrator',
        'MCPCommunicationManager',
        'EnhancedAgent'
    ]
    
    print("✅ Core module loaded successfully")
    
except ImportError as e:
    print(f"⚠️  Warning: Some core modules could not be imported: {e}")
    # Import solo los módulos que funcionan
    __all__ = []
    
    try:
        from .ai_interface import AIInterface
        __all__.append('AIInterface')
    except ImportError:
        pass
    
    try:
        from .planner import ProjectPlanner
        __all__.append('ProjectPlanner')
    except ImportError:
        pass
    
    try:
        from .pm_bot import PMBotEnterprise
        __all__.append('PMBotEnterprise')
    except ImportError:
        pass
'''
    
    try:
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(init_content)
        print(f"✅ Creado/actualizado {init_file}")
        return True
    except Exception as e:
        print(f"❌ Error creando {init_file}: {e}")
        return False

def create_necessary_directories():
    """Crear todos los directorios necesarios"""
    
    directories = [
        "data", "logs", "agents", "templates", 
        "prompts", "projects", "models", 
        "dashboard/templates", "dashboard/static"
    ]
    
    print("📁 Creando directorios necesarios...")
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ Creado: {directory}")
        else:
            print(f"   ✅ Existe: {directory}")
    
    return True

def create_empty_files():
    """Crear archivos vacíos necesarios"""
    
    empty_files = [
        "data/modules_status.json",
        "data/pm_state.log", 
        "logs/auth_backend.log",
        "logs/payments_ta.log",
        "models/ollama_models.json",
        "agents/auth_agents.json",
        "agents/cart_agents.json",
        "agents/profile_agents.json"
    ]
    
    print("📄 Creando archivos vacíos necesarios...")
    
    for file_path in empty_files:
        path = Path(file_path)
        if not path.exists():
            # Crear contenido básico según el tipo de archivo
            if file_path.endswith('.json'):
                content = '{}'
            else:
                content = ''
            
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"   ✅ Creado: {file_path}")
            except Exception as e:
                print(f"   ❌ Error creando {file_path}: {e}")
        else:
            print(f"   ✅ Existe: {file_path}")
    
    return True

def verify_requirements():
    """Verificar que requirements.txt existe y tiene contenido básico"""
    
    req_file = Path("requirements.txt")
    
    if not req_file.exists():
        print("📦 Creando requirements.txt básico...")
        
        basic_requirements = '''# PM Bot Enterprise - Dependencias básicas
aiohttp>=3.8.0
asyncio-mqtt>=0.11.0
python-dotenv>=0.19.0
pydantic>=1.9.0
fastapi>=0.68.0
uvicorn>=0.15.0
sqlalchemy>=1.4.0
psycopg2-binary>=2.9.0
redis>=4.0.0
anthropic>=0.3.0
openai>=1.0.0
requests>=2.28.0
flask>=2.2.0
flask-cors>=3.0.0
docker>=6.0.0
pyyaml>=6.0
jinja2>=3.1.0
click>=8.0.0
colorama>=0.4.0
rich>=12.0.0
'''
        
        try:
            with open(req_file, 'w', encoding='utf-8') as f:
                f.write(basic_requirements)
            print("✅ Creado requirements.txt")
        except Exception as e:
            print(f"❌ Error creando requirements.txt: {e}")
            return False
    else:
        print("✅ requirements.txt existe")
    
    return True

def create_basic_templates():
    """Crear templates básicos si no existen"""
    
    templates = {
        "templates/standard_module_trio.json": {
            "backend_agent": {
                "type": "backend",
                "model": "deepseek-r1:14b",
                "expertise": ["Node.js", "Express", "PostgreSQL", "REST APIs"]
            },
            "frontend_agent": {
                "type": "frontend", 
                "model": "claude-3-5-sonnet",
                "expertise": ["React", "TypeScript", "Tailwind CSS", "Next.js"]
            },
            "qa_agent": {
                "type": "qa",
                "model": "claude-3-5-sonnet",
                "expertise": ["Jest", "Cypress", "API Testing", "E2E Testing"]
            }
        },
        
        "templates/qa_agent.json": {
            "name": "qa_specialist",
            "type": "qa",
            "model": "claude-3-5-sonnet",
            "expertise": ["Test Automation", "Quality Assurance", "Bug Detection"],
            "responsibilities": ["Unit Tests", "Integration Tests", "E2E Tests", "Performance Tests"]
        },
        
        "templates/deploy_agent.json": {
            "name": "devops_specialist",
            "type": "devops",
            "model": "qwen2.5-coder:7b",
            "expertise": ["Docker", "Kubernetes", "CI/CD", "AWS", "Terraform"],
            "responsibilities": ["Deployment", "Infrastructure", "Monitoring", "Security"]
        }
    }
    
    print("📋 Creando templates básicos...")
    
    for file_path, content in templates.items():
        path = Path(file_path)
        if not path.exists():
            try:
                import json
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(content, f, indent=2)
                print(f"   ✅ Creado: {file_path}")
            except Exception as e:
                print(f"   ❌ Error creando {file_path}: {e}")
        else:
            print(f"   ✅ Existe: {file_path}")
    
    return True

def create_example_prompts():
    """Crear prompts de ejemplo"""
    
    prompts = {
        "prompts/startup_example_1.txt": """Crear una plataforma SaaS de gestión de proyectos con:

- Dashboard con analytics en tiempo real
- Sistema de equipos y colaboración
- API REST completa con autenticación JWT
- Notificaciones push y email
- Facturación con Stripe
- Aplicación móvil iOS/Android
- Panel de administración
- Reportes y exportación de datos

Tecnologías preferidas: React, Node.js, PostgreSQL
Timeline: 3 meses
Equipo: 8 desarrolladores""",

        "prompts/marketplace_prompt.txt": """Marketplace de productos digitales con:

- Catálogo de productos con búsqueda avanzada
- Sistema de vendedores con dashboard
- Pagos con Stripe y PayPal
- Chat en tiempo real entre compradores y vendedores
- Sistema de reviews y ratings
- App móvil para compradores
- Panel de administración
- Analytics para vendedores
- Sistema de comisiones automático

Debe soportar miles de usuarios concurrentes.
Compliance: PCI DSS, GDPR
Budget: Enterprise
Timeline: 6 meses"""
    }
    
    print("📝 Creando prompts de ejemplo...")
    
    for file_path, content in prompts.items():
        path = Path(file_path)
        if not path.exists():
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"   ✅ Creado: {file_path}")
            except Exception as e:
                print(f"   ❌ Error creando {file_path}: {e}")
        else:
            print(f"   ✅ Existe: {file_path}")
    
    return True

def main():
    """Setup principal"""
    
    print("=" * 60)
    print("🚀 PM BOT ENTERPRISE - QUICK SETUP")
    print("=" * 60)
    
    current_dir = Path.cwd()
    print(f"📁 Directorio actual: {current_dir}")
    
    # Verificar que estamos en el directorio correcto
    if not (current_dir / "core").exists():
        print("❌ ERROR: No se encuentra el directorio 'core'")
        print("   Asegúrate de estar en el directorio raíz del proyecto PM Bot Enterprise")
        return False
    
    steps = [
        ("Creando core/__init__.py", create_core_init),
        ("Creando directorios", create_necessary_directories),
        ("Creando archivos vacíos", create_empty_files),
        ("Verificando requirements.txt", verify_requirements),
        ("Creando templates básicos", create_basic_templates),
        ("Creando prompts de ejemplo", create_example_prompts)
    ]
    
    success_count = 0
    
    for step_name, step_func in steps:
        print(f"\n🔧 {step_name}...")
        try:
            if step_func():
                print(f"✅ {step_name} - Completado")
                success_count += 1
            else:
                print(f"❌ {step_name} - Falló")
        except Exception as e:
            print(f"❌ {step_name} - Error: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 SETUP COMPLETADO: {success_count}/{len(steps)} pasos exitosos")
    
    if success_count == len(steps):
        print("🎉 ¡SETUP COMPLETO!")
        print("\n💡 Próximos pasos:")
        print("1. Ejecuta: python test_fix_updated.py")
        print("2. Si los tests pasan, ejecuta: python run_pm.py --help")
        print("3. Crea tu primer proyecto: python run_pm.py --prompt 'Blog con React' --auto")
    elif success_count >= len(steps) // 2:
        print("⚠️  Setup parcialmente completado")
        print("💡 Puedes intentar ejecutar: python test_fix_updated.py")
    else:
        print("❌ Setup falló")
        print("🔧 Revisa los errores arriba")
    
    print("=" * 60)
    
    return success_count >= len(steps) // 2

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)