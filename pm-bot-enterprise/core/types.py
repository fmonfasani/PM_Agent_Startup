# core/types.py
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional

class ProjectStatus(Enum):
    PLANNING = "Planning"
    INITIATING = "Initiating"
    DEVELOPING = "Developing"
    TESTING = "Testing"
    DEPLOYING = "Deploying"
    COMPLETED = "Completed"
    MAINTENANCE = "Maintenance"
    CANCELLED = "Cancelled"

class ProjectState(Enum):
    INITIAL = "Initial Prompt Received"
    REQUIREMENTS_GATHERED = "Requirements Gathered"
    PLAN_GENERATED = "Project Plan Generated"
    ARCHITECTURE_DEFINED = "Architecture Defined"
    MODULES_IDENTIFIED = "Modules Identified"
    DEVELOPMENT_STARTED = "Development Started"
    TESTING_IN_PROGRESS = "Testing In Progress"
    DEPLOYMENT_INITIATED = "Deployment Initiated"
    PROJECT_CLOSED = "Project Closed"
    ADJUSTING_PLAN = "Adjusting Plan"

@dataclass
class ModuleSpec:
    name: str
    type: str # e.g., 'backend', 'frontend', 'database', 'devops', 'fullstack', 'mobile'
    description: str
    dependencies: List[str] # Other module names
    agents_needed: List[str] # Types of agents needed, e.g., 'backend', 'frontend', 'devops'
    complexity: int # 1-10
    estimated_hours: int
    tech_stack: List[str]
    apis_needed: List[str] # List of API endpoints/functionalities
    database_entities: List[str] # List of database tables/collections

@dataclass
class ProjectConfig:
    name: str
    description: str
    complexity: int
    timeline: str # e.g., "3-6 months"
    budget: str # e.g., "medium", "high"
    requirements: List[str]
    tech_stack: List[str]
    team_size: int
    compliance: List[str] = field(default_factory=list) # e.g., GDPR, HIPAA
    modules: List[ModuleSpec] = field(default_factory=list) # Generated modules

@dataclass
class AgentRole:
    name: str
    description: str
    skills: List[str]
    tech_stack_expertise: List[str]
    priority_modules: List[str] = field(default_factory=list) # Modules this agent typically works on

@dataclass
class TaskSpec:
    task_id: str
    module_name: str
    description: str
    estimated_hours: int
    assigned_to_agent: Optional[str] = None # Agent ID or Role Name
    status: str = "pending" # e.g., "pending", "in_progress", "completed", "blocked"
    dependencies: List[str] = field(default_factory=list) # Other task_ids
    output_expected: Optional[str] = None # Description of expected output for validation
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)