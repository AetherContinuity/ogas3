# Stance — validoinnin tulokset

Yksiköitä 31. Ihmisen jakauma: kannattaa_muutoksin 18, vastustaa 7, ei_kantaa 3, kannattaa 3

## kimi · low
- toisto 1: κ 0.634 (95 % 0.35–0.85) · raaka 77% · otehylkäys 0% · virheitä 0 · hinta 0.17 $
- toisto 2: κ 0.680 (95 % 0.39–0.89) · raaka 81% · otehylkäys 0% · virheitä 0 · hinta 0.17 $
- κ toistojen välillä: 0.947

| ihminen \ malli | kannattaa | kannattaa_mu | vastustaa | ei_kantaa | epaselva | virhe |
|---|---|---|---|---|---|---|
| kannattaa | 3 | 0 | 0 | 0 | 0 | 0 |
| kannattaa_muutoksin | 3 | 14 | 1 | 0 | 0 | 0 |
| vastustaa | 0 | 3 | 4 | 0 | 0 | 0 |
| ei_kantaa | 0 | 0 | 0 | 3 | 0 | 0 |
| epaselva | 0 | 0 | 0 | 0 | 0 | 0 |

## kimi · max
- toisto 1: κ 0.680 (95 % 0.39–0.89) · raaka 81% · otehylkäys 0% · virheitä 0 · hinta 0.35 $
- toisto 2: κ 0.637 (95 % 0.35–0.85) · raaka 77% · otehylkäys 0% · virheitä 0 · hinta 0.32 $
- κ toistojen välillä: 0.947

| ihminen \ malli | kannattaa | kannattaa_mu | vastustaa | ei_kantaa | epaselva | virhe |
|---|---|---|---|---|---|---|
| kannattaa | 3 | 0 | 0 | 0 | 0 | 0 |
| kannattaa_muutoksin | 3 | 15 | 0 | 0 | 0 | 0 |
| vastustaa | 0 | 3 | 4 | 0 | 0 | 0 |
| ei_kantaa | 0 | 0 | 0 | 3 | 0 | 0 |
| epaselva | 0 | 0 | 0 | 0 | 0 | 0 |

## sonnet · high
- toisto 1: κ 0.625 (95 % 0.39–0.82) · raaka 74% · otehylkäys 0% · virheitä 4 · hinta 0.19 $
- toisto 2: κ 0.702 (95 % 0.47–0.90) · raaka 81% · otehylkäys 0% · virheitä 2 · hinta 0.18 $
- κ toistojen välillä: 0.910

| ihminen \ malli | kannattaa | kannattaa_mu | vastustaa | ei_kantaa | epaselva | virhe |
|---|---|---|---|---|---|---|
| kannattaa | 3 | 0 | 0 | 0 | 0 | 0 |
| kannattaa_muutoksin | 1 | 12 | 1 | 1 | 0 | 3 |
| vastustaa | 0 | 1 | 5 | 0 | 0 | 1 |
| ei_kantaa | 0 | 0 | 0 | 3 | 0 | 0 |
| epaselva | 0 | 0 | 0 | 0 | 0 | 0 |

## sonnet · low
- toisto 1: κ 0.678 (95 % 0.39–0.89) · raaka 81% · otehylkäys 0% · virheitä 0 · hinta 0.18 $
- toisto 2: κ 0.745 (95 % 0.52–0.94) · raaka 84% · otehylkäys 0% · virheitä 1 · hinta 0.18 $
- κ toistojen välillä: 0.899

| ihminen \ malli | kannattaa | kannattaa_mu | vastustaa | ei_kantaa | epaselva | virhe |
|---|---|---|---|---|---|---|
| kannattaa | 3 | 0 | 0 | 0 | 0 | 0 |
| kannattaa_muutoksin | 1 | 15 | 1 | 1 | 0 | 0 |
| vastustaa | 0 | 3 | 4 | 0 | 0 | 0 |
| ei_kantaa | 0 | 0 | 0 | 3 | 0 | 0 |
| epaselva | 0 | 0 | 0 | 0 | 0 | 0 |

## Mallien välinen yhtäpitävyys (toisto 1)

- kimi:low vs sonnet:high: κ 0.678
- kimi:low vs sonnet:low: κ 0.896
- kimi:max vs sonnet:high: κ 0.628
- kimi:max vs sonnet:low: κ 0.840

## Päätössääntö (kehikko + T2)

| malli | effort | κ(ihminen) min | otehylkäys max | κ(toistot) | tulos | hinta |
|---|---|---|---|---|---|---|
| kimi | low | 0.634 | 0% | 0.947 | KÄYTTÖÖN | 0.34 $ |
| kimi | max | 0.637 | 0% | 0.947 | KÄYTTÖÖN | 0.67 $ |
| sonnet | high | 0.625 | 0% | 0.910 | KÄYTTÖÖN | 0.37 $ |
| sonnet | low | 0.678 | 0% | 0.899 | KÄYTTÖÖN | 0.35 $ |

## Herkkyys: jäsennin ottaa ensimmäisen JSON-objektin (poikkeama 2)

Ensisijainen tulos ja päätössääntö yllä ovat lukitun jäsentimen mukaiset. Tässä jäsennysvirheet luetaan uudelleen ensimmäisestä kokonaisesta JSON-objektista; muut virheet pysyvät virheinä.

- kimi_low_1: κ 0.634 · raaka 77% · virheitä 0
- kimi_low_2: κ 0.680 · raaka 81% · virheitä 0
- kimi_max_1: κ 0.680 · raaka 81% · virheitä 0
- kimi_max_2: κ 0.637 · raaka 77% · virheitä 0
- sonnet_high_1: κ 0.694 · raaka 81% · virheitä 1
- sonnet_high_2: κ 0.737 · raaka 84% · virheitä 0
- sonnet_low_1: κ 0.678 · raaka 81% · virheitä 0
- sonnet_low_2: κ 0.737 · raaka 84% · virheitä 0

### Valinta

**kimi · low** (κ 0.634).
