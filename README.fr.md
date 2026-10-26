<p align="center">
 <img src="assets/readme-banner.png" alt="Silex le lynx et Rivet l’automate examinent un indice cuivré." width="100%">
</p>

<h1 align="center">OSINT Forge Skills</h1>

<p align="center">
 <strong>Des sources aux conclusions. Gardez les preuves.</strong><br>
 16 skills OSINT et forensic pour les assistants IA.<br>
 Claude Code · Codex · OpenCode · Gemini CLI
</p>

<p align="center">
 <a href="VERSION"><img src="https://img.shields.io/badge/Version-0.3.0-965D31?style=flat&amp;labelColor=24292F&amp;logo=github&amp;logoColor=white" alt="Version 0.3.0"></a>
 <a href="#les-skills"><img src="https://img.shields.io/badge/Skills-16-64748B?style=flat&amp;labelColor=24292F" alt="16 Skills"></a>
 <a href="#les-outils-utilisables"><img src="https://img.shields.io/badge/Optional_Tools-4-786452?style=flat&amp;labelColor=24292F" alt="4 Outils Optionnels"></a>
 <a href="docs/installation.md"><img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat&amp;labelColor=24292F&amp;logo=python&amp;logoColor=white" alt="Python 3.11+"></a>
 <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache--2.0-5C6670?style=flat&amp;labelColor=24292F" alt="Licence : Apache-2.0"></a>
</p>

<p align="center">
 <a href="README.md">English</a> · <a href="#démarrer-en-cinq-minutes">Démarrage</a> · <a href="#les-outils-utilisables">Outils</a> · <a href="#rechercher-avec-google-dorking">Dorking</a> · <a href="#les-skills">16 skills</a> · <a href="#benchmarks">Benchmarks</a>
</p>

Documents, captures de sources, journaux et exports d’historique deviennent un
dossier portable : pièces conservées, conclusions référencées et inconnues explicites.
Utilisez les outils web de votre assistant pour rechercher des sources publiques,
puis conservez et examinez les pièces sélectionnées localement. Vous choisissez
l’assistant et le modèle ; le runtime Python inclus reste hors ligne.

## Pourquoi utiliser OSINT Forge Skills ?

| Avantage | Apport concret |
| --- | --- |
| **Conclusions traçables** | Originaux conservés, contrôle des octets, sources référencées et citations localisables |
| **Relecture structurée** | Hypothèses concurrentes, contradictions, indépendance des sources et conclusions signalées lorsque leurs prémisses changent |
| **Reprise guidée** | File de relecture priorisée avec références et skills suggérés ; tableau de bord HTML privé avec recherche, en français ou en anglais |
| **Recherche ciblée** | Fiches de sources datées, six parcours de rebond et Google dorking pour préparer le prochain contrôle |
| **Exports exploitables** | Sélection locale d'archives Wayback, chronologies de publications BODACC par SIREN et passages SRT/WebVTT avec contrôle des citations de sous-titres |
| **Contrôle local** | Bibliothèque standard Python, aucune télémétrie du runtime, aucun service obligatoire ni installation automatique d’outils |
| **Travail portable** | Skills autonomes, export/restauration de dossiers privés, rapports FR/EN, GraphML et CSV aux champs Timesketch |

