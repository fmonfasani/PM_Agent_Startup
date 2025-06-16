# dashboard/app.py
"""
PM Bot Enterprise Dashboard - Web Interface
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path

# Agregar path del core
sys.path.append(str(Path(__file__).parent.parent))

from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_cors import CORS
import threading
import queue

from core.pm_bot import PMBotEnterprise, ProjectStatus
from core.ai_interface import AIInterface


class DashboardApp:
    """Dashboard web para PM Bot Enterprise"""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = 'pm-bot-enterprise-secret-key-change-in-production'
        
        # Configurar CORS para API calls
        CORS(self.app)
        
        # Inicializar PM Bot
        self.pm_bot = PMBotEnterprise()
        self.ai_interface = AIInterface()
        
        # Cola para comunicación async/sync
        self.request_queue = queue.Queue()
        self.response_queue = queue.Queue()
        
        # Configurar rutas
        self._setup_routes()
        
        # Iniciar worker thread para operaciones async
        self.worker_thread = threading.Thread(target=self._async_worker, daemon=True)
        self.worker_thread.start()
    
    def _setup_routes(self):
        """Configurar todas las rutas del dashboard"""
        
        # === PÁGINAS PRINCIPALES ===
        
        @self.app.route('/')
        def dashboard():
            """Dashboard principal"""
            try:
                # Obtener proyectos recientes
                projects = self._sync_call(self.pm_bot.list_projects)
                
                # Obtener métricas del sistema
                metrics = self.pm_bot.get_system_metrics()
                
                # Verificar estado de AI
                ai_status = self._sync_call(self.ai_interface.health_check)
                
                return render_template('dashboard.html', 
                                     projects=projects[:5],  # Solo los 5 más recientes
                                     metrics=metrics,
                                     ai_status=ai_status)
            except Exception as e:
                flash(f'Error loading dashboard: {str(e)}', 'error')
                return render_template('dashboard.html', 
                                     projects=[], 
                                     metrics={}, 
                                     ai_status={})
        
        @self.app.route('/projects')
        def projects_list():
            """Lista de todos los proyectos"""
            try:
                projects = self._sync_call(self.pm_bot.list_projects)
                return render_template('projects.html', projects=projects)
            except Exception as e:
                flash(f'Error loading projects: {str(e)}', 'error')
                return render_template('projects.html', projects=[])
        
        @self.app.route('/project/<project_id>')
        def project_detail(project_id):
            """Detalle de un proyecto específico"""
            try:
                status = self._sync_call(self.pm_bot.get_project_status, project_id)
                return render_template('project_detail.html', project=status)
            except Exception as e:
                flash(f'Error loading project: {str(e)}', 'error')
                return redirect(url_for('projects_list'))
        
        @self.app.route('/create-project')
        def create_project_form():
            """Formulario para crear nuevo proyecto"""
            return render_template('create_project.html')
        
        @self.app.route('/agents')
        def agents_dashboard():
            """Dashboard de agentes"""
            try:
                agents = self.pm_bot.agent_spawner.get_all_agents()
                utilization = self._sync_call(self.pm_bot.agent_spawner.get_agent_utilization)
                
                return render_template('agents.html', 
                                     agents=agents, 
                                     utilization=utilization)
            except Exception as e:
                flash(f'Error loading agents: {str(e)}', 'error')
                return render_template('agents.html', agents={}, utilization={})
        
        @self.app.route('/system')
        def system_status():
            """Estado del sistema"""
            try:
                metrics = self.pm_bot.get_system_metrics()
                ai_status = self._sync_call(self.ai_interface.health_check)
                available_models = self._sync_call(self.ai_interface.get_available_models)
                
                return render_template('system.html', 
                                     metrics=metrics,
                                     ai_status=ai_status,
                                     available_models=available_models)
            except Exception as e:
                flash(f'Error loading system status: {str(e)}', 'error')
                return render_template('system.html', 
                                     metrics={}, 
                                     ai_status={}, 
                                     available_models=[])
        
        # === API ENDPOINTS ===
        
        @self.app.route('/api/projects', methods=['GET'])
        def api_projects():
            """API: Listar proyectos"""
            try:
                projects = self._sync_call(self.pm_bot.list_projects)
                return jsonify({"success": True, "projects": projects})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
        
        @self.app.route('/api/projects', methods=['POST'])
        def api_create_project():
            """API: Crear nuevo proyecto"""
            try:
                data = request.get_json()
                
                if not data or 'description' not in data:
                    return jsonify({"success": False, "error": "Description required"}), 400
                
                description = data['description']
                kwargs = {k: v for k, v in data.items() if k != 'description'}
                
                project_id = self._sync_call(self.pm_bot.create_project, description, **kwargs)
                
                return jsonify({
                    "success": True, 
                    "project_id": project_id,
                    "message": f"Project {project_id} created successfully"
                })
                
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
        
        @self.app.route('/api/projects/<project_id>/execute', methods=['POST'])
        def api_execute_project(project_id):
            """API: Ejecutar proyecto"""
            try:
                success = self._sync_call(self.pm_bot.execute_project, project_id)
                
                if success:
                    return jsonify({
                        "success": True, 
                        "message": f"Project {project_id} execution started"
                    })
                else:
                    return jsonify({
                        "success": False, 
                        "error": "Project execution failed"
                    }), 500
                    
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
        
        @self.app.route('/api/projects/<project_id>/status', methods=['GET'])
        def api_project_status(project_id):
            """API: Estado del proyecto"""
            try:
                status = self._sync_call(self.pm_bot.get_project_status, project_id)
                return jsonify({"success": True, "status": status})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
        
        @self.app.route('/api/projects/<project_id>/pause', methods=['POST'])
        def api_pause_project(project_id):
            """API: Pausar proyecto"""
            try:
                success = self._sync_call(self.pm_bot.pause_project, project_id)
                return jsonify({
                    "success": success,
                    "message": f"Project {project_id} {'paused' if success else 'could not be paused'}"
                })
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
        
        @self.app.route('/api/projects/<project_id>/resume', methods=['POST'])
        def api_resume_project(project_id):
            """API: Reanudar proyecto"""
            try:
                success = self._sync_call(self.pm_bot.resume_project, project_id)
                return jsonify({
                    "success": success,
                    "message": f"Project {project_id} {'resumed' if success else 'could not be resumed'}"
                })
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
        
        @self.app.route('/api/agents', methods=['GET'])
        def api_agents():
            """API: Listar agentes"""
            try:
                agents = self.pm_bot.agent_spawner.get_all_agents()
                utilization = self._sync_call(self.pm_bot.agent_spawner.get_agent_utilization)
                
                # Convertir AgentConfig a dict
                agents_dict = {}
                for agent_id, agent_config in agents.items():
                    agents_dict[agent_id] = {
                        "id": agent_config.id,
                        "name": agent_config.name,
                        "role": agent_config.role,
                        "specialization": agent_config.specialization,
                        "status": agent_config.status,
                        "model": agent_config.model,
                        "expertise": agent_config.expertise,
                        "tools": agent_config.tools
                    }
                
                return jsonify({
                    "success": True, 
                    "agents": agents_dict,
                    "utilization": utilization
                })
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
        
        @self.app.route('/api/agents/<agent_id>/status', methods=['GET'])
        def api_agent_status(agent_id):
            """API: Estado de un agente específico"""
            try:
                status = self._sync_call(self.pm_bot.agent_spawner.get_agent_status, agent_id)
                return jsonify({"success": True, "status": status})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
        
        @self.app.route('/api/system/metrics', methods=['GET'])
        def api_system_metrics():
            """API: Métricas del sistema"""
            try:
                metrics = self.pm_bot.get_system_metrics()
                return jsonify({"success": True, "metrics": metrics})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
        
        @self.app.route('/api/system/health', methods=['GET'])
        def api_system_health():
            """API: Salud del sistema"""
            try:
                ai_status = self._sync_call(self.ai_interface.health_check)
                available_models = self._sync_call(self.ai_interface.get_available_models)
                
                health = {
                    "ai_status": ai_status,
                    "available_models": available_models,
                    "timestamp": datetime.now().isoformat()
                }
                
                return jsonify({"success": True, "health": health})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
        
        # === FORM HANDLERS ===
        
        @self.app.route('/create-project', methods=['POST'])
        def handle_create_project():
            """Manejar formulario de creación de proyecto"""
            try:
                description = request.form.get('description')
                timeline = request.form.get('timeline')
                budget = request.form.get('budget')
                team_size = request.form.get('team_size')
                
                if not description:
                    flash('Project description is required', 'error')
                    return redirect(url_for('create_project_form'))
                
                kwargs = {}
                if timeline:
                    kwargs['timeline'] = timeline
                if budget:
                    kwargs['budget'] = budget
                if team_size and team_size.isdigit():
                    kwargs['team_size'] = int(team_size)
                
                project_id = self._sync_call(self.pm_bot.create_project, description, **kwargs)
                
                flash(f'Project {project_id} created successfully!', 'success')
                
                # Preguntar si ejecutar automáticamente
                auto_execute = request.form.get('auto_execute')
                if auto_execute:
                    try:
                        success = self._sync_call(self.pm_bot.execute_project, project_id)
                        if success:
                            flash(f'Project {project_id} execution started!', 'info')
                        else:
                            flash(f'Project created but execution failed', 'warning')
                    except Exception as e:
                        flash(f'Project created but execution error: {str(e)}', 'warning')
                
                return redirect(url_for('project_detail', project_id=project_id))
                
            except Exception as e:
                flash(f'Error creating project: {str(e)}', 'error')
                return redirect(url_for('create_project_form'))
        
        # === WEBSOCKET ENDPOINTS (para tiempo real) ===
        
        @self.app.route('/api/projects/<project_id>/logs')
        def api_project_logs(project_id):
            """API: Logs del proyecto (polling)"""
            try:
                # En una implementación real, leerías logs desde archivos
                logs = []
                log_file = f"logs/project_{project_id}.log"
                
                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        logs = f.readlines()[-50:]  # Últimas 50 líneas
                
                return jsonify({
                    "success": True, 
                    "logs": [line.strip() for line in logs]
                })
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
        
        # === ERROR HANDLERS ===
        
        @self.app.errorhandler(404)
        def not_found(error):
            return render_template('error.html', 
                                 error_code=404, 
                                 error_message="Page not found"), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            return render_template('error.html', 
                                 error_code=500, 
                                 error_message="Internal server error"), 500
    
    def _async_worker(self):
        """Worker thread para operaciones asíncronas"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        while True:
            try:
                # Obtener tarea de la cola
                task = self.request_queue.get(timeout=1)
                
                if task is None:  # Señal de shutdown
                    break
                
                func, args, kwargs, response_id = task
                
                try:
                    # Ejecutar función async
                    if asyncio.iscoroutinefunction(func):
                        result = loop.run_until_complete(func(*args, **kwargs))
                    else:
                        result = func(*args, **kwargs)
                    
                    # Devolver resultado
                    self.response_queue.put((response_id, result, None))
                    
                except Exception as e:
                    # Devolver error
                    self.response_queue.put((response_id, None, e))
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Worker error: {e}")
    
    def _sync_call(self, func, *args, **kwargs):
        """Ejecutar función async de manera síncrona"""
        import uuid
        response_id = str(uuid.uuid4())
        
        # Agregar tarea a la cola
        self.request_queue.put((func, args, kwargs, response_id))
        
        # Esperar respuesta
        while True:
            try:
                resp_id, result, error = self.response_queue.get(timeout=30)
                if resp_id == response_id:
                    if error:
                        raise error
                    return result
            except queue.Empty:
                raise TimeoutError("Operation timed out")
    
    def create_templates(self):
        """Crear templates HTML básicos"""
        templates_dir = Path(__file__).parent / "templates"
        templates_dir.mkdir(exist_ok=True)
        
        # Template base
        base_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}PM Bot Enterprise{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .status-badge { font-size: 0.8em; }
        .progress-small { height: 10px; }
        .sidebar { min-height: 100vh; background: #f8f9fa; }
        .main-content { padding: 20px; }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <!-- Sidebar -->
            <div class="col-md-2 sidebar">
                <div class="p-3">
                    <h4><i class="fas fa-robot"></i> PM Bot</h4>
                    <hr>
                    <nav class="nav flex-column">
                        <a class="nav-link" href="{{ url_for('dashboard') }}">
                            <i class="fas fa-tachometer-alt"></i> Dashboard
                        </a>
                        <a class="nav-link" href="{{ url_for('projects_list') }}">
                            <i class="fas fa-folder"></i> Projects
                        </a>
                        <a class="nav-link" href="{{ url_for('create_project_form') }}">
                            <i class="fas fa-plus"></i> Create Project
                        </a>
                        <a class="nav-link" href="{{ url_for('agents_dashboard') }}">
                            <i class="fas fa-users"></i> Agents
                        </a>
                        <a class="nav-link" href="{{ url_for('system_status') }}">
                            <i class="fas fa-server"></i> System
                        </a>
                    </nav>
                </div>
            </div>
            
            <!-- Main Content -->
            <div class="col-md-10 main-content">
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ 'danger' if category == 'error' else category }} alert-dismissible fade show" role="alert">
                                {{ message }}
                                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                            </div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                
                {% block content %}{% endblock %}
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>'''
        
        with open(templates_dir / "base.html", "w") as f:
            f.write(base_template)
        
        # Dashboard template
        dashboard_template = '''{% extends "base.html" %}

