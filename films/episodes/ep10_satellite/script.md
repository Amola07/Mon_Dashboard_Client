# Épisode 10 — « Pourquoi un satellite ne tombe jamais ? »

## Ce que font les vidéos de référence (mathoholic.ch : satellite, écran, avion, voix au téléphone)
- **Sujet** : comment fonctionne un objet du quotidien qu'on croit comprendre. On ne raconte pas une anecdote :
  on démonte un mécanisme, étape par étape.
- **Accroche** : un paradoxe en 2 phrases + une question (« sans moteur… pourquoi ne tombe-t-il pas ? »), puis un
  retournement immédiat qui contredit l'intuition.
- **Rythme** : phrases très courtes (5 à 12 mots), une idée par phrase, une image par phrase. Chiffres précis.
  Chaque bloc ouvre une nouvelle question → on reste pour la réponse suivante.
- **Durée** : 2 à 3,5 min (éligible à la rémunération, temps de visionnage élevé si le rythme tient).
- **Fin** : retour vers le spectateur et son quotidien (« quand tu utilises ton téléphone… »), ton émouvant.
- **Image** : hologramme bleu sur fond noir, un plan par phrase, sous-titres d'une ligne au centre bas.

Script ci-dessous : écrit pour nous (texte original), même mécanique. Durée estimée : 1 min 50 à 2 min 10.

## Texte à générer (ElevenLabs, balises d'émotion)

```
[intrigued] Au-dessus de ta tête, des milliers de machines filent dans le noir. Sans moteur allumé. Sans rien pour les retenir. [short pause] Alors pourquoi elles ne tombent pas ?

[serious] La réponse va te surprendre : elles tombent. [short pause] Tout le temps. Depuis des années.

[calm] Imagine une montagne si haute qu'elle dépasse l'atmosphère. Au sommet, un canon. [short pause] Tu tires doucement : le boulet retombe un peu plus loin. Tu tires plus fort : il retombe encore plus loin.

[amazed] Et si tu tires assez fort… le sol se courbe sous lui avant qu'il ne le touche. [slowly] Il tombe, encore et encore… mais il rate la Terre, à chaque fois.

[serious] C'est ça, une orbite. Une chute qui ne finit jamais.

[fast] À quatre cents kilomètres d'altitude, il faut filer à vingt-huit mille kilomètres-heure. Plus lent : tu t'écrases. Plus rapide : tu t'échappes dans l'espace.

[intrigued] Et la gravité, là-haut ? [short pause] Elle est presque aussi forte qu'ici. Environ quatre-vingt-dix pour cent. [softly] Les astronautes ne flottent pas. Ils tombent… en même temps que leur station.

[amazed] À cette vitesse, ils font le tour de la Terre en une heure et demie. Seize levers de soleil… par jour.

[mysterious] Plus haut, à trente-six mille kilomètres, il se passe quelque chose d'étrange. [short pause] Un satellite y tourne exactement à la vitesse de la Terre. Vu d'ici… il ne bouge plus. [short pause] C'est pour ça que ta parabole reste pointée au même endroit, toute ta vie.

[intrigued] Et ton GPS ? [short pause] Il écoute des horloges atomiques qui volent au-dessus de toi. Mais là-haut… le temps ne s'écoule pas à la même vitesse. [serious] Einstein avait raison : sans correction, ta position serait fausse de dix kilomètres chaque jour.

[ominous] Mais un satellite ne vit pas éternellement. Quand il n'a plus de carburant pour corriger sa trajectoire, il meurt… et continue de tourner. [short pause] Des millions de débris filent déjà autour de nous, plus vite qu'une balle. Une seule collision peut en créer des milliers d'autres.

[thoughtful] Alors la prochaine fois que tu regardes une carte, la météo, ou l'heure sur ton téléphone… [short pause] pense à ces machines qui tombent sans fin au-dessus de toi. [whispers] Juste assez vite… pour ne jamais arriver.
```

Conseil voix : démarrer sans silence ; « elles tombent. » sec, juste après la question (≈ 6 s).

## Vérification des faits
- Satellites actifs : plus de 10 000 en 2025 (la majorité Starlink) → « des milliers », sans chiffre exact.
- Canon de Newton : expérience de pensée de Newton (*De mundi systemate*, 1728).
- Orbite basse (≈ 400 km, Station spatiale) : ≈ 7,66 km/s ≈ 27 600 km/h → « vingt-huit mille » ; un tour en ≈ 92 min ;
  ≈ 16 levers de soleil par jour.
- Gravité à 400 km : g × (6371 / 6771)² ≈ 0,89 g → « environ 90 % ».
- Orbite géostationnaire : 35 786 km d'altitude (« trente-six mille ») ; période = un jour sidéral ; utilisée pour la
  télévision par satellite (paraboles fixes).
- GPS : horloges atomiques à bord ; effets relativistes cumulés ≈ +38 µs/jour ; non corrigés, l'erreur de distance
  croîtrait d'environ 10 km par jour (38 µs × vitesse de la lumière ≈ 11 km).
- Débris : estimations ESA ≈ 1 million d'objets de plus de 1 cm, plus de 100 millions de plus de 1 mm → « des millions »;
  vitesse relative jusqu'à ≈ 10 km/s, bien au-delà d'une balle (≈ 1 km/s). Réaction en chaîne : syndrome de Kessler.
