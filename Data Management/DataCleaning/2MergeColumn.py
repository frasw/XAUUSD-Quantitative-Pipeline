import csv
import os

"""
=========================================================================================
FILE: 2MergeColumn.py

OBIETTIVO: 
Ricomporre i prezzi precedentemente separati (parte intera e parte decimale) in un unico 
valore numerico, restituendo al dataset la sua struttura originale a 11 colonne, ma 
con i dati allineati e formattati correttamente per l'analisi dati.

FUNZIONAMENTO:
- Definisce un'intestazione pulita a 11 colonne per il nuovo file.
- Legge il file a 19 colonne generato dallo step 1, saltando la sua vecchia intestazione.
- Itera sulle righe: se una riga ha 19 colonne, unisce a due a due le 16 colonne 
  centrali (i prezzi) inserendo il punto ('.') come separatore decimale standard.
- Ricompatta la riga in 11 colonne (Date, Time, 8 Prezzi, TotalTicks) e la salva.

INPUT:  Processed_Data/1DataConverted.csv
OUTPUT: Processed_Data/2DataMerged.csv
=========================================================================================
"""

# Definizione esplicita dell'intestazione finale pulita
HEADER = ["Date", "Time", "OpenBid", "HighBid", "LowBid", "CloseBid", 
          "OpenAsk", "HighAsk", "LowAsk", "CloseAsk", "Total Ticks"]

script_dir = os.path.dirname(os.path.abspath(__file__))
input_file = os.path.join(script_dir, 'Processed_Data', '1DataConverted.csv') # Il file con 19 colonne (prezzi separati in due parti)
output_file = os.path.join(script_dir, 'Processed_Data', '2DataMerged.csv') # Il file finale con 11 colonne

with open(input_file, newline='', encoding='utf-8') as fin, \
     open(output_file, 'w', newline='', encoding='utf-8') as fout:
    
    reader = csv.reader(fin, delimiter=',')
    writer = csv.writer(fout, delimiter=',')

    # 1. Si scrive subito l'intestazione pulita nel nuovo file
    writer.writerow(HEADER)

    # 2. Si salta la prima riga del file di input (qualunque sia)
    next(reader, None)

    for row in reader:
        # Controllo preliminare: la riga deve avere 19 colonne
        if len(row) != 19:
            print("Warning: la riga non ha 19 colonne, saltata:")
            print(row)
            continue

        # Creazione della nuova riga:
        # Le prime due colonne (Date e Time) si mantengono inalterate.
        merged_row = [row[0], row[1]]

        # Unione delle 16 colonne di prezzo a due a due
        # Le prossime 16 colonne di prezzo sono attualmente divise in 2 colonne ciascuna:
        # OpenBid_int, OpenBid_dec, HighBid_int, HighBid_dec, ... , CloseAsk_int, CloseAsk_dec.
        # Vengono combinati unendoli con un punto come separatore decimale.
        for i in range(8):
            int_part = row[2 + i * 2]
            dec_part = row[3 + i * 2]

            # Unione: ad es. '1234' e '56' diventeranno '1234.56'
            price = int_part + '.' + dec_part
            merged_row.append(price)

        # Infine si aggiunge l'ultima colonna TotalTicks (colonna 19 nel file a 0-index: posizione 18)
        merged_row.append(row[18])

        writer.writerow(merged_row)

print("File 2MergeColumn.py eseguito con successo! Dati unificati a 11 colonne.")