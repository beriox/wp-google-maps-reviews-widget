# 📍 Google Maps Reviews Static Widget

## 📌 Context & Objective
Questo progetto nasce per estrarre, preservare e pubblicare sul web le recensioni registrate da un profilo utente **Google Local Guide** (con alto volume di visualizzazioni). 

Poiché i link brevi nativi di Google Maps (`goo.gl/maps` o `maps.app.goo.gl`) scadono o cambiano struttura dopo tempo impedendo di visualizzare la singola recensione, questo sistema genera un **widget statico e permanente** privo di dipendenze da API a pagamento.

---

## 🏗️ System Architecture & Workflow

1. **Data Source (Google Takeout):**
   * L'utente esporta i propri dati da `takeout.google.com` spuntando esclusivamente la voce **Maps (i tuoi luoghi) > Recensioni**.
   * Il file estratto (GeoJSON / JSON raw) viene processato da uno script ETL locale.

2. **ETL Pipeline (`parse_takeout.py`):**
   * Script Python per trasformare l'export di Takeout in un file `data.json` minimizzato e strutturato:
     ```json
     [
       {
         "Luogo": "Duomo di Milano",
         "Valutazione": 5,
         "Recensione": "Testo della recensione...",
         "URL_GoogleMaps": "[https://www.google.com/maps/](https://www.google.com/maps/)..."
       }
     ]
     ```

3. **Frontend & Rendering (`embed.html`):**
   * Widget sviluppato in **Vanilla JavaScript (ES6)** statico (zero PHP, zero server side required).
   * Progettato per essere ospitato gratuitamente su **GitHub Pages**.
   * Riceve i parametri tramite URL Query String:
     * `?id=0`: indice della recensione da mostrare.
     * `?json=data.json`: URL del file JSON sorgente.

4. **Integration (WordPress.com Free):**
    * Poiché i blog gratuiti bloccano l'installazione di plugin PHP custom e script JS diretti, l'integrazione avviene inserendo un blocco **HTML Personalizzato** contenente un `<iframe>`. In questo caso:
     ```html
     <iframe 
       src="https://beriox.github.io/wp-google-maps-reviews-widget/embed.html?id=0" 
       width="100%" 
       height="340" 
       frameborder="0">
     </iframe>
     ``` 

---

## 🛡️ Security & OWASP Hardening (JavaScript Vanilla)

Il widget lato client applica le seguenti mitigazioni di sicurezza:

* **A03:2021 – Reflected & DOM-based XSS:** Neutralizzato. Viene usato rigorosamente `textContent` per l'inserimento dei dati nel DOM. Nessuna manipolazione tramite `innerHTML`.
* **A03:2021 – Injection via Links (`javascript:` URIs):** Gli URL verso Google Maps vengono sanitizzati verificando lo schema tramite il costruttore nativo `new URL()` (si accettano unicamente i protocolli `http:` e `https:`).
* **A05:2021 – Reverse Tabnabbing:** Tutti i collegamenti esterni verso Google Maps impostano l'attributo `rel="noopener noreferrer"`.
* **A08:2021 – Defensive Type Checking:** Conversione esplicita e parsing difensivo di interi (`Number.parseInt`) per impedire Prototype Pollution o crash su JSON malformati.

---

## 🛠️ Quick Steps to Publish

1. Esegui il parser indicando il file JSON/GeoJSON di Takeout; il file di output predefinito è `data.json`:
  ```sh
  python3 parse_takeout.py "percorso/al/file-di-takeout.json"
  ```
  Per scegliere un altro nome o percorso di output, aggiungi `--output percorso/output.json`.
  Il `data.json` incluso nel repository è solo un esempio dimostrativo con le coordinate del Duomo di Milano: sostituiscilo con il risultato del parser prima della pubblicazione.
2. Esegui la commit di `embed.html` e `data.json` sul tuo repository GitHub.
3. Attiva **GitHub Pages** dalle impostazioni del repository (sulla root o cartella `/docs`).
4. Inserisci il tag `<iframe>` nel blog WordPress target puntando all'URL di GitHub Pages.