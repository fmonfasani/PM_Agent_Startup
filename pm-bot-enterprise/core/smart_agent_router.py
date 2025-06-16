# core/smart_agent_router.py
"""
Smart Agent Router - Optimización inteligente de asignación de agentes
basada en especialización, costo y calidad
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging

class TaskComplexity(Enum):
    SIMPLE = 1      # Tareas rutinarias, templates, boilerplate
    MEDIUM = 2      # Lógica de negocio estándar
    COMPLEX = 3     # Arquitectura, optimización, debugging avanzado
    CRITICAL = 4    # Seguridad, performance crítica, algoritmos complejos

class CostTier(Enum):
    FREE = 0        # Modelos locales (Llama, DeepSeek)
    LOW = 1         # Modelos básicos cloud
    MEDIUM = 2      # Claude Sonnet, GPT-4o
    HIGH = 3        # Claude Opus, GPT-4 Turbo

@dataclass
class AgentCapability:
    model: str
    cost_tier: CostTier
    specializations: List[str]
    quality_scores: Dict[str, float]  # Por tipo de tarea
    context_window: int
    speed_rating: float  # tokens/segundo
    reliability_score: float  # 0-1

class SmartAgentRouter:
    """Router inteligente que selecciona el mejor agente según costo/calidad"""
    
    def __init__(self):
        self.logger = logging.getLogger('SmartAgentRouter')
        
        # Configuración de agentes disponibles
        self.agent_capabilities = {
            # TIER FREE - Modelos Locales
            "deepseek-r1:14b": AgentCapability(
                model="deepseek-r1:14b",
                cost_tier=CostTier.FREE,
                specializations=[
                    "backend_implementation", "api_design", "database_schema",
                    "code_optimization", "debugging", "algorithm_implementation",
                    "system_architecture", "performance_tuning"
                ],
                quality_scores={
                    "backend_development": 0.9,
                    "algorithm_implementation": 0.95,
                    "code_optimization": 0.9,
                    "debugging": 0.85,
                    "api_design": 0.85,
                    "frontend_development": 0.6,
                    "ui_design": 0.4,
                    "content_creation": 0.5
                },
                context_window=32768,
                speed_rating=0.8,
                reliability_score=0.9
            ),
            
            "llama3.2:latest": AgentCapability(
                model="llama3.2:latest",
                cost_tier=CostTier.FREE,
                specializations=[
                    "general_coding", "documentation", "testing",
                    "code_review", "simple_frontend", "scripting"
                ],
                quality_scores={
                    "general_coding": 0.8,
                    "documentation": 0.85,
                    "testing": 0.8,
                    "code_review": 0.75,
                    "simple_frontend": 0.7,
                    "backend_development": 0.7,
                    "algorithm_implementation": 0.7,
                    "ui_design": 0.5
                },
                context_window=8192,
                speed_rating=0.9,
                reliability_score=0.8
            ),
            
            "qwen2.5-coder:7b": AgentCapability(
                model="qwen2.5-coder:7b",
                cost_tier=CostTier.FREE,
                specializations=[
                    "devops", "infrastructure", "docker", "kubernetes",
                    "ci_cd", "automation", "configuration"
                ],
                quality_scores={
                    "devops": 0.9,
                    "infrastructure": 0.85,
                    "automation": 0.85,
                    "configuration": 0.8,
                    "backend_development": 0.7,
                    "testing": 0.75,
                    "frontend_development": 0.5
                },
                context_window=16384,
                speed_rating=0.85,
                reliability_score=0.85
            ),
            
            # TIER MEDIUM - Cloud Premium
            "claude-3-5-sonnet": AgentCapability(
                model="claude-3-5-sonnet",
                cost_tier=CostTier.MEDIUM,
                specializations=[
                    "frontend_development", "ui_design", "user_experience",
                    "complex_logic", "analysis", "planning", "architecture_review",
                    "security_analysis", "code_quality"
                ],
                quality_scores={
                    "frontend_development": 0.95,
                    "ui_design": 0.9,
                    "user_experience": 0.9,
                    "analysis": 0.95,
                    "planning": 0.9,
                    "security_analysis": 0.9,
                    "code_quality": 0.95,
                    "backend_development": 0.85,
                    "algorithm_implementation": 0.85
                },
                context_window=200000,
                speed_rating=0.7,
                reliability_score=0.95
            ),
            
            "gpt-4o": AgentCapability(
                model="gpt-4o",
                cost_tier=CostTier.MEDIUM,
                specializations=[
                    "creative_solutions", "complex_problem_solving",
                    "integration", "full_stack", "mobile_development",
                    "user_interaction", "business_logic"
                ],
                quality_scores={
                    "creative_solutions": 0.9,
                    "complex_problem_solving": 0.9,
                    "integration": 0.85,
                    "mobile_development": 0.85,
                    "full_stack": 0.8,
                    "frontend_development": 0.8,
                    "backend_development": 0.8,
                    "ui_design": 0.75
                },
                context_window=128000,
                speed_rating=0.75,
                reliability_score=0.9
            )
        }
        
        # Patrones para detectar tipo de tarea
        self.task_patterns = {
            "backend_development": [
                r"api", r"endpoint", r"server", r"backend", r"database",
                r"authentication", r"authorization", r"middleware",
                r"express", r"fastapi", r"django", r"nodejs"
            ],
            "frontend_development": [
                r"react", r"vue", r"angular", r"frontend", r"ui", r"interface",
                r"component", r"styling", r"css", r"html", r"javascript",
                r"typescript", r"responsive"
            ],
            "algorithm_implementation": [
                r"algorithm", r"optimization", r"performance", r"complexity",
                r"sorting", r"search", r"data structure", r"efficient"
            ],
            "devops": [
                r"docker", r"kubernetes", r"deployment", r"ci/cd", r"pipeline",
                r"infrastructure", r"terraform", r"ansible", r"aws", r"azure"
            ],
            "testing": [
                r"test", r"testing", r"unit test", r"integration", r"e2e",
                r"jest", r"cypress", r"qa", r"quality"
            ],
            "ui_design": [
                r"design", r"layout", r"user interface", r"user experience",
                r"wireframe", r"mockup", r"prototype", r"usability"
            ],
            "security_analysis": [
                r"security", r"vulnerability", r"encryption", r"authentication",
                r"authorization", r"owasp", r"penetration", r"audit"
            ],
            "documentation": [
                r"documentation", r"readme", r"docs", r"manual", r"guide",
                r"comments", r"explain", r"describe"
            ]
        }
    
    def analyze_task_type(self, task_description: str) -> Tuple[str, TaskComplexity]:
        """Analizar tipo de tarea y complejidad basado en la descripción"""
        
        task_description_lower = task_description.lower()
        
        # Detectar tipo de tarea
        task_type = "general_coding"  # default
        max_matches = 0
        
        for task_type_name, patterns in self.task_patterns.items():
            matches = sum(1 for pattern in patterns if re.search(pattern, task_description_lower))
            if matches > max_matches:
                max_matches = matches
                task_type = task_type_name
        
        # Detectar complejidad
        complexity = self._assess_complexity(task_description_lower)
        
        self.logger.info(f"Task analyzed: type={task_type}, complexity={complexity.name}")
        return task_type, complexity
    
    def _assess_complexity(self, task_description: str) -> TaskComplexity:
        """Evaluar complejidad de la tarea"""
        
        complexity_indicators = {
            TaskComplexity.SIMPLE: [
                r"simple", r"basic", r"template", r"boilerplate", r"example",
                r"crud", r"straightforward", r"standard"
            ],
            TaskComplexity.MEDIUM: [
                r"integrate", r"implement", r"business logic", r"workflow",
                r"feature", r"functionality", r"moderate", r"standard"
            ],
            TaskComplexity.COMPLEX: [
                r"architecture", r"optimize", r"complex", r"advanced",
                r"scalable", r"performance", r"sophisticated", r"intricate"
            ],
            TaskComplexity.CRITICAL: [
                r"mission critical", r"high performance", r"security critical",
                r"enterprise grade", r"production ready", r"fault tolerant"
            ]
        }
        
        # Puntaje por complejidad
        scores = {complexity: 0 for complexity in TaskComplexity}
        
        for complexity, patterns in complexity_indicators.items():
            for pattern in patterns:
                if re.search(pattern, task_description):
                    scores[complexity] += 1
        
        # Indicadores adicionales de complejidad
        complexity_words = len(re.findall(r'\w+', task_description))
        if complexity_words > 100:
            scores[TaskComplexity.COMPLEX] += 1
        elif complexity_words > 50:
            scores[TaskComplexity.MEDIUM] += 1
        
        # Retornar la complejidad con mayor puntaje
        return max(scores.keys(), key=lambda k: scores[k]) if max(scores.values()) > 0 else TaskComplexity.MEDIUM
    
    def select_optimal_agent(self, task_description: str, budget_preference: str = "balanced") -> Tuple[str, float, str]:
        """
        Seleccionar el agente óptimo basado en costo/calidad
        
        Args:
            task_description: Descripción de la tarea
            budget_preference: "cost_optimized", "balanced", "quality_first"
            
        Returns:
            Tuple[model_name, expected_quality, reasoning]
        """
        
        task_type, complexity = self.analyze_task_type(task_description)
        
        # Calcular scores para cada agente
        agent_scores = []
        
        for model_name, capability in self.agent_capabilities.items():
            # Score de calidad para este tipo de tarea
            quality_score = capability.quality_scores.get(task_type, 0.5)
            
            # Ajustar por complejidad
            if complexity == TaskComplexity.SIMPLE and capability.cost_tier == CostTier.FREE:
                quality_score += 0.1  # Bonus para modelos locales en tareas simples
            elif complexity == TaskComplexity.CRITICAL and capability.cost_tier in [CostTier.MEDIUM, CostTier.HIGH]:
                quality_score += 0.05  # Bonus para modelos premium en tareas críticas
            
            # Score de costo (invertido, menor costo = mayor score)
            cost_score = 1.0 - (capability.cost_tier.value / 3.0)
            
            # Score combinado según preferencia
            if budget_preference == "cost_optimized":
                combined_score = 0.2 * quality_score + 0.8 * cost_score
            elif budget_preference == "quality_first":
                combined_score = 0.8 * quality_score + 0.2 * cost_score
            else:  # balanced
                combined_score = 0.6 * quality_score + 0.4 * cost_score
            
            # Bonus por especialización
            if task_type in capability.specializations:
                combined_score += 0.1
            
            # Penalty por baja confiabilidad
            combined_score *= capability.reliability_score
            
            agent_scores.append((model_name, combined_score, quality_score, capability))
        
        # Seleccionar el mejor agente
        best_agent = max(agent_scores, key=lambda x: x[1])
        model_name, combined_score, quality_score, capability = best_agent
        
        # Generar razonamiento
        reasoning = self._generate_selection_reasoning(
            model_name, task_type, complexity, budget_preference, capability
        )
        
        self.logger.info(f"Selected agent: {model_name} (score: {combined_score:.3f}, quality: {quality_score:.3f})")
        
        return model_name, quality_score, reasoning
    
    def _generate_selection_reasoning(self, model_name: str, task_type: str, 
                                    complexity: TaskComplexity, budget_preference: str,
                                    capability: AgentCapability) -> str:
        """Generar explicación de por qué se seleccionó este agente"""
        
        reasons = []
        
        # Especialización
        if task_type in capability.specializations:
            reasons.append(f"especializado en {task_type}")
        
        # Costo
        if capability.cost_tier == CostTier.FREE:
            reasons.append("modelo local gratuito")
        elif capability.cost_tier == CostTier.MEDIUM and budget_preference != "cost_optimized":
            reasons.append("balance óptimo costo/calidad")
        
        # Complejidad
        if complexity == TaskComplexity.SIMPLE and capability.cost_tier == CostTier.FREE:
            reasons.append("adecuado para tareas simples")
        elif complexity == TaskComplexity.CRITICAL and capability.cost_tier in [CostTier.MEDIUM, CostTier.HIGH]:
            reasons.append("necesario para tareas críticas")
        
        # Calidad
        quality_score = capability.quality_scores.get(task_type, 0.5)
        if quality_score > 0.9:
            reasons.append("excelente calidad esperada")
        elif quality_score > 0.8:
            reasons.append("buena calidad esperada")
        
        reasoning = f"Seleccionado {model_name}: {', '.join(reasons)}"
        return reasoning
    
    def get_cost_estimate(self, model_name: str, estimated_tokens: int) -> Dict[str, any]:
        """Estimar costo de ejecución"""
        
        if model_name not in self.agent_capabilities:
            return {"error": "Model not found"}
        
        capability = self.agent_capabilities[model_name]
        
        # Costos aproximados por 1K tokens (USD)
        cost_per_1k_tokens = {
            CostTier.FREE: 0.0,
            CostTier.LOW: 0.001,
            CostTier.MEDIUM: 0.003,
            CostTier.HIGH: 0.01
        }
        
        base_cost = (estimated_tokens / 1000) * cost_per_1k_tokens[capability.cost_tier]
        
        return {
            "model": model_name,
            "estimated_tokens": estimated_tokens,
            "cost_tier": capability.cost_tier.name,
            "estimated_cost_usd": base_cost,
            "is_local": capability.cost_tier == CostTier.FREE,
            "context_window": capability.context_window
        }
    
    def recommend_agent_for_module(self, module_spec: Dict[str, any], 
                                 budget_preference: str = "balanced") -> Dict[str, str]:
        """Recomendar agentes para un módulo completo"""
        
        module_type = module_spec.get("type", "backend")
        description = module_spec.get("description", "")
        complexity = module_spec.get("complexity", 5)
        
        recommendations = {}
        
        # Tareas típicas por tipo de módulo
        module_tasks = {
            "backend": [
                ("API design and implementation", "backend_development"),
                ("Database schema design", "backend_development"),
                ("Authentication implementation", "security_analysis"),
                ("Testing and validation", "testing")
            ],
            "frontend": [
                ("UI component development", "frontend_development"),
                ("User interface design", "ui_design"),
                ("Component testing", "testing"),
                ("Integration with backend", "integration")
            ],
            "fullstack": [
                ("Backend API development", "backend_development"),
                ("Frontend implementation", "frontend_development"),
                ("Full-stack integration", "integration"),
                ("End-to-end testing", "testing")
            ],
            "qa": [
                ("Test planning and strategy", "testing"),
                ("Automated testing implementation", "testing"),
                ("Quality analysis", "code_quality")
            ],
            "devops": [
                ("Infrastructure setup", "devops"),
                ("CI/CD pipeline configuration", "devops"),
                ("Deployment automation", "automation")
            ]
        }
        
        tasks = module_tasks.get(module_type, module_tasks["backend"])
        
        for task_name, task_type in tasks:
            task_desc = f"{task_name} for {description}"
            
            # Ajustar budget preference según complejidad
            if complexity >= 8:
                budget_pref = "quality_first"
            elif complexity <= 3:
                budget_pref = "cost_optimized"
            else:
                budget_pref = budget_preference
            
            model, quality, reasoning = self.select_optimal_agent(task_desc, budget_pref)
            
            recommendations[task_name] = {
                "model": model,
                "expected_quality": quality,
                "reasoning": reasoning,
                "task_type": task_type
            }
        
        return recommendations

# Función helper para usar en el sistema principal
def create_smart_router() -> SmartAgentRouter:
    """Factory function para crear el router inteligente"""
    return SmartAgentRouter()

# Ejemplo de uso
if __name__ == "__main__":
    router = SmartAgentRouter()
    
    # Ejemplo 1: Tarea simple de backend
    task1 = "Create a simple REST API endpoint for user authentication"
    model1, quality1, reasoning1 = router.select_optimal_agent(task1, "cost_optimized")
    print(f"Task 1: {model1} (Quality: {quality1:.2f}) - {reasoning1}")
    
    # Ejemplo 2: Tarea compleja de frontend
    task2 = "Design and implement a complex interactive dashboard with real-time data visualization and advanced user interactions"
    model2, quality2, reasoning2 = router.select_optimal_agent(task2, "quality_first")
    print(f"Task 2: {model2} (Quality: {quality2:.2f}) - {reasoning2}")
    
    # Ejemplo 3: Tarea de DevOps
    task3 = "Setup Docker containerization and Kubernetes deployment with CI/CD pipeline"
    model3, quality3, reasoning3 = router.select_optimal_agent(task3, "balanced")
    print(f"Task 3: {model3} (Quality: {quality3:.2f}) - {reasoning3}")