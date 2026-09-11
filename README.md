# Documentazione di Progetto: Pipeline di Previsione Direzionale su Serie Storiche (XAUUSD)

## 0. Installazione e Setup dell'Ambiente
Per garantire la totale riproducibilità del codice e prevenire conflitti di versione tra le librerie locali, è caldamente consigliato eseguire il progetto all'interno di un ambiente virtuale isolato (`venv`).

Per inizializzare l'ambiente e installare le dipendenze necessarie, eseguire i seguenti comandi nel terminale, assicurandosi di operare dalla directory principale (*root*) del progetto:

**1. Creazione dell'ambiente virtuale:**
```bash
python -m venv
```

**2. Attivazione dell'ambiente virtuale:**
- Su Windows (PowerShell):
```powershell
.\venv\Scripts\activate
```

- Su macOS / Linux:
```bash
source venv/bin/activate
```

**3. Installazione delle dipendenze:**
Una volta attivato l'ambiente (confermato dalla comparsa del prefisso (venv) nel prompt del terminale), installare i pacchetti richiesti tramite il gestore pip:
```bash
pip install -r requirements.txt
```


## 1. Introduzione al Progetto
Il presente progetto ha come obiettivo lo sviluppo, il miglioramento e la validazione statistica di un algoritmo per la previsione della direzione della candela successiva in un mercato finanziario (asset primario: XAUUSD). 

Originariamente implementato in ambiente MQL4 tramite un approccio basato su *Pattern Matching* e *Cosine Similarity* (1-Nearest Neighbor), il sistema è in fase di migrazione e potenziamento in ambiente Python. L'obiettivo metodologico è trasformare un sistema di trading euristico in una pipeline di Data Science rigorosa, integrando tecniche avanzate di preprocessing, esplorazione statistica e modelli di Machine Learning (Classificazione e Regressione) per massimizzare la precisione predittiva. 

L'algoritmo analizza vettori di feature composti da sequenze storiche (es. 9 candele consecutive con valori OHLC) per prevedere la polarità (BUY/SELL) della candela successiva.

---

## 2. La Fase di Data Cleaning: Motivazioni e Risoluzione dei Problemi
La fase di preparazione dei dati (Data Cleaning e Preprocessing) rappresenta le fondamenta dell'intera pipeline analitica. I modelli di Machine Learning e le metriche di similarità vettoriale richiedono input rigorosamente strutturati, continui e numerici. 

I dati storici grezzi (estratti in questo caso da FXCM a timeframe 1 minuto, comprensivi di Bid e Ask) presentano nativamente diverse criticità strutturali e informative che renderebbero impossibile l'addestramento di un modello:
1. **Ambiguità dei Delimitatori:** I dataset europei o estratti da specifiche piattaforme utilizzano spesso la virgola (`,`) sia come separatore dei campi CSV, sia come separatore decimale per i prezzi. Questo genera un disallineamento strutturale delle matrici di dati.
2. **Tipi di Dato Errati:** Un prezzo formattato con la virgola viene interpretato dai parser statistici (come Pandas) come dato testuale (Stringa) anziché come numero a virgola mobile (Float), impedendo qualsiasi operazione matematica.
3. **Inconsistenze Temporali:** Presenza di gap dovuti alle chiusure dei mercati (weekend) o a tick mancanti, che distorcono la continuità delle finestre temporali utilizzate per i sample.

La presente sezione della pipeline si occupa della *Normalizzazione Strutturale* del dataset, garantendo che i dati grezzi vengano convertiti in un formato tabellare leggibile, coerente e tipizzato correttamente per le successive fasi di analisi statistica.

---

## 3. Pipeline di Normalizzazione Strutturale

### 3.1 Step 1: Risoluzione delle Anomalie Strutturali (`1Converter.py`)
Il primo script della pipeline affronta il problema critico dell'ambiguità dei delimitatori nel file CSV grezzo.

* **Problema:** A causa dell'utilizzo della virgola sia come separatore di colonna che come separatore decimale (es. `2062,14`), un parser standard divide un singolo valore di prezzo in due colonne distinte. Inoltre, i prezzi privi di decimali (es. `2062`) non subiscono questa divisione, generando righe con un numero variabile di campi e causando il fallimento sistematico dell'importazione dei dati.
* **Metodologia:** L'algoritmo `1Converter.py` opera riga per riga per ricostruire l'integrità strutturale. Isola le colonne temporali (Date, Time) e processa sequenzialmente i successivi valori. Sfruttando la lunghezza delle stringhe, l'algoritmo discrimina tra la parte intera di un prezzo e la sua potenziale parte decimale. Qualora un prezzo si presenti come numero intero puro, il sistema provvede all'imputazione di un campo fittizio (`'00'`) per ripristinare il corretto offset delle colonne.
* **Output:** Il risultato è un dataset intermedio (`1DataConverted.csv`) in cui ogni riga è forzata in modo deterministico a una lunghezza costante di 19 campi, separando provvisoriamente la radice intera dalla mantissa decimale.

