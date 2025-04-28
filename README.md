# Planificator de Călătorii în România

Aplicație desktop pentru descoperirea și planificarea călătoriilor în România, folosind algoritmi de machine learning pentru recomandări personalizate.

## Descriere

Aplicația ajută utilizatorii să descopere cele mai interesante locații turistice din orașele României, bazându-se pe:
- Preferințele personale ale utilizatorului
- Rating-uri și recenzii existente
- Tipul locațiilor (muzee, parcuri, monumente istorice etc.)
- Distanța între obiective

## Funcționalități

1. **Recomandări Personalizate**
   - Introducere text liber cu preferințele utilizatorului
   - Analiză de text pentru identificarea categoriilor preferate
   - Calculare automată a compatibilității cu locațiile disponibile

2. **Vizualizare pe Hartă**
   - Afișare top 5 locații recomandate
   - Traseu optimizat între obiective
   - Calcul distanțe între locații

3. **Informații Detaliate**
   - Rating-uri și evaluări
   - Categorii și tipuri de activități
   - Estimări de preț
   - Distanțe și rute

## Cerințe Tehnice

- Python 3.6+
- Pachete necesare:
  - tkinter: interfața grafică
  - ttkbootstrap: stilizare modernă
  - tkintermapview: vizualizare hartă
  - scikit-learn: machine learning
  - pandas: procesare date
  - nltk: procesare text
  - pillow: procesare imagini
  - requests: comunicare API

## Instalare

```bash
pip install ttkbootstrap tkintermapview pillow requests polyline scikit-learn pandas nltk
```

## Utilizare

1. Rulați aplicația:
```bash
python app.py
```

2. În fereastra principală:
   - Selectați orașul dorit
   - Descrieți preferințele (ex: "Îmi plac muzeele și arhitectura")
   - Apăsați "Generează Plan"

3. Veți primi:
   - Top 5 locații recomandate
   - Hartă interactivă cu traseu
   - Distanțe între obiective
