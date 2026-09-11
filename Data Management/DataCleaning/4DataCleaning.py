import os
import pandas as pd
from pandas.core.frame import DataFrame

"""
========================================================================================
FILE: 4DataCleaning.py

OBIETTIVO: 
Effettuare l'ispezione temporale e la risoluzione dei gap intra-day.
Usa una logica a "Reindex per Blocchi": identifica i macro-gap (weekend, festività, 
chiusure > 12h) e li usa come punti di taglio. Reindicizza solo i segmenti attivi di mercato.
I micro-gap interni vengono riempiti tramite propagazione dell'ultimo prezzo di chiusura 
(Flat Doji a zero spread e zero volume) per azzerare il Data Leakage da interpolazione.

FUNZIONAMENTO:
- Carica il dataset unificato.
- Unisce Date e Time in un unico oggetto Datetime e ordina cronologicamente.
- Calcola le differenze temporali (diff) tra i tick.
- Isola i gap anomali e calcola l'incidenza di weekend e festività.
- Effettua un 'reindex' forzando la creazione di una riga per ogni minuto assoluto.
- Risolve i valori NaN generati dal reindex:
    * Gap < 5 min: Interpolazione lineare.
    * 5 min <= Gap < 1 giorno: Forward Fill (mantiene l'ultimo prezzo noto).
    * Gap >= 1 giorno: Lasciati a NaN (contrassegnati da colonna "Missing").

INPUT:  Processed_Data/3FixedData.csv (o 3FixedAskData.csv)
OUTPUT: Processed_Data/gap_temporali.csv (Report log)
        Processed_Data/FinalData.csv     (Dataset espanso e pulito)
=========================================================================================
"""

pd.set_option("display.max_rows", None)

# Configurazione dinamica dei percorsi
script_dir = os.path.dirname(os.path.abspath(__file__))
input_file = os.path.join(script_dir, 'Processed_Data', '3FixedData.csv')
output_gap = os.path.join(script_dir, 'Processed_Data', 'gap_temporali.csv')
output_file = os.path.join(script_dir, 'Processed_Data', 'FinalData.csv')
ready_data_dir = os.path.join(script_dir, '..', 'ReadyData')
os.makedirs(ready_data_dir, exist_ok=True) # Crea la cartella se non esiste
final_output_file = os.path.join(ready_data_dir, 'XAUUSD_ReadyToUse.csv')

def create_csv() -> DataFrame:
    df = pd.read_csv(input_file)
    print(f"Dataset Iniziale -> Colonne: {len(df.columns)} | Righe: {len(df)}")
    
    # Creazione indice temporale cronologico
    df["Datetime"] = pd.to_datetime(df["Date"] + " " + df["Time"], format="%Y.%m.%d %H:%M")
    df = df.sort_values(by="Datetime").reset_index(drop=True)

    return df

def temporal_gap_resolution(df: DataFrame) -> DataFrame:
    print("\nAvvio Taglio a Blocchi e Risoluzione Micro-Gap (Flat Doji)...")

    # 1. IDENTIFICAZIONE DEI BLOCCHI DI TRADING (Taglio su Gap > 12 ore)
    df['TimeDiff'] = df['Datetime'].diff()
    
    # Crea un ID incrementale ogni volta che c'è un gap > 12 ore (Weekend o Festività)
    # La prima riga è NaT, quindi si inizia da Block_ID = 0
    df['Block_ID'] = (df['TimeDiff'] > pd.Timedelta(hours=12)).cumsum()
    
    tot_blocks = df['Block_ID'].nunique()
    print(f"Mercato segmentato in {tot_blocks} blocchi operativi continui (esclusi weekend/festività).")

    processed_blocks = []
    
    # 2. REINDEX E FLAT DOJI PER SINGOLO BLOCCO
    for block_id, block_df in df.groupby('Block_ID'):
        block_start = block_df['Datetime'].min()
        block_end = block_df['Datetime'].max()
        
        # Genera il calendario ideale SOLO per la durata di questa specifica settimana/sessione
        block_range = pd.date_range(start=block_start, end=block_end, freq='min')
        
        # Allinea i dati al calendario del blocco
        block_full = block_df.set_index('Datetime').reindex(block_range)
        block_full.index.name = 'Datetime'
        
        # Identifica i minuti vuoti appena creati
        is_missing = block_full['Close'].isna()
        
        # Estrae l'ultimo prezzo di chiusura valido noto (Forward Fill)
        last_close = block_full['Close'].ffill()
        
        # FLAT DOJI FILL: Assegna a OHLC esattamente l'ultimo prezzo di chiusura
        block_full.loc[is_missing, 'Open'] = last_close[is_missing]
        block_full.loc[is_missing, 'High'] = last_close[is_missing]
        block_full.loc[is_missing, 'Low'] = last_close[is_missing]
        block_full.loc[is_missing, 'Close'] = last_close[is_missing]
        
        # Setta il volume a 0 per i minuti senza scambi reali
        block_full.loc[is_missing, 'TotalTicks'] = 0.0
        
        # Arrotondamento a 2 decimali per omogeneità strutturale (XAUUSD = centesimi)
        price_cols = ['Open', 'High', 'Low', 'Close']
        block_full[price_cols] = block_full[price_cols].round(2)
        
        # Marca le righe iniettate (Utile per tracciare i micro-gap, ma non causeranno spike nel backtest)
        block_full['Missing'] = is_missing
        
        processed_blocks.append(block_full)

    # 3. RICOMPOSIZIONE DEL DATASET
    df_final = pd.concat(processed_blocks)
    
    # Ricostruzione per retrocompatibilità formativa
    df_final["Date"] = df_final.index.strftime("%Y.%m.%d")
    df_final["Time"] = df_final.index.strftime("%H:%M")

    return df_final

def finalize_and_export(df_full: DataFrame):
    print("\nAvvio fase di formattazione ed esportazione...")
    # Drop delle colonne ausiliarie utilizzate per l'elaborazione logica
    cols_to_drop = ["TimeDiff", "Block_ID"]
    df_full = df_full.drop(columns=[c for c in cols_to_drop if c in df_full.columns])

    df_full.to_csv(output_file, index=True)
    
    # Estrazione finalizzata
    df_ready = df_full.drop(columns=["Date", "Time"]).reset_index()
    df_ready.to_csv(final_output_file, index=False)
    print(f"Dataset finale salvato: {final_output_file}")

def compare_df():
    df_start = pd.read_csv(input_file)
    df_final = pd.read_csv(output_file)
    
    print("\n================ CONFRONTO FINALE ================")
    print(f"Righe Originali (Raw Data)      : {len(df_start)}")
    print(f"Righe Finali (Trading Time)     : {len(df_final)}")
    print(f"Micro-gap intra-day colmati     : {len(df_final) - len(df_start)}")
    print("==================================================\n")

def temporal_holes_management():
    df = create_csv()
    df_resolved = temporal_gap_resolution(df)
    finalize_and_export(df_resolved)
    compare_df()

if __name__ == "__main__":
    temporal_holes_management()