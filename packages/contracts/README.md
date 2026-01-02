# API Contracts

Questa directory contiene le definizioni JSON Schema per tutti i contratti API nella Strategy Analysis Platform, organizzati per microservizio.

## Struttura

### API Gateway
- `api_gateway/common.json` - Tipi condivisi e schemi di base
- `api_gateway/user.json` - Schemi per la gestione degli utenti
- `api_gateway/strategy.json` - Schemi per la gestione delle strategie
- `api_gateway/trading.json` - Schemi per le operazioni di trading
- `api_gateway/market_data.json` - Schemi per i dati di mercato

### ML Core
- `ml_core/dataset.json` - Schemi per la gestione dei dataset
- `ml_core/ml_training.json` - Schemi per l'addestramento ML

## Nota

Il file `api_contracts.json` rimane come schema monolitico “storico”. I file nelle sottocartelle sono la versione modulare per microservizio.
