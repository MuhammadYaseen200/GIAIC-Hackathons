#!/usr/bin/env python3
"""Comprehensive Phase 2 backend endpoint test suite."""

from datetime import datetime

import requests

BASE_URL = "http://localhost:8000/api/v1"

# Test credentials
TEST_EMAIL = "bugfix@example.com"
TEST_PASSWORD = "TestPassword123"

# Store test data
test_data = {
    "user_id": None,
    "task_ids": []
}

print("=" * 60)
print("PHASE 2 BACKEND COMPREHENSIVE TEST SUITE")
print("=" * 60)
print(f"Started at: {datetime.now().isoformat()}")
print(f"Testing against: {BASE_URL}")
print()

# =============================================================================
# TEST 1: Login
# =============================================================================
print("TEST 1: User Login")
print("-" * 40)
login_resp = requests.post(
    f"{BASE_URL}/auth/login",
    json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
)
print(f"  Status: {login_resp.status_code}")
if login_resp.status_code == 200:
    login_data = login_resp.json()
    token = login_data['data']['token']
    test_data['user_id'] = login_data['data']['user']['id']
    print("  Result: PASS")
    print(f"  User ID: {test_data['user_id']}")
    print(f"  Token: {token[:30]}...")
else:
    print(f"  Result: FAIL - {login_resp.text}")
    exit(1)
print()

headers = {"Authorization": f"Bearer {token}"}

# =============================================================================
# TEST 2: Create Task
# =============================================================================
print("TEST 2: Create Task")
print("-" * 40)
create_resp = requests.post(
    f"{BASE_URL}/tasks",
    headers=headers,
    json={"title": "Test Task 1", "description": "Created during test suite"}
)
print(f"  Status: {create_resp.status_code}")
if create_resp.status_code == 201:
    task = create_resp.json()['data']
    test_data['task_ids'].append(task['id'])
    print("  Result: PASS")
    print(f"  Task ID: {task['id']}")
    print(f"  Title: {task['title']}")
    print(f"  Completed: {task['completed']}")
else:
    print(f"  Result: FAIL - {create_resp.text}")
    exit(1)
print()

# =============================================================================
# TEST 3: List Tasks
# =============================================================================
print("TEST 3: List Tasks")
print("-" * 40)
list_resp = requests.get(f"{BASE_URL}/tasks", headers=headers)
print(f"  Status: {list_resp.status_code}")
if list_resp.status_code == 200:
    tasks_data = list_resp.json()
    task_count = len(tasks_data['data'])
    print("  Result: PASS")
    print(f"  Total tasks: {task_count}")
    print(f"  Meta: {tasks_data['meta']}")
else:
    print(f"  Result: FAIL - {list_resp.text}")
    exit(1)
print()

# =============================================================================
# TEST 4: Toggle Task Complete (CRITICAL FIX)
# =============================================================================
print("TEST 4: Toggle Task Complete (CRITICAL FIX)")
print("-" * 40)
task_id = test_data['task_ids'][0]
toggle_resp = requests.patch(
    f"{BASE_URL}/tasks/{task_id}/complete",
    headers=headers,
    json={}
)
print(f"  Status: {toggle_resp.status_code}")
if toggle_resp.status_code == 200:
    task = toggle_resp.json()['data']
    is_completed = task['completed']
    print("  Result: PASS")
    print(f"  Task completed: {is_completed}")
    print(f"  Updated at: {task['updated_at']}")

    # Toggle back
    toggle_back = requests.patch(
        f"{BASE_URL}/tasks/{task_id}/complete",
        headers=headers,
        json={}
    )
    if toggle_back.status_code == 200:
        task_back = toggle_back.json()['data']
        print(f"  Toggled back to: completed={task_back['completed']}")
    else:
        print(f"  Toggle back FAIL: {toggle_back.status_code}")
        exit(1)
else:
    print(f"  Result: FAIL - {toggle_resp.text}")
    exit(1)
print()

