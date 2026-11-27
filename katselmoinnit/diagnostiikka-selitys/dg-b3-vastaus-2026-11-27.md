# Katselmointi (LLM) — lausunto, ei mittaus

```json
{
 "pyynto": "katselmoinnit/diagnostiikka-selitys/dg-b3-pyynto.txt",
 "pyynto_sha256": "e448244d093bdb009ebad89fff405a825b760f44dd2aa83d82dcc3d445181f21",
 "malli": "kimi-k3.1-pro",
 "response_model": "kimi-k3.1-pro",
 "effort": "max",
 "aika": "2026-11-27T19:13:16+00:00",
 "finish_reason": "stop",
 "usage": {
  "prompt_tokens": 4111,
  "completion_tokens": 11550,
  "total_tokens": 15661,
  "completion_tokens_details": {
   "reasoning_tokens": 10096
  },
  "prompt_tokens_details": {
   "cache_write_tokens": 4096
  }
 },
 "hinta_usd": 0.1237
}
```

```json
{
  "esiintymat": [
    {
      "id": "DG-001:001",
      "paperi": "DG-001",
      "kohta": "§ Havainnot",
      "lainaus": "Ankarana talvena urakoitsijat hoitavat ensin oman sopimuksensa kohteet.",
      "merkinta": "ei_merkitty",
      "tiedosto": "papers/dg-001-seudullinen-talvikunnossapito.html"
    },
    {
      "id": "DG-001:002",
      "paperi": "DG-001",
      "kohta": "§ Johtopäätökset",
      "lainaus": "Ankarana talvena hälytysreittien aukipito riippuu siitä, minkä urakan kalusto sattuu olemaan lähimpänä.",
      "merkinta": "ei_merkitty",
      "tiedosto": "papers/dg-001-seudullinen-talvikunnossapito.html"
    },
    {
      "id": "DG-001:003",
      "paperi": "DG-001",
      "kohta": "§ Johtopäätökset",
      "lainaus": "reitit ylittävät urakka-alueiden rajoja",
      "merkinta": "ei_merkitty",
      "tiedosto": "papers/dg-001-seudullinen-talvikunnossapito.html"
    },
    {
      "id": "DG-001:004",
      "paperi": "DG-001",
      "kohta": "§ Johtopäätökset",
      "lainaus": "Kunta arvioi katuverkkoa, maakunta päätieverkkoa ja pelastuslaitos hälytysreittejä.",
      "merkinta": "ei_merkitty",
      "tiedosto": "papers/dg-001-seudullinen-talvikunnossapito.html"
    },
    {
      "id": "DG-001:005",
      "paperi": "DG-001",
      "kohta": "§ Johtopäätökset",
      "lainaus": "Yhteisen varakaluston arvo ei kuulu kenenkään tehtävään",
      "merkinta": "ei_merkitty",
      "tiedosto": "papers/dg-001-seudullinen-talvikunnossapito.html"
    },
    {
      "id": "DG-001:006",
      "paperi": "DG-001",
      "kohta": "§ Johtopäätökset",
      "lainaus": "se syntyy vasta, kun verkot tarkastellaan yhdessä",
      "merkinta": "ei_merkitty",
      "tiedosto": "papers/dg-001-seudullinen-talvikunnossapito.html"
    }
  ],
  "suhteet": [
    {
      "id": "S001",
      "lahde": "DG-001:002",
      "kohde": "DG-001:001",
      "laji": "depends_on",
      "perusta": "eksplisiittinen",
      "perustelu": "Johtopäätökset-kohdan 'Tämä seuraa suoraan' -virke nimeää perusteeksi urakoitsijoiden omien kohteiden ensisijaisen hoidon. Havainnot-kohdan esiintymä sisältää tämän perusteen.",
      "kirjaaja": "kimi-k3.1-pro",
      "tila": "ehdotettu"
    },
    {
      "id": "S002",
      "lahde": "DG-001:002",
      "kohde": "DG-001:003",
      "laji": "depends_on",
      "perusta": "eksplisiittinen",
      "perustelu": "Sama 'Tämä seuraa suoraan' -virke nimeää päätelmän toiseksi perusteeksi reittien urakka-alueiden rajojen ylittämisen.",
      "kirjaaja": "kimi-k3.1-pro",
      "tila": "ehdotettu"
    },
    {
      "id": "S003",
      "lahde": "DG-001:005",
      "kohde": "DG-001:006",
      "laji": "depends_on",
      "perusta": "eksplisiittinen",
      "perustelu": "Sama virke sitoo päätelmän 'koska'-sanalla siihen, että arvo syntyy vasta, kun verkot tarkastellaan yhdessä.",
      "kirjaaja": "kimi-k3.1-pro",
      "tila": "ehdotettu"
    },
    {
      "id": "S004",
      "lahde": "DG-001:005",
      "kohde": "DG-001:004",
      "laji": "depends_on",
      "perusta": "rekonstruoitu",
      "perustelu": "Johtopäätökset-kohdassa erilliset arvioinnit ja niitä tiivistävä väite 'Kukin hoitaa oman osuutensa' edeltävät päätelmää, jonka koska-peruste on verkkojen yhteistarkastelu. Kirjoittamaton välivaihe on, että erilliset osuudet eivät kata yhteistarkastelusta syntyvää arvoa.",
      "kirjaaja": "kimi-k3.1-pro",
      "tila": "ehdotettu"
    }
  ]
}
```

En yhdistänyt § Kaksi vajetta -kohdan tieto- tai sopimusvajetta johtopäätöksiin, koska paperi ei osoita niitä päätelmien perusteiksi.

En kirjannut rajalla aurattavaa hälytysreittiä koskevaa havaintoa päätelmän tueksi: § Johtopäätökset nimeää suoraan vain rajojen ylittämisen ja omien kohteiden ensisijaisen hoidon.
