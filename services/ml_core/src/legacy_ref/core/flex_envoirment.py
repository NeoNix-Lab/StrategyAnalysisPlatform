from abc import abstractmethod
from turtle import done
from typing import Callable
import pandas as pd
from ctypes import Array
import gym as gym
from gym import spaces
import numpy as np
import copy
#from Models import logs_classes as lgc

class EnvFlex(gym.Env):

    def __init__(self, full_data:pd.DataFrame, reward_function: Callable, reward_colums:list[str], 
                 action_spaces_tab:pd.DataFrame, 
                 position_space_tab:pd.DataFrame,windows_size=20, fees=0.01, initial_balance = 100000, 
                 first_reword=0,use_additional_reward_colum:bool = False):
        # Chiamata al init di gym.env
        super(EnvFlex, self).__init__()

        # TODO : Validare i dati

        # Variabili Immutate
        self.last_qty_both = 0
        self.fees = fees
        self.current_step = 0
        self.done = False
        self.window_size = windows_size
        self.window = []
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        # Full data need to include min e max val
        self.data = full_data
        self.position_tab = position_space_tab
        self.last_position_status = 0
        self.last_action = 0
        self.last_Reward = first_reword
        self.current_price = None
        self.first_reword = first_reword
        self.action_space_tab = action_spaces_tab
        self.use_additional_reward = use_additional_reward_colum

        # Variabili di flessibilita 
        self.reward_colum = reward_colums
        self.Obseravtion_DataFrame = self.set_DF_Obs()
        # HINT: takes a int will be one hot encoded with dtype int8
        self.SetAction_Space() 
        # HINT: takes a pd.Dataframe ['Val']['MinVal]['MaxVal'] will be one hot encoded with dtype float64
        self.reward_function = reward_function
        self.SetObservation_Space()
        #self.reset()

    #@abstractmethod TODO: Commentato momentaneamnete per accedere al metodo tramite la classe
    def Endcode(self, enc_list, convert_val=0):
        """
        Restituisce un DataFrame one-hot, l'array selezionato e la label.

        enc_list: lista di etichette, es. ['wait','buy','sell']
        convert_val: indice (int) o etichetta (str)
        """
        n = len(enc_list)
        # 1) DF one-hot n×n: righe 0..n-1, colonne enc_list
        dic = pd.DataFrame(
            data = np.eye(n, dtype=int),
            columns = enc_list,
            index   = range(n)
        )

        # 2) Seleziona in base al tipo di convert_val
        if isinstance(convert_val, int):
            idx = convert_val
            selected_array = dic.iloc[idx].to_numpy()
            selected_name  = enc_list[idx]
            selected_index = idx

        elif isinstance(convert_val, str):
            selected_array = dic[convert_val].to_numpy()
            selected_index = enc_list.index(convert_val)
            selected_name  = convert_val

        else:
            raise ValueError(f"Tipo non supportato: {type(convert_val)}")

        return dic, selected_array, selected_name, selected_index
        
    def reset(self) :
        self.Obseravtion_DataFrame = None
        self.set_DF_Obs()
        #HINT: steps for Windows_size
        self.current_step = 0
        self.done = False
        self.current_balance = self.initial_balance

        _, _, first_action, _ = self.Endcode(self.action_space_tab, 0)
        _, _, first_position, _ = self.Endcode(self.position_tab, 0)

        # self explanatory iterato per la lunghezza della finestra
        for i in range(self.window_size):

            self.Obseravtion_DataFrame.iloc[self.current_step, 'step'] = self.current_step
            self.Obseravtion_DataFrame.iloc[self.current_step, 'balance'] = self.current_balance
            self.Obseravtion_DataFrame.iloc[self.current_step, 'action'] = first_action
            self.last_action = first_action
            self.Obseravtion_DataFrame.iloc[self.current_step, 'position_status'] = first_position
            self.last_position_status = first_position
            self.Obseravtion_DataFrame.iloc[self.current_step, 'reword'] = self.first_reword


            self.current_step = self.current_step+1

        self.window = self.set_Wind()

        return copy.deepcopy(self.window) , copy.deepcopy(self.last_Reward), copy.deepcopy(self.done), copy.deepcopy(self.Obseravtion_DataFrame)

    def step(self, action) :

        if self.done:
            return

        # TODO: Autoconversione di action 
        print(f'@@@@@@@@@@@@ current env _step{self.current_step}')
        print(f'@@@@@@@@@@@@ env len(self.data.index)-1{len(self.data.index)-1}')

        if self.current_step == len(self.data.index)-1:
            self.done = True
            self.done = True

        # TODO : funzione di forzatura chiusura posizioni E da spostare
        _, act_array, act_name, act_index = self.Endcode(self.action_space_tab, action)
        self.last_action = act_name

        _, pos_array, poss_name, poss_index = self.Endcode(self.position_tab, self.last_position_status)

        print(f'@@@@@@@@@@@@ current env poss_name {poss_name}')


        if self.done:
            if poss_name == 'long' or poss_name == 1:
                action = 2
            elif poss_name == 'short' or poss_name == 2:
                action = 1

        # TODO: azioni obbligate

        # TODO : sistema di ritorno
        # TODO: dubbi riguardo l'ordine del processo

        # HACK: ho rimosso il parametro self in quanto dovrebbe essere gia espresso nella dichiarazione self        self.reward_function(action)
        #self.window = self.set_Wind()
        self.updatewind()

        self.reward_function(self,action)
        print(f'@@@@@@@@@@@@ env reward {self.last_Reward}')


        self.current_step = self.current_step+1

        return copy.deepcopy(self.window) , copy.deepcopy(self.last_Reward), copy.deepcopy(self.done), copy.deepcopy(self.Obseravtion_DataFrame)

    # HACK: Metodi Ausiliari
    def set_DF_Obs(self):
        lengh = len(self.data.iloc[:,0])

        self.Obseravtion_DataFrame = copy.deepcopy(self.data)

        if self.use_additional_reward:
            for i in range(len(self.reward_colum)):

                new_df = pd.DataFrame({
                    f'{self.reward_colum[i]}' : np.zeros(lengh)})

                self.Obseravtion_DataFrame = pd.concat([self.Obseravtion_DataFrame, new_df], axis=1)


        classic_DF = pd.DataFrame({
            'step': np.zeros(lengh),
            'balance': np.zeros(lengh),
            'action': np.zeros(lengh),
            'reword': np.zeros(lengh),
            'position_status': np.zeros(lengh)})

        return pd.concat([self.Obseravtion_DataFrame, classic_DF], axis=1)

    # TODO: funzione d'aggiornamento della finestra
    def updatewind(self):
        basicbar = self.data.iloc[self.current_step]

        # TODO: ottenere il valore one hot encoding
        pos_status = self.Obseravtion_DataFrame['position_status'].iloc[self.current_step]
        #conversione in indice
        #_,_,name_val, index = EnvFlex.Endcode(self.position_tab, pos_status)

        #ripeto la creazione e concatenazione
        for colum in self.position_tab:
            if colum == pos_status:
                basicbar[colum] = 1
            else:
                basicbar[colum] = 0

        self.window = self.window.drop(self.window.index[0])
        self.window.loc[self.current_step] = basicbar # iloc[len(self.window)] = basicbar #concat([self.window,basicbar] ,axis=0)

    # Setta La Finestra Iniziale
    # TODO : possibilita di aggiungere nuovi par alla finestra
    # TODO : e sbagliata la codifica di action e status
    def set_Wind(self):

        minimo = self.current_step-self.window_size
        massimo = self.current_step

        datfram = self.data.iloc[minimo : massimo]

        pos_status = self.Obseravtion_DataFrame['position_status'].iloc[minimo : massimo]

        #TODO : tento di restituire schema one hot
        for colum in self.position_tab:

            if colum == self.position_tab[0]:
                serie = pd.DataFrame({
                    f'{colum}' : np.ones(datfram.shape[0])})
            else:
                serie = pd.DataFrame({
                f'{colum}' : np.zeros(datfram.shape[0])})
            
            datfram = pd.concat([datfram, serie], axis=1)
        

        #for i in range(len(pos_status)):
        #    _, newval, name, index = EnvFlex.Endcode(self.position_tab, pos_status.iloc[i])
        #    pos_status.iloc[i] =  name 

        return datfram#pd.concat([ datfram, copy.copy(pos_status)], axis=1 )

    def SetAction_Space(self):
        lenght = len(self.action_space_tab)

        self.action_space = spaces.Box(low=np.zeros(lenght), high=np.ones(lenght), dtype=np.int8)
    
    # Setto lo spazio delle osservazioni dal numero inizializzero in seguito il df per tenerne traccia aggiungo il current_step e balance
    # TODO: i min e max value sono indefiniti e manca la logica tabulare per definirli  .... completamente da rifare
    def SetObservation_Space(self):
        lenght = len(self.action_space_tab)

        self.observation_space = spaces.Box(low=np.zeros(lenght), high=np.ones(lenght), dtype=np.int8)

        # infine concatenero osservazioni Azioni e risultati

    

    def render(self):
        return copy.deepcopy(self.Obseravtion_DataFrame)

    @abstractmethod
    def calculatefees(self):
        return self.current_balance * self.fees
    
    def coutobservationVar(self):
        return len(self.window.columns)

    def coutnaction(self):
        return len(self.action_space_tab)