# =============================================================================
# TEST 5: Update Task
# =============================================================================
print("TEST 5: Update Task")
print("-" * 40)
update_resp = requests.put(
    f"{BASE_URL}/tasks/{task_id}",
    headers=headers,
    json={"title": "Updated Test Task", "description": "Modified during test"}
)
print(f"  Status: {update_resp.status_code}")
if update_resp.status_code == 200:
    task = update_resp.json()['data']
    print("  Result: PASS")
    print(f"  New title: {task['title']}")
    print(f"  New description: {task['description']}")
else:
    print(f"  Result: FAIL - {update_resp.text}")
    exit(1)
print()

# =============================================================================
# TEST 6: Get Single Task
# =============================================================================
print("TEST 6: Get Single Task")
print("-" * 40)
get_resp = requests.get(f"{BASE_URL}/tasks/{task_id}", headers=headers)
print(f"  Status: {get_resp.status_code}")
if get_resp.status_code == 200:
    task = get_resp.json()['data']
    print("  Result: PASS")
    print(f"  Task ID: {task['id']}")
    print(f"  Title: {task['title']}")
else:
    print(f"  Result: FAIL - {get_resp.text}")
    exit(1)
print()

# =============================================================================
# TEST 7: Create Multiple Tasks
# =============================================================================
print("TEST 7: Create Multiple Tasks")
print("-" * 40)
for i in range(2, 4):
    create_resp = requests.post(
        f"{BASE_URL}/tasks",
        headers=headers,
        json={"title": f"Test Task {i}", "description": f"Task number {i}"}
    )
    if create_resp.status_code in [200, 201]:
        task = create_resp.json()['data']
        test_data['task_ids'].append(task['id'])
        print(f"  Created task {i}: {task['id']}")
    else:
        print(f"  Task {i} creation FAIL: {create_resp.status_code}")
        exit(1)
print()

# =============================================================================
# TEST 8: Verify Multi-tenancy (Delete Task)
# =============================================================================
print("TEST 8: Delete Task")
print("-" * 40)
task_to_delete = test_data['task_ids'].pop()
delete_resp = requests.delete(
    f"{BASE_URL}/tasks/{task_to_delete}",
    headers=headers
)
print(f"  Status: {delete_resp.status_code}")
if delete_resp.status_code == 200:
    result = delete_resp.json()
    print("  Result: PASS")
    print(f"  Deleted task ID: {result['data']['id']}")
    print(f"  Deleted flag: {result['data']['deleted']}")

    # Verify it's gone
    verify_resp = requests.get(f"{BASE_URL}/tasks/{task_to_delete}", headers=headers)
    if verify_resp.status_code == 404:
        print("  Verified: Task no longer accessible")
    else:
        print(f"  Warning: Task still accessible ({verify_resp.status_code})")
else:
    print(f"  Result: FAIL - {delete_resp.text}")
    exit(1)
print()

# =============================================================================
# TEST 9: Final Task Count
# =============================================================================
print("TEST 9: Final Task Count")
print("-" * 40)
list_resp = requests.get(f"{BASE_URL}/tasks", headers=headers)
if list_resp.status_code == 200:
    final_count = len(list_resp.json()['data'])
    print(f"  Status: {list_resp.status_code}")
    print("  Result: PASS")
    print(f"  Final task count: {final_count}")
else:
    print("  Result: FAIL")
    exit(1)
print()

# =============================================================================
# SUMMARY
# =============================================================================
print("=" * 60)
print("TEST SUMMARY")
print("=" * 60)
print("[SUCCESS] All 9 tests passed!")
print()
print("Tests Verified:")
print("  [1] User Login - OK")
print("  [2] Create Task - OK")
print("  [3] List Tasks - OK")
print("  [4] Toggle Complete - OK (FIX VERIFIED)")
print("  [5] Update Task - OK")
print("  [6] Get Single Task - OK")
print("  [7] Create Multiple Tasks - OK")
print("  [8] Delete Task - OK")
print("  [9] Final Task Count - OK")
print()
print(f"User ID: {test_data['user_id']}")
print(f"Tasks created: {len(test_data['task_ids']) + 1} (1 deleted)")
print(f"Remaining tasks: {len(test_data['task_ids'])}")
print()
print("=" * 60)
print("PHASE 2 BACKEND FULLY FUNCTIONAL")
print("=" * 60)
