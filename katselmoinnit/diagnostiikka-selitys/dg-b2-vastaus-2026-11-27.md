# Katselmointi (LLM) — lausunto, ei mittaus

```json
{
 "pyynto": "katselmoinnit/diagnostiikka-selitys/dg-b2-pyynto.txt",
 "pyynto_sha256": "e448244d093bdb009ebad89fff405a825b760f44dd2aa83d82dcc3d445181f21",
 "malli": "kimi-k3.1-pro",
 "response_model": "kimi-k3.1-pro",
 "effort": "max",
 "aika": "2026-11-27T19:16:28+00:00",
 "finish_reason": "stop",
 "usage": {
  "prompt_tokens": 4111,
  "completion_tokens": 17557,
  "total_tokens": 21668,
  "completion_tokens_details": {
   "reasoning_tokens": 15765
  },
  "prompt_tokens_details": {
   "cache_write_tokens": 4096
  }
 },
 "hinta_usd": 0.1838
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
      "kohta": "§ Johtopäätökset",
      "lainaus": "Ankarana talvena hälytysreittien aukipito riippuu siitä, minkä urakan kalusto sattuu olemaan lähimpänä.",
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
      "lainaus": "Kukin hoitaa oman osuutensa.",
      "merkinta": "ei_merkitty",
      "tiedosto": "papers/dg-001-seudullinen-talvikunnossapito.html"
    },
    {
      "id": "DG-001:006",
      "paperi": "DG-001",
      "kohta": "§ Johtopäätökset",
      "lainaus": "Yhteisen varakaluston arvo ei kuulu kenenkään tehtävään",
      "merkinta": "ei_merkitty",
      "tiedosto": "papers/dg-001-seudullinen-talvikunnossapito.html"
    },
    {
      "id": "DG-001:007",
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
      "lahde": "DG-001:003",
      "kohde": "DG-001:001",
      "laji": "depends_on",
      "perusta": "eksplisiittinen",
      "perustelu": "Johtopäätökset-kohdan ”Tämä seuraa suoraan” -lause nimeää perusteeksi urakoitsijoiden oman alueen kohteiden ensisijaisen hoidon eli Havainnot-kohdan väitteen 001.",
      "kirjaaja": "kimi-k3.1-pro",
      "tila": "ehdotettu"
    },
    {
      "id": "S002",
      "lahde": "DG-001:003",
      "kohde": "DG-001:002",
      "laji": "depends_on",
      "perusta": "rekonstruoitu",
      "perustelu": "Johtopäätökset-kohta nimeää perusteeksi reittien urakka-alueiden rajojen ylityksen, ja Havainnot-kohta kuvaa kahden urakka-alueen rajalla kulkevan reitin aurattavan viimeisenä. Rekonstruktion välivaihe on tämän raja-aluehavainnon liittäminen päätelmän yleiseen reittiperusteeseen.",
      "kirjaaja": "kimi-k3.1-pro",
      "tila": "ehdotettu"
    },
    {
      "id": "S003",
      "lahde": "DG-001:006",
      "kohde": "DG-001:004",
      "laji": "depends_on",
      "perusta": "rekonstruoitu",
      "perustelu": "Johtopäätökset-kohdan selitys alkaa sanoilla ”Miksi tätä ei ole arvioitu”, ja erilliset arviointivastuut esitetään tässä selityksessä ennen väitettä 006. Välivaihe on, että erikseen tehdyt verkkoarvioinnit eivät ole väitteen 007 edellyttämää verkkojen yhteistarkastelua.",
      "kirjaaja": "kimi-k3.1-pro",
      "tila": "ehdotettu"
    },
    {
      "id": "S004",
      "lahde": "DG-001:006",
      "kohde": "DG-001:005",
      "laji": "depends_on",
      "perusta": "rekonstruoitu",
      "perustelu": "Väite 005 tiivistää tehtäväjaon ja edeltää välittömästi väitettä 006 Johtopäätökset-kohdan samassa selityksessä. Välivaihe on, että pelkät omat osuudet jättävät väitteen 007 kuvaaman verkkojen yhteistarkastelun tehtäväjaon ulkopuolelle.",
      "kirjaaja": "kimi-k3.1-pro",
      "tila": "ehdotettu"
    },
    {
      "id": "S005",
      "lahde": "DG-001:006",
      "kohde": "DG-001:007",
      "laji": "depends_on",
      "perusta": "eksplisiittinen",
      "perustelu": "Väitteet 006 ja 007 ovat samassa lauseessa, ja koska-rakenne esittää arvon syntymisen vain verkkojen yhteistarkastelussa suoraan väitteen 006 perusteeksi.",
      "kirjaaja": "kimi-k3.1-pro",
      "tila": "ehdotettu"
    }
  ]
}
```

- En liittänyt tieto- tai sopimusvajetta johtopäätöksiin, koska paperi ei osoita näitä riippuvuuksia.
- Lopun hankintaehdotusta koskevasta lauseesta en kirjannut qualifies-suhdetta, koska sen täsmällistä kohdeväitettä ei ilmoiteta.
