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

Style d'écriture repris des références : vouvoiement, phrases déclaratives très courtes, triades
(« sans moteur, sans carburant, sans… »), sentences-chocs (« La vitesse est la clé. »), un bloc par fonction,
ton de documentaire neutre, fin « Souvenez-vous ». Texte original. Durée estimée : 2 min 30 à 3 min.

## Texte à générer (ElevenLabs — balises sobres, voix de narrateur posée)

```
[serious] Des milliers de satellites tournent au-dessus de vous. Sans aile. Sans moteur allumé. Sans câble pour les retenir. [short pause] Pourquoi ne tombent-ils pas ?

[intrigued] Parce qu'ils tombent. [short pause] En permanence.

[calm] Un satellite est en chute libre. Il tombe vers la Terre à chaque instant. Mais il avance si vite que la Terre se dérobe sous lui. Le sol s'éloigne aussi vite qu'il tombe. Il ne touche jamais.

[serious] C'est le principe de l'orbite. Une chute sans fin.

Newton l'avait compris il y a plus de trois cents ans. Un boulet tiré du haut d'une montagne retombe plus loin. Tiré plus fort, encore plus loin. Tiré assez fort, il fait le tour de la planète.

[calm] La vitesse est la clé. Vingt-huit mille kilomètres-heure à quatre cents kilomètres d'altitude. Un tour de la Terre en quatre-vingt-dix minutes. Trop lent, il retombe. Trop rapide, il s'en va. [short pause] Pas de marge. Pas de deuxième chance.

La gravité ne s'arrête pas là-haut. À quatre cents kilomètres, elle garde presque toute sa force. Les astronautes ne sont pas en apesanteur. Ils tombent avec leur station. Ensemble. Au même rythme.

[serious] Mettre un satellite en orbite, c'est un tir de précision. La fusée le monte. Puis elle le pousse à l'horizontale. Puis elle le lâche. [short pause] Une erreur de quelques mètres par seconde, et la mission est perdue.

[calm] Une fois là-haut, plus besoin de moteur. Rien ne le freine. Pas d'air. Pas de frottement. Il tourne seul, pendant des années.

Chaque satellite a un métier.

Les satellites de communication sont des relais. Ils captent un signal. Ils l'amplifient. Ils le renvoient de l'autre côté du globe. Une vidéo, un appel, un paiement. En quelques fractions de seconde.

Les satellites d'observation regardent. En infrarouge. En radar. De jour comme de nuit. À travers les nuages. Ils voient les forêts brûler, les glaces fondre, les villes grandir.

Les satellites météo surveillent l'atmosphère. Les nuages. Les vents. La température des océans. Ils voient les tempêtes naître des jours avant qu'elles n'arrivent.

[intrigued] Et puis il y a le GPS. [short pause] Des horloges atomiques en orbite. Chacune envoie l'heure exacte. Votre téléphone mesure le retard de chaque signal. Quatre satellites suffisent pour savoir où vous êtes.

[serious] Mais là-haut, le temps ne passe pas à la même vitesse. Einstein l'avait prédit. Sans correction, votre position dériverait de dix kilomètres par jour. [short pause] Chaque fois que vous suivez un itinéraire, vous utilisez la relativité.

[mysterious] Certains satellites semblent immobiles. À trente-six mille kilomètres, ils tournent exactement à la vitesse de la Terre. Ils restent au-dessus du même point. Toujours. [short pause] C'est vers eux que pointent les paraboles.

[calm] Un satellite doit tout supporter. Les vibrations du décollage. Le vide. Les radiations. Plus de deux cents degrés d'écart entre l'ombre et le soleil. Sans réparation. Sans entretien. Pendant quinze ans.

[ominous] Puis vient la fin. Le carburant s'épuise. Le satellite ne peut plus corriger sa trajectoire. Il s'éteint. [short pause] Mais il continue de tourner.

Autour de la Terre, des millions de débris filent plus vite qu'une balle. Un boulon peut détruire un satellite. Une collision peut en provoquer des milliers d'autres. Une réaction en chaîne.

[thoughtful] Alors souvenez-vous. Quand vous regardez la météo. Quand vous suivez un itinéraire. Quand vous appelez quelqu'un à l'autre bout du monde. [short pause] Il y a, au-dessus de vous, une machine qui tombe depuis des années… [whispers] et qui ne touchera jamais le sol.
```

Conseil voix : narrateur calme et régulier, sans emphase excessive ; « Parce qu'ils tombent. » détaché, juste après
la question. Pas de silence au début.

## Vérification des faits
- Satellites actifs : plus de 10 000 en 2025 (la majorité Starlink) → « des milliers », sans chiffre exact.
- Canon de Newton : expérience de pensée de Newton (*De mundi systemate*, 1728).
- Orbite basse (≈ 400 km, Station spatiale) : ≈ 7,66 km/s ≈ 27 600 km/h → « vingt-huit mille » ; un tour en ≈ 92 min ;
  ≈ 16 levers de soleil par jour.
- Gravité à 400 km : g × (6371 / 6771)² ≈ 0,89 g → « presque toute sa force ».
- Écart thermique en orbite : de ≈ −150 °C à l'ombre à ≈ +120 °C au soleil → « plus de deux cents degrés ».
- Durée de vie : satellites géostationnaires conçus pour ≈ 15 ans.
- Orbite géostationnaire : 35 786 km d'altitude (« trente-six mille ») ; période = un jour sidéral ; utilisée pour la
  télévision par satellite (paraboles fixes).
- GPS : horloges atomiques à bord ; effets relativistes cumulés ≈ +38 µs/jour ; non corrigés, l'erreur de distance
  croîtrait d'environ 10 km par jour (38 µs × vitesse de la lumière ≈ 11 km).
- Débris : estimations ESA ≈ 1 million d'objets de plus de 1 cm, plus de 100 millions de plus de 1 mm → « des millions »;
  vitesse relative jusqu'à ≈ 10 km/s, bien au-delà d'une balle (≈ 1 km/s). Réaction en chaîne : syndrome de Kessler.