{% block title %}Dashboard - PM Bot Enterprise{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h1><i class="fas fa-tachometer-alt"></i> Dashboard</h1>
    <a href="{{ url_for('create_project_form') }}" class="btn btn-primary">
        <i class="fas fa-plus"></i> New Project
    </a>
</div>

<!-- Metrics Cards -->
<div class="row mb-4">
    <div class="col-md-3">
        <div class="card bg-primary text-white">
            <div class="card-body">
                <h5><i class="fas fa-folder"></i> Total Projects</h5>
                <h2>{{ metrics.get('projects_created', 0) }}</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-success text-white">
            <div class="card-body">
                <h5><i class="fas fa-check"></i> Completed</h5>
                <h2>{{ metrics.get('projects_completed', 0) }}</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-info text-white">
            <div class="card-body">
                <h5><i class="fas fa-users"></i> Active Agents</h5>
                <h2>{{ metrics.get('active_projects', 0) }}</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-warning text-white">
            <div class="card-body">
                <h5><i class="fas fa-percentage"></i> Success Rate</h5>
                <h2>{{ "%.1f"|format(metrics.get('success_rate', 0)) }}%</h2>
            </div>
        </div>
    </div>
</div>

<!-- Recent Projects -->
<div class="row">
    <div class="col-md-8">
        <div class="card">
            <div class="card-header">
                <h5><i class="fas fa-folder"></i> Recent Projects</h5>
            </div>
            <div class="card-body">
                {% if projects %}
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Status</th>
                                    <th>Progress</th>
                                    <th>Modules</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for project in projects %}
                                <tr>
                                    <td>
                                        <a href="{{ url_for('project_detail', project_id=project.id) }}">
                                            {{ project.name }}
                                        </a>
                                    </td>
                                    <td>
                                        <span class="badge bg-{{ 'success' if project.status == 'completed' else 'primary' if project.status == 'in_progress' else 'secondary' }}">
                                            {{ project.status }}
                                        </span>
                                    </td>
                                    <td>
                                        <div class="progress progress-small">
                                            <div class="progress-bar" style="width: {{ project.progress }}%"></div>
                                        </div>
                                        {{ "%.1f"|format(project.progress) }}%
                                    </td>
                                    <td>{{ project.modules_count }}</td>
                                    <td>
                                        <a href="{{ url_for('project_detail', project_id=project.id) }}" class="btn btn-sm btn-outline-primary">
                                            <i class="fas fa-eye"></i>
                                        </a>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                {% else %}
                    <p class="text-muted">No projects yet. <a href="{{ url_for('create_project_form') }}">Create your first project</a>.</p>
                {% endif %}
            </div>
        </div>
    </div>
    
    <div class="col-md-4">
        <div class="card">
            <div class="card-header">
                <h5><i class="fas fa-heartbeat"></i> System Health</h5>
            </div>
            <div class="card-body">
                <div class="mb-3">
                    <strong>AI Status:</strong>
                    <span class="badge bg-{{ 'success' if ai_status.get('local', {}).get('available') else 'danger' }}">
                        {{ 'Online' if ai_status.get('local', {}).get('available') else 'Offline' }}
                    </span>
                </div>
                
                <div class="mb-3">
                    <strong>Available Models:</strong>
                    <ul class="list-unstyled">
                        {% for model in ai_status.get('local', {}).get('models', [])[:3] %}
                            <li><small class="text-muted">{{ model }}</small></li>
                        {% endfor %}
                    </ul>
                </div>
                
                <div>
                    <strong>Memory Usage:</strong>
                    <div class="progress progress-small mt-1">
                        <div class="progress-bar" style="width: {{ metrics.get('memory_usage', {}).get('percent', 0) }}%"></div>
                    </div>
                    <small class="text-muted">{{ "%.1f"|format(metrics.get('memory_usage', {}).get('rss', 0)) }} MB</small>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''
        
        with open(templates_dir / "dashboard.html", "w") as f:
            f.write(dashboard_template)
        
        # Create Project template
        create_template = '''{% extends "base.html" %}

{% block title %}Create Project - PM Bot Enterprise{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8">
        <div class="card">
            <div class="card-header">
                <h4><i class="fas fa-plus"></i> Create New Project</h4>
            </div>
            <div class="card-body">
                <form method="POST">
                    <div class="mb-3">
                        <label for="description" class="form-label">Project Description *</label>
                        <textarea class="form-control" id="description" name="description" rows="5" 
                                  placeholder="Describe your project in detail. Include features, technologies, timeline, etc."
                                  required></textarea>
                        <div class="form-text">Be as detailed as possible. Example: "Create an e-commerce platform with user authentication, payment processing via Stripe, real-time chat, and mobile app."</div>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="timeline" class="form-label">Timeline</label>
                                <select class="form-select" id="timeline" name="timeline">
                                    <option value="">Auto-estimate</option>
                                    <option value="1 week">1 week</option>
                                    <option value="2 weeks">2 weeks</option>
                                    <option value="1 month">1 month</option>
                                    <option value="2 months">2 months</option>
                                    <option value="3 months">3 months</option>
                                    <option value="6 months">6 months</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="budget" class="form-label">Budget Range</label>
                                <select class="form-select" id="budget" name="budget">
                                    <option value="">Auto-estimate</option>
                                    <option value="startup">Startup ($5k-$50k)</option>
                                    <option value="medium">Medium ($50k-$200k)</option>
                                    <option value="enterprise">Enterprise ($200k+)</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="team_size" class="form-label">Team Size</label>
                                <input type="number" class="form-control" id="team_size" name="team_size" 
                                       min="2" max="20" placeholder="Auto-calculate">
                            </div>
                        </div>
                    </div>
                    
                    <div class="mb-3 form-check">
                        <input type="checkbox" class="form-check-input" id="auto_execute" name="auto_execute">
                        <label class="form-check-label" for="auto_execute">
                            Start execution immediately after creation
                        </label>
                    </div>
                    
                    <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                        <a href="{{ url_for('dashboard') }}" class="btn btn-secondary me-md-2">Cancel</a>
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-rocket"></i> Create Project
                        </button>
                    </div>
                </form>
            </div>
        </div>
        
        <!-- Examples -->
        <div class="card mt-4">
            <div class="card-header">
                <h5><i class="fas fa-lightbulb"></i> Example Prompts</h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <h6>E-commerce Platform:</h6>
                        <p class="text-muted small">Create marketplace with product catalog, shopping cart, Stripe payments, user reviews, admin dashboard, and mobile app (React Native).</p>
                    </div>
                    <div class="col-md-6">
                        <h6>SaaS Dashboard:</h6>
                        <p class="text-muted small">Build project management SaaS with team collaboration, real-time updates, analytics dashboard, API, and user authentication.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''
        
        with open(templates_dir / "create_project.html", "w") as f:
            f.write(create_template)
        
        print(f"✅ Templates created in {templates_dir}")
    
    def run(self, host='127.0.0.1', port=5000, debug=True):
        """Ejecutar servidor de dashboard"""
        print(f"🚀 Starting PM Bot Enterprise Dashboard...")
        print(f"📱 Dashboard URL: http://{host}:{port}")
        print(f"🔧 Debug mode: {debug}")
        
        # Crear templates si no existen
        self.create_templates()
        
        self.app.run(host=host, port=port, debug=debug)


def main():
    """Función principal para ejecutar dashboard"""
    import argparse
    
    parser = argparse.ArgumentParser(description="PM Bot Enterprise Dashboard")
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--no-debug', action='store_true', help='Disable debug mode')
    
    args = parser.parse_args()
    
    dashboard = DashboardApp()
    dashboard.run(
        host=args.host,
        port=args.port,
        debug=not args.no_debug
    )


if __name__ == '__main__':
    main()