Ces fonctions sont implémentées. Les essais de modèles consignés ne démontrent
pas de gain général en précision, en vitesse ou en coût de tokens. Votre client
contrôle l’accès du modèle et la transmission des données. [Tests et limites](#benchmarks).

![Conserver les pièces sélectionnées, examiner les sources et contradictions, transmettre un rapport relu.](assets/workflow.fr.svg)

<a id="démarrer-en-cinq-minutes"></a>

## Essayer un dossier

Depuis la racine du dépôt source, avec **Python 3.11+**. Aucun compte ni clé API requis.

```bash
mkdir -p cases
python3 scripts/demo.py --out cases/demo
```

<details>
<summary>Windows / PowerShell</summary>

```powershell
New-Item -ItemType Directory -Force .\cases | Out-Null
py -3 scripts/demo.py --out .\cases\demo
```

</details>

Utilisez un dossier de sortie **neuf**. Ouvrez `cases/demo/case/reports/report.fr.md`.
La démo hors ligne enregistre **7 pièces et 2 conclusions**, puis vérifie un export
et sa restauration. Les libellés sont français, le corpus reste anglais.
[Guide pas à pas →](docs/demarrage.md)

> **Trois articles. Une seule source initiale.** Dans le cas synthétique Dock 7,
> trois articles reprennent le même bulletin ; l’heure exacte reste inconnue.
> Ces conclusions sont préétablies, pas découvertes par un modèle. [Explorer le cas](examples/PROVENANCE.md).

**Relire un dossier corrigé :** lancez
`python3 examples/review_demo.py --out cases/review-demo`, puis ouvrez
`cases/review-demo/case/reports/report.fr.html`. L’exemple synthétique présente
les références précises, l’historique des corrections, les recherches incomplètes,
les événements annotés et les relations candidates. [Guide de relecture et d’échange](shared/review-workflows.md).

**Revoir les dépendances et citations :** lancer
`python3 examples/assurance_demo.py --out cases/assurance-demo`, puis ouvrir
son rapport HTML FR. Lancez `python3 scripts/forge.py review-queue --case cases/assurance-demo/case`
pour les prochains contrôles priorisés. La démo affiche les conclusions à réexaminer, la couverture
déclarée et une citation volontairement incorrecte.
[Planification et revue](shared/assurance-workflows.md) · [Fiches de sources](shared/source-workflows.md).

<a id="les-outils-utilisables"></a>

## Les outils à disposition

| Outil | Utilisation |
| --- | --- |
| **Forge · inclus** | Conserver les pièces, trier, créer des chronologies, corréler et exporter |
| **Google dorking · inclus** | Composer des requêtes ciblées et des URL de recherche ; exécuter avec les outils web autorisés du client |
| **MCP stdio · inclus, optionnel** | Exposer cinq outils locaux de planification/recherche ; vérifier un dossier choisi en option |
| **ExifTool · optionnel** | Métadonnées PNG, JPEG et PDF |
| **pdftotext · optionnel** | Texte d’une sélection de pages PDF |
| **Tesseract · optionnel** | OCR sur les images PNG/JPEG |
| **ffprobe · optionnel** | Métadonnées des conteneurs et flux audio/vidéo |

```bash
python3 scripts/forge.py tools
python3 scripts/forge.py plan --kind organization
```

**Suivre une piste :** six fiches de rebond et un générateur de requêtes hors
ligne précisent le prochain contrôle, ses prérequis et ses conditions d'arrêt.
[Parcours de recherche](shared/research-workflows.md).

**Utiliser MCP :** activez explicitement le serveur local dans votre client pour
accéder aux plans, fiches de sources, rebonds, modèles de requêtes et dorks.
Choisissez un dossier au démarrage pour ajouter un outil de vérification dont
le retour se limite au statut et aux compteurs. [Configuration MCP](docs/mcp.md).

Les quatre adaptateurs sont inclus ; **vous installez et choisissez les exécutables tiers**.
Chaque résultat conserve l’empreinte de la pièce, la version de l’outil, ses paramètres et sa sortie.
L’import groupé garde la provenance de chaque fichier. Analysez les captures
HTML/MHTML fournies, comparez des versions texte, mappez les colonnes d’un CSV
forensic et exportez en GraphML ou en CSV aux champs Timesketch.
La réutilisation explicite d’un résultat reste distincte d’une nouvelle exécution.
Recherche web, DNS/RDAP et cartes dépendent des outils disponibles et autorisés du client.
[Commandes et limites](docs/cli.md#optional-local-tools) · [Workflows des outils](shared/tool-workflows.md)

## Rechercher avec Google dorking

![Préparer localement, rechercher via les outils web autorisés, puis conserver et vérifier les sources choisies dans un dossier local. Le moteur reçoit les termes de recherche.](assets/search-workflow.fr.svg)

Préparez une requête localement :

```bash
python3 scripts/forge.py dorks --phrase "Harbor Example Ltd" --site example.org --filetype pdf --after 2024-01-01
```

Le résultat JSON contient `site:example.org "Harbor Example Ltd" filetype:pdf
after:2024-01-01` et une URL Google encodée. Ajoutez `--before` ou répétez
`--exclude` pour affiner. Cet exemple utilise un nom synthétique et un domaine réservé.

Demandez à l’assistant **d’exécuter la requête avec son outil de recherche ou
son navigateur autorisé**, de consigner le moteur réel, la requête et la date,
puis de vérifier les sources originales. L’outil MCP inclus `forge_dorks`
prépare le même résultat. Un client peut utiliser un autre moteur : il faut
alors vérifier la prise en charge de la syntaxe Google. Sans outil web,
la requête et l’URL restent utilisables manuellement.
[Opérateurs et parcours d’exécution](shared/research-workflows.md#google-dorking-with-host-web-tools).

## Ce que nous utilisons

![Socle Forge hors ligne, quatre outils locaux optionnels et capacités assistant et web contrôlées par le client. Rapports FR/EN, archives, GraphML et CSV aux champs Timesketch portables.](assets/toolkit.fr.svg)

Le runtime et les parcours publics sont originaux. La recherche progressive
et les rebonds s’inspirent d’approches examinées dans `smixs/osint-skill`,
`frangelbarrera/osint-agent-skills` et OpenOSINT ; leurs codes et services ne
sont pas des dépendances embarquées. [Références et attribution](shared/research-workflows.md#design-references).

<a id="installer-dans-son-assistant-ia"></a>

## Connecter son assistant

Chaque dossier complet dans `skills/` s’installe directement avec son runtime local.
[Copie d’un skill ou installation avec le CLI Skills →](docs/installation.md#direct-installation-with-the-skills-cli)

Pour les plugins natifs et les archives ZIP, construisez avec `python3 scripts/package.py`, puis installez depuis `dist/` :

| Claude Code | Codex | OpenCode · Gemini CLI |
| :---: | :---: | :---: |
| [Plugin natif](docs/installation.md#native-claude-code-plugin) | [Plugin natif](docs/installation.md#native-codex-plugin) | [Skills autonomes](docs/installation.md#standalone-skills-all-four-clients) |

> Utilise `of-case-start` sur ces documents, sans requête réseau.
> Vérifie l’indépendance des sources, examine les contradictions et prépare un rapport référencé.

<a id="les-12-skills"></a>
<a id="les-skills"></a>

## Choisir son étape d’enquête

| Étape | Skills |
| --- | --- |
| **Cadrer** | [Ouvrir un dossier](skills/of-case-start/SKILL.md) |
| **Vérifier les sources** | [Provenance](skills/of-source-provenance/SKILL.md) · [Domaines](skills/of-domain-infrastructure/SKILL.md) · [Organisations](skills/of-organization-research/SKILL.md) · [Géolocalisation](skills/of-geolocation/SKILL.md) |
| **Examiner les fichiers** | [Documents](skills/of-document-triage/SKILL.md) · [Médias](skills/of-media-forensics/SKILL.md) · [Historique navigateur](skills/of-browser-artifacts/SKILL.md) · [Exports Windows](skills/of-windows-artifacts/SKILL.md) · [Exports d’agents](skills/of-agent-artifacts/SKILL.md) |
| **Confronter les explications** | [Chronologie](skills/of-log-timeline/SKILL.md) · [Corrélation](skills/of-evidence-correlate/SKILL.md) · [Hypothèses](skills/of-hypothesis-audit/SKILL.md) · [Comparaison de versions](skills/of-version-compare/SKILL.md) |
| **Transmettre** | [Rapport](skills/of-investigation-report/SKILL.md) · [Export](skills/of-case-export/SKILL.md) |

<a id="ce-qui-est-vérifié-aujourdhui"></a>
<a id="benchmarks"></a>

## Tests et benchmarks

La version **0.3.0** ajoute les exports cohérents, l'installation ciblée sans
fabrication d'archives, la planification par actions, les hypothèses/tests/origines
du schéma 4, les citations PDF par page et la comparaison directe de textes dérivés.
Le MCP optionnel expose les méthodes statiques, des contrats de sortie validés
et des opérations de dossier bornées et annulables.
Voir les [commandes et limites](docs/cli.md#schema-4-investigation-workflow),
la [qualification MCP](docs/mcp.md) et le [registre daté](docs/compatibility.json).

Consigné le **15 octobre 2026** : **166 tests réussis** sous Linux/WSL, dont
**15 tests synthétiques des adaptateurs**. [Benchmarks et essais réels →](benchmarks/README.md)

<details>
<summary>Périmètre des contrôles et essais restant à réaliser</summary>

- 16 runtimes autonomes, 4 adaptateurs d’installation, revue de schéma 3, citations, export et restauration de la démo.
- Neuf nouvelles sessions Codex terminées sur trois conditions ; critères de contenu acceptés dans les neuf,
  avec un écart de workspace. Skills lus dans les trois sessions qui en disposaient ; aucun gain général de qualité démontré.
- GraphML lu et réécrit avec NetworkX 3.7. Les anciens essais de binaires, navigateur et
  six sessions de revue gardent leurs snapshots du 14 octobre.
- La composition des dorks et le MCP stdio passent les tests locaux ; efficacité sur un moteur réel et intégration à un client MCP restent à tester.
- Quatre nouveaux SVG FR/EN rendus et inspectés localement ; affichage GitHub non testé.
- Les résultats historiques hors ligne et SkillsBench restent disponibles avec leurs limites.
- La couverture de tous les skills et clients, la qualité générale d’enquête, la résistance aux injections,
  Windows/macOS natifs et les imports dans des applications tierces restent à valider.
- Les observations des manifestes sont datées dans le [registre de compatibilité](docs/compatibility.json).
  Les résultats historiques s’appliquent à leurs snapshots de sources.

</details>

**Avant de traiter des pièces réelles :** un assistant distant peut transmettre ce qu’il lit.
Les empreintes vérifient les octets, pas l’authenticité. Relisez les exports avant partage ;
le masquage ne garantit pas l’anonymisation. [Sécurité](SECURITY.md) · [Formats et limites](docs/cli.md#capabilities-and-limits)

## Participer au projet

Avis, bug ou amélioration ? **[Ouvrez une issue](https://github.com/OSINT-Forge-Community/osint-forge-skills/issues)**
et choisissez un label. [Guide de contribution](CONTRIBUTING.md)

Sécurité : [security@osint-forge.com](mailto:security@osint-forge.com)<br>
Données personnelles : [privacy@osint-forge.com](mailto:privacy@osint-forge.com)

---

[Documentation](docs/README.md) · [CLI](docs/cli.md) · [Dépannage](docs/depannage.md) · [Version du paquet](VERSION) · [Changelog](CHANGELOG.md)

Logiciel, skills et textes : **[Apache-2.0](LICENSE)** · [NOTICE](NOTICE).<br>
Visuels © OSINT Forge, tous droits réservés. [Provenance](docs/branding/README.md).<br>
Silex et Rivet sont des mascottes promotionnelles. Les noms des clients n’impliquent aucune affiliation ni recommandation.
