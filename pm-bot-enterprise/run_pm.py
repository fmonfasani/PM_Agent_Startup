#!/usr/bin/env python3
"""
run_pm.py - Script principal para iniciar el PM Bot Enterprise
"""

import asyncio
import argparse
import sys
import os
import json
from pathlib import Path

# Agregar el directorio actual al path para imports
sys.path.append(str(Path(__file__).parent))

from core.pm_bot import PMBotEnterprise


def setup_environment():
    """Configurar entorno y verificar dependencias"""
    
    print("🔧 Configurando entorno PM Bot Enterprise...")
    
    # Crear directorios necesarios
    directories = [
        "data", "logs", "agents", "templates", 
        "prompts", "models", "dashboard", "projects"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"📁 Directorio creado/verificado: {directory}")
    
    # Verificar archivo .env
    if not os.path.exists('.env'):
        create_env_template()
    
    print("✅ Entorno configurado correctamente")


def create_env_template():
    """Crear template de archivo .env"""
    
    env_template = """# PM Bot Enterprise - Configuración de Variables de Entorno

# ============ Modelos AI Locales (Ollama) ============
OLLAMA_HOST=http://localhost:11434
DEEPSEEK_MODEL=deepseek-r1:14b
LLAMA_MODEL=llama3.2:latest
QWEN_MODEL=qwen2.5-coder:7b

# ============ APIs Cloud (Opcional - Fallbacks) ============
# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# OpenAI GPT
OPENAI_API_KEY=sk-proj-your-key-here

# Google Gemini
GOOGLE_API_KEY=your-google-ai-key

# xAI Grok
XAI_API_KEY=your-xai-key

# ============ Integración de Herramientas ============
# GitHub
GITHUB_TOKEN=ghp_your-github-token

# Slack (para notificaciones)
SLACK_BOT_TOKEN=xoxb-your-slack-token

# Brave Search (para web search)
BRAVE_API_KEY=your-brave-search-key

# ============ Base de Datos ============
DATABASE_URL=postgresql://user:pass@localhost:5432/pm_bot_enterprise

# ============ Cloud Services (Opcional) ============
# AWS
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1

# Azure
AZURE_SUBSCRIPTION_ID=your-azure-subscription-id
AZURE_CLIENT_ID=your-azure-client-id
AZURE_CLIENT_SECRET=your-azure-client-secret

# ============ Configuración del Sistema ============
MAX_CONCURRENT_PROJECTS=5
DEFAULT_TEAM_SIZE=6
TASK_TIMEOUT_HOURS=2
LOG_LEVEL=INFO
"""
    
    with open('.env', 'w') as f:
        f.write(env_template)
    
    print("📄 Archivo .env creado con configuraciones por defecto")
    print("⚠️  IMPORTANTE: Edita .env con tus API keys antes de ejecutar")


def load_example_prompts():
    """Cargar prompts de ejemplo"""
    
    examples = {
        "startup_saas": """
Crear plataforma SaaS de gestión de proyectos con:
- Autenticación de usuarios y equipos
- Dashboard con analytics en tiempo real  
- Sistema de tareas con asignaciones
- Notificaciones push y email
- API REST completa
- Panel de administración
- Facturación con Stripe
- Aplicación móvil (React Native)

Tecnologías preferidas: Node.js, React, PostgreSQL, Redis
Timeline: 3 meses
Presupuesto: Startup ($50k)
Compliance: GDPR
""",
        
        "ecommerce_marketplace": """
Desarrollar marketplace de productos artesanales con:
- Catálogo de productos con búsqueda avanzada
- Sistema de vendedores independientes
- Carrito de compras y checkout
- Pagos con Stripe y PayPal
- Reviews y calificaciones
- Chat en tiempo real entre compradores/vendedores
- Sistema de envíos
- Panel de analytics para vendedores
- App móvil iOS/Android

Tecnologías: MERN Stack (MongoDB, Express, React, Node.js)
Timeline: 6 meses
Presupuesto: Enterprise ($200k)
Compliance: PCI DSS
""",
        
        "fintech_app": """
Aplicación fintech para gestión de inversiones con:
- Dashboard de portfolio en tiempo real
- Integración con APIs de mercados financieros
- Sistema de alertas y notificaciones
- Análisis de riesgo automatizado
- Reportes y analytics avanzados
- KYC/AML compliance
- Autenticación biométrica
- Trading automatizado
- App móvil nativa

Tecnologías: Python/FastAPI backend, React frontend, PostgreSQL
Timeline: 8 meses  
Presupuesto: Enterprise ($500k)
Compliance: SOX, GDPR, regulatory compliance
""",
        
        "simple_blog": """
Blog personal con CMS simple:
- Sistema de posts con markdown
- Comentarios básicos
- Categorías y tags
- Panel de administración
- SEO optimizado
- Responsive design

Tecnologías: Next.js, Tailwind CSS
Timeline: 1 mes
Presupuesto: Básico ($5k)
"""
    }
    
    # Crear archivos de ejemplo
    for name, content in examples.items():
        prompt_file = f"prompts/{name}.txt"
        with open(prompt_file, 'w') as f:
            f.write(content.strip())
    
    print(f"📝 {len(examples)} prompts de ejemplo creados en /prompts/")


