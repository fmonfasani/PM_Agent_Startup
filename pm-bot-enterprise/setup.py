#!/usr/bin/env python3
"""
Setup script para PM Bot Enterprise
"""

from setuptools import setup, find_packages
from pathlib import Path
import os

# Leer README para descripción larga
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8') if (this_directory / "README.md").exists() else ""

# Leer requirements
def read_requirements(filename):
    """Leer archivo de requirements y retornar lista de dependencias"""
    req_file = this_directory / filename
    if req_file.exists():
        with open(req_file, 'r', encoding='utf-8') as f:
            return [
                line.strip() 
                for line in f 
                if line.strip() 
                and not line.startswith('#') 
                and not line.startswith('-')
                and '://' not in line  # Excluir URLs de git
            ]
    return []

# Dependencias principales
install_requires = read_requirements('requirements.txt')

# Dependencias de desarrollo
dev_requires = [
    'pytest>=7.4.0',
    'pytest-asyncio>=0.21.0',
    'pytest-mock>=3.11.0',
    'pytest-cov>=4.1.0',
    'black>=23.9.0',
    'isort>=5.12.0',
    'flake8>=6.1.0',
    'mypy>=1.6.0',
    'pre-commit>=3.5.0'
]

# Dependencias opcionales por categoría
extras_require = {
    'dev': dev_requires,
    'dashboard': [
        'flask>=3.0.0',
        'flask-cors>=4.0.0'
    ],
    'cloud': [
        'boto3>=1.29.0',
        'azure-storage-blob>=12.18.0',
        'google-cloud-storage>=2.10.0'
    ],
    'ai-cloud': [
        'anthropic>=0.35.0',
        'openai>=1.40.0',
        'google-generativeai>=0.8.0'
    ],
    'monitoring': [
        'prometheus-client>=0.17.0',
        'sentry-sdk>=1.38.0'
    ],
    'ml': [
        'numpy>=1.24.0',
        'pandas>=2.1.0',
        'scikit-learn>=1.3.0'
    ],
    'all': dev_requires + [
        'flask>=3.0.0',
        'flask-cors>=4.0.0',
        'boto3>=1.29.0',
        'anthropic>=0.35.0',
        'openai>=1.40.0'
    ]
}

# Leer versión desde archivo
def get_version():
    """Obtener versión desde core/__init__.py"""
    version_file = this_directory / "core" / "__init__.py"
    if version_file.exists():
        with open(version_file, 'r') as f:
            for line in f:
                if line.startswith('__version__'):
                    return line.split('=')[1].strip().strip('"\'')
    return "1.0.0"

setup(
    name="pm-bot-enterprise",
    version=get_version(),
    author="PM Bot Enterprise Team",
    author_email="team@pm-bot-enterprise.com",
    description="Sistema de Gestión de Proyectos con Agentes IA Multi-Especializados",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pm-bot-enterprise/pm-bot-enterprise",
    project_urls={
        "Bug Tracker": "https://github.com/pm-bot-enterprise/pm-bot-enterprise/issues",
        "Documentation": "https://docs.pm-bot-enterprise.com",
        "Source Code": "https://github.com/pm-bot-enterprise/pm-bot-enterprise",
    },
    
    # Paquetes
    packages=find_packages(exclude=['tests*', 'docs*']),
    include_package_data=True,
    
    # Archivos de datos
    package_data={
        'pm_bot_enterprise': [
            'templates/*.json',
            'prompts/*.txt',
            'config/*.json',
            'dashboard/templates/*.html',
            'dashboard/static/*'
        ]
    },
    
    # Scripts ejecutables
    entry_points={
        'console_scripts': [
            'pm-bot=run_pm:main',
            'pm-bot-dashboard=dashboard.app:main',
        ],
    },
    
    # Dependencias
    install_requires=install_requires,
    extras_require=extras_require,
    
    # Metadatos
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Project Management",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    
    # Requisitos de Python
    python_requires=">=3.9",
    
    # Keywords para búsqueda
    keywords=[
        "project-management", "ai", "automation", "agents", 
        "development", "software", "enterprise", "saas"
    ],
    
    # Configuración adicional
    zip_safe=False,
    
    # Test suite
    test_suite='tests',
    tests_require=dev_requires,
    
    # Configuración de build
    options={
        'build_scripts': {
            'executable': '/usr/bin/env python3',
        },
    },
)