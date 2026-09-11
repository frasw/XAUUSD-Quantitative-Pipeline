import os
import matplotlib
matplotlib.use('Agg') # Forza il backend non interattivo per evitare i blocchi di Windows
import matplotlib.pyplot as plt
import seaborn as sns
import time
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import seaborn as sns
from sklearn.decomposition import PCA
from xgboost import XGBClassifier, XGBRegressor
from sklearn.metrics import accuracy_score, f1_score, precision_score, classification_report, confusion_matrix, mean_absolute_error

"""
=========================================================================================
MODULO: Addestramento e Valutazione Modelli di Machine Learning (Random Forest & XGBoost - Classificazione e Regressione)

OBIETTIVO: 
Superare la logica puramente geometrica (Cosine Similarity) addestrando algoritmi di
Intelligenza Artificiale capaci di estrarre relazioni non lineari dalle sliding windows.
- Classificazione: Prevedere la direzione binaria (Rialzista/Ribassista).
- Regressione: Prevedere l'ampiezza quantitativa del movimento del prezzo per filtrare 
  i falsi segnali e superare la frizione dello spread.

FUNZIONAMENTO:
- Rigenera le feature spaziali (Flattening a 40 dimensioni).
- Esegue uno Split Cronologico rigoroso (80% Training, 20% Testing) per evitare Data Leakage.
- Addestra un Random Forest Classifier (Ensemble di alberi indipendenti).
- Addestra un XGBoost Classifier (Ensemble sequenziale ad alte prestazioni).
- Valuta i modelli sul Test Set invisibile, stampando Accuracy, Precision e Report.
=========================================================================================
"""



def create_sliding_windows(df, window_size=10):
    """
    Ritorna la matrice X e DUE vettori target (y_class per la classificazione binaria, 
    y_reg per la regressione continua dell'ampiezza in punti).
    """
    df_features = df.copy()
    
    df_features['Body'] = df_features['Close'] - df_features['Open']
    df_features['Range'] = df_features['High'] - df_features['Low']
    df_features['Upper_Shadow'] = df_features['High'] - df_features[['Open', 'Close']].max(axis=1)
    df_features['Lower_Shadow'] = df_features[['Open', 'Close']].min(axis=1) - df_features['Low']

    # Target Classificazione (0 = Buy, 1 = Sell)
    df_features['Target'] = np.where(df_features['Body'] >= 0, 0, 1)
    # Target Regressione (Valore numerico continuo del Body)
    target_reg_array = df_features['Body'].values
    
    X, y, y_reg = [], [], []
    features_array = df_features[['Body', 'Range', 'Upper_Shadow', 'Lower_Shadow']].values
    target_array = df_features['Target'].values
    
    for i in range(len(df_features) - window_size):
        window = features_array[i : i + window_size].flatten()
        label = target_array[i + window_size]
        X.append(window)
        y.append(label)
        y_reg.append(target_reg_array[i + window_size])
        
    return np.array(X), np.array(y), np.array(y_reg)

def evaluate_and_print(model_name, y_true, y_pred, execution_time):
    """
    Formatta e stampa le metriche di valutazione chiave in modo leggibile.
    """
    acc = accuracy_score(y_true, y_pred)
    # Calcolo della precision macro per avere una media bilanciata tra i due risultati
    prec = precision_score(y_true, y_pred, average='macro')
    
    print(f"\n==================================================")
    print(f" RISULTATI MODELLO: {model_name}")
    print(f" Tempo di Addestramento e Previsione: {execution_time:.2f} secondi")
    print(f"==================================================")
    print(f" Accuracy Globale : {acc * 100:.2f}%")
    print(f" Precision Media  : {prec * 100:.2f}%")
    print("\n Report Classificazione Dettagliato:")
    print(classification_report(y_true, y_pred, target_names=["Rialzista (0)", "Ribassista (1)"]))
    
    print(" Matrice di Confusione:")
    cm = confusion_matrix(y_true, y_pred)
    print(f"Vero Rialzista previsto corretto : {cm[0][0]}")
    print(f"Vero Rialzista previsto errato   : {cm[0][1]} (Falso Ribassista)")
    print(f"Vero Ribassista previsto errato  : {cm[1][0]} (Falso Rialzista)")
    print(f"Vero Ribassista previsto corretto: {cm[1][1]}")
    print(f"==================================================\n")

