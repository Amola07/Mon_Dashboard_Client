# Épisode 32 — Paris aurait dû s'effondrer (style @alfred.explique, en bleu, 100 % code)

Durée visée ≈ 1 min 50 (≈ 320 mots). Ton : « vous », relances, fin coupée.

## Texte à lire

Paris, 1774. Rue d'Enfer. Le sol s'ouvre… et la rue disparaît dans un trou.
Et le pire ? Aujourd'hui, un immeuble parisien sur cinq est construit au-dessus du même vide.

Vous pensez sûrement que Paris est construit sur du solide. Sauf que sous la ville, il y a 280 kilomètres de galeries.
Pendant des siècles, on a creusé sous Paris pour en sortir le calcaire. Les monuments, les immeubles : une grande partie de la pierre vient de là, juste en dessous.
Résultat : la ville repose sur des carrières oubliées. Sans plan. Sans vrais piliers.

Mais attendez. La rue d'Enfer n'est que le début. D'autres rues craquent. Paris est un gruyère, et personne ne sait où sont les trous.

1777. Louis XVI nomme un homme : Charles-Axel Guillaumot. Sa mission : cartographier tout le vide sous Paris, et le consolider. Piliers, murs, galeries remblayées. Il fait graver des noms de rues sur les parois, pour savoir ce qu'il y a au-dessus.
Cette carte, on la met encore à jour aujourd'hui. Et elle peut vous dire si votre immeuble est construit au-dessus du vide. Comment la consulter ? Je vous le montre dans le prochain épisode.

Et puis il y a un autre problème. Les cimetières de Paris débordent. Le plus grand, celui des Innocents, est devenu insalubre.
En 1786, on commence à transférer les ossements… dans les carrières. Au total, environ six millions de Parisiens. Les catacombes sont nées.

Et le plus fou ? L'entrée des catacombes est aujourd'hui place Denfert-Rochereau. Juste à côté de l'ancienne… rue d'Enfer.

Le danger a-t-il disparu ? Non. En 1961, à Clamart, juste à côté de Paris, un quartier entier s'effondre dans une ancienne carrière. Vingt et un morts.

Aujourd'hui encore, l'Inspection des carrières descend surveiller ces 280 kilomètres de galeries. Parce qu'au-dessus, il y a un immeuble sur cinq.
Alors la prochaine fois que vous marchez dans Paris, dites-vous que…

## Découpage (pixel bleu, 100 % code)

| Passage | Image | Jeu / interface |
|---|---|---|
| Accroche (0 s : l'événement tout de suite) | une rue parisienne (immeubles haussmanniens, réverbères, passants) ; le sol s'ouvre, la chaussée et un fiacre tombent dans le vide → ◀◀ VHS | jauge « VIDE » (aiguille), titre « PARIS » |
| « vous pensez… sauf que » | la rue intacte ; la caméra descend sous la chaussée : coupe du sol, galeries | étiquette « SOUS VOS PIEDS » |
| le calcaire | des carriers taillent des blocs, les blocs remontent par un puits et deviennent des façades | compteur « KM DE GALERIES » qui monte |
| 1774 | gros « 1774 » ; la rue d'Enfer s'enfonce (vue en coupe) | tampon rouge « EFFONDREMENT » |
| « Mais attendez » | fissures qui courent sous plusieurs rues ; trous qui clignotent sur une carte | « ? » partout |
| 1777, Guillaumot | personnage en redingote avec une lanterne ; piliers qui se montent, murs, plaques gravées « RUE D'ENFER » | jauge qui redescend |
| les Innocents, 1786 | cimetière débordant ; charrettes de nuit vers un puits ; murs d'ossements | compteur « 6 000 000 » |
| Denfert-Rochereau | plaque de rue « PL. DENFERT-ROCHEREAU » ↔ « RUE D'ENFER » | tampon |
| Clamart 1961 | un quartier s'enfonce de 3 m | « 21 » en rouge |
| aujourd'hui | une rue : 1 immeuble sur 5 s'allume au-dessus d'une galerie ; une lampe d'inspecteur dans les galeries | « 1 / 5 » |
| fin coupée | la rue, la nuit ; un passant ; noir | « LA SUITE DEMAIN ▶ » |

## Faits et sources (vérifiés le 10 octobre 2026)

| Phrase | Fait | Source |
|---|---|---|
| 280 km de galeries | l'IGC inspecte 280 km de galeries ; ≈ 300 km selon la presse | Ville de Paris (paris.fr) ; Sortir à Paris |
| un immeuble sur cinq | « 20 % des immeubles parisiens se situent au-dessus d'une carrière » | Ville de Paris |
| calcaire, pierre de Paris | carrières de calcaire lutétien exploitées depuis l'époque gallo-romaine | Ville de Paris ; Paris ZigZag |
| 17 décembre 1774, rue d'Enfer | date la plus citée (une source donne avril 1774 ; l'étendue varie selon les sources) | Sortir à Paris ; Part-Time Parisian |
| 1777, Guillaumot | décret du 4 avril 1777, Charles-Axel Guillaumot inspecteur général ; cartographie, consolidation, inscriptions | annales.org ; Sortir à Paris |
| Innocents, 1786, ≈ 6 millions | transferts à partir du 7 avril 1786 ; ≈ 6 millions de défunts | catacombes.paris.fr ; Paris ZigZag |
| charrettes de nuit | transferts nocturnes en charrettes (récit courant) | à confirmer |
| Denfert-Rochereau / rue d'Enfer | la rue d'Enfer est devenue l'avenue Denfert-Rochereau ; entrée des catacombes place Denfert-Rochereau | Sortir à Paris ; catacombes.paris.fr |
| Clamart 1961 | 1er juin 1961, effondrement d'une ancienne carrière de craie, 21 morts, 45 blessés | Paris ZigZag ; INERIS |

| Abonnement (ép. suivant) | août-septembre 2004 : la police découvre un cinéma clandestin équipé (écran, projecteur, bar, électricité) dans les carrières sous le Trocadéro ; mot laissé : « Ne cherchez pas » | Gizmodo ; Boing Boing (2004) ; Futility Closet |
| Raison de suivre (milieu du texte) | l'IGC tient un atlas des anciennes carrières mis à jour en continu ; sur igc.paris.fr, une demande en ligne donne un document certifiant la présence ou l'absence d'anciennes carrières sous une parcelle | Ville de Paris (rapports IGC) |
