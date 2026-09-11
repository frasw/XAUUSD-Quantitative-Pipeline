import os
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

"""
=========================================================================================
MODULO: Feature Engineering & Sliding Windows (Per Baseline Cosine Similarity)

OBIETTIVO: 
1.  Trasformare la serie storica temporale in un dataset supervisionato (matrice X, vettore y) 
    pronto per l'algoritmo di Pattern Matching vettoriale (Cosine Similarity / 1-NN).
    Risolve il problema della non-stazionarietà passando dai prezzi assoluti a 
    metriche geometriche spaziali relative per ciascuna candela.
2.  Eseguire il Pattern Matching vettoriale (Distanza del Coseno) per trovare la finestra
    storica più simile a un pattern di input e prevederne la direzione futura.

FUNZIONAMENTO:
- Riceve in input il dataset ripulito (privo di macro-gap temporali).
- Calcola 4 metriche spaziali stazionarie per ogni candela: 
  1. Body (Close - Open)
  2. Range (High - Low)
  3. Upper Shadow (High - Max(Open, Close))
  4. Lower Shadow (Min(Open, Close) - Low)
- Scorre il dataset creando finestre mobili (pattern) di N candele (default: 10).
- Esegue il 'Flattening': converte la finestra (es. 10 candele x 4 feature) in un 
  singolo array unidimensionale (vettore a 40 elementi).
- Previene il Data Leakage isolando rigorosamente la Target Label (la direzione della 
  candela esterna e successiva alla finestra analizzata):
  Label 0 -> Candela Rialzista o Flat (Body >= 0)
  Label 1 -> Candela Ribassista (Body < 0)

OUTPUT:  X (Matrice dei Pattern), y (Vettore delle Label predittive)
=========================================================================================
"""

def create_sliding_windows(df, window_size=10):
    print(f"⚙️ Estrazione feature geometriche e generazione pattern (Window Size: {window_size})...")
    df_features = df.copy()

    # 1. TRASFORMAZIONE SPAZIALE: Calcolo delle 4 feature intra-candela
    df_features['Body'] = df_features['Close'] - df_features['Open']
    df_features['Range'] = df_features['High'] - df_features['Low']
    df_features['Upper_Shadow'] = df_features['High'] - df_features[['Open', 'Close']].max(axis=1)
    df_features['Lower_Shadow'] = df_features[['Open', 'Close']].min(axis=1) - df_features['Low']

    # 2. DEFINIZIONE DELLA LABEL (y): Direzione della candela (0=Rialzista, 1=Ribassista)
    # Replica esatta della logica MQL4 originale
    df_features['Target'] = np.where(df_features['Body'] >= 0, 0, 1)

    # 3. INIZIALIZZAZIONE STRUTTURE DATI
    X, y = [], []
    
    # Conversione in array Numpy per massimizzare la velocità computazionale nel ciclo
    features_array = df_features[['Body', 'Range', 'Upper_Shadow', 'Lower_Shadow']].values
    target_array = df_features['Target'].values

    # 4. SLIDING WINDOW (Scorrimento Temporale)
    # Il ciclo si ferma prima del margine finale per garantire l'esistenza della candela "Target"
    for i in range(len(df_features) - window_size):
        
        # Estrae la finestra storica e la "appiattisce" (flatten) in un vettore 1D continuo.
        # Con window_size=10 e 4 feature, produce un array di 40 elementi.
        window = features_array[i : i + window_size].flatten()
        
        # Estrae la Label della candela SUCCESSIVA alla finestra storica
        label = target_array[i + window_size]

        X.append(window)
        y.append(label)

    # Conversione finale in Tensori (Matrici Numpy)
    X_numpy = np.array(X)
    y_numpy = np.array(y)
    
    print(f" Generazione completata. Dimensione Matrice X: {X_numpy.shape}, Vettore y: {y_numpy.shape}")
    return X_numpy, y_numpy

def predict_next_candle(target_pattern, history_X, history_y):
    """
    Calcola la Cosine Similarity tra il pattern attuale e l'intero storico,
    restituendo l'indice del gemello storico, il grado di similarità e la previsione.
    """
    # reshape(1, -1) è richiesto da sklearn per vettori singoli
    target_reshaped = target_pattern.reshape(1, -1)
    
    # cosine_similarity restituisce un array di similarità tra il target e tutte le righe di history_X
    similarities = cosine_similarity(target_reshaped, history_X)[0]
    
    # Trova l'indice del valore più alto (il Nearest Neighbor)
    best_match_idx = np.argmax(similarities)
    best_similarity_score = similarities[best_match_idx]
    
    # Estrae la Label corrispondente al "gemello" storico
    prediction = history_y[best_match_idx]
    
    return best_match_idx, best_similarity_score, prediction

# ==========================================
# ESECUZIONE TEST SUL DATASET
# ==========================================
if __name__ == "__main__":
    # Caricamento dinamico dal path principale
    
    file_path = os.path.join(os.getcwd(), 'Data Management', 'ReadyData', 'XAUUSD_ReadyToUse.csv')
    
    df = pd.read_csv(file_path, parse_dates=['Datetime'])
    
    # Pulizia dai macro-gap (weekend) prima della vettorizzazione
    df_clean = df[df['Missing'] == False].copy().reset_index(drop=True)
    
    # Calcolo preventivo delle Sliding Windows
    w_size = 10
    expected_windows = len(df_clean) - w_size
    print(f" Dataset caricato: {len(df_clean)} candele valide (No Macro-Gap).")
    print(f" Previsione: verranno generate esattamente {expected_windows} Sliding Windows.\n")
    
    # Chiamata alla funzione
    X, y = create_sliding_windows(df_clean, window_size=w_size)
    
    # Stampa di debug del primo pattern per verifica dimensionale
    print("\n Ispezione del primo pattern (X[0]):")
    print(X[0])
    print(f"Label corrispondente (y[0]): {y[0]}")
    print(f" Generazione completata. Pattern estratti: {X.shape[0]}")
    
    # ==========================================
    # TEST DI PREVISIONE (Out-of-Sample)
    # ==========================================
    print("\n Avvio Ricerca Cosine Similarity (1-NN)...")
    
    # Simulazione del trading in tempo reale: 
    # Si considera l'ULTIMO pattern disponibile come "Oggi" e si utilizza tutto il resto come Storico
    history_X = X[:-1]
    history_y = y[:-1]
    
    current_pattern = X[-1]
    actual_future_label = y[-1] # La vera direzione registrata dal mercato, utile per verifica
    
    best_idx, sim_score, pred_label = predict_next_candle(current_pattern, history_X, history_y)
    
    # Decodifica della label per una lettura umana
    direction_map = {0: "RIALZISTA (BUY)", 1: "RIBASSISTA (SELL)"}
    
    print(f" Pattern Analizzato: Ultima finestra disponibile nel dataset.")
    print(f" Match Trovato all'indice storico: {best_idx}")
    print(f" Grado di Similarità (Coseno): {sim_score:.4f} (1.0 = Gemello Perfetto)")
    print(f" Previsione Suggerita dall'Algoritmo: {direction_map[pred_label]}")
    print(f" Direzione Reale del Mercato: {direction_map[actual_future_label]}")