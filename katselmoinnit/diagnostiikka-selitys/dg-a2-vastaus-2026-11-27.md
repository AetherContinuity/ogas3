# Katselmointi (LLM) — lausunto, ei mittaus

```json
{
 "pyynto": "katselmoinnit/diagnostiikka-selitys/dg-a2-pyynto.txt",
 "pyynto_sha256": "f88116b5c1632d90424f099f12f789be230c34364dfffbc2706d4d7679375d02",
 "malli": "kimi-k3.1-pro",
 "response_model": "kimi-k3.1-pro",
 "effort": "max",
 "aika": "2026-11-27T19:13:47+00:00",
 "finish_reason": "stop",
 "usage": {
  "prompt_tokens": 4111,
  "completion_tokens": 15187,
  "total_tokens": 19298,
  "completion_tokens_details": {
   "reasoning_tokens": 13141
  },
  "prompt_tokens_details": {
   "cache_write_tokens": 4096
  }
 },
 "hinta_usd": 0.1601
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
      "kohta": "§ Havainnot",
      "lainaus": "Hälytysreitti, joka kulkee kahden urakka-alueen rajalla, aurataan viimeisenä kummallakin alueella.",
      "merkinta": "ei_merkitty",
      "tiedosto": "papers/dg-001-seudullinen-talvikunnossapito.html"
    },
    {
      "id": "DG-001:003",
      "paperi": "DG-001",
      "kohta": "§ Kaksi vajetta",
      "lainaus": "Sama kahden vajeen rakenne toistuu seudun kaikissa kunnissa.",
      "merkinta": "ei_merkitty",
      "tiedosto": "papers/dg-001-seudullinen-talvikunnossapito.html"
    },
    {
      "id": "DG-001:004",
      "paperi": "DG-001",
      "kohta": "§ Kaksi vajetta",
      "lainaus": "Tietovaje: kunnat eivät tiedä toistensa kalustosta eivätkä sen käyttöasteesta.",
      "merkinta": "ei_merkitty",
      "tiedosto": "papers/dg-001-seudullinen-talvikunnossapito.html"
    },
    {
      "id": "DG-001:005",
      "paperi": "DG-001",
      "kohta": "§ Kaksi vajetta",
      "lainaus": "Sopimusvaje: urakkasopimukset eivät salli kaluston siirtämistä urakka-alueen ulkopuolelle.",
      "merkinta": "ei_merkitty",
      "tiedosto": "papers/dg-001-seudullinen-talvikunnossapito.html"
    },
    {
      "id": "DG-001:006",
      "paperi": "DG-001",
      "kohta": "§ Johtopäätökset",
      "lainaus": "Ankarana talvena hälytysreittien aukipito riippuu siitä, minkä urakan kalusto sattuu olemaan lähimpänä.",
      "merkinta": "ei_merkitty",
      "tiedosto": "papers/dg-001-seudullinen-talvikunnossapito.html"
    },
    {
      "id": "DG-001:007",
      "paperi": "DG-001",
      "kohta": "§ Johtopäätökset",
      "lainaus": "Kunta arvioi katuverkkoa, maakunta päätieverkkoa ja pelastuslaitos hälytysreittejä.",
      "merkinta": "ei_merkitty",
      "tiedosto": "papers/dg-001-seudullinen-talvikunnossapito.html"
    },
    {
      "id": "DG-001:008",
      "paperi": "DG-001",
      "kohta": "§ Johtopäätökset",
      "lainaus": "Yhteisen varakaluston arvo ei kuulu kenenkään tehtävään",
      "merkinta": "ei_merkitty",
      "tiedosto": "papers/dg-001-seudullinen-talvikunnossapito.html"
    },
    {
      "id": "DG-001:009",
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
      "lahde": "DG-001:006",
      "kohde": "DG-001:001",
      "laji": "depends_on",
      "perusta": "eksplisiittinen",
      "perustelu": "Päätelmän mukaan se seuraa suoraan siitä, että urakoitsijat hoitavat ensin omat kohteensa; tämä toistaa Havainnot-kohdan väitteen.",
      "kirjaaja": "kimi-k3.1-pro",
      "tila": "ehdotettu"
    },
    {
      "id": "S002",
      "lahde": "DG-001:006",
      "kohde": "DG-001:002",
      "laji": "depends_on",
      "perusta": "rekonstruoitu",
      "perustelu": "§ Johtopäätökset perustelee päätelmää reittien rajojen ylityksellä ja omien kohteiden etusijalla. § Havainnot esittää yhdistävänä välivaiheena, että kahden alueen rajalla kulkeva reitti aurataan viimeisenä kummallakin alueella.",
      "kirjaaja": "kimi-k3.1-pro",
      "tila": "ehdotettu"
    },
    {
      "id": "S003",
      "lahde": "DG-001:004",
      "kohde": "DG-001:003",
      "laji": "qualifies",
      "perusta": "eksplisiittinen",
      "perustelu": "Tietovaje-virke täsmentää yleisväitteessä mainitun kahden vajeen rakenteen ensimmäisen vajeen sisällön.",
      "kirjaaja": "kimi-k3.1-pro",
      "tila": "ehdotettu"
    },
    {
      "id": "S004",
      "lahde": "DG-001:005",
      "kohde": "DG-001:003",
      "laji": "qualifies",
      "perusta": "eksplisiittinen",
      "perustelu": "Sopimusvaje-virke täsmentää yleisväitteessä mainitun kahden vajeen rakenteen toisen vajeen sisällön.",
      "kirjaaja": "kimi-k3.1-pro",
      "tila": "ehdotettu"
    },
    {
      "id": "S005",
      "lahde": "DG-001:008",
      "kohde": "DG-001:007",
      "laji": "depends_on",
      "perusta": "eksplisiittinen",
      "perustelu": "Kappale alkaa selityksellä 'Miksi tätä ei ole arvioitu' ja esittää toimijakohtaiset arvioinnit välittömästi ennen väitettä siitä, ettei yhteisen varakaluston arvo kuulu kenellekään.",
      "kirjaaja": "kimi-k3.1-pro",
      "tila": "ehdotettu"
    },
    {
      "id": "S006",
      "lahde": "DG-001:008",
      "kohde": "DG-001:009",
      "laji": "depends_on",
      "perusta": "eksplisiittinen",
      "perustelu": "Sama virke yhdistää väitteet sanalla 'koska': arvo ei kuulu kenenkään tehtävään, koska se syntyy vasta verkkojen yhdessä tarkastelussa.",
      "kirjaaja": "kimi-k3.1-pro",
      "tila": "ehdotettu"
    }
  ]
}
```

Huomioita:
- Tieto- ja sopimusvajetta ei yhdistetty loppupäätelmiin riippuvuuksina, koska paperi ei nimeä niitä niiden perusteiksi.
- Virkettä ”Tämä ei ole hankintaehdotus” ei liitetty yksittäiseen väitteeseen, koska sen täsmällinen kohde jää auki.
