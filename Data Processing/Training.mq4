// Funzione aggiuntiva per la Tesi
// - Crea 10000 sample conservati in 1000 vettori da 10 elementi di
// (iClose(Symbol(), PERIOD_M5, 1) - iOpen(Symbol(), PERIOD_M5, 1), ......).
// - Successivamente prende le 10 candele da 5' più vicine al tempo corrente
// rispetto a quando è stato premuto "Addestra".
// - Poi crea un "vettore confronto" Out of Sample che verrà confrontato con
// tutti gli altri 1000 vettori fino a trovare quello più simile.
// - Una volta trovato quello più simile, il "vettore simile", prenderemo il
// "valore Label" associato al "vettore simile" e lo daremo come Output di
// consiglio relativo al "vettore confronto".
// - Per associare ad ogni vettore un "vettore label" prenderò l'esito
// dell'elemento [9] (ultimo elemento di ogni vettore) e
// se sarà negativo ((C) - (O)) <= 0 Allora la candela è ribassista -> 1
// se sarà positivo ((C) - (O)) >= 0 Allora la candela è rialzista  -> 0

// Nell'11° elemento salvo il Label del Vettore
// Nel 12° salvo il valore della Similarità del Coseno col Vettore Confronto
void Training()
{
   int i, j, k;

   double vettori[DIM_VETTORI][12];
   double vConfronto[11];
   double pDot = 0;        // Salvo il Temporaneo Prodotto Scalare tra il 'Vettore k' appena creato con il 'Vettore Confronto'
   double gVConfronto = 0; // Salvo la Grandezza Vettoriale del 'Vettore Confronto'
   double gVVetK = 0;      // Salvo la Grandezza Vettoriale del 'Vettore k' appena creato
   int cosSimID = -1;      // Salvo l'indice del vettore che contiene la Similarità del Coseno più vicina a 1

   ArrayInitialize(vettori, EMPTY_VALUE);
   ArrayInitialize(vConfronto, EMPTY_VALUE);

   for(k = 0; k < DIM_VETTORI + 1; k++)
   {
      //Print("INIZIO VETTORE ", k);

      i = k + 1;

      for(j = 9; j >= 0; j--)
      {
         double chiusura = iClose(Symbol(), PERIOD_M5, i);
         double apertura = iOpen(Symbol(), PERIOD_M5, i);
         datetime orarioApertura = iTime(Symbol(), PERIOD_M5, i);
         int hOA = TimeHour(orarioApertura);
         int mOA = TimeMinute(orarioApertura);

         //vettori[k][j] = CutString((chiusura - apertura), 5);

         // Creo il Primo Vettore che sarà quello Confronto
         if(k == 0)
         {
            vConfronto[j] = chiusura - apertura;
            //Print("E: ", j, " | i: ", i, ") Time: ", hOA, ":", mOA, " | C: (", chiusura, ") - O: (", apertura, ") = ", vConfronto[j]);
            gVConfronto += MathPow(vConfronto[j], 2);
         }

         else
         {
            vettori[k - 1][j] = chiusura - apertura;
            //Print("E: ", j, " | i: ", i, ") Time: ", hOA, ":", mOA, " | C: (", chiusura, ") - O: (", apertura, ") = ", vettori[k - 1][j]);
         }

         if((k - 1) > 0 && j == 0)
         {
            if(vettori[k - 1][9] >= 0)
               vettori[k - 1][10] = 0;
            else
               vettori[k - 1][10] = 1;

            //Print("Ho assegnato ", vettori[k - 1][10], " | in vettori[", k - 1, "][10]");
         }

         // Al termine della creazione di ogni Vettore Sample calcolo la similarità del coseno rispetto al "Primo Vettore Creato"
         // Calcolo il Prodotto scalare tra il 'Vettore k' appena creato e il 'vettore Confronto'
         // Calcolo la Grandezza Vettoriale del 'Vettore k' "MathSqrt(MathPow(vettori[k][0]) + ... + MathPow(vettori[k][9]))"
         if(k > 0)
         {
            pDot += vConfronto[j] * vettori[k - 1][j];

            gVVetK += MathPow(vettori[k - 1][j], 2);
         }

         i++;
      }

      if(k > 0)
      {
         //if((MathSqrt(gVConfronto) * MathSqrt(gVVetK)) != 0)
         vettori[k - 1][11] = pDot / (MathSqrt(gVConfronto) * MathSqrt(gVVetK));
         //Print("Ho assegnato ", vettori[k - 1][11], " | in vettori[", k - 1, "][11]");

         //Print("FINE VETTORE ", k);
      }

      // Aggiorno l'indice del Vettore che conterrò la similarità del coseno più Alta
      if(k == 1)
         cosSimID = 0;
      else if(k > 1 && vettori[k - 1][11] > vettori[cosSimID][11])
         cosSimID = k - 1;
   }

   Print("Il vettore più simile al vettore confronto ha ID: ", cosSimID, " e similarità del coseno col vettore confronto pari a: ", vettori[cosSimID][11]);

   /*Print("Vettore simile: ");
   for(j = 0; j < 11; j++)
      Print("E: ", j, " | = ", vettori[cosSimID][j]);

   Print("Vettore Confornto: ");
   for(j = 0; j < 10; j++)
      Print("E: ", j, " | = ", vConfronto[j]);*/

   // Assegno la previsione della candela successiva al vettore Confronto
   vConfronto[10] = vettori[cosSimID][10];

   if(vConfronto[10] == 0)
      Print("La Candela successiva al vettore confronto è più probabile che sia Rialzista");
   else
      Print("La Candela successiva al vettore confronto è più probabile che sia Ribassista");
}