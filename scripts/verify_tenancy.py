import httpx
import uuid

BASE_URL = "http://localhost:8000/api"

def get_auth_token(email, password):
    try:
        data = {
            "username": email,
            "password": password
        }
        # Assuming URL encoded login form
        response = httpx.post(f"{BASE_URL}/auth/token", data=data, timeout=30.0)
        if response.status_code == 200:
            return response.json()["access_token"]
        elif response.status_code == 404:
             # Try /auth/login as seen in some routers or /token
             response = httpx.post(f"{BASE_URL}/auth/login", data=data, timeout=30.0) 
             if response.status_code == 200:
                 return response.json()["access_token"]
        
        print(f"Login failed for {email}: {response.status_code} {response.text}")
        return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

def register_user(email, password):
    try:
        payload = {"email": email, "password": password}
        response = httpx.post(f"{BASE_URL}/auth/register", json=payload, timeout=30.0)
        if response.status_code in [200, 201]:
            print(f"Registered {email}")
            return True
        elif response.status_code == 400 and "already registered" in response.text:
            print(f"User {email} exists")
            return True
        else:
            print(f"Registration failed for {email}: {response.status_code} {response.text}")
            return False
    except Exception as e:
        print(f"Register error: {e}")
        return False

def verify_tenancy():
    print("--- Setting up Users ---")
    email_a = f"tenantA_{uuid.uuid4().hex[:6]}@test.com"
    email_b = f"tenantB_{uuid.uuid4().hex[:6]}@test.com"
    password = "password123"
    
    register_user(email_a, password)
    register_user(email_b, password)
    
    token_a = get_auth_token(email_a, password)
    token_b = get_auth_token(email_b, password)
    
    if not token_a or not token_b:
        print("Failed to get tokens. Aborting.")
        return

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    print("\n--- Testing Strategy Isolation ---")
    
    run_req = {
        "strategy_id": f"strat_A_{uuid.uuid4().hex[:6]}",
        "parameters": {},
        "run_type": "BACKTEST"
    }
    
    print(f"User A creating strategy {run_req['strategy_id']}...")
    res = httpx.post(f"{BASE_URL}/runs/start", json=run_req, headers=headers_a, timeout=30.0)
    if res.status_code != 200:
        print(f"Failed to start run/create strat: {res.status_code} {res.text}")
    else:
        print("Strategy A created.")
        
    # Check List
    print("User A listing strategies...")
    res_a = httpx.get(f"{BASE_URL}/strategies/", headers=headers_a, timeout=30.0)
    strats_a = res_a.json()
    ids_a = [s['strategy_id'] for s in strats_a]
    print(f"User A sees: {ids_a}")
    
    if run_req['strategy_id'] not in ids_a:
        print("FAIL: User A cannot see own strategy!")
    else:
        print("SUCCESS: User A sees own strategy.")
        
    print("User B listing strategies...")
    res_b = httpx.get(f"{BASE_URL}/strategies/", headers=headers_b, timeout=30.0)
    strats_b = res_b.json()
    ids_b = [s['strategy_id'] for s in strats_b]
    print(f"User B sees: {ids_b}")
    
    if run_req['strategy_id'] in ids_b:
        print("FAIL: User B CAN see User A's strategy!")
    else:
        print("SUCCESS: User B does NOT see User A's strategy.")
        
    # Direct Access Check
    print(f"User B trying to GET strategy {run_req['strategy_id']}...")
    res_fail = httpx.get(f"{BASE_URL}/strategies/{run_req['strategy_id']}", headers=headers_b, timeout=30.0)
    if res_fail.status_code in [403, 404]: 
        print(f"SUCCESS: User B blocked (Status {res_fail.status_code})")
    else:
        print(f"FAIL: User B accessed User A's strategy! (Status {res_fail.status_code})")
        
    print("\n--- Testing ML Process Isolation ---")
    proc_req = {
        "name": f"Proc_A_{uuid.uuid4().hex[:6]}",
        "description": "User A process"
    }
    print(f"User A creating ML Process {proc_req['name']}...")
    res = httpx.post(f"{BASE_URL}/ml/studio/processes", json=proc_req, headers=headers_a, timeout=30.0)
    if res.status_code != 200:
        print(f"Failed to create proc: {res.status_code} {res.text}")
    else:
        proc_id = res.json().get("process_id")
        print(f"Process created: {proc_id}")
        
        print("User B listing Processes...")
        res_b = httpx.get(f"{BASE_URL}/ml/studio/processes", headers=headers_b, timeout=30.0)
        procs_b = res_b.json()
        ids_b = [p['process_id'] for p in procs_b]
        
        if proc_id in ids_b:
             print("FAIL: User B CAN see User A's process!")
        else:
             print("SUCCESS: User B does NOT see User A's process.")


if __name__ == "__main__":
    verify_tenancy()
