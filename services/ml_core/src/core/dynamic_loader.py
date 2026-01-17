from typing import Callable, Any, Dict, List
import pandas as pd
import numpy as np

class DynamicRewardLoader:
    """
    Safely compiles and loads user-defined Python reward functions.
    Provides necessary namespaces and context variables.
    """
    
    @staticmethod
    def load_reward_function(code: str, action_labels: List[str], status_labels: List[str]) -> Callable:
        """
        Compiles the string code into a callable function.
        
        Args:
            code: The Python source code (must define `calculate_reward(env, action)` or result variable).
            action_labels: List of action names for namespace injection.
            status_labels: List of status names for namespace injection.
            
        Returns:
            A function with signature `fn(env, action) -> float`
        """
        
        # 1. Create Namespaces
        class Namespace: pass
        
        actions_ns = Namespace()
        for idx, label in enumerate(action_labels):
            setattr(actions_ns, label.upper(), idx)
            
        status_ns = Namespace()
        for idx, label in enumerate(status_labels):
            setattr(status_ns, label.upper(), idx)
            
        # 2. Define Wrapper
        def wrapped_reward_fn(env, action: int) -> float:
            # Inject dynamic namespaces into env if not already present
            # (Though ideally EnvFlex should have them, this ensures safety)
            if not hasattr(env, 'actions'):
                env.actions = actions_ns
            if not hasattr(env, 'status'):
                env.status = status_ns
                
            # Prepare Local Scope
            local_scope = {
                "env": env,
                "action": action,
                "np": np,
                "pd": pd,
                "math": __import__('math')
            }
            
            try:
                exec(code, {}, local_scope)
                
                # Check for return via function or variable
                if "calculate_reward" in local_scope and callable(local_scope["calculate_reward"]):
                    return float(local_scope["calculate_reward"](env, action))
                elif "reward" in local_scope:
                    return float(local_scope["reward"])
                else:
                    # No result found, return 0.0 (or log warning)
                    return 0.0
            except Exception as e:
                # In training, we might not want to crash, but returning 0 is safe
                # print(f"Reward Error: {e}") 
                return 0.0

        return wrapped_reward_fn
