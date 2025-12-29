from src.database.connection import get_db
from src.database.models import Order, Execution

def check_integrity():
    db = next(get_db())
    print("Checking Data Integrity...")
    
    orders = db.query(Order).all()
    executions = db.query(Execution).all()
    
    print(f"Total Orders: {len(orders)}")
    print(f"Total Executions: {len(executions)}")
    
    if not executions:
        print("No executions found.")
        return

    # Check linkage
    linked_count = 0
    
    order_ids = {o.order_id for o in orders}
    
    for exc in executions:
        if exc.order_id in order_ids:
            linked_count += 1
        else:
            print(f"WARNING: Execution {exc.execution_id} references missing order_id: {exc.order_id}")
            
    print(f"Executions with valid Order linkage: {linked_count}/{len(executions)}")

if __name__ == "__main__":
    check_integrity()
