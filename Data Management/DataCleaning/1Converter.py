"""
=========================================================================================
FILE: 1Converter.py

OBIETTIVO: 
Risolvere il disallineamento strutturale delle colonne del CSV grezzo.
Il problema nasce dal fatto che i dati FXCM utilizzano la virgola (',') sia come 
separatore di colonna CSV, sia come separatore decimale per i prezzi (es. 2062,14).

FUNZIONAMENTO:
- Legge il file riga per riga.
- Isola Date e Time (sempre corretti).
- Ricostruisce sequenzialmente le 8 colonne di prezzo (Open, High, Low, Close per Bid e Ask).
- Se identifica un numero di 1 o 2 cifre, lo tratta come parte decimale del prezzo precedente.
- Se un prezzo è un numero intero netto (es. 2062), inietta un '00' come decimale mancante.
- Ricompatta le righe a una lunghezza fissa di 19 campi.

INPUT:  XAUUSD_Data/XAUUSD_m1_BidAndAsk.csv
OUTPUT: Processed_Data/1DataConverted.csv
=========================================================================================
"""

import csv
import os

# Ottiene la cartella esatta in cui si trova questo script (1Converter.py)
script_dir = os.path.dirname(os.path.abspath(__file__))

# Costruisce i percorsi in modo dinamico
input_file = os.path.join(script_dir, 'XAUUSD_Data', 'XAUUSD_m1_BidAndAsk.csv')
output_file = os.path.join(script_dir, 'Processed_Data', '1DataConverted.csv')

# In base al file originale:
# Colonne: Date, Time, poi 8 colonne di prezzo (ognuna idealmente "divisa" in 2: intero e decimale) e infine TotalTicks.
# Se tutti i prezzi hanno parte decimale, il numero totale di campi è 2 + (8*2) + 1 = 19.

EXPECTED_FIELDS = 19

def fix_row(fields):
    """
    Corregge la riga "scomposta" in cui alcune colonne prezzo non hanno separato l'intero dal decimale.
    I primi due campi (Date e Time) sono sempre corretti.
    le successive 16 posizioni (8 colonne prezzo in 2 parti ciascuna, divisi in intero e decimale) vanno verificate.
    Infine l'ultimo campo è TotalTicks.
    Se la parte decimale (il campo atteso dopo il campo intero) non è una stringa numerica di 2 cifre,
    allora si assume che il decimale manchi e si inserisce '00'.
    """
    # Le prime due colonne vengono lasciate inalterate
    new_fields = fields[:2]
    pos = 2  # posizione corrente nella lista "fields"

    # Processamento delle 8 colonne prezzo
    for _ in range(8):
        # Se c'è almeno un campo disponibile
        if pos < len(fields):
            integer_part = fields[pos]
        else:
            # In caso di riga troppo corta, si forza a '00'
            integer_part = '00'

        # Per la parte decimale, si controlla se esiste il campo successivo
        if pos + 1 < len(fields):
            decimal_candidate = fields[pos + 1]
            # Se il candidato è composto da 2 cifre (e quindi probabilmente è il decimale atteso)
            if decimal_candidate.isdigit() and len(decimal_candidate) in (1, 2):
                # Allora i due campi sono corretti
                new_fields.append(integer_part)
                new_fields.append(decimal_candidate)
                pos += 2
                continue
        # Se non è presente o non rispetta il formato, significa che manca il decimale:
        new_fields.append(integer_part)
        new_fields.append('00')
        pos += 1  # si sposta di 1 (poiché il campo decimale non è stato individuato)

    # Il campo rimanente è TotalTicks: viene unificato
    if pos < len(fields):
        total_ticks = ','.join(fields[pos:])
    else:
        total_ticks = ''
    new_fields.append(total_ticks)

    return new_fields


# Procedimento di lettura e correzione riga per riga
with open(input_file, newline='', encoding='utf-8') as fin, \
     open(output_file, 'w', newline='', encoding='utf-8') as fout:

    writer = csv.writer(fout, delimiter=',')

    for line in fin:
        # Rimozione di eventuali spazi bianchi finali e suddivisione per virgola
        fields = line.strip().split(',')

        # Se la riga è corretta (19 campi), viene scritta così com'è, altrimenti viene corretta
        if len(fields) < EXPECTED_FIELDS:
            fixed = fix_row(fields)
            
            writer.writerow(fixed)
        else:
            writer.writerow(fields)

print("File 1Converter.py eseguito con successo! Dati convertiti salvati in Processed_Data.")
