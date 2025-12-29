from rl_rnn_core.core.mod_esecutor_refactored import EnvFlex
def flex_buy_andSell(env: EnvFlex, price_column_name: str, action: str):
    price = env.Obseravtion_DataFrame.loc[env.current_step, price_column_name]
    fees = env.calculatefees()  # TODO: applicare effettivamente fees al guadagno

    if action_name == 'wait':
        env.last_Reward = 0

    elif action_name == 'buy':
        if statuscode in ('flat', 0):
            env.last_qty_both = env.current_balance / price
            env.last_Reward = 0
            env.last_position_status = 'long'
        elif statuscode in ('short', 2):
            gain = (env.last_qty_both * price) - env.current_balance - fees
            env.last_Reward = gain
            env.current_balance += gain
            env.last_position_status = 'flat'
            env.last_qty_both = 0
        else:  # già long
            env.last_Reward = 0

    elif action_name == 'sell':
        if statuscode in ('flat', 0):
            env.last_Reward = 0
            env.last_qty_both = env.current_balance / price
            env.last_position_status = 'short'
        elif statuscode in ('long', 1):
            gain = (env.last_qty_both * price) - env.current_balance - fees
            env.last_Reward = gain
            env.current_balance += gain
            env.last_position_status = 'flat'
            env.last_qty_both = 0
        else:  # già short
            env.last_Reward = 0

    if env.current_balance <= 0:
        env.done = True


def fillTab(env):
    step = env.current_step
    df = env.Obseravtion_DataFrame
    df.loc[step, 'position_status'] = env.last_position_status
    df.loc[step, 'step'] = step
    df.loc[step, 'action'] = env.last_action
    df.loc[step, 'balance'] = env.current_balance
    df.loc[step, 'reword'] = env.last_Reward  # mantenuto refuso per compatibilità


def premia(env, action):
    env.last_action = action
    flex_buy_andSell(env, price_column_name='Price', action=action)
    fillTab(env)
