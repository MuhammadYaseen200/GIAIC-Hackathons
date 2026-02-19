#!/usr/bin/env python3
"""Test script to verify task completion fix."""

import json

import requests

# Login to get token
print("Step 1: Logging in to get token...")
login_resp = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"email": "bugfix@example.com", "password": "TestPassword123"}
)
print(f"  Login status: {login_resp.status_code}")
if login_resp.status_code == 200:
    token = login_resp.json()['data']['token']
    print(f"  Token received: {token[:50]}...")
else:
    print(f"  Login failed: {login_resp.text}")
    exit(1)

# Create a test task
print("\nStep 2: Creating test task...")
create_resp = requests.post(
    "http://localhost:8000/api/v1/tasks",
    headers={"Authorization": f"Bearer {token}"},
    json={"title": "Test Task for Fix Verification"}
)
print(f"  Task creation status: {create_resp.status_code}")
if create_resp.status_code == 200 or create_resp.status_code == 201:
    task_data = create_resp.json()['data']
    task_id = task_data['id']
    print(f"  Task created: {task_id}")
else:
    print(f"  Task creation failed: {create_resp.text}")
    exit(1)

# Test task completion toggle
print("\nStep 3: Testing task completion toggle...")
toggle_resp = requests.patch(
    f"http://localhost:8000/api/v1/tasks/{task_id}/complete",
    headers={"Authorization": f"Bearer {token}"},
    json={}
)
print(f"  Toggle status: {toggle_resp.status_code}")
if toggle_resp.status_code == 200:
    result = toggle_resp.json()
    print(f"  Success! Response: {json.dumps(result, indent=2)}")

    # Toggle back
    print("\nStep 4: Toggling back...")
    toggle_back_resp = requests.patch(
        f"http://localhost:8000/api/v1/tasks/{task_id}/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={}
    )
    if toggle_back_resp.status_code == 200:
        print(f"  Toggle back status: {toggle_back_resp.status_code}")
        print("\n[SUCCESS] All tests passed! Task completion is working correctly.")
    else:
        print(f"  Toggle back failed: {toggle_back_resp.status_code}")
        exit(1)
else:
    print(f"  Toggle failed with status {toggle_resp.status_code}")
    print(f"  Error: {toggle_resp.text}")
    exit(1)
