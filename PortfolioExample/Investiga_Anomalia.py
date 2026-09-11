import os
import pandas as pd

file_path = os.path.join(os.getcwd(), 'Data Management', 'ReadyData', 'XAUUSD_ReadyToUse.csv')
print("⏳ Caricamento dataset per indagine...")
df = pd.read_csv(file_path, parse_dates=['Datetime'])

# Isoliamo esattamente il 28 Dicembre 2024 (Sabato)
sabato_28 = df[df['Datetime'].dt.date == pd.to_datetime('2024-12-28').date()]

print(f"\nCandele trovate il 28 Dicembre 2024 (Sabato): {len(sabato_28)}")

if len(sabato_28) > 0:
    print("\n🔍 PRIMA DEL 28 DICEMBRE (Chiusura del Venerdì notte):")
    venerdi_notte = df[(df['Datetime'] >= '2024-12-27 23:55:00') & (df['Datetime'] <= '2024-12-27 23:59:00')]
    print(venerdi_notte[['Datetime', 'Open', 'High', 'Low', 'Close']])
    
    print("\n👻 I PRIMI 10 'GHOST TICKS' DEL SABATO:")
    print(sabato_28[['Datetime', 'Open', 'High', 'Low', 'Close']].head(10))
    
    print("\n👻 GLI ULTIMI 10 'GHOST TICKS' DEL SABATO:")
    print(sabato_28[['Datetime', 'Open', 'High', 'Low', 'Close']].tail(10))