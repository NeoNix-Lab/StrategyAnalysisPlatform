from src.database.connection import init_db
import os

def main():
    print("Avvio Strategy Analysis Platform...")
    
    # 1. Inizializza Database
    init_db()
    
    print("Setup completato. Il database è pronto per ricevere dati.")

if __name__ == "__main__":
    main()
