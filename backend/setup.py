from setuptools import setup, find_packages
from pathlib import Path

# Read requirements from requirements.txt
def read_requirements():
    """Read requirements.txt and return list of dependencies."""
    requirements_file = Path(__file__).parent / "requirements.txt"
    if requirements_file.exists():
        with open(requirements_file, 'r', encoding='utf-8') as f:
            # Filter out comments and empty lines
            return [
                line.strip() 
                for line in f 
                if line.strip() and not line.startswith('#')
            ]
    return []

setup(
    name="sleepy-storybook-backend",
    version="0.1.0",
    packages=find_packages(),
    install_requires=read_requirements(),
    python_requires=">=3.11",  # Required for LangGraph CLI
    description="LangGraph-based bedtime story generation system",
    author="Sleepy Storybook Team",
    long_description=open("README.md", encoding="utf-8").read() if Path("README.md").exists() else "",
    long_description_content_type="text/markdown",
)
