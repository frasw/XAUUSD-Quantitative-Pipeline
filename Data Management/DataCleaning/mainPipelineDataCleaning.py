import subprocess
import os

base_dir = os.path.dirname(os.path.abspath(__file__))

# Lista ordinata dei file da eseguire
scripts = [
    "1Converter.py",
    "2MergeColumn.py",
    "3DoMedian.py",  # Oppure 3_1DeleteAsk.py | ATTENZIONE! -> Vedere suggerimento modifica anche nel path di 'input_file' in 4DataCleaning.py
    "4DataCleaning.py"
]

print("AVVIO PIPELINE DI DATA CLEANING...\n")

for script in scripts:
    script_path = os.path.join(base_dir, script)
    print(f"Esecuzione in corso: {script}...")
    
    # Esecuzione del file come fosse da terminale
    result = subprocess.run(["python", script_path], capture_output=True, text=True)
    
    # Stampa dei log del file o eventuali errori
    if result.returncode == 0:
        print(result.stdout)
    else:
        print(f"ERRORE IN {script}:\n{result.stderr}")
        break

print("PIPELINE COMPLETATA CON SUCCESSO!")