import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from xgboost import XGBRegressor

"""
=========================================================================================
MODULO: Simulazione di Portafoglio (Backtesting Vettorializzato Filtrato)

OBIETTIVO: 
Utilizzare un modello di Regressione (XGBoost Regressor) per stimare l'ampiezza in dollari 
della candela successiva. Introduce un "Filtro Operativo": il sistema esegue un trade 
solo se l'ampiezza prevista supera una soglia minima, risparmiando il costo dello spread 
sui falsi segnali o sui mercati laterali.
=========================================================================================
"""

def prepare_backtest_data(df, window_size=10):
    """
    Rielabora la logica delle sliding windows restituendo il target di regressione (y_reg)
    e un DataFrame allineato.
    """
    df_features = df.copy()
    
    # Feature spaziali
    df_features['Body'] = df_features['Close'] - df_features['Open']
    df_features['Range'] = df_features['High'] - df_features['Low']
    df_features['Upper_Shadow'] = df_features['High'] - df_features[['Open', 'Close']].max(axis=1)
    df_features['Lower_Shadow'] = df_features[['Open', 'Close']].min(axis=1) - df_features['Low']
    
    # Target Regressione (Body reale della candela)
    target_reg_array = df_features['Body'].values
    
    X, y_reg = [], []
    features_array = df_features[['Body', 'Range', 'Upper_Shadow', 'Lower_Shadow']].values
    
    for i in range(len(df_features) - window_size):
        X.append(features_array[i : i + window_size].flatten())
        y_reg.append(target_reg_array[i + window_size])
        
    df_aligned = df_features.iloc[window_size:].copy().reset_index(drop=True)
        
    return np.array(X), np.array(y_reg), df_aligned

def run_vectorized_backtest(df_test, predictions, initial_capital=10000.0, lot_size=0.1, spread=0.15, min_move_threshold=0.20):
    """
    Motore finanziario. Applica il filtro di tolleranza, calcola le posizioni dinamiche, 
    detrae i costi di transazione e calcola l'Equity Curve.
    """
    df = df_test.copy()
    df['Prediction_Reg'] = predictions
    
    # 1. LOGICA DEL FILTRO OPERATIVO
    # Segnale puro: 1 per Long (previsione >= 0), -1 per Short (previsione < 0)
    df['Signal'] = np.where(df['Prediction_Reg'] >= 0, 1, -1)
    
    # Posizione effettiva: Entra a mercato SOLO se la previsione in valore assoluto supera la soglia
    # Altrimenti resta fuori dal mercato (0)
    df['Position'] = np.where(df['Prediction_Reg'].abs() >= min_move_threshold, df['Signal'], 0)
    
    # 2. CALCOLI FINANZIARI
    contract_multiplier = 100 * lot_size
    df['Market_Move'] = df['Close'] - df['Open']
    
    # PnL Lordo
    df['Gross_PnL_Points'] = df['Market_Move'] * df['Position']
    
    # Costo di transazione: si paga lo spread SOLO quando si è a mercato (Position != 0)
    df['Trade_Cost'] = spread * df['Position'].abs()
    
    # PnL Netto
    df['Net_PnL_Points'] = df['Gross_PnL_Points'] - df['Trade_Cost']
    df['Net_PnL_USD'] = df['Net_PnL_Points'] * contract_multiplier
    
    # 3. METRICHE DI PORTAFOGLIO
    df['Equity_Curve'] = initial_capital + df['Net_PnL_USD'].cumsum()
    df['Peak'] = df['Equity_Curve'].cummax()
    df['Drawdown'] = df['Equity_Curve'] - df['Peak']
    
    return df

