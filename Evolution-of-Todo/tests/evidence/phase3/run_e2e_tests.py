"""Phase 3 E2E Validation Tests"""
import requests
import json
import sqlite3
import os
from datetime import datetime

BASE_URL = 'http://localhost:8000/api/v1'
DB_PATH = 'phase-3-chatbot/backend/todo_app.db'

def print_header(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def print_test(name):
    print(f"\n--- {name} ---")

def get_db_tasks():
    """Query database directly"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT id, title, completed, priority, tags FROM tasks')
    rows = cur.fetchall()
    conn.close()
    return rows

def clean_db():
    """Clean tasks table"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('DELETE FROM tasks')
    conn.commit()
    conn.close()

def main():
    results = []

    print_header("PHASE 3 E2E VALIDATION")
    print(f"Timestamp: {datetime.now().isoformat()}")

    # Login
    login_resp = requests.post(f'{BASE_URL}/auth/login', json={
        'email': 'test_e2e_2@example.com',
        'password': 'TestPassword123!'
    })

    if login_resp.status_code != 200:
        print("LOGIN FAILED - Cannot proceed")
        return

    token = login_resp.json()['data']['token']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    print(f"Logged in successfully")

    # Clean database
    clean_db()
    print("Database cleaned")

    # ============================================
    # SCENARIO A: SINGLE OPERATIONS
    # ============================================
    print_header("SCENARIO A: SINGLE CRUD OPERATIONS")

    # TEST A1: Add task with high priority
    print_test("A1: Add high priority task")
    resp = requests.post(f'{BASE_URL}/tasks', headers=headers, json={
        'title': 'Buy Milk',
        'priority': 'high',
        'tags': ['shopping']
    })
    task_id = None
    if resp.status_code == 201:
        task_id = resp.json()['data']['id']
        db_tasks = get_db_tasks()
        passed = len(db_tasks) == 1 and db_tasks[0][3] == 'high'
        results.append(('A1', 'Add high priority task', passed))
        print(f"PASS: Task created with priority=high" if passed else "FAIL")
    else:
        results.append(('A1', 'Add high priority task', False))
        print(f"FAIL: {resp.status_code}")

    # TEST A2: Update task title
    print_test("A2: Update task title")
    if task_id:
        resp = requests.put(f'{BASE_URL}/tasks/{task_id}', headers=headers, json={
            'title': 'Buy Groceries'
        })
        if resp.status_code == 200:
            db_tasks = get_db_tasks()
            passed = db_tasks[0][1] == 'Buy Groceries'
            results.append(('A2', 'Update task title', passed))
            print(f"PASS: Title updated" if passed else "FAIL")
        else:
            results.append(('A2', 'Update task title', False))
            print(f"FAIL: {resp.status_code}")

    # TEST A3: Complete task
    print_test("A3: Complete task")
    if task_id:
        resp = requests.patch(f'{BASE_URL}/tasks/{task_id}/complete', headers=headers)
        if resp.status_code == 200:
            db_tasks = get_db_tasks()
            passed = db_tasks[0][2] == 1  # completed = True
            results.append(('A3', 'Complete task', passed))
            print(f"PASS: Task completed" if passed else "FAIL")
        else:
            results.append(('A3', 'Complete task', False))

    # TEST A4: Mark as pending
    print_test("A4: Mark as pending")
    if task_id:
        resp = requests.patch(f'{BASE_URL}/tasks/{task_id}/complete', headers=headers)
        if resp.status_code == 200:
            db_tasks = get_db_tasks()
            passed = db_tasks[0][2] == 0  # completed = False
            results.append(('A4', 'Mark as pending', passed))
            print(f"PASS: Task marked pending" if passed else "FAIL")
        else:
            results.append(('A4', 'Mark as pending', False))

    # TEST A5: Delete task
    print_test("A5: Delete task")
    if task_id:
        resp = requests.delete(f'{BASE_URL}/tasks/{task_id}', headers=headers)
        if resp.status_code == 200:
            db_tasks = get_db_tasks()
            passed = len(db_tasks) == 0
            results.append(('A5', 'Delete task', passed))
            print(f"PASS: Task deleted" if passed else "FAIL")
        else:
            results.append(('A5', 'Delete task', False))

    # ============================================
    # SCENARIO B: BULK OPERATIONS
    # ============================================
    print_header("SCENARIO B: BULK OPERATIONS")

    # TEST B1: Bulk add
    print_test("B1: Bulk add 3 tasks with different priorities")
    tasks_to_create = [
        {'title': 'Write Code', 'priority': 'high', 'tags': ['work']},
        {'title': 'Review PR', 'priority': 'medium', 'tags': ['work']},
        {'title': 'Deploy App', 'priority': 'low', 'tags': ['devops']}
    ]
    for t in tasks_to_create:
        requests.post(f'{BASE_URL}/tasks', headers=headers, json=t)
    db_tasks = get_db_tasks()
    passed = len(db_tasks) == 3
    results.append(('B1', 'Bulk add 3 tasks', passed))
    print(f"PASS: {len(db_tasks)} tasks created" if passed else f"FAIL: {len(db_tasks)} tasks")

    # Verify priorities
    priorities = [t[3] for t in db_tasks]
    has_all_priorities = 'high' in priorities and 'medium' in priorities and 'low' in priorities
    print(f"  Priorities: {priorities} - {'CORRECT' if has_all_priorities else 'MISSING'}")

    # TEST B2: List with filter (via list endpoint)
    print_test("B2: List tasks (all)")
    resp = requests.get(f'{BASE_URL}/tasks', headers=headers)
    if resp.status_code == 200:
        tasks = resp.json()['data']
        passed = len(tasks) == 3
        results.append(('B2', 'List all tasks', passed))
        print(f"PASS: {len(tasks)} tasks returned" if passed else "FAIL")
        for t in tasks:
            print(f"  - {t['title']} | {t['priority']} | {t['tags']}")

    # TEST B3: Update all tasks to high priority
    print_test("B3: Update all tasks to HIGH priority")
    for task in get_db_tasks():
        task_id = task[0]
        requests.put(f'{BASE_URL}/tasks/{task_id}', headers=headers, json={'priority': 'high'})
    db_tasks = get_db_tasks()
    all_high = all(t[3] == 'high' for t in db_tasks)
    results.append(('B3', 'Update all to high priority', all_high))
    print(f"PASS: All tasks are high priority" if all_high else "FAIL")

    # TEST B4: Delete all tasks
    print_test("B4: Delete all tasks")
    for task in get_db_tasks():
        requests.delete(f'{BASE_URL}/tasks/{task[0]}', headers=headers)
    db_tasks = get_db_tasks()
    passed = len(db_tasks) == 0
    results.append(('B4', 'Delete all tasks', passed))
    print(f"PASS: All tasks deleted" if passed else f"FAIL: {len(db_tasks)} remaining")

    # ============================================
    # SCENARIO C: EDGE CASES
    # ============================================
    print_header("SCENARIO C: EDGE CASES")

    # TEST C1: Invalid priority
    print_test("C1: Create task with invalid priority")
    resp = requests.post(f'{BASE_URL}/tasks', headers=headers, json={
        'title': 'Test Task',
        'priority': 'superduper'  # Invalid
    })
    # Should either fail validation or default to medium
    passed = resp.status_code in [422, 400]  # Validation error expected
    results.append(('C1', 'Invalid priority handling', passed))
    print(f"PASS: Rejected with {resp.status_code}" if passed else f"FAIL: {resp.status_code}")

    # TEST C2: Empty search (no matching tasks)
    print_test("C2: Search for non-existent tasks")
    # Since REST search endpoint doesn't exist, test via list and client-side filter
    clean_db()
    resp = requests.get(f'{BASE_URL}/tasks', headers=headers)
    tasks = resp.json()['data']
    passed = len(tasks) == 0
    results.append(('C2', 'Empty task list', passed))
    print(f"PASS: No tasks returned" if passed else "FAIL")

    # ============================================
    # SUMMARY
    # ============================================
    print_header("TEST SUMMARY")

    passed_count = sum(1 for r in results if r[2])
    total_count = len(results)

    print(f"\nTotal Tests: {total_count}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {total_count - passed_count}")
    print(f"Success Rate: {(passed_count/total_count)*100:.1f}%")

    print("\nDetailed Results:")
    print("-" * 50)
    for test_id, test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {test_id}: {test_name} - {status}")

    print("\n" + "=" * 60)
    if passed_count == total_count:
        print("ALL TESTS PASSED")
    else:
        print(f"SOME TESTS FAILED ({total_count - passed_count})")
    print("=" * 60)

if __name__ == '__main__':
    main()
