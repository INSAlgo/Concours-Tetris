Voici une version **dans le même style**, adaptée à un **concours de Tetris en solo** 👇
Tu peux bien sûr ajuster les détails (scoring, contraintes, dates).

---

# Concours Tetris – INSAlgo 🧱

Bienvenue à la prestigieuse compétition de **Tetris d’INSAlgo** !

Il s’agit d’un jeu **en solo**, dont le but est simple :
**faire le meilleur score possible** en plaçant intelligemment les pièces de Tetris pour compléter des lignes sans faire déborder la grille.

Pour participer, il vous suffit de développer une petite **IA capable de jouer à Tetris**, dans le langage de votre choix parmi ceux autorisés.
À la fin, toutes les IA seront évaluées dans les mêmes conditions, et les meilleures remporteront des prix !

```plaintext
⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛
⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛
⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛
⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛
⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛
⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛
⬛⬛🟦🟦⬛⬛⬛⬛⬛⬛
⬛⬛🟦🟦🟩🟩🟩⬛⬛⬛
⬛🟥🟥🟥🟥🟩⬛⬛⬛⬛
🟨🟨🟨🟨🟩🟩🟪🟪🟪🟪
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

* Pour chaque pièce (N lignes suivantes) :
  - Une ligne contenant le nom de la pièce suivi des coordonnées de sa forme (par exemple : `I 0,0 1,0 2,0 3,0` pour une barre horizontale).

Le moteur gère la séquence des pièces via l'argument `--seed` (même seed pour toutes les IA), mais **la seed n'est pas envoyée** aux programmes participants.

Contraintes : la grille utilisée par le moteur est par défaut `W=10`, `H=20`.

Temps limite par décision (IA) : **0.1 seconde** (les humains ont un timeout plus long dans le contexte Discord).

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

* Chaque ligne effacée rapporte **+100 points** (par ligne). Par exemple, effacer 2 lignes donne +200 points.
* Bonus de survie : **+1 point par pièce placée**.

La partie se termine lorsque plus aucune pièce ne peut être placée.

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

Remarque : le moteur actuel utilise une grille fixe 10x20 et envoie `10 20` en première ligne à l'IA, il n'expose pas d'option `-g W H` dans l'interface CLI par défaut.

Les programmes acceptés sont :

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

Joignez votre fichier dans le même message et donnez à votre programme le nom de votre pseudo.

⚠️ Seule la **dernière soumission** sera prise en compte.

Pour le tournoi final, **le code source est requis**, pas un exécutable.

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

- **Éligibilité** : Tous les étudiants de l'INSA Lyon peuvent participer. La participation en groupe est autorisée (une seule soumission par groupe).
- **Originalité** : Les soumissions doivent être originales. Les organisateurs vérifieront le code source avant de valider les résultats.
- **Langages acceptés** : Python 3 (`.py`), JavaScript (`.js`), C++ (`.cpp`, compilé avec `-O3`), Java (`.java`), C# (`.cs`), Rust (`.rs`). Pour tout autre langage, contacter un membre de l'équipe.
- **Format et soumission** : Envoyez votre code source en message privé au bot Dijkstra-Chan avec la commande :

```plaintext
!game submit tetris
```

Joignez votre fichier dans le même message et indiquez votre pseudo. Seule la **dernière soumission** sera prise en compte.
- **Exécution et contraintes** : Les IA seront lancées via le moteur `tetris.py` fourni. Chaque IA joue plusieurs parties (mêmes seeds que pour toutes les IA). Le score final d'une IA est la **moyenne** des scores obtenus sur l'ensemble des parties.
- **Temps et validations** : Temps d'exécution garanti : **1 seconde** par décision (par tour). Un dépassement du temps limite ou une sortie invalide met fin à la partie concernée.
- **Coups invalides** : Un coup invalide (collision immédiate, sortie de la grille, etc.) met fin à la partie.
- **Interdictions** : Il est interdit de modifier le moteur de jeu (`tetris.py`) ou d'altérer la génération des pièces. Les organisateurs se réservent le droit de disqualifier toute soumission suspecte.
- **Notation et fair-play** : Rédigez du code lisible et commenté ; fournissez le code source pour le tournoi final (les exécutables seuls ne suffiront pas).

Soyez honnêtes : écrivez du code clair, lisible et commenté 🙂

---

## Prix 🏆

* **64 €** pour le premier
* **32 €** pour le deuxième
* **16 €** pour le troisième

Les membres du bureau d’INSAlgo et les organisateurs ne peuvent pas gagner de prix.

En cas d’égalité, les montants correspondants sont partagés équitablement.

---

Si tu veux, je peux aussi te faire :

* une version **plus technique / orientée IA**
* un **README plus court** pour GitHub
* ou une **affiche/description Discord** pour promouvoir le concours 🎯