async def interactive_mode():
    """Modo interactivo para crear proyectos"""
    
    print("\n🎯 PM Bot Enterprise - Modo Interactivo")
    print("=" * 50)
    
    pm_bot = PMBotEnterprise()
    
    while True:
        print("\n🤖 ¿Qué quieres crear hoy?")
        print("1. 📝 Describir proyecto personalizado")
        print("2. 📋 Usar prompt de ejemplo")
        print("3. 📊 Ver proyectos activos")
        print("4. 📈 Ver métricas del sistema")
        print("5. 🛑 Salir")
        
        choice = input("\nSelecciona una opción (1-5): ").strip()
        
        try:
            if choice == "1":
                await handle_custom_project(pm_bot)
            elif choice == "2":
                await handle_example_project(pm_bot)
            elif choice == "3":
                await show_active_projects(pm_bot)
            elif choice == "4":
                show_system_metrics(pm_bot)
            elif choice == "5":
                print("👋 ¡Hasta luego!")
                break
            else:
                print("❌ Opción inválida. Por favor selecciona 1-5.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Interrumpido por el usuario. ¡Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


async def handle_custom_project(pm_bot):
    """Manejar creación de proyecto personalizado"""
    
    print("\n📝 Describe tu proyecto en detalle:")
    print("💡 Incluye funcionalidades, tecnologías preferidas, timeline, etc.")
    print("(Escribe 'cancelar' para volver al menú)")
    
    description = input("\n🎯 Descripción del proyecto: ").strip()
    
    if description.lower() == 'cancelar':
        return
    
    if len(description) < 10:
        print("❌ Descripción muy corta. Proporciona más detalles.")
        return
    
    # Parámetros opcionales
    print("\n⚙️ Configuración adicional (opcional, presiona Enter para omitir):")
    
    timeline = input("⏱️ Timeline deseado (ej: 3 months): ").strip()
    budget = input("💰 Presupuesto (startup/medium/enterprise): ").strip()
    team_size = input("👥 Tamaño de equipo preferido (número): ").strip()
    
    # Crear kwargs
    kwargs = {}
    if timeline:
        kwargs['timeline'] = timeline
    if budget:
        kwargs['budget'] = budget
    if team_size and team_size.isdigit():
        kwargs['team_size'] = int(team_size)
    
    print(f"\n🚀 Creando proyecto: {description[:50]}...")
    
    try:
        # Crear proyecto
        project_id = await pm_bot.create_project(description, **kwargs)
        print(f"✅ Proyecto creado: {project_id}")
        
        # Preguntar si ejecutar inmediatamente
        execute = input("\n▶️ ¿Ejecutar proyecto ahora? (s/N): ").strip().lower()
        
        if execute in ['s', 'si', 'sí', 'y', 'yes']:
            print("🔥 Ejecutando proyecto...")
            success = await pm_bot.execute_project(project_id)
            
            if success:
                print("🎉 ¡Proyecto completado exitosamente!")
                
                # Mostrar resumen
                status = await pm_bot.get_project_status(project_id)
                print(f"📊 Progreso: {status['progress']:.1f}%")
                print(f"📁 Ubicación: {pm_bot.projectConfig.workingDir}")
            else:
                print("❌ El proyecto falló durante la ejecución")
        else:
            print("📋 Proyecto creado y listo para ejecutar")
            
    except Exception as e:
        print(f"❌ Error creando/ejecutando proyecto: {e}")


async def handle_example_project(pm_bot):
    """Manejar selección de proyecto de ejemplo"""
    
    # Listar prompts disponibles
    prompts_dir = Path("prompts")
    prompt_files = list(prompts_dir.glob("*.txt"))
    
    if not prompt_files:
        print("❌ No hay prompts de ejemplo disponibles")
        print("💡 Ejecuta con --setup para crear ejemplos")
        return
    
    print("\n📋 Prompts de ejemplo disponibles:")
    for i, prompt_file in enumerate(prompt_files, 1):
        name = prompt_file.stem.replace('_', ' ').title()
        print(f"{i}. {name}")
    
    try:
        choice = int(input(f"\nSelecciona un prompt (1-{len(prompt_files)}): ")) - 1
        
        if 0 <= choice < len(prompt_files):
            selected_file = prompt_files[choice]
            
            with open(selected_file, 'r') as f:
                description = f.read().strip()
            
            print(f"\n📝 Proyecto seleccionado: {selected_file.stem}")
            print(f"📋 Descripción:\n{description[:200]}...")
            
            confirm = input("\n🚀 ¿Crear este proyecto? (S/n): ").strip().lower()
            
            if confirm in ['', 's', 'si', 'sí', 'y', 'yes']:
                project_id = await pm_bot.create_project(description)
                print(f"✅ Proyecto creado: {project_id}")
                
                # Auto-ejecutar ejemplos
                print("🔥 Ejecutando proyecto automáticamente...")
                success = await pm_bot.execute_project(project_id)
                
                if success:
                    print("🎉 ¡Proyecto de ejemplo completado!")
                else:
                    print("❌ El proyecto falló")
            else:
                print("❌ Creación cancelada")
        else:
            print("❌ Selección inválida")
            
    except ValueError:
        print("❌ Por favor ingresa un número válido")


async def show_active_projects(pm_bot):
    """Mostrar proyectos activos"""
    
    projects = await pm_bot.list_projects()
    
    if not projects:
        print("📋 No hay proyectos activos")
        return
    
    print(f"\n📊 Proyectos Activos ({len(projects)}):")
    print("-" * 80)
    
    for project in projects:
        status_icon = {
            'planning': '📋',
            'in_progress': '🔥', 
            'completed': '✅',
            'failed': '❌',
            'paused': '⏸️'
        }.get(project['status'], '❓')
        
        print(f"{status_icon} {project['name']}")
        print(f"   ID: {project['id']}")
        print(f"   Estado: {project['status']}")
        print(f"   Progreso: {project['progress']:.1f}%")
        print(f"   Módulos: {project['modules_count']}")
        print(f"   Agentes: {project['agents_count']}")
        print(f"   Inicio: {project['start_time']}")
        print()


def show_system_metrics(pm_bot):
    """Mostrar métricas del sistema"""
    
    metrics = pm_bot.get_system_metrics()
    
    print("\n📈 Métricas del Sistema:")
    print("-" * 40)
    print(f"🎯 Proyectos creados: {metrics['projects_created']}")
    print(f"✅ Proyectos completados: {metrics['projects_completed']}")
    print(f"🤖 Agentes generados: {metrics['agents_spawned']}")
    print(f"📦 Módulos generados: {metrics['modules_generated']}")
    print(f"📊 Tasa de éxito: {metrics['success_rate']:.1f}%")
    print(f"⏱️ Tiempo promedio: {metrics['average_completion_time']:.1f}s")
    print(f"🔥 Proyectos activos: {metrics['active_projects']}")
    print(f"💾 Uso de memoria: {metrics['memory_usage']['rss']:.1f} MB")


async def batch_mode(prompt_file: str, auto_execute: bool = False):
    """Modo batch para ejecutar desde archivo"""
    
    if not os.path.exists(prompt_file):
        print(f"❌ Archivo no encontrado: {prompt_file}")
        return
    
    with open(prompt_file, 'r') as f:
        description = f.read().strip()
    
    print(f"📝 Ejecutando proyecto desde: {prompt_file}")
    print(f"📋 Descripción: {description[:100]}...")
    
    pm_bot = PMBotEnterprise()
    
    try:
        # Crear proyecto
        project_id = await pm_bot.create_project(description)
        print(f"✅ Proyecto creado: {project_id}")
        
        if auto_execute:
            print("🔥 Ejecutando proyecto...")
            success = await pm_bot.execute_project(project_id)
            
            if success:
                print("🎉 ¡Proyecto completado exitosamente!")
                
                # Mostrar métricas finales
                status = await pm_bot.get_project_status(project_id)
                print(f"📊 Progreso final: {status['progress']:.1f}%")
                
                return True
            else:
                print("❌ El proyecto falló durante la ejecución")
                return False
        else:
            print("📋 Proyecto creado (no ejecutado)")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Función principal"""
    
    parser = argparse.ArgumentParser(
        description="PM Bot Enterprise - Sistema de Gest