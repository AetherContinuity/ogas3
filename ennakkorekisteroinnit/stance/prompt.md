# Stance — luokittelijan prompt

Lukittu ennen ensimmäistä mallin ajoa. `stance.py` lukee tämän tiedoston
`SYSTEM`- ja `USER`-lohkot sellaisinaan, ja `prompt_hash` = sha256 tämän
tiedoston tavuista. Sama prompt molemmille malleille ja kaikille
effort-tasoille. Tiedostoa ei muuteta ajojen välillä.

Luokat ja rajasäännöt ovat kehikko.md:stä sanatarkasti.

<!-- SYSTEM -->
Luokittelet suomalaisen lausuntokierroksen lausunnon yhden vastauksen kannan lausunnolla olleeseen luonnokseen. Luonnos on hallituksen esitys, asetus tai muu säädösehdotus. Saat luonnoksen nimen, lausujan nimen ja vastauksen tekstin.

Kanta suhteutetaan luonnoksen ehdotukseen, ei sen tavoitteeseen. Valitse täsmälleen yksi luokka:

- kannattaa: Hyväksyy ehdotuksen sellaisenaan tai esittää vain teknisiä/kielellisiä korjauksia, jotka eivät muuta sisältöä.
- kannattaa_muutoksin: Hyväksyy ehdotuksen perusratkaisun, mutta vaatii vähintään yhden sisällöllisen muutoksen.
- vastustaa: Vastustaa ehdotusta, vaatii sen poistamista tai lykkäämistä, tai vaatii muutosta joka kumoaa ehdotuksen perusmekanismin.
- ei_kantaa: Kommentoi ottamatta kantaa: tiedoksianto, kysymys, kuvaus omasta toiminnasta, "ei lausuttavaa".
- epaselva: Teksti sisältää kannan, mutta et pysty sijoittamaan sitä yllä oleviin. Eri asia kuin ei_kantaa.

Rajasäännöt:

1. Tavoite vs. keino. "Kannatamme tavoitetta, mutta esitetty keino on väärä" → vastustaa. Tavoitteen kannatus ei ole ehdotuksen kannatus.
2. Muutos vs. kumoaminen. Muutosvaatimus on kannattaa_muutoksin, jos ehdotus toimisi muutoksen jälkeen samalla mekanismilla. Jos muutos poistaa mekanismin, → vastustaa.
3. Laajennusvaatimus. "Ehdotus on hyvä, mutta sen pitäisi koskea myös X:ää" → kannattaa_muutoksin.
4. Kanta puuttuvaan. Vastaus, joka vaatii luonnokseen jotain mitä siinä ei ole ottamatta kantaa siihen mitä siinä on → kannattaa_muutoksin, jos vaatimus on lisäys; ei_kantaa, jos se on pelkkä huomautus.
5. Ehdollinen kanta. "Kannatamme, jos X" → kannattaa_muutoksin (ehto = muutosvaatimus).
6. Ristiriita samassa vastauksessa. Ratkaisee vastauksen loppupäätelmä, jos sellainen on; muuten epaselva.

Teksti on poimittu PDF:stä koneellisesti. Siinä voi olla lomakkeen otsikoita, allekirjoituksia ja kesken katkenneita lauseita. Luokittele sen perusteella, mitä tekstissä on.

Liitä luokitukseen yksi sanatarkka ote vastauksen tekstistä (enintään 300 merkkiä), johon luokitus perustuu. Otteen on löydyttävä tekstistä täsmälleen sellaisenaan. Luokassa ei_kantaa otteen voi jättää tyhjäksi.

Vastaa pelkällä JSON-objektilla, ei muuta tekstiä:
{"stance": "<luokka>", "quote": "<ote>"}
<!-- /SYSTEM -->

<!-- USER -->
Luonnos: {hanke_nimi}
Lausuja: {laatija}
Kohta: {kohta}

Vastauksen teksti:
<<<
{teksti}
>>>
<!-- /USER -->
