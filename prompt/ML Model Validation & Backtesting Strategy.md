ML Model Validation & Backtesting Strategy
1. Visione Generale
L'obiettivo di questa fase è trasformare il sottosistema di Machine Learning da "scatola nera di addestramento" a strumento di ricerca quantitativa rigoroso. Non è sufficiente addestrare un modello; è necessario validarne le performance su dati mai visti ("Test Set") e proiettare i risultati in un formato standard (
StrategyRun
, Trades) compatibile con gli strumenti di analisi e visualizzazione della piattaforma (Trade Replayer, Performance Report).

2. Obiettivi Chiave
Rigore Scientifico (Data Partitioning): Garantire che la valutazione delle performance avvenga su dati distinti da quelli usati per l'addestramento, prevenendo il Look-ahead Bias e l'Overfitting illusorio.
Persistenza del Contesto: Salvare la configurazione esatta di partizionamento (Train/Val/Test) nel database per garantire la riproducibilità.
Compatibilità di Sistema: L'output di un test ML deve essere indistinguibile dall'output di una strategia algoritmica classica. Deve generare Barre, Ordini e Trade visualizzabili sul grafico.
Flusso Train -> Freeze -> Test: Implementare il ciclo di vita completo: Addestramento -> Congelamento Pesi -> Esecuzione Deterministica (Inferenza).
3. Analisi delle Difficoltà e Rischi
Incertezza Temporale del Dataset: I dataset ML attuali sono spesso matrici di feature pre-calcolate senza un chiaro riferimento temporale "continuo". Per il Replayer, è essenziale ricostruire la linea temporale esatta (ts_utc) per allineare i trade alle candele.
Discrepanza di Formato: Il training ML ottimizza una Reward Function astratta, mentre il backtest deve produrre Trade con Prezzi, Commissioni e PnL reali. L'
EnvFlex
 usa logiche semplificate che devono essere "indurite" per il backtest.
Gestione dello Stato: Durante il training, l'ambiente viene resettato (
reset()
) migliaia di volte (episodi). Nel backtest, l'esecuzione deve essere un unico "episodio" continuo sul Test Set, simulando un'operatività reale.
4. Architettura Concettuale
A. Gestione Partizionamento Dati
Non duplicheremo i dati fisici. Definiremo il partizionamento tramite metadati temporali o indici salvati nella configurazione dell'
MlIteration
 o della 
MlTrainingSession
.

Schema Configurazione Partitioning:
"split_config": {
    "method": "TIME_SERIES", // vs RANDOM (sconsigliato per time series)
    "train_range": {"start": "2023-01-01", "end": "2023-06-30"},
    "validation_range": {"start": "2023-07-01", "end": "2023-08-31"},
    "test_range": {"start": "2023-09-01", "end": "2023-12-31"}
}
B. Modalità Operative del Runner
Il 
TrainingRunner
 dovrà supportare due modalità distinte:

TRAIN_MODE:

Input: Train Set + Validation Set.
Logica: Esplorazione (epsilon > 0), aggiornamento pesi (Backprop), reset frequenti.
Output: File del Modello (.h5 / .pt), Logs di Loss/Reward. Nessun Trade su DB.
INFERENCE_MODE (Backtest):

Input: Test Set (o range Arbitrario) + Modello Addestrato (Frozen).
Logica: Nessuna esplorazione (epsilon = 0), Nessun learning. Esecuzione sequenziale unica.
Output: Record 
StrategyRun
, 
Order
, 
Trade
, 
Execution
 nel DB.
5. Piano d'Azione Dettagliato
Step 1: Database & Schema Update
Obiettivo: Predisporre il DB a salvare le configurazioni di split.
Azione: Verificare e formalizzare l'uso del campo split_config_json nella tabella ml_iterations o ml_training_sessions. Assicurarsi che la UI possa scriverci.
Step 2: UI Partitioning Controls
Obiettivo: Permettere all'utente di definire i range.
Azione:
Nel wizard di avvio Training, aggiungere un selettore di range (Date Picker o Slider percentuale).
Visualizzare graficamente come il dataset viene tagliato.
Step 3: Refactoring ML Core Runner
Obiettivo: Implementare la logica di INFERENCE_MODE.
Azione:
Modificare 
runner.py
 per accettare un flag 
mode
.
Implementare un TradeRecorder: una classe che si aggancia all'
EnvFlex
 o all'
FSMExecutionEngine
. Quando l'FSM genera un evento OPEN/CLOSE, il Recorder scrive immediatamente nel DB (quant_shared.models.Trade e 
Order
).
Assicurare che il Recorder linki i trade alla corretta run_id.
Step 4: Integrazione Backend-Frontend
Obiettivo: Chiudere il cerchio.
Azione:
Nell'API Gateway, l'endpoint di completamento training deve esporre l'ID della 
StrategyRun
 generata (se in backtest mode).
Nel Frontend, aggiungere un bottone "View Results on Chart" che naviga al Trade Replayer passando l'ID della run appena generata.
Step 5: Verifica Allineamento Dati
Obiettivo: Assicurare che il Replayer trovi le candele.
Azione:
Verificare che il 
Dataset
 ML mantenga il riferimento alla 
RunSeries
 originale (l'ID della serie di candele).
Se il Dataset è "sintetico" (solo feature engineerizzate), il sistema deve sapere quale SeriesID originale caricare sul grafico per sovrapporre i trade.