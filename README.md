# Documentazione di Progetto: Pipeline di Previsione Direzionale su Serie Storiche (XAUUSD)

## 0. Installazione e Setup dell'Ambiente
Per garantire la totale riproducibilità del codice e prevenire conflitti di versione tra le librerie locali, è caldamente consigliato eseguire il progetto all'interno di un ambiente virtuale isolato (`venv`).

Per inizializzare l'ambiente e installare le dipendenze necessarie, eseguire i seguenti comandi nel terminale, assicurandosi di operare dalla directory principale (*root*) del progetto:

**1. Creazione dell'ambiente virtuale:**
```bash
python -m venv venv

````

**2. Attivazione dell'ambiente virtuale:**

- Su Windows (PowerShell):

PowerShell

```
.\venv\Scripts\activate

```

- Su macOS / Linux:

Bash

```
source venv/bin/activate

```

**3. Installazione delle dipendenze:** Una volta attivato l'ambiente (confermato dalla comparsa del prefisso (venv) nel prompt del terminale), installare i pacchetti richiesti tramite il gestore pip:

Bash

```
pip install -r requirements.txt

```

## 1. Introduzione al Progetto

Il progetto ha l'obiettivo di sviluppare e validare un algoritmo per la previsione direzionale sul mercato XAUUSD (timeframe 1 minuto). Il sistema evolve un precedente approccio basato sul Pattern Matching in una rigorosa pipeline di Data Science, integrando tecniche di preprocessing, analisi statistica e modelli di Machine Learning (Classificazione e Regressione).

L'algoritmo analizza vettori composti da sequenze storiche (es. finestre di 9 candele OHLC) per prevedere la polarità della candela successiva.