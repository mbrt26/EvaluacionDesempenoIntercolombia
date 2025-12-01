#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/home/mrodriguez/proyectos/EvaluacionDesempenoIntercolombia/sistema_planes')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from planes.models import Proveedor, Evaluacion

# Create test client
client = Client()

# Login as tecnico1
login_result = client.login(username='tecnico1', password='tecnico123')
print(f"Login successful: {login_result}")

if not login_result:
    # Try to create/reset the user
    try:
        user = User.objects.get(username='tecnico1')
        user.set_password('tecnico123')
        user.save()
        print("Password reset for tecnico1")
    except User.DoesNotExist:
        user = User.objects.create_user('tecnico1', 'tecnico1@example.com', 'tecnico123')
        user.first_name = 'Técnico'
        user.last_name = 'Uno'
        user.save()
        print("Created tecnico1 user")
    
    # Try login again
    login_result = client.login(username='tecnico1', password='tecnico123')
    print(f"Login after reset: {login_result}")

# Test the view
print("\n--- Testing /tecnico/proveedores/ ---")
response = client.get('/tecnico/proveedores/')
print(f"Response status: {response.status_code}")
print(f"Response URL: {response.url if hasattr(response, 'url') else 'N/A'}")

if response.status_code == 200:
    content = response.content.decode('utf-8')
    
    # Check for key elements
    print(f"\nContent length: {len(content)} characters")
    print(f"Contains 'Lista de Proveedores': {'Lista de Proveedores' in content}")
    print(f"Contains table: {'<table' in content}")
    print(f"Contains tbody: {'<tbody' in content}")
    
    # Count providers in table
    import re
    rows = re.findall(r'<tr[^>]*>.*?</tr>', content, re.DOTALL)
    print(f"Number of table rows found: {len(rows)}")
    
    # Check context data
    if hasattr(response, 'context') and response.context:
        print(f"\nContext keys: {list(response.context.keys())}")
        if 'datos' in response.context:
            print(f"Number of providers in context: {len(response.context['datos'])}")
            for item in response.context['datos'][:3]:  # Show first 3
                print(f"  - {item['proveedor'].razon_social}: {item['evaluacion'].puntaje} puntos")
    
    # Save the HTML for inspection
    with open('/tmp/proveedores_output.html', 'w') as f:
        f.write(content)
    print("\nHTML saved to /tmp/proveedores_output.html")
    
    # Extract just the body content
    body_match = re.search(r'<body[^>]*>(.*?)</body>', content, re.DOTALL)
    if body_match:
        body_content = body_match.group(1)
        print(f"\nBody content length: {len(body_content)} characters")
        
        # Check for error messages
        if 'error' in body_content.lower() or 'exception' in body_content.lower():
            print("WARNING: Error or exception found in content")
        
        # Check for specific elements in our template
        if 'stat-card' in body_content:
            print("✓ Statistics cards found")
        if 'table-container' in body_content:
            print("✓ Table container found")
        if 'btn-info' in body_content:
            print("✓ Action buttons found")
            
elif response.status_code == 302:
    print(f"Redirected to: {response.url}")
    print("User may not be authenticated properly")
else:
    print(f"Unexpected status code: {response.status_code}")

# Check monitoring output
print("\n--- Checking server output ---")