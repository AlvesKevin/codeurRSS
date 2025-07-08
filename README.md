# 🤖 Bot Discord - Surveillance Missions Codeur.com

Bot automatisé qui surveille les flux RSS de Codeur.com et envoie des notifications Discord lorsqu'une nouvelle mission est disponible.

## ✨ Fonctionnalités

- 🔍 **Surveillance multi-flux RSS** : Surveillez plusieurs mots-clés simultanément
- 📢 **Notifications Discord** : Messages formatés avec webhooks Discord
- 🚫 **Anti-doublons** : Évite les notifications répétées
- ⚙️ **Configuration flexible** : Via fichiers YAML et variables d'environnement  
- 🐳 **Déploiement Docker** : Prêt pour la production
- 📊 **Statistiques** : Suivi des missions traitées
- 🔄 **Mode daemon** : Surveillance continue avec planificateur

## 🚀 Installation rapide avec Docker

### 1. Prérequis

- Docker et Docker Compose installés
- Un webhook Discord configuré

### 2. Cloner le projet

```bash
git clone <repo-url>
cd botDiscordMissionCodeur
```

### 3. Configuration

Créez votre fichier `.env` :

```bash
cp .env.example .env
nano .env
```

Configurez votre webhook Discord :

```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL
DISCORD_USERNAME=Bot Missions Codeur
CHECK_INTERVAL_MINUTES=5
```

### 4. Personnaliser les flux RSS

Éditez `config.yaml` pour ajouter vos mots-clés :

```yaml
rss_feeds:
  - name: "Scraping"
    url: "https://www.codeur.com/projects?format=rss&keywords=Scraping&order=most_recent"
    color: 0x00ff00
  - name: "Python"
    url: "https://www.codeur.com/projects?format=rss&keywords=Python&order=most_recent"
    color: 0x3776ab
  - name: "API"
    url: "https://www.codeur.com/projects?format=rss&keywords=API&order=most_recent"
    color: 0xff6b00
```

### 5. Démarrer le bot

```bash
# Tester la connexion Discord
docker-compose run --rm mission-bot python main.py --test

# Lancer le bot en mode daemon
docker-compose up -d

# Voir les logs
docker-compose logs -f mission-bot
```

## 📋 Installation manuelle (sans Docker)

### 1. Prérequis

- Python 3.8+
- pip

### 2. Installation des dépendances

```bash
pip install -r requirements.txt
```

### 3. Configuration

```bash
cp .env.example .env
# Éditer .env avec vos paramètres
```

### 4. Lancement

```bash
# Test de connexion
python main.py --test

# Vérification unique
python main.py --once

# Mode daemon
python main.py
```

## 🛠️ Configuration avancée

### Variables d'environnement

| Variable | Description | Défaut |
|----------|-------------|---------|
| `DISCORD_WEBHOOK_URL` | URL du webhook Discord | **Requis** |
| `DISCORD_USERNAME` | Nom du bot | `Bot Missions Codeur` |
| `DISCORD_AVATAR_URL` | Avatar du bot | Favicon Codeur.com |
| `CHECK_INTERVAL_MINUTES` | Intervalle en minutes | `5` |
| `LOG_LEVEL` | Niveau de log | `INFO` |

### Fichier config.yaml

```yaml
# Configuration Discord
discord:
  webhook_url: "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL"
  username: "Bot Missions Codeur"
  avatar_url: "https://www.codeur.com/favicon.ico"

# Flux RSS à surveiller
rss_feeds:
  - name: "Scraping"
    url: "https://www.codeur.com/projects?format=rss&keywords=Scraping&order=most_recent"
    color: 0x00ff00
  - name: "Python" 
    url: "https://www.codeur.com/projects?format=rss&keywords=Python&order=most_recent"
    color: 0x3776ab

# Paramètres de surveillance
surveillance:
  check_interval_minutes: 5
  max_items_per_check: 10

# Stockage des données
storage:
  data_file: "missions_seen.json"
```

## 📖 Commandes disponibles

```bash
# Mode daemon (par défaut)
python main.py

# Vérification unique
python main.py --once

# Test de connexion Discord
python main.py --test

# Afficher les statistiques
python main.py --stats

# Remettre à zéro l'état
python main.py --reset

# Fichier de config personnalisé
python main.py --config mon-config.yaml
```

## 🐳 Utilisation avec Docker

### Commandes Docker Compose

```bash
# Construire et démarrer
docker-compose up -d

# Voir les logs en temps réel
docker-compose logs -f mission-bot

# Arrêter le service
docker-compose down

# Reconstruire après changement
docker-compose up -d --build

# Exécuter des commandes ponctuelles
docker-compose run --rm mission-bot python main.py --test
docker-compose run --rm mission-bot python main.py --stats
```

### Volumes et persistance

- `./data` : Données du bot (missions vues)
- `./logs` : Fichiers de logs
- `./config.yaml` : Configuration (lecture seule)

## 🔧 Comment obtenir un webhook Discord

1. **Aller sur votre serveur Discord**
2. **Paramètres du serveur** → **Intégrations** → **Webhooks**
3. **Nouveau Webhook**
4. Choisir le salon de destination
5. Copier l'URL du webhook
6. Coller dans `.env` ou `config.yaml`

## 📊 Notifications Discord

Le bot envoie des notifications formatées avec :

- 📋 **Titre** de la mission (lien cliquable)
- 💰 **Budget** estimé
- 🏷️ **Catégories** du projet
- 📅 **Date** de publication
- 📝 **Extrait** de la description
- 🎨 **Couleur** selon le flux RSS

## 🔍 Dépannage

### Le bot ne démarre pas

```bash
# Vérifier les logs
docker-compose logs mission-bot

# Tester la configuration
docker-compose run --rm mission-bot python main.py --test
```

### Pas de notifications reçues

1. Vérifier l'URL du webhook Discord
2. Tester la connexion : `python main.py --test`
3. Vérifier les logs pour les erreurs
4. S'assurer que de nouvelles missions existent

### Trop de notifications

Ajuster dans `config.yaml` :
```yaml
surveillance:
  check_interval_minutes: 15  # Moins fréquent
  max_items_per_check: 5      # Moins d'items par fois
```

## 📁 Structure du projet

```
botDiscordMissionCodeur/
├── main.py                 # Application principale
├── rss_parser.py          # Parser RSS
├── discord_notifier.py    # Notifications Discord  
├── state_manager.py       # Gestion d'état
├── config.yaml           # Configuration
├── requirements.txt      # Dépendances Python
├── Dockerfile           # Image Docker
├── docker-compose.yml   # Orchestration
├── .env.example        # Variables d'environnement
└── README.md          # Cette documentation
```

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :

- Signaler des bugs
- Proposer des améliorations
- Ajouter de nouvelles fonctionnalités

## 📄 Licence

Ce projet est sous licence MIT.

## ❓ Support

Pour toute question ou problème :

1. Vérifiez la section [Dépannage](#🔍-dépannage)
2. Consultez les logs : `docker-compose logs mission-bot`
3. Ouvrez une issue sur le projet

---

**Bonne surveillance de missions ! 🚀** 