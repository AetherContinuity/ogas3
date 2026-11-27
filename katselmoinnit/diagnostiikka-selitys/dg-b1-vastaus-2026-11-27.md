# Katselmointi (LLM) — lausunto, ei mittaus

```json
{
 "pyynto": "katselmoinnit/diagnostiikka-selitys/dg-b1-pyynto.txt",
 "pyynto_sha256": "e448244d093bdb009ebad89fff405a825b760f44dd2aa83d82dcc3d445181f21",
 "malli": "kimi-k3.1-pro",
 "response_model": "kimi-k3.1-pro",
 "effort": "max",
 "aika": "2026-11-27T19:14:01+00:00",
 "finish_reason": "stop",
 "usage": {
  "prompt_tokens": 4111,
  "completion_tokens": 15594,
  "total_tokens": 19705,
  "completion_tokens_details": {
   "reasoning_tokens": 13162
  },
  "prompt_tokens_details": {
   "cache_write_tokens": 4096
  }
 },
 "hinta_usd": 0.1642
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
      "kohta": "§ Kaksi vajetta",
      "lainaus": "Sama kahden vajeen rakenne toistuu seudun kaikissa kunnissa.",
      "merkinta": "ei_merkitty",
      "tiedosto": "papers/dg-001-seudullinen-talvikunnossapito.html"
    },
    {
      "id": "DG-001:003",
      "paperi": "DG-001",
      "kohta": "§ Kaksi vajetta",
      "lainaus": "kunnat eivät tiedä toistensa kalustosta eivätkä sen käyttöasteesta.",
      "merkinta": "ei_merkitty",
      "tiedosto": "papers/dg-001-seudullinen-talvikunnossapito.html"
    },
    {
      "id": "DG-001:004",
      "paperi": "DG-001",
      "kohta": "§ Kaksi vajetta",
      "lainaus": "urakkasopimukset eivät salli kaluston siirtämistä urakka-alueen ulkopuolelle.",
      "merkinta": "ei_merkitty",
      "tiedosto": "papers/dg-001-seudullinen-talvikunnossapito.html"
    },
    {
      "id": "DG-001:005",
      "paperi": "DG-001",
      "kohta": "§ Johtopäätökset",
      "lainaus": "Ankarana talvena hälytysreittien aukipito riippuu siitä, minkä urakan kalusto sattuu olemaan lähimpänä.",
      "merkinta": "ei_merkitty",
      "tiedosto": "papers/dg-001-seudullinen-talvikunnossapito.html"
    },
    {
      "id": "DG-001:006",
      "paperi": "DG-001",
      "kohta": "§ Johtopäätökset",
      "lainaus": "reitit ylittävät urakka-alueiden rajoja",
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
    },
    {
      "id": "DG-001:010",
      "paperi": "DG-001",
      "kohta": "§ Johtopäätökset",
      "lainaus": "Tämä ei ole hankintaehdotus.",
      "merkinta": "ei_merkitty",
      "tiedosto": "papers/dg-001-seudullinen-talvikunnossapito.html"
    }
  ],
  "suhteet": [
    {
      "id": "S001",
      "lahde": "DG-001:003",
      "kohde": "DG-001:002",
      "laji": "qualifies",
      "perusta": "eksplisiittinen",
      "perustelu": "§ Kaksi vajetta -kohdan yleisväite täsmentyy heti seuraavaksi nimettyyn tietovajeeseen. Väite DG-001:003 täsmentää siten, mitä yksi väitteen DG-001:002 kahdesta vajeesta sisältää.",
      "kirjaaja": "kimi-k3.1-pro",
      "tila": "ehdotettu"
    },
    {
      "id": "S002",
      "lahde": "DG-001:004",
      "kohde": "DG-001:002",
      "laji": "qualifies",
      "perusta": "eksplisiittinen",
      "perustelu": "Sopimusvaje on toinen väitteen DG-001:002 kahden vajeen rakenteelle heti nimetty osa. Väite DG-001:004 täsmentää yleisväitettä sen sopimuksia koskevalla osalla.",
      "kirjaaja": "kimi-k3.1-pro",
      "tila": "ehdotettu"
    },
    {
      "id": "S003",
      "lahde": "DG-001:005",
      "kohde": "DG-001:001",
      "laji": "depends_on",
      "perusta": "eksplisiittinen",
      "perustelu": "§ Johtopäätökset -kohdan toinen virke sanoo väitteen DG-001:005 seuraavan suoraan siitä, että urakoitsijat hoitavat ensin omat kohteensa. Tämä on § Havainnot -kohdan väitteen DG-001:001 sisältö.",
      "kirjaaja": "kimi-k3.1-pro",
      "tila": "ehdotettu"
    },
    {
      "id": "S004",
      "lahde": "DG-001:005",
      "kohde": "DG-001:006",
      "laji": "depends_on",
      "perusta": "eksplisiittinen",
      "perustelu": "Väitettä DG-001:005 seuraava virke alkaa 'Tämä seuraa suoraan siitä, että' ja nimeää reittien urakka-alueiden rajojen ylittämisen ensimmäiseksi perusteeksi.",
      "kirjaaja": "kimi-k3.1-pro",
      "tila": "ehdotettu"
    },
    {
      "id": "S005",
      "lahde": "DG-001:008",
      "kohde": "DG-001:009",
      "laji": "depends_on",
      "perusta": "eksplisiittinen",
      "perustelu": "Väitteiden välinen syy-yhteys nimetään sanalla 'koska': yhteisen varakaluston arvo ei kuulu kenenkään tehtävään, koska se syntyy vasta verkkojen yhteistarkastelussa.",
      "kirjaaja": "kimi-k3.1-pro",
      "tila": "ehdotettu"
    },
    {
      "id": "S006",
      "lahde": "DG-001:008",
      "kohde": "DG-001:007",
      "laji": "depends_on",
      "perusta": "rekonstruoitu",
      "perustelu": "§ Johtopäätökset -kohdan alaosa 'Miksi tätä ei ole arvioitu' esittää erilliset arvioinnit DG-001:007 ennen väitettä DG-001:008. Välivaihe on kohdan virke 'Kukin hoitaa oman osuutensa': erillinen tehtäväjako yhdessä väitteen DG-001:009 kanssa johtaa siihen, ettei yhteistarkastelusta syntyvä arvo kuulu kenenkään omaan osuuteen.",
      "kirjaaja": "kimi-k3.1-pro",
      "tila": "ehdotettu"
    },
    {
      "id": "S007",
      "lahde": "DG-001:010",
      "kohde": "DG-001:008",
      "laji": "qualifies",
      "perusta": "eksplisiittinen",
      "perustelu": "Väite DG-001:010 seuraa välittömästi yhteisen varakaluston arvoa käsittelevää väitettä DG-001:008. Sen 'Tämä'-viittaus rajaa edeltävän tarkastelun pois hankintaehdotuksesta.",
      "kirjaaja": "kimi-k3.1-pro",
      "tila": "ehdotettu"
    }
  ]
}
```

- Aineistossa ei ole rivinumeroita, joten perustelut viittaavat kohtatunnuksiin.
- Vajeita ei yhdistetty hälytysreittipäätelmään tai varakaluston arvoon, koska paperi ei osoita näitä riippuvuuksia.
- Havainto reitin auraamisesta viimeisenä jätettiin ilman suhdetta: pelkkä vierekkäisyys ei riitä osoittamaan riippuvuutta.
