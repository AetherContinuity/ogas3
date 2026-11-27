# Polttoainekoe 1 — poikkeama 1 (28.11.2026, ennen analyysin ajoa ja ennen kuin Suomen sarjaa on katsottu)

**Havainto (laskettu ilman dataa).** 2005–2026 on noin 1 140 viikkoa. Tarkalla kiertonollamallilla sallittuja siirtoja on n − 2·16 ≈ 1 108, joten pienin mahdollinen p on noin 0,0009. Ennakkokirjauksen 16 sarjaa × 15 × 5 viivettä tekee 1 200 testiä, ja BH:n tiukin raja on 0,05 / 1 200 ≈ 0,00004. Kirjattu asetelma ei siis voi hyväksyä yhtään ehdokasta, oli datassa mitä tahansa.

**Muutos.** p lasketaan kiertojakaumaan sovitetusta negatiivisesta binomista (keskiarvo ja varianssi kiertojakaumasta; jos varianssi ≤ keskiarvo, käytetään Poissonia): `synapsi.arvioi(..., p_menetelma="nb")`. Tarkka kierto-p raportoidaan rinnalla (`p_tarkka`). Muut ennakkokirjauksen kohdat ennallaan: sarjat, kynnykset, viive, vähimmäissiirto, BH α = 0,05 kaikkien parien yli, odotukset H1–H5 ja tulkinta.

**Kalibrointi ennen ajoa** (synteettinen, sama koko: n = 1 140, 16 sarjaa, purskeiset eli klusteroituvat tapahtumat):
- nollatilanne ilman yhteyksiä: 40 ajosta 0 ajoa, joissa yksikin ehdokas (1 200 testiä per ajo)
- istutettu yhteys viiveellä 1, 60 % tapahtumista kytketty: löytyi 20/20

**Rajoite.** NB-sovitus on approksimaatio. Jos kiertojakauman häntä on raskaampi kuin NB:n, p on liian pieni. Tämä on tarkistettava ehdokkaittain: ehdokas, jonka `p_tarkka` on lähellä 1/(K+1), on havaittu kaikkien kiertojen yläpuolella. Ehdokas, jonka `p_tarkka` on selvästi suurempi, nojaa approksimaation häntään. Tämä raportoidaan.
