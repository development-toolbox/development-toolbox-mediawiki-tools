#!/usr/bin/env python3
"""
Test runner script for MediaWiki Migration Tools test suite.

This script provides a convenient way to run all tests with proper
configuration and reporting.
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(command, description):
    """Run a command and return success/failure."""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, shell=True, check=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False


def main():
    """Main test runner function."""
    print("🚀 MediaWiki Migration Tools - Test Suite Runner")
    print("=" * 60)
    
    # Change to project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    print(f"📁 Working directory: {project_root}")
    
    # Check if pytest is available
    try:
        import pytest
        print(f"✅ pytest version: {pytest.__version__}")
    except ImportError:
        print("❌ pytest not found. Please install test dependencies:")
        print("   pip install -r tests/requirements-test.txt")
        sys.exit(1)
    
    # Test commands to run
    test_commands = [
        {
            'command': 'python -m pytest tests/ -v --tb=short',
            'description': 'Running all unit and integration tests'
        },
        {
            'command': 'python -m pytest tests/ --cov=migration --cov=templates --cov=. --cov-report=term-missing --cov-report=html',
            'description': 'Running tests with coverage analysis'
        },
        {
            'command': 'python -m pytest tests/ -m "not slow" -x',
            'description': 'Running fast tests only (excluding slow tests)'
        }
    ]
    
    # Ask user which tests to run
    print("\nAvailable test options:")
    for i, cmd in enumerate(test_commands, 1):
        print(f"{i}. {cmd['description']}")
    print("4. Run all test commands")
    print("0. Exit")
    
    try:
        choice = input("\nSelect option (0-4): ").strip()
        
        if choice == "0":
            print("👋 Test runner exiting")
            return
        elif choice in ["1", "2", "3"]:
            cmd_index = int(choice) - 1
            cmd_info = test_commands[cmd_index]
            success = run_command(cmd_info['command'], cmd_info['description'])
            
            if success:
                print(f"\n🎉 Test execution completed successfully!")
                
                # Show coverage report location if coverage was run
                if 'cov-report=html' in cmd_info['command']:
                    print(f"📊 HTML coverage report available at: {project_root}/htmlcov/index.html")
            else:
                print(f"\n❌ Test execution failed. Check the output above for details.")
                sys.exit(1)
                
        elif choice == "4":
            print("\n🔄 Running all test commands...")
            all_success = True
            
            for cmd_info in test_commands:
                success = run_command(cmd_info['command'], cmd_info['description'])
                if not success:
                    all_success = False
                    print(f"⚠️  Continuing with remaining tests...")
            
            if all_success:
                print(f"\n🎉 All test commands completed successfully!")
                print(f"📊 HTML coverage report available at: {project_root}/htmlcov/index.html")
            else:
                print(f"\n⚠️  Some test commands failed. Check the output above for details.")
                
        else:
            print("❌ Invalid choice. Please select 0-4.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Test execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()