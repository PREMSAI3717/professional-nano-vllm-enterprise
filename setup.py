#!/usr/bin/env python3
"""
Professional Nano-LLM Engine - Setup Script
Automated setup per ambiente di sviluppo
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

class ProjectSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.python_version = "3.9"
        
    def check_requirements(self):
        """Verifica requisiti di sistema"""
        print("🔍 Checking system requirements...")
        
        # Check Python version
        current_python = f"{sys.version_info.major}.{sys.version_info.minor}"
        if sys.version_info < (3, 9):
            print(f"❌ Python {self.python_version}+ required, found {current_python}")
            return False
        print(f"✅ Python {current_python} - OK")
        
        # Check GPU availability
        try:
            import torch
            if torch.cuda.is_available():
                gpu_count = torch.cuda.device_count()
                gpu_name = torch.cuda.get_device_name(0)
                print(f"✅ GPU detected: {gpu_name} (Count: {gpu_count})")
            else:
                print("⚠️  No GPU detected - CPU only mode")
        except ImportError:
            print("⚠️  PyTorch not installed - will install during setup")
            
        return True
        
    def setup_virtual_environment(self):
        """Setup virtual environment"""
        print("\n🐍 Setting up virtual environment...")
        
        venv_path = self.project_root / "venv"
        if venv_path.exists():
            print("✅ Virtual environment already exists")
            return True
            
        try:
            subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
            print("✅ Virtual environment created")
            
            # Activate virtual environment
            if platform.system() == "Windows":
                activate_script = venv_path / "Scripts" / "activate.bat"
                pip_path = venv_path / "Scripts" / "pip.exe"
            else:
                activate_script = venv_path / "bin" / "activate"
                pip_path = venv_path / "bin" / "pip"
                
            print(f"📝 To activate: {activate_script}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error creating virtual environment: {e}")
            return False
            
    def install_dependencies(self):
        """Install Python dependencies"""
        print("\n📦 Installing dependencies...")
        
        # Core dependencies
        core_deps = [
            "torch>=2.0.0",
            "transformers>=4.30.0", 
            "fastapi>=0.100.0",
            "uvicorn>=0.22.0",
            "pydantic>=2.0.0",
            "numpy>=1.24.0",
            "pyyaml>=6.0",
            "requests>=2.31.0"
        ]
        
        # Development dependencies  
        dev_deps = [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0"
        ]
        
        # Monitoring dependencies
        monitoring_deps = [
            "prometheus-client>=0.17.0",
            "psutil>=5.9.0"
        ]
        
        all_deps = core_deps + dev_deps + monitoring_deps
        
        try:
            for dep in all_deps:
                print(f"Installing {dep}...")
                subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                             check=True, capture_output=True)
            print("✅ All dependencies installed")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error installing dependencies: {e}")
            return False
            
    def clone_nano_vllm(self):
        """Clone nano-vLLM repository"""
        print("\n📥 Cloning nano-vLLM repository...")
        
        nano_vllm_path = self.project_root / "external" / "nano-vllm"
        if nano_vllm_path.exists():
            print("✅ nano-vLLM already cloned")
            return True
            
        try:
            os.makedirs(self.project_root / "external", exist_ok=True)
            subprocess.run([
                "git", "clone", 
                "https://github.com/GeeeekExplorer/nano-vllm.git",
                str(nano_vllm_path)
            ], check=True)
            print("✅ nano-vLLM cloned successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error cloning nano-vLLM: {e}")
            return False
            
    def setup_project_structure(self):
        """Setup project directory structure"""
        print("\n📁 Setting up project structure...")
        
        directories = [
            "src/professional_nano_llm",
            "src/professional_nano_llm/core",
            "src/professional_nano_llm/api", 
            "src/professional_nano_llm/monitoring",
            "src/professional_nano_llm/utils",
            "tests/unit",
            "tests/integration", 
            "tests/performance",
            "docs/api",
            "docs/deployment",
            "scripts",
            "configs",
            "logs"
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            
            # Create __init__.py for Python packages
            if directory.startswith("src/"):
                init_file = dir_path / "__init__.py"
                if not init_file.exists():
                    init_file.touch()
                    
        print("✅ Project structure created")
        return True
        
    def create_initial_files(self):
        """Create initial project files"""
        print("\n📄 Creating initial files...")
        
        # requirements.txt
        requirements_content = """# Core dependencies
torch>=2.0.0
transformers>=4.30.0
fastapi>=0.100.0
uvicorn>=0.22.0
pydantic>=2.0.0
numpy>=1.24.0
pyyaml>=6.0
requests>=2.31.0

# Development dependencies
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.0.0

# Monitoring dependencies  
prometheus-client>=0.17.0
psutil>=5.9.0
"""
        
        with open(self.project_root / "requirements.txt", "w") as f:
            f.write(requirements_content)
            
        # .gitignore
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
logs/
*.log

# OS
.DS_Store
Thumbs.db

# Model files
models/
checkpoints/
*.bin
*.safetensors

# Configuration
.env
config.local.yaml

# Testing
.coverage
.pytest_cache/
htmlcov/

# External
external/
"""
        
        with open(self.project_root / ".gitignore", "w") as f:
            f.write(gitignore_content)
            
        print("✅ Initial files created")
        return True
        
    def run_setup(self):
        """Run complete setup process"""
        print("🚀 Professional Nano-LLM Engine Setup")
        print("=" * 50)
        
        steps = [
            ("Checking requirements", self.check_requirements),
            ("Setting up virtual environment", self.setup_virtual_environment), 
            ("Installing dependencies", self.install_dependencies),
            ("Cloning nano-vLLM", self.clone_nano_vllm),
            ("Setting up project structure", self.setup_project_structure),
            ("Creating initial files", self.create_initial_files)
        ]
        
        for step_name, step_func in steps:
            if not step_func():
                print(f"\n❌ Setup failed at: {step_name}")
                return False
                
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Activate virtual environment")
        print("2. Review configuration in config.yaml")
        print("3. Start with Sprint 1 tasks")
        print("4. Begin nano-vLLM code analysis")
        
        return True

if __name__ == "__main__":
    setup = ProjectSetup()
    success = setup.run_setup()
    sys.exit(0 if success else 1)
