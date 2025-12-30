#!/usr/bin/env python
import os
import subprocess

print("Starting Vercel build...")

# Collect static files
print("Collecting static files...")
subprocess.run(["python", "manage.py", "collectstatic", "--noinput", "--clear"], check=True)

# Run migrations
print("Running migrations...")
subprocess.run(["python", "manage.py", "migrate", "--noinput"], check=True)

print("Build completed successfully!")