def train_and_evaluate_regressor(X_train, X_test, y_reg_train, y_reg_test, y_class_test):
    """
    Addestra un modello XGBoost Regressor per prevedere l'ampiezza continua 
    del movimento di mercato (Body) e ne stampa le metriche di valutazione.
    """
    print("\n Avvio addestramento XGBoost REGRESSOR...")
    start_time = time.time()
    
    # Inizializzazione e addestramento
    xgb_reg = XGBRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    xgb_reg.fit(X_train, y_reg_train)
    
    # Previsione dei valori continui (ampiezza candela)
    y_pred_reg = xgb_reg.predict(X_test)
    exec_time_reg = time.time() - start_time
    
    # Metriche di Regressione
    mae = mean_absolute_error(y_reg_test, y_pred_reg)
    
    # Derivazione dell'accuracy direzionale dalla regressione per confronto con i classificatori.
    # Se la previsione numerica è >= 0 equivale a un BUY (Label 0), altrimenti SELL (Label 1)
    y_pred_reg_class_derived = np.where(y_pred_reg >= 0, 0, 1)
    reg_directional_accuracy = accuracy_score(y_class_test, y_pred_reg_class_derived)
    
    print(f"\n==================================================")
    print(f" REGRESSIONE: XGBoost Regressor")
    print(f"⏱ Tempo: {exec_time_reg:.2f} secondi")
    print(f"==================================================")
    print(f" Errore Medio Assoluto (MAE) : {mae:.4f} punti")
    print(f" Accuracy Direzionale (Derivata): {reg_directional_accuracy * 100:.2f}%")
    print(f" Esempio Previsioni (Punti) : {y_pred_reg[:5].round(3)}")
    print(f" Valori Reali (Punti)       : {y_reg_test[:5].round(3)}")
    print(f"==================================================\n")
    
    # Restituisce il modello e le previsioni per eventuali utilizzi futuri
    return xgb_reg, y_pred_reg

def generate_academic_plots(X_train, X_test, y_train, y_test, y_pred_rf, y_pred_xgb):
    """
    Genera e salva i grafici richiesti per la relazione accademica.
    """
    os.makedirs('Plots', exist_ok=True)
    import matplotlib
    matplotlib.use('Agg') # Sicurezza aggiuntiva per ambienti non interattivi
    import matplotlib.pyplot as plt
    import seaborn as sns
    from sklearn.decomposition import PCA
    import numpy as np
    from sklearn.metrics import accuracy_score, f1_score

    sns.set_theme(style="whitegrid")
    
    # --- 1. Istogrammi delle Feature ---
    plt.figure(figsize=(12, 5))
    
    # Estrazione sicura dei dati (Gestisce sia DataFrame che Array NumPy)
    if hasattr(X_train, 'columns'):
        data1 = X_train.iloc[:, 0]
        data2 = X_train.iloc[:, 1]
        label1 = f"Distribuzione: {X_train.columns[0]}"
        label2 = f"Distribuzione: {X_train.columns[1]}"
    else:
        data1 = X_train[:, 0]
        data2 = X_train[:, 1]
        label1 = "Distribuzione: Feature Spaziale 1 (Body)"
        label2 = "Distribuzione: Feature Spaziale 2 (Range)"

    plt.subplot(1, 2, 1)
    sns.histplot(data1, bins=100, kde=True, color='steelblue')
    plt.title(label1)
    plt.xlabel('Valore')
    plt.ylabel('Frequenza')
    plt.xlim(-3, 3)

    plt.subplot(1, 2, 2)
    sns.histplot(data2, bins=100, kde=True, color='steelblue')
    plt.title(label2)
    plt.xlabel('Valore')
    plt.ylabel('Frequenza')
    plt.xlim(0, 5)

    plt.tight_layout()
    plt.savefig('Plots/1_Feature_Histograms.png', dpi=300)
    plt.close()

    # --- 2. Proiezione 2D tramite PCA ---
    print("[INFO] Calcolo PCA in corso per la visualizzazione 2D...")
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_train)
    
    plt.figure(figsize=(9, 7))
    scatter = plt.scatter(X_pca[:, 0], X_pca[:, 1], c=y_train, cmap='coolwarm', alpha=0.3, s=2)
    plt.title('Proiezione PCA (2D) - Sovrapposizione delle Classi (Train Set)')
    plt.xlabel(f'Principal Component 1 ({pca.explained_variance_ratio_[0]*100:.1f}%)')
    plt.ylabel(f'Principal Component 2 ({pca.explained_variance_ratio_[1]*100:.1f}%)')
    plt.legend(handles=scatter.legend_elements()[0], labels=['Rialzista (0)', 'Ribassista (1)'])
    plt.savefig('Plots/2_PCA_Projection.png', dpi=300)
    plt.close()

    # --- 3. Grafico a Barre Comparativo ---
    rf_acc = accuracy_score(y_test, y_pred_rf)
    rf_f1 = f1_score(y_test, y_pred_rf, average='macro')
    xgb_acc = accuracy_score(y_test, y_pred_xgb)
    xgb_f1 = f1_score(y_test, y_pred_xgb, average='macro')
    
    labels = ['Accuracy', 'F1-Score (Macro)']
    rf_scores = [rf_acc, rf_f1]
    xgb_scores = [xgb_acc, xgb_f1]
    x = np.arange(len(labels))
    width = 0.35

    plt.figure(figsize=(8, 6))
    plt.bar(x - width/2, rf_scores, width, label='Random Forest', color='teal')
    plt.bar(x + width/2, xgb_scores, width, label='XGBoost', color='darkorange')
    
    plt.ylabel('Score')
    plt.title('Confronto Prestazioni Classificatori (Out-of-Sample)')
    plt.xticks(x, labels)
    plt.ylim(0.4, 0.6)
    plt.axhline(0.5, color='red', linestyle='--', linewidth=1.5, label='Random Walk (50%)')
    plt.legend(loc='lower right')
    
    plt.savefig('Plots/3_Models_Comparison.png', dpi=300)
    plt.close()
    
    # --- ADD-ON: Classificazione sui dati proiettati (PCA) ---
    print("\n[INFO] Addestramento XGBoost sulle 2 Componenti Principali (PCA)...")
    from xgboost import XGBClassifier
    
    # Ora X_test è disponibile e si può trasformare
    X_test_pca = pca.transform(X_test)
    
    xgb_pca = XGBClassifier(random_state=42, n_jobs=-1, eval_metric='logloss')
    xgb_pca.fit(X_pca, y_train)
    y_pred_pca = xgb_pca.predict(X_test_pca)
    
    acc_pca = accuracy_score(y_test, y_pred_pca)
    print(f"[RISULTATO] Accuracy XGBoost (40 Feature Originali): {xgb_acc:.4f}")
    print(f"[RISULTATO] Accuracy XGBoost (2 Componenti PCA):    {acc_pca:.4f}")
    print("-" * 50)
    
    print("[INFO] Grafici accademici generati e salvati nella cartella 'Plots/'.")

