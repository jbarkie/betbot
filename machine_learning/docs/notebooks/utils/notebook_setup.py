"""
Utility functions for Jupyter notebook setup and configuration.
"""
import sys
from pathlib import Path

def setup_notebook_env():
    """
    Set up the notebook environment by adding the project root to sys.path.
    This allows notebooks to import from the project's Python packages.
    
    Returns:
        Path: The project root path
    """
    notebook_path = Path.cwd()
    
    current_path = notebook_path
    while current_path.name != 'betbot':
        if current_path.parent == current_path:
            raise RuntimeError("Could not find project root directory")
        current_path = current_path.parent
    
    project_root = current_path
    
    if str(project_root) not in sys.path:
        sys.path.append(str(project_root))
    
    return project_root

def load_env_variables():
    """
    Load environment variables from the project's .env file.
    """
    from dotenv import load_dotenv
    
    project_root = setup_notebook_env()
    dotenv_path = project_root / 'api/.env'
    load_dotenv(dotenv_path)