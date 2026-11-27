# Katselmointi (LLM) — lausunto, ei mittaus

```json
{
 "pyynto": "katselmoinnit/diagnostiikka-selitys/dg-a1-pyynto.txt",
 "pyynto_sha256": "f88116b5c1632d90424f099f12f789be230c34364dfffbc2706d4d7679375d02",
 "malli": "kimi-k3.1-pro",
 "response_model": "kimi-k3.1-pro",
 "effort": "max",
 "aika": "2026-11-27T19:12:52+00:00",
 "finish_reason": "stop",
 "usage": {
  "prompt_tokens": 4111,
  "completion_tokens": 15289,
  "total_tokens": 19400,
  "completion_tokens_details": {
   "reasoning_tokens": 13450
  },
  "prompt_tokens_details": {
   "cache_write_tokens": 4096
  }
 },
 "hinta_usd": 0.1611
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
      "lainaus": "Yhteisen varakaluston arvo ei kuulu kenenkään tehtävään, koska se syntyy vasta, kun verkot tarkastellaan yhdessä.",
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
      "perustelu": "Johtopäätökset-osan seuraava virke sanoo päätelmän seuraavan suoraan siitä, että urakoitsijat hoitavat ensin omat kohteensa. Tämä on Havainnot-osan esiintymässä esitetty havainto.",
      "kirjaaja": "kimi-k3.1-pro",
      "tila": "ehdotettu"
    },
    {
      "id": "S002",
      "lahde": "DG-001:006",
      "kohde": "DG-001:002",
      "laji": "depends_on",
      "perusta": "rekonstruoitu",
      "perustelu": "Johtopäätökset-osassa rajojen ylittävät reitit nimetään päätelmän välittömäksi perusteeksi. Yhteys Havainnot-osan esiintymään vaatii välivaiheen, jossa kahden urakka-alueen rajalla kulkeva ja viimeisenä aurattava hälytysreitti liitetään tähän yleiseen rajanylitysperusteeseen.",
      "kirjaaja": "kimi-k3.1-pro",
      "tila": "ehdotettu"
    },
    {
      "id": "S003",
      "lahde": "DG-001:004",
      "kohde": "DG-001:003",
      "laji": "qualifies",
      "perusta": "eksplisiittinen",
      "perustelu": "Kahden vajeen yhteenveto täsmennetään välittömästi seuraavassa virkkeessä: Tietovaje nimeää ensimmäisen vajeen ja kertoo sen sisällön.",
      "kirjaaja": "kimi-k3.1-pro",
      "tila": "ehdotettu"
    },
    {
      "id": "S004",
      "lahde": "DG-001:005",
      "kohde": "DG-001:003",
      "laji": "qualifies",
      "perusta": "eksplisiittinen",
      "perustelu": "Tietovajeen jälkeen Sopimusvaje nimeää yhteenvetoväitteen toisen vajeen ja täsmentää sen koskemaan kaluston siirtämistä urakka-alueen ulkopuolelle.",
      "kirjaaja": "kimi-k3.1-pro",
      "tila": "ehdotettu"
    },
    {
      "id": "S005",
      "lahde": "DG-001:008",
      "kohde": "DG-001:007",
      "laji": "depends_on",
      "perusta": "eksplisiittinen",
      "perustelu": "Johtopäätökset-osan selitys kysymykseen Miksi tätä ei ole arvioitu etenee tahojen erillisistä verkkoarvioinneista väitteen Kukin hoitaa oman osuutensa kautta siihen, ettei yhteisen varakaluston arvo kuulu kenellekään.",
      "kirjaaja": "kimi-k3.1-pro",
      "tila": "ehdotettu"
    }
  ]
}
```

En yhdistänyt tieto- tai sopimusvajetta johtopäätöksiin, koska paperi ei esitä niitä niiden perusteina.