if __name__ == "__main__":
    # 1. CARICAMENTO DATI
    file_path = os.path.join(os.getcwd(), 'Data Management', 'ReadyData', 'XAUUSD_ReadyToUse.csv')
    print(" Caricamento dataset...")
    df = pd.read_csv(file_path, parse_dates=['Datetime'])
    df_clean = df[df['Missing'] == False].copy().reset_index(drop=True)
    
    # 2. GENERAZIONE MATRICI
    print(" Creazione delle Sliding Windows (40 feature)...")
    X, y, y_reg = create_sliding_windows(df_clean, window_size=10)
    
    # 3. SPLIT CRONOLOGICO (80% Train, 20% Test)
    print(" Suddivisione dataset (Split Cronologico)...")
    split_index = int(len(X) * 0.8)
    
    X_train, X_test = X[:split_index], X[split_index:]
    y_train, y_test = y[:split_index], y[split_index:]
    y_reg_train, y_reg_test = y_reg[:split_index], y_reg[split_index:]
    
    print(f" Training Set : {X_train.shape[0]} candele (Passato)")
    print(f" Testing Set  : {X_test.shape[0]} candele (Futuro/Out-of-Sample)")
    
    # 4. ADDESTRAMENTO RANDOM FOREST
    print("\n Avvio addestramento Random Forest (potrebbe richiedere un minuto)...")
    start_time = time.time()
    
    # n_jobs=-1 utilizza tutti i core della CPU per velocizzare
    # n_estimators=100 crea 100 alberi decisionali
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    rf_model.fit(X_train, y_train)
    y_pred_rf = rf_model.predict(X_test)
    
    evaluate_and_print("Random Forest", y_test, y_pred_rf, time.time() - start_time)
    
    # 5. ADDESTRAMENTO XGBOOST
    print(" Avvio addestramento XGBoost...")
    start_time = time.time()
    
    xgb_model = XGBClassifier(n_estimators=100, random_state=42, n_jobs=-1, eval_metric='logloss')
    xgb_model.fit(X_train, y_train)
    y_pred_xgb = xgb_model.predict(X_test)
    
    evaluate_and_print("XGBoost", y_test, y_pred_xgb, time.time() - start_time)

    # 3. ADDESTRAMENTO XGBOOST REGRESSOR
    # Chiamata alla nuova funzione modulare
    xgb_reg_model, y_pred_reg = train_and_evaluate_regressor(X_train, X_test, y_reg_train, y_reg_test, y_test)

    generate_academic_plots(X_train, X_test, y_train, y_test, y_pred_rf, y_pred_xgb)