### 3.2 Step 2: Standardizzazione Numerica e Unificazione (`2MergeColumn.py`)
Il secondo script finalizza la formattazione strutturale, preparando i dati per l'ingestione in librerie di calcolo scientifico come `pandas` e `scikit-learn`.

* **Problema:** I dati in uscita dallo Step 1, pur essendo allineati, presentano i prezzi frammentati in due colonne e necessitano di essere convertiti nello standard internazionale (floating-point con separatore a punto) per abilitare le operazioni matematiche.
* **Metodologia:** L'algoritmo `2MergeColumn.py` acquisisce il file a 19 campi. Dopo aver instanziato un'intestazione pulita a 11 colonne (escludendo eventuali header corrotti del file precedente), itera sulle righe del dataset. Le coppie di colonne rappresentanti la parte intera e decimale vengono concatenate utilizzando il punto (`.`) come operatore di giunzione testuale (es. `2062` e `14` diventano `2062.14`). 
* **Output:** Il risultato è il dataset `2DataMerged.csv`, perfettamente ricompattato nella sua struttura originale a 11 colonne (Date, Time, 8 serie di prezzi OHLC Bid/Ask, TotalTicks). I dati sono ora pronti per essere elaborati algoritmicamente senza errori di parsing.

### 3.3 Step 3: Compressione Informativa e Standardizzazione Temporale
A valle della normalizzazione strutturale, il dataset presenta ridondanza informativa sotto forma di doppia quotazione bidirezionale (Bid e Ask). In questa fase, la pipeline si biforca per consentire due approcci metodologici distinti alla rappresentazione del prezzo dell'asset, applicando contemporaneamente una standardizzazione ai formati temporali (adattamento ai formati `YYYY.MM.DD` e `HH:MM` tipici delle piattaforme di trading algoritmico).

* **Opzione A - Calcolo del Mid-Price (`3DoMedian.py`):** Questo script opera una sintesi delle quotazioni calcolando la media aritmetica (Mid-Price) tra le curve di Bid e Ask per ogni componente della candela (OHLC). Questo approccio neutralizza le fluttuazioni transitorie dello spread, fornendo un "Fair Value" continuo del sottostante, ideale per i modelli regressivi.
* **Opzione B - Estrazione Selettiva (`3_1DeleteAsk.py`):** In alternativa, questo script applica un filtro colonnare selettivo, isolando esclusivamente la curva dei prezzi Bid. Questa metrica riflette l'effettivo prezzo di liquidazione per posizioni long, risultando utile per simulazioni e metriche finanziarie orientate all'operatività reale.

**Nota Metodologica (Defensive Programming e Dati Sporchi):**
In aggiunta alle trasformazioni core, entrambi gli script implementano un livello di *Defensive Programming* essenziale per la gestione dei file estratti da provider finanziari. Durante l'iterazione di lettura, i parser verificano attivamente la presenza di stringhe testuali (es. la keyword "bid") all'interno dei record dati. Questo meccanismo di filtro permette di intercettare e scartare "intestazioni orfane" o righe testuali finite accidentalmente nel mezzo del dataset—un'anomalia tipica nel Data Mining finanziario quando si aggregano storici pluriennali o esportazioni multi-file. Prevenendo l'ingestione di queste righe sporche, si evitano crash fatali (eccezioni di cast a `float`) e si garantisce la continuità dell'elaborazione.

Entrambi gli script restituiscono un dataset snellito a 7 colonne (Date, Time, Open, High, Low, Close, TotalTicks), fungendo da input standardizzato per la successiva fase di pulizia statistica e gestione delle discontinuità (Gap temporali).

### 3.4 Step 4: Data Imputation, Risoluzione Discontinuità e Vettorizzazione (`4DataCleaning.py`)
Le serie storiche finanziarie, in particolare su timeframe ad alta frequenza (M1), sono fisiologicamente soggette a discontinuità. Queste possono essere classificate in interruzioni macroscopiche sistemiche (chiusure per weekend o festività) o micro-interruzioni anomale dovute a tick persi o assenza di liquidità. Per addestrare modelli basati su sequenze storiche continue, la totale assenza di discontinuità sull'asse temporale è un requisito non negoziabile.

Il quarto step rappresenta il core della pipeline di preparazione dati. L'architettura software di questo modulo è basata sul *Single Responsibility Principle* ed è suddivisa in tre macro-fasi orchestrate sequenzialmente:

