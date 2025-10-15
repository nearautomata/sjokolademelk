# Studieplan GUI

En liten skrivebordsapp (Tkinter) for å registrere emner og sette opp en enkel studieplan (6 semestre) for et bachelorløp i ingeniørfag. Appen følger oppgaveteksten: registrere emner, legge dem i riktig semester, sjekke at hvert semester har 30 studiepoeng, og lagre/åpne fra fil. Vi valgte GUI fordi det er mer oversiktlig enn en terminalmeny.

---

## Kort forklaring 

**Hva gjør programmet?**

* Du legger inn emner med *emnekode*, *semester (høst/vår)* og *studiepoeng*.
* Du fordeler emnene i seks semesterbokser (1–6). Høstemnene kan bare ligge i 1/3/5, våremnene i 2/4/6.
* Appen passer på at du ikke legger inn samme emne to ganger, at semestervalget er lovlig, og at **sum per semester aldri overstiger 30 studiepoeng**.
* Med ett klikk sjekker den om hele studieplanen er gyldig: Den er gyldig når **alle seks semestre har akkurat 30 studiepoeng**.
* Du kan **lagre** arbeidet til en JSON-fil og **åpne** det igjen senere.
* Du kan også **slette** et emne helt (det fjernes da fra planen)

**Hvorfor er dette nyttig?**

* Du får raskt oversikt over planen din.
* Regler håndheves automatisk, så du unngår småfeil.
* Du kan mellomlagre og fortsette senere.

**Hvordan bruker jeg den? (2 minutter)**

1. Klikk **➕ Nytt emne** og legg inn noen emner (f.eks. MAT100, høst, 10 stp).
2. Marker et emne i venstre tabell, klikk **📥 Legg i semester** og velg semester (1–6).
3. Følg med på **0/30 stp**-indikatoren under hvert semester.
4. Trykk ✅ Valider (eller F5) for å sjekke at alle semestre har 30 stp.
5. **💾 Lagre** når du er fornøyd. **📂 Åpne** for å fortsette senere.

---

## Funksjoner (koblet til oppgaveteksten)

1. **Lag et nytt emne** – dialog med emnekode, semester (høst/vår), studiepoeng.
2. **Legg til et emne i studieplanen** – med automatiske regler (ikke duplikater, riktig semester, maks 30 stp).
3. **Vis alle registrerte emner** – tabell i venstre panel med sortérbar oversikt.
4. **Vis studieplanen per semester** – seks ruter (1–6) med sum og fremdriftsindikator mot 30 stp.
5. **Sjekk om planen er gyldig** – én knapp: grønt hvis alt er 30, ellers liste over avvik.
6. **Lagre til fil** – lagrer både emner og studieplan i én JSON-fil.
7. **Les fra fil** – åpner samme format og rydder bort eventuelle feilreferanser.
8. **Avslutt** – via menylinje eller knapp.
9. *(Frivillig)* **Slett emne** – fjerner emnet også fra planen.
10. *(Frivillig)* **Fjern fra studieplan** – «Fjern valgt»/«Tøm» per semester.

> Valgemner (11–14) er ikke implementert i basis, men er beskrevet under «Videre arbeid».

---

## Slik kjører du

* **Krav:** Python 3.10+ (Tkinter følger vanligvis med standardinstallasjonen).
* **Start:**

  ```bash
  python main.py
  ```
* **Snarveier:** `Ctrl+N` nytt emne · `Ctrl+S` lagre · `Ctrl+O` åpne · `F5` validér · Temabytt: 🌙/☀️-knapp.

---

## Filformat (JSON)

Vi lagrer én fil som inneholder både emner og studieplan.

```json
{
  "next_id": 7,
  "courses": [
    {"id": 1, "kode": "MAT100", "semester": "høst", "stp": 10},
    {"id": 2, "kode": "DAT101", "semester": "høst", "stp": 10},
    {"id": 4, "kode": "MAT200", "semester": "vår",  "stp": 10}
  ],
  "plan": [
    [1, 2],   // semester 1
    [4],      // semester 2
    [],       // semester 3
    [],       // semester 4
    [],       // semester 5
    []        // semester 6
  ]
}
```

* `courses` er «fasiten» for emnene.
* `plan` refererer til emnene via `id`. Ved innlasting rydder appen bort ugyldige referanser automatisk.

---

## Valideringsregler (kort forklart)

* **Riktig årstid:** Høst-emner → semester **1/3/5**, Vår-emner → **2/4/6**.
* **Ikke duplikater:** Samme emne kan ikke ligge i flere semestre.
* **30 stp-grense:** Et semester kan *ikke overstige* 30 stp (du får feilmelding).
* **Gyldig studieplan:** Når *alle seks* semestre har **akkurat 30 stp**.

---

## Teknisk forklaring

> Denne delen forklarer *hvordan* appen virker under panseret – uten å forutsette at du er utvikler.

### Arkitektur i to ord: **Modell + Skjermbilde**

* **Model (logikk):** Lagrer emner og studieplan og har reglene: «hvilket semester er lov», «maks 30 stp», «ikke duplikater». Modellen vet *ingenting* om GUI.
* **GUI (Tkinter):** Viser knapper, tabeller og meldinger. Når du klikker, spør GUI modellen: «Er dette lov?» – og oppdaterer visningen.

Dette kalles ofte separasjon av ansvar: reglene bor ett sted (enkelt å teste), visningen et annet (enkelt å endre utseende).

### De viktigste datastrukturene

* **Emner (courses):** Liste med objekter: `{id, kode, semester, stp}`.
* **Studieplan (plan):** 6 lister (for 6 semestre) som inneholder `id`-ene til emnene.
* **Hvorfor id og ikke emnekode i planen?** Id-er gjør det enkelt å endre koder uten å ødelegge planen. Vi sørger samtidig for at kodene er unike.

### Slik håndheves reglene

Når du prøver å legge et emne i et semester, sjekker modellen i denne rekkefølgen:

1. **Finnes emnet?** (ellers feil)
2. **Er emnet allerede i planen?** (ellers feil)
3. **Matcher årstid?** Høst ↔ 1/3/5, Vår ↔ 2/4/6 (ellers feil med tydelig melding)
4. **Blir det >30 stp?** (ellers feil)
5. **Hvis alt ok:** Legg inn og oppdater summen i GUI.

### Lagring og innlasting

* Ved **lagring** skriver vi hele modellen til en JSON-fil.
* Ved **åpning** leser vi inn og **validerer** dataene: kaster ugyldige emner, ignorerer plan-id-er som ikke finnes, og begrenser stp til 1–30.

### GUI-strukturen (kort)

* Venstre side: tabell over registrerte emner.
* Høyre side: seks ruter (semester 1–6) med fremdriftslinje (0/30 stp) og knapper for «Fjern valgt» og «Tøm».
* Topp: verktøylinje (legg til, legg i semester, slett, lagre/åpne, valider, tema, avslutt) og menylinje (Fil).
* Bunn: statuslinje for korte beskjeder.

### Snarveier og små detaljer

* **Ctrl+N**: nytt emne · **Ctrl+S**: lagre · **Ctrl+O**: åpne · **F5**: valider.
* **Mørk/lys modus** med én knapp – bare kosmetikk, ikke funksjonelt.
* Varsler (info/feil) vises i dialoger og i statuslinjen.
