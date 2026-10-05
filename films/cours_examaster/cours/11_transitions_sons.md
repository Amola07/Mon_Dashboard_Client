---
titre: Transitions, flashs et sons
apercu: Les trois fonctions du bas du fichier qui font le montage.
---
# Transitions, flashs et sons

En bas de chaque épisode, trois fonctions font le **montage**.

## `tableaux()` : l'ordre et les transitions

```python
(début, fonction, transition)
```

| Transition | Effet |
|---|---|
| `None` | aucune (le premier tableau) |
| `"neige"` | neige de télévision |
| `"balayage"` | une ligne lumineuse qui balaie l'écran |
| `"glitch"` | des bandes décalées |
| `"noir"` | retour au noir, puis tout se redessine |

> **Variez-les.** La même transition à chaque fois devient invisible.

## `chocs()` : flashs et secousses

```python
def chocs():
    flashs = [s(3)]
    secousses = [(s(3), 0.2)]
    return flashs, secousses
```

À réserver aux **révélations** : un impact, un chiffre énorme, le « NON ».

## `effets()` : les sons

```python
def effets(tabs):
    ev = [
        (0.0, Z.thump(0.35)),
        (s(3), Z.boom(0.5, 60)),
    ]
    return ev
```

Les bips du faisceau et de la frappe sont **automatiques**. Vous ajoutez les sons qui racontent.

## La boîte à sons

| Famille | Sons |
|---|---|
| Impacts | `thump`, `boom`, `clang`, `craquement` |
| Mouvements | `whoosh`, `riser`, `chirp(f0, f1)` |
| Notes | `cloche`, `pince`, `ding_ascenseur` |
| Ambiances | `vent`, `bulles`, `vibration`, `foule`, `applaudissements` |
| Tension | `tictac`, `alarme`, `coeur`, `grincement` |
| Effets d'écran | `glitch`, `neige` |

> **Astuce son :** un silence juste avant une révélation la rend deux fois plus forte.
