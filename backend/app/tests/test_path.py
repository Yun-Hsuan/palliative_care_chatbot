from pathlib import Path
import os
import sys
import subprocess
import pytest

# Add the parent directory to sys.path to allow importing from app
sys.path.append(str(Path(__file__).parent.parent))

from core.config import get_env_file

def print_environment_sources(execution_dir: str):
    """Print all possible sources of the ENVIRONMENT variable"""
    print(f"\nEnvironment Variable Sources (executing from {execution_dir}):")
    print(f"Current working directory: {os.getcwd()}")
    
    # 1. Check system environment variable
    print("\n1. System Environment:")
    print(f"   os.environ.get('ENVIRONMENT'): {os.environ.get('ENVIRONMENT', 'not set')}")
    
    # 2. Check environment from shell
    print("\n2. Shell Environment:")
    try:
        shell_env = subprocess.check_output('echo $ENVIRONMENT', shell=True, text=True).strip()
        print(f"   Shell $ENVIRONMENT: {shell_env or 'not set'}")
    except subprocess.CalledProcessError:
        print("   Failed to get shell environment")
    
    # 3. Check .env files
    print("\n3. .env Files:")
    root_dir = Path(__file__).parent.parent.parent.parent
    env_files = [
        root_dir / ".env",
        root_dir / "env-config" / "local" / ".env",
        root_dir / "env-config" / "staging" / ".env",
        root_dir / "env-config" / "production" / ".env"
    ]
    
    for env_file in env_files:
        print(f"\n   Checking {env_file}:")
        if env_file.exists():
            print("   File exists")
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.strip().startswith('ENVIRONMENT='):
                            print(f"   Found setting: {line.strip()}")
                            print(f"   Absolute path: {env_file.resolve()}")
                            print(f"   Relative to cwd: {env_file.relative_to(os.getcwd())}")
            except Exception as e:
                print(f"   Error reading file: {e}")
        else:
            print("   File does not exist")

def test_environment_resolution():
    """Test how environment variables are resolved from different sources"""
    original_env = os.environ.get('ENVIRONMENT')
    original_cwd = os.getcwd()
    
    try:
        # Test in backend directory
        backend_dir = Path(__file__).parent.parent.parent
        os.chdir(backend_dir)
        print("\n=== Testing in backend directory ===")
        run_environment_tests("backend directory")
        
        # Test in project root directory
        project_root = backend_dir.parent
        os.chdir(project_root)
        print("\n=== Testing in project root directory ===")
        run_environment_tests("project root")
        
    finally:
        # Restore original state
        os.chdir(original_cwd)
        if original_env is not None:
            os.environ['ENVIRONMENT'] = original_env
        else:
            os.environ.pop('ENVIRONMENT', None)

def run_environment_tests(context: str):
    """Run environment tests in the current directory"""
    print_environment_sources(context)
    
    print("\nTesting Environment Resolution:")
    
    # 1. Without environment variable
    if 'ENVIRONMENT' in os.environ:
        del os.environ['ENVIRONMENT']
    env_file = get_env_file()
    print(f"\n1. With no environment variable:")
    print(f"   get_env_file() returns: {env_file}")
    print(f"   Absolute path: {Path(env_file).resolve()}")
    try:
        print(f"   Relative to cwd: {Path(env_file).relative_to(os.getcwd())}")
    except ValueError:
        print("   Cannot make path relative to cwd")
    
    # 2. Test with different environments
    for env in ['local', 'staging', 'production', 'invalid']:
        os.environ['ENVIRONMENT'] = env
        env_file = get_env_file()
        print(f"\n2. With ENVIRONMENT={env}:")
        print(f"   get_env_file() returns: {env_file}")
        abs_path = Path(env_file).resolve()
        print(f"   Absolute path: {abs_path}")
        print(f"   File exists: {abs_path.exists()}")
        try:
            print(f"   Relative to cwd: {Path(env_file).relative_to(os.getcwd())}")
        except ValueError:
            print("   Cannot make path relative to cwd")

if __name__ == "__main__":
    print("Testing environment variable resolution in different contexts...")
    test_environment_resolution() 