1. **Ordinamento Strutturale e Reindicizzazione (Time-Series Expansion):**
   Il dataset subisce un ordinamento cronologico rigoroso sull'indice temporale (`Datetime`) per prevenire anomalie differenziali. Successivamente, viene forzata una reindicizzazione (`reindex` in pandas) sull'intero range temporale disponibile a frequenza fissa (1 minuto). Questa operazione espande la matrice dati, trasformando i minuti mancanti (buchi temporali) in righe con valori espliciti `NaN`.
   
   * **Nota Metodologica (Gestione Edge Cases Temporali):** Il filtro per le festività è ingegnerizzato con un livello di *Defensive Programming*: il sistema verifica l'esistenza di quotazioni antecedenti e successive alla festività analizzata prima di classificarla come gap sistemico. Questo impedisce eccezioni fatali qualora la serie storica processata non copra l'intero anno solare.

2. **Data Imputation Dinamica a Soglie Esaustive:**
   La risoluzione dei gap (i valori `NaN` iniettati dal `reindex`) avviene tramite l'applicazione di maschere condizionali mutualmente esclusive:
   * **Micro-gap (< 5 minuti):** Vengono risolti tramite **Interpolazione Lineare**, creando una rampa di prezzo artificiale per unire due tick vicini.
   * **Medium-gap (5 min <= gap < 1 giorno):** Vengono risolti tramite **Forward Fill**. Viene mantenuto e trascinato in avanti l'ultimo prezzo noto, simulando un mercato fermo/illiquido per evitare la genesi di falsi micro-trend derivanti dall'interpolazione.
   * **Macro-gap (>= 1 giorno):** Vengono mantenuti vuoti e identificati da una feature booleana (`Missing = True`), permettendo ai successivi modelli di scartare automaticamente le finestre temporali che accavalerebbero le chiusure settimanali ("Weekend Gaps").

3. **Finalizzazione e Vettorizzazione (Export Ready):**
   Per minimizzare il collo di bottiglia dell'I/O (lettura/scrittura su disco di un dataset >500.000 righe), lo script gestisce in memoria la dicotomia dell'esportazione:
   * Viene generato un dataset intermedio di appoggio (`FinalData.csv`) comprensivo di Date e Time formattati, utile per ispezioni umane, log e debug visivo.
   * Il dataframe in memoria subisce istantaneamente un *Feature Drop* per eliminare le variabili testuali ridondanti (Data e Ora stringa), estraendo esclusivamente l'indice `Datetime` e le variabili continue. Il risultato è un tensore puramente numerico (`XAUUSD_ReadyToUse.csv`), ottimizzato computazionalmente per l'ingestione diretta nell'algoritmo di similarità e nei modelli di Machine Learning.

   * Le logiche di riempimento condizionale (*masking*) sono ingegnerizzate per essere mutualmente esclusive e logicamente esaustive, azzerando il rischio di partizioni non coperte ("terre di nessuno"). Ogni minuto generato ricade in una sola delle seguenti casistiche:
   * **Micro-gap (< 5 minuti):** Vengono risolti tramite **Interpolazione Lineare**. Assumendo che l'assenza di tick per pochi minuti non alteri il trend sottostante, si crea una rampa di prezzo artificiale per unire un punto all'altro.
   * **Medium-gap (5 min <= gap < 1 giorno):** Vengono risolti tramite **Forward Fill**. Viene mantenuto e trascinato in avanti l'ultimo prezzo noto, simulando un mercato fermo/illiquido. Un'interpolazione lineare su archi temporali così ampi (es. ore) introdurrebbe un bias predittivo inaccettabile, simulando falsi trend stabili.
   * **Macro-gap (>= 1 giorno):** Vengono mantenuti vuoti (`NaN`) ma etichettati tramite una feature booleana (`Missing = True`). Questo permette alla successiva finestra mobile (Sliding Window) dell'algoritmo di scartare automaticamente i sample che accavallerebbero la chiusura del venerdì con l'apertura del lunedì, evitando i distorsivi "Weekend Gaps".

### 3.5 Automazione e Orchestrazione della Pipeline (`mainPipelineDataCleaning.py`)
Al fine di garantire la totale riproducibilità del processo di Data Preprocessing e preparare il sistema per un ambiente di test intensivo (es. *Walk-Forward Validation* su lotti di dati futuri), l'esecuzione sequenziale dei moduli è stata automatizzata tramite uno script orchestratore centralizzato.