def print_tearsheet_and_plot(df_results, initial_capital=10000.0, spread=0.15, min_move_threshold=0.20):
    """
    Estrae le statistiche finali dal DataFrame processato e disegna il grafico delle performance.
    """
    # Statistiche operative calcolate SOLO sui trade effettivamente eseguiti
    executed_trades = df_results[df_results['Position'] != 0]
    total_trades = len(executed_trades)
    
    # Prevenzione errore divisione per zero nel caso in cui il filtro sia troppo stringente e blocchi tutti i trade
    if total_trades > 0:
        winning_trades = len(executed_trades[executed_trades['Net_PnL_USD'] > 0])
        win_rate = (winning_trades / total_trades) * 100
    else:
        win_rate = 0.0

    final_equity = df_results['Equity_Curve'].iloc[-1]
    net_profit = final_equity - initial_capital
    return_pct = (net_profit / initial_capital) * 100
    max_drawdown = df_results['Drawdown'].min()
    
    print("\n==================================================")
    print(" TEARSHEET SIMULAZIONE (Modello Filtrato Out-of-Sample)")
    print("==================================================")
    print(f"Capitale Iniziale : ${initial_capital:,.2f}")
    print(f"Capitale Finale   : ${final_equity:,.2f}")
    print(f"Profitto Netto    : ${net_profit:,.2f} ({return_pct:.2f}%)")
    print(f"Drawdown Massimo  : ${max_drawdown:,.2f}")
    print(f"Spread per Trade  : {spread} Punti")
    print(f"Soglia Operativa  : Entrata > {min_move_threshold} Punti attesi")
    print("--------------------------------------------------")
    print(f"Candele Totali (Test): {len(df_results):,}")
    print(f"Trade Eseguiti       : {total_trades:,} (Mercato ignorato nel {100 - (total_trades/len(df_results)*100):.1f}% del tempo)")
    print(f"Win Rate (Netto)     : {win_rate:.2f}%")
    print("==================================================\n")
    
    plt.figure(figsize=(12, 6))
    plt.plot(df_results['Datetime'], df_results['Equity_Curve'], color='green', linewidth=1.5, label='Filtered Strategy (XGBRegressor)')
    plt.axhline(initial_capital, color='black', linestyle='--', linewidth=1, label='Break Even')
    
    plt.fill_between(df_results['Datetime'], initial_capital, df_results['Equity_Curve'], 
                     where=(df_results['Equity_Curve'] < initial_capital), color='red', alpha=0.3)
    
    plt.title(f"Equity Curve: Modello di Regressione Filtrato (Soglia: {min_move_threshold} pt)", fontsize=14, fontweight='bold')
    plt.xlabel("Data (Segmento Out-of-Sample)", fontsize=12)
    plt.ylabel("Capitale (USD)", fontsize=12)
    plt.legend()
    plt.grid(alpha=0.4)
    plt.tight_layout()
    plt.show()

# =========================================================
# ESECUZIONE PRINCIPALE (MAIN)
# =========================================================
if __name__ == "__main__":
    file_path = os.path.join(os.getcwd(), 'Data Management', 'ReadyData', 'XAUUSD_ReadyToUse.csv')
    print("[INFO] Caricamento e allineamento storico...")
    df = pd.read_csv(file_path, parse_dates=['Datetime'])
    df_clean = df[df['Missing'] == False].copy().reset_index(drop=True)
    
    X, y_reg, df_aligned = prepare_backtest_data(df_clean, window_size=10)
    
    # Split Cronologico (80/20)
    split_index = int(len(X) * 0.8)
    X_train, y_reg_train = X[:split_index], y_reg[:split_index]
    X_test, y_reg_test = X[split_index:], y_reg[split_index:]
    df_test = df_aligned.iloc[split_index:].copy().reset_index(drop=True)
    
    print("[INFO] Addestramento XGBoost Regressor sul passato (80%)...")
    xgb_reg = XGBRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    xgb_reg.fit(X_train, y_reg_train)
    
    print("[INFO] Generazione stime quantitative di ampiezza sul futuro (20%)...")
    predictions = xgb_reg.predict(X_test)
    
    print("[INFO] Avvio simulazione di portafoglio vettorializzata...")
    # Si può variare la soglia operativa (min_move_threshold) per essere più o meno aggressivo
    df_results = run_vectorized_backtest(
        df_test=df_test, 
        predictions=predictions,
        initial_capital=10000.0,
        lot_size=0.1,
        spread=0.15,
        min_move_threshold=0.20
    )
    
    print_tearsheet_and_plot(df_results)
    
    # 1. Raggruppamento per giorno
    df_results['Date_Only'] = df_results['Datetime'].dt.date
    daily_stats = df_results.groupby('Date_Only').agg(
        Profitto_Giornaliero=('Net_PnL_USD', 'sum'),
        Trade_Eseguiti=('Position', lambda x: (x != 0).sum())
    )
    
    print("--- Top 5 Giorni per Profitto Netto ---")
    print(daily_stats.sort_values(by='Profitto_Giornaliero', ascending=False).head(5))
    
    # 2. Controllo integrità del dataset (Righe duplicate e ordine temporale)
    duplicati = df_results['Datetime'].duplicated().sum()
    print(f"\n--- Integrità Dati: Timestamp duplicati trovati = {duplicati}")
    
    # Verifica se il file torna indietro nel tempo
    df_results['Time_Diff'] = df_results['Datetime'].diff().dt.total_seconds()
    salti_indietro = (df_results['Time_Diff'] < 0).sum()
    print(f"--- Integrità Dati: Salti temporali negativi (disordine) = {salti_indietro}")