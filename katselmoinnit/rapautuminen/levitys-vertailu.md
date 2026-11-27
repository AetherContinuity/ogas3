# Levitysvertailu 1: rekisteri vs grep (27.11.2026)

**Kysymys:** tutkimuskäytössä 1 todettiin, ettei SM-009:n väite "The divergence between scenarios grows nonlinearly — which means the cost of delay is not linear but accelerating" saa tukea WP-013:sta. Sama koskee "Core paradigm finding" -kohdan väitettä "The ratio of these costs grows nonlinearly with time". Mitkä korpuksen väitteet nojaavat näihin ja pitää tarkistaa?

**Rekisteri** (`taytto-kimi.json`, 63 esiintymää):
- Väite ei ole esiintymä. SM-009:002:n lainaus päättyy ennen epälineaarisuuslausetta, eikä "Core paradigm finding" -kohtaa poimittu.
- `alavirta SM-009:002` palauttaa tyhjän. `alavirta SM-009:001` palauttaa SM-009:005:n, mutta se on ketjua koskeva väite eikä epälineaarisuus.
- Kustannus: yksi kysely. Tyhjää vastausta ei voi erottaa kattavuusaukosta: rekisteri ei kata papereita, jotka viittaavat SM-009:ään.

**Grep** (sivusto @ main, papers/ ja supplements/, hakemistosivut pois):
1. `nonlinear|non-linear|epälineaari|accelerating|kiihtyv|cost of delay|viiveen (hinta|kustannus)|ratio of these costs|grows nonlinearly` → 42 tiedostoa, 86 osumaa. Osumat suodatettiin kontekstissa sanoihin viive, päätös, korjaus, instituutio, mittaus ja ikkuna, ja jäljelle jääneet luettiin.
2. `paid once|cost of measurement|measurement absence|…` ja `SM-009` → 12 tiedostoa viittaa SM-009:ään. Kaikkien viittauskohdat luettiin.

**Tulos (lähdeteksteistä tarkistettu):**
- **Kumpaakaan väitettä ei toista eikä käytä mikään muu paperi.** Muiden papereiden epälineaarisuusväitteillä on oma perustansa, eivätkä ne viittaa SM-009:ään. Esimerkkejä:
  - WP-008: Monte Carlo -kynnysvaikutus;
  - SP-001: firming-kustannus keston funktiona;
  - DRD-sarja: C2-vaihesiirtymät;
  - SP-005: yhteisvaikutus;
  - TN-015: tipping-indikaattori.
- **SM-009:ään viittaavat 12 paperia käyttävät kolmen vajeen ketjua tai mittausvajetta**, eivät epälineaarisuutta:
  - CN-007, CN-008, CN-009, SM-010, SM-016, TN-009 ja TN-010 viittaavat ketjuun tai § 09:ään;
  - SM-017 ja SM-018 viittaavat § 11:een;
  - DA-008 viittaa § 08:aan;
  - WP-020 ja analyysi-tanska viittaavat yleisesti.
- **WP-013 käyttää ilmausta "cost of delay"** ("makes the cost of delay visible in concrete terms") ilman epälineaarisuutta.
- **Tarkistettavaa korjauksen jälkeen on vain SM-009 itse.**

**Arvio mittarilla:** grep tuotti perustellun kielteisen vastauksen noin kymmenen minuutin lukemisella. Rekisteri tuotti tyhjän vastauksen, jota ei voi tulkita. Tässä tapauksessa rekisteri ei löytänyt eikä ylläpitänyt tietoa paremmin kuin tavallinen haku. Syy ei ole kyselyssä vaan kattavuudessa: rekisterissä on 10 paperia, korpuksessa yli sata. Rekisterin poissaolo ei ole korpuksen poissaolo.

**Seuraus:** levityksen lisäarvo edellyttää, että rekisterin kattavuus on tunnettu ja riittävä. Muuten tyhjä alavirta on harhaanjohtavampi kuin grep. Tätä tulosta ei yleistetä tapauksiin, joissa riippuvuus on sanastoltaan erilainen kuin väite. Sellaisessa tapauksessa grep voi hävitä, mutta sitä ei tässä testattu.
