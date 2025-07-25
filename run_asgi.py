#!/usr/bin/env python
"""
ASGI server startup script for development with WebSocket support
"""
import os
import django
from daphne.cli import CommandLineInterface

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelancehub_backend.settings')

# Setup Django before importing any apps
django.setup()

if __name__ == '__main__':
    # Run Daphne with proper arguments
    import sys
    sys.argv = [
        'daphne',
        '-b', '0.0.0.0',
        '-p', '8000',
        '--verbosity', '2',
        'freelancehub_backend.asgi:application'
    ]
    
    cli = CommandLineInterface()
    cli.run(sys.argv[1:])
