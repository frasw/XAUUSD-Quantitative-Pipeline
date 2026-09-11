import csv
import os

"""
=========================================================================================
FILE: 3DoMedian.py (Mid-Price Calculation)

OBIETTIVO: 
Semplificare il dataset passando da una doppia quotazione (Bid/Ask) a una singola 
quotazione rappresentativa (Mid-Price o Prezzo Medio). 
Inoltre, formatta le colonne temporali per standardizzarle e mantenere la compatibilità 
con i formati MetaTrader.

FUNZIONAMENTO:
- Legge il file a 11 colonne generato nello Step 2.
- Sostituisce l'intestazione con una nuova a 7 colonne (OHLC unificato).
- Converte la data dal formato "MM/DD/YYYY" a "YYYY.MM.DD".
- Tronca l'orario da "HH:MM:SS" a "HH:MM".
- Calcola la media aritmetica (Mid-Price) tra i prezzi Bid e Ask per Open, High, Low, Close.
- Formatta i prezzi risultanti a 2 cifre decimali.

INPUT:  Processed_Data/2DataMerged.csv
OUTPUT: Processed_Data/3FixedData.csv
=========================================================================================
"""

# Costruzione dinamica dei percorsi relativi
script_dir = os.path.dirname(os.path.abspath(__file__))
input_file = os.path.join(script_dir, 'Processed_Data', '2DataMerged.csv') # File a 11 colonne (il file ottenuto dal precedente merging)
output_file = os.path.join(script_dir, 'Processed_Data', '3FixedData.csv') # File finale con le colonne trasformate

# Definizione esplicita dell'intestazione finale pulita con valori univoci del prezzo
HEADER = ["Date", "Time", "Open", "High", "Low", "Close", "TotalTicks"]

def avg_price(bid_str, ask_str):
    """
    Calcola la media (Mid-Price) tra due valori stringa.
    Nota: Il .replace(',', '.') funge da strato di sicurezza (Defensive Programming) 
    nel caso in cui i dati in input presentino ancora la virgola europea.
    """

    bid = float(bid_str.replace(',', '.'))
    ask = float(ask_str.replace(',', '.'))
    avg_val = (bid + ask) / 2.0
    return f"{avg_val:.2f}"  # Restituisce, ad es., "1234.56"

with open(input_file, newline='', encoding='utf-8') as fin, \
     open(output_file, 'w', newline='', encoding='utf-8') as fout:
    
    reader = csv.reader(fin, delimiter=',')
    writer = csv.writer(fout, delimiter=',')

    for row_index, row in enumerate(reader):
        # Riconoscimento della riga header:
        # Se la riga è la prima oppure uno dei campi contiene la stringa "bid" (case-insensitive)
        # viene considerata header e viene sostituita con quella desiderata (titoli di colonne).
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

        # --- Conversione della Time ---
        # Da "HH:MM:SS" a "HH:MM"
        old_time = row[1]
        new_time = old_time[:5]

        # --- Calcolo delle medie dei prezzi ---
        # Si assume la seguente mappatura:
        # Colonna 2: OpenBid, Colonna 3: HighBid, Colonna 4: LowBid, Colonna 5: CloseBid,
        # Colonna 6: OpenAsk, Colonna 7: HighAsk, Colonna 8: LowAsk, Colonna 9: CloseAsk,
        # Colonna 10: TotalTicks.
        open_avg = avg_price(row[2], row[6])
        high_avg = avg_price(row[3], row[7])
        low_avg = avg_price(row[4], row[8])
        close_avg = avg_price(row[5], row[9])

        # Recupero corretto di TotalTicks all'indice 10
        total_ticks = row[10]

        # --- Costruzione della nuova riga ---
        new_row = [new_date, new_time, open_avg, high_avg, low_avg, close_avg, total_ticks]
        writer.writerow(new_row)

print("File 3DoMedian.py eseguito con successo! Calcolato il Mid-Price e formattate le date.")