L'approccio manuale "step-by-step", utile in fase di sviluppo e ispezione, è stato sostituito da un'architettura software di tipo *Pipeline*.
* **Meccanismo di Esecuzione:** Lo script sfrutta la libreria nativa `subprocess` per istanziare processi terminale indipendenti. I quattro nodi della pipeline (`1Converter.py`, `2MergeColumn.py`, lo step di compressione informativa e `4DataCleaning.py`) vengono richiamati in un rigoroso ordine cronologico.
* **Logging e Gestione degli Errori:** L'orchestratore implementa un sistema di cattura dell'output (sia `stdout` che `stderr`). In caso di successo, i log di ogni singolo modulo vengono consolidati e stampati a video per fornire un report di esecuzione. Qualora un nodo dovesse generare un'eccezione (es. file sorgente mancante o errore di parsing), la logica di *error handling* blocca immediatamente la pipeline (*halt*), prevenendo l'elaborazione a cascata di dati corrotti.

Questa soluzione fornisce un singolo *entry point* di esecuzione ("One-Click Run") che trasforma i dati grezzi estratti dal broker nel tensore matematico `XAUUSD_ReadyToUse.csv`, azzerando il rischio di errori operativi umani e abbattendo i tempi di preparazione del dataset.

## 4. Exploratory Data Analysis (EDA) e Validazione Statistica

A valle della pipeline di preprocessing, il dataset `XAUUSD_ReadyToUse.csv` si presenta come una matrice densa e continua, pronta per la modellazione. Tuttavia, prima di procedere con l'implementazione degli algoritmi predittivi (Pattern Matching e Machine Learning), è imperativo condurre un'Analisi Esplorativa dei Dati (EDA) per estrarre le proprietà statistiche del sottostante, mappare la dimensionalità delle feature e verificare l'assenza di bias introdotti durante la fase di imputazione.

Lo script di esplorazione (`EDA.py`) opera sulle seguenti tre direttrici analitiche:

### 4.1 Statistiche Descrittive e Filtro delle Anomalie Sistemiche
Prima di qualsiasi computazione statistica, il modulo EDA applica un filtro logico essenziale: l'esclusione temporanea delle righe contrassegnate dalla flag `Missing = True`. 
Poiché lo Step 4 della pipeline ha iniettato valori vuoti (`NaN`) per mantenere la continuità assoluta dell'asse temporale durante i weekend, includere questi "macro-gap" nel calcolo delle medie o delle varianze introdurrebbe un grave bias statistico (sottostima artificiale della volatilità). Le metriche descrittive (Media, Deviazione Standard, Min/Max, Quartili) vengono pertanto calcolate esclusivamente sui dati di mercato reali (mercato aperto).

### 4.2 Analisi Distribuzionale (Feature Spaziali)
La distribuzione spaziale delle variabili di prezzo (Open, High, Low, Close) e di volume (TotalTicks) viene ispezionata visivamente tramite un pannello di istogrammi. 
Questo passaggio permette di identificare:
* L'assenza di valori *outlier* anomali derivanti da errori del data provider (es. flash crash inesistenti a valore 0).
* La forte asimmetria (skewness) tipica dei volumi tick-by-tick, dominati da micro-variazioni (candele a basso volume) alternate a rari e violenti *spike* di liquidità (oltre 5000 tick/minuto), solitamente coincidenti con rilasci macroeconomici.

### 4.3 Stagionalità Intraday e Volatilità
Le serie storiche finanziarie, in particolare l'asset XAUUSD, presentano una marcata eteroschedasticità legata agli orari operativi delle piazze globali. L'algoritmo raggruppa i dati per ora solare (0-23) e ne calcola la deviazione standard del parametro `TotalTicks`. 
Questa metrica funge da *proxy* per la volatilità intraday, permettendo di isolare visivamente i regimi di mercato: l'incremento di volatilità fisiologico durante le sovrapposizioni delle sessioni di Londra e New York (14:00 - 17:00) rispetto alle fasi di lateralità della sessione asiatica.

### 4.4 Analisi di Multicollinearità (Matrice di Correlazione)
La fase conclusiva dell'EDA calcola la Matrice di Correlazione di Pearson tra tutte le variabili numeriche. Nell'analisi ad altissima frequenza (Timeframe M1), le componenti OHLC mostrano fisiologicamente una correlazione prossima a `1.00`, indicando una ridondanza informativa (Multicollinearità) a livello di prezzo assoluto. 
Questa evidenza empirica giustifica matematicamente il passaggio successivo dell'algoritmo predittivo: per calcolare la Cosine Similarity o addestrare una rete neurale, non verranno forniti i prezzi assoluti, bensì le *variazioni relative* (rendimenti o shape del pattern) in modo da rendere le feature stazionarie e informativamente indipendenti.