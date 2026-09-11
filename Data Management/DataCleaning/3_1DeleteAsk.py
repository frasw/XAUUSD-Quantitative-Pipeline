import csv
import os

"""
=========================================================================================
FILE: 3_1DeleteAsk.py (Bid-Only Extraction)

OBIETTIVO: 
Filtrare il dataset mantenendo esclusivamente i prezzi Bid e scartando i prezzi Ask.
Formatta le colonne temporali per standardizzarle (YYYY.MM.DD e HH:MM) mantenendo
la compatibilità visiva e strutturale con l'ambiente MetaTrader.

FUNZIONAMENTO:
- Legge il file a 11 colonne generato nello Step 2.
- Sostituisce l'intestazione con una nuova a 7 colonne (OHLC Bid + TotalTicks).
- Converte la data dal formato "MM/DD/YYYY" a "YYYY.MM.DD".
- Tronca l'orario da "HH:MM:SS" a "HH:MM".
- Estrae solo OpenBid, HighBid, LowBid e CloseBid, formattandoli a 2 decimali.
- Recupera il volume (TotalTicks) dall'indice corretto.

INPUT:  Processed_Data/2DataMerged.csv
OUTPUT: Processed_Data/3FixedAskData.csv
=========================================================================================
"""

# Costruzione dinamica dei percorsi relativi
script_dir = os.path.dirname(os.path.abspath(__file__))
input_file = os.path.join(script_dir, 'Processed_Data', '2DataMerged.csv') # File a 11 colonne (il file ottenuto dal precedente merging)
output_file = os.path.join(script_dir, 'Processed_Data', '3FixedAskData.csv') # File finale con le colonne trasformate

# Definizione esplicita dell'intestazione finale pulita con valori univoci (Bid) del prezzo
HEADER = ["Date", "Time", "Open", "High", "Low", "Close", "TotalTicks"]

with open(input_file, newline='', encoding='utf-8') as fin, \
     open(output_file, 'w', newline='', encoding='utf-8') as fout:
    
    reader = csv.reader(fin, delimiter=',')
    writer = csv.writer(fout, delimiter=',')

    for row_index, row in enumerate(reader):
        # Riconoscimento della riga header:
        # Se la riga è la prima oppure uno dei campi contiene la stringa "bid" (case-insensitive)
        # viene considerata header e viene sostituita con quella desiderata.
        if row_index == 0 or any("bid" in cell.lower() for cell in row):
            writer.writerow(HEADER)
            continue

        # --- Conversione della Data ---
        # Dal formato "MM/DD/YYYY" al formato "YYYY.MM.DD"
        old_date = row[0]
        try:
            month, day, year = old_date.split('/') # Assume formato in input "MM/DD/YYYY"
            new_date = f"{year}.{int(month):02d}.{int(day):02d}"
        except Exception:
            new_date = old_date  # Se il formato non è come atteso, si lascia invariato

        if len(row) > 10:
            # --- Conversione della Time ---
            # Da "HH:MM:SS" a "HH:MM"
            old_time = row[1]
            new_time = old_time[:5]

            # Sostituzione delle ',' con i '.' e formattazione a due cifre decimali
            open_bid = f"{float(row[2].replace(',', '.')):.2f}"
            high_bid = f"{float(row[3].replace(',', '.')):.2f}"
            low_bid = f"{float(row[4].replace(',', '.')):.2f}"
            close_bid = f"{float(row[5].replace(',', '.')):.2f}"

            # Recupero corretto di TotalTicks all'indice 10
            total_ticks = row[10]

            # --- Costruzione della nuova riga ---
            new_row = [new_date, new_time, open_bid, high_bid, low_bid, close_bid, total_ticks]
            writer.writerow(new_row)
            
print("File 3_1DeleteAsk.py eseguito con successo! Dati Bid estratti e formattati.")