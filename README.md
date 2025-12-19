Voici une version **dans le même style**, adaptée à un **concours de Tetris en solo** 👇
Tu peux bien sûr ajuster les détails (scoring, contraintes, dates).

---

# Concours Tetris – INSAlgo

Bienvenue à la prestigieuse compétition de **Tetris d’INSAlgo** !

Il s’agit d’un jeu **en solo**, dont le but est simple :
**faire le meilleur score possible** en plaçant intelligemment les pièces de Tetris pour compléter des lignes sans faire déborder la grille.

Pour participer, il vous suffit de développer une **IA capable de jouer à Tetris**, dans le langage de votre choix parmi ceux autorisés.
À la fin, toutes les IA seront évaluées dans les mêmes conditions, et les meilleures remporteront des prix !

```plaintext
⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛
⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛
⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛
⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛
⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛
⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛
⬛⬛🟦🟦⬛⬛⬛⬛⬛⬛
⬛⬛🟦🟦⬛🟩⬛⬛⬛⬛
🟨🟥🟥🟥🟥🟩⬛⬛⬛⬛
🟨🟨🟨⬛🟩🟩🟪🟪🟪🟪
```

---

# Programme

## Spécification

La communication avec votre programme est **entièrement automatisée**.
Votre IA joue une partie complète de Tetris, contrôlée par le moteur du jeu.

### Initialisation

Au début de la partie, votre programme reçoit :

* Une ligne contenant 2 entiers séparés par un espace :
  `W` la largeur de la grille et `H` la hauteur de la grille.

* Une ligne contenant un entier : le nombre de pièces `N`.

* Pour chaque pièce (`N` lignes suivantes) :
  - Une ligne contenant le nom de la pièce suivi des coordonnées de sa forme (par exemple : `I 0,0 1,0 2,0 3,0` pour une barre horizontale).

Le moteur gère la séquence des pièces via l'argument `--seed` (même seed pour toutes les IA), mais **la seed n'est pas envoyée** aux programmes participants.

## Contraintes

`10 <= W <= H < 100` Les dimensions de la grille

`1 <= N < 52` Le nombre de pièces

`1 <= W_i < W ; 1 <= H_i < W` La taille maximale des pièces

Chaque pièce sera identifiée par un unique caractère (a-z, A-Z).

Temps limite d'execution : **0.1 seconde** par tour.

**Note** : Les pièces tombent du haut de la grille et **ne peuvent plus être tournées** une fois la rotation choisie. Les T-spins et autres techniques obscures ne sont donc **pas** supportés.

Dû à un biais des organisateurs, les humains seront privilégiés et auront le droit a un timeout plus long.

---

### Boucle de jeu

Pour chaque tour :

* Le moteur envoie :

  * Une ligne contenant le **nom de la pièce courante**.
    (Remarque : le moteur **n'envoie pas** l'état complet de la grille aux IA — les IA doivent garder leur propre représentation interne du plateau.)
* Votre programme doit répondre par :


  * La **colonne** (`COL`) où lâcher la pièce et la **rotation** (`ROT`) choisie (rotation en nombres entiers 0–3).

Format de sortie attendu (une seule ligne) :

```plaintext
COL ROT
```

Exemples : `3 0` (poser en colonne 3 sans rotation), `0 1` (poser en colonne 0 avec rotation 1).

Un coup invalide (collision immédiate, sortie de grille, etc.) met fin à la partie.

Pour faciliter le debug, toutes les sorties commençant par `>` seront affichées à l’écran mais ignorées par le jeu.

Un exemple d’IA très simple est fourni pour vous aider à démarrer.

---

### Score

Le score est calculé selon les règles suivantes :

* Une ligne effacée rapporte **100 points**.
* **Bonus pour lignes multiples** :
  * Double (2 lignes) : **300 points**
  * Triple (3 lignes) : **500 points**
  * Tetris (4+ lignes) : **800 points**
* Bonus de survie : **+1 point par pièce placée**.

La partie se termine lorsque plus aucune pièce ne peut être placée, ou qu'une pièce a été placée à un endroit invalide (hors du terrain de jeu)

---

## Tester un programme en local

Récupérez le script `tetris.py`, qui permet de lancer des parties locales et de tester votre IA :

```bash
python tetris.py [OPTIONS] prog
```

Exemples :

* Partie jouée par un humain : `python tetris.py`
* Partie jouée par votre IA : `python tetris.py prog`
* Partie avec seed imposée : `python tetris.py -s 42 prog`

Options disponibles :

* `-p N` / `--players N` : nombre de joueurs (tous jouent indépendamment avec la même séquence de pièces)
* `-s` / `--silent` : mode silencieux (affiche seulement le résultat — ne fonctionne que pour les AIs)
* `-n` / `--nodebug` : n'affiche pas les sorties de debug des programmes
* `--seed SEED` : seed aléatoire utilisée par le moteur pour générer la séquence de pièces (même seed pour toutes les IA)

Les languages acceptés sont :

* scripts Python `.py`
* scripts JavaScript `.js`
* classes Java compilées `.class`
* exécutables compilés (C++, Rust, …)

---

# Le concours

## Déroulement du concours

Toutes les informations importantes seront communiquées sur le
[Discord d’INSAlgo](https://discord.gg/68NE6tGMVk).

La phase de développement et de soumission des IA s’étend jusqu’au **11 mars 2025**.

Chaque IA sera évaluée sur **plusieurs parties**, toutes jouées avec les **mêmes seeds**.
Le score final d’une IA correspond à la **moyenne de ses scores** sur l’ensemble des parties.

Un dépassement du temps limite ou une sortie invalide met fin à la partie concernée.

---

## Participer au concours

Les soumissions se font par message privé au bot **Dijkstra-Chan** sur le serveur Discord.

Commande à envoyer :

```plaintext
!game submit tetris
```

Joignez votre fichier dans le même message. (Le script, pas l'exécutable! Les fichiers seront automatiquement compilés par Dijkstra-Chan)

⚠️ Seule la **dernière soumission** sera prise en compte.

Langages acceptés :

* Python 3 `.py`
* JavaScript `.js`
* C++ `.cpp` (compilé avec `-O3`)
* Java `.java`
* C# `.cs`
* Rust `.rs`

Pour tout autre langage, contactez un membre du bureau d’INSAlgo.

---

## Règles du concours

- **Éligibilité** : Tout membre du salon Discord INSAlgo peut participer. La participation en équipe est autorisée (une seule soumission par équipe). 
- **Originalité** : Les soumissions doivent être originales. Les organisateurs vérifieront le code source avant de valider les résultats.
- **Exécution et contraintes** : Les IA seront lancées via le moteur `tetris.py` fourni. Chaque IA joue plusieurs parties (mêmes seeds que pour toutes les IA). Le score final d'une IA est la **moyenne** des scores obtenus sur l'ensemble des parties.
- **Notation et fair-play** : Rédigez du code lisible et commenté.

---

## Prix 🏆

* **64 €** pour le premier
* **32 €** pour le deuxième
* **16 €** pour le troisième

Les membres du bureau d’INSAlgo et les organisateurs ne peuvent pas gagner de prix.

En cas d’égalité, les montants correspondants sont partagés équitablement. 