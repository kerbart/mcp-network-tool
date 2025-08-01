# 🌐 MCP Network Tools

> **Serveur MCP (Model Context Protocol) pour outils de diagnostic réseau**

Un serveur MCP complet qui expose des outils de diagnostic réseau sécurisés via Claude Desktop, Claude Code et toute application compatible MCP.

## ✨ Fonctionnalités

### 🔧 Outils réseau disponibles

| Outil | Description | Paramètres |
|-------|-------------|------------|
| **ping** | Test de connectivité et latence | `host`, `count`, `timeout` |
| **traceroute** | Traçage de route réseau | `host`, `max_hops` |
| **whois** | Informations sur domaines/IP | `target` |
| **nslookup** | Résolution DNS | `domain`, `record_type` |
| **dig** | Requêtes DNS avancées | `domain`, `record_type` |
| **nmap** | Scan de ports sécurisé | `host`, `ports`, `scan_type` |
| **curl** | Requêtes HTTP/HTTPS | `url`, `method`, `headers` |
| **netstat** | Connexions réseau actives | `protocol`, `state` |

### 🚀 Modes de transport

- **stdio** : Mode par défaut, compatible Claude Desktop/Code
- **http** : Serveur HTTP pour intégrations personnalisées

### 🔒 Sécurité

- Validation stricte des paramètres d'entrée
- Protection contre les injections de commandes
- Limitation des privilèges et timeouts
- Filtrage des domaines et IP sensibles

## 📋 Prérequis

### Système

- **Python 3.8+** 
- **Outils réseau système** (ping, traceroute, nmap, etc.)

### Installation des outils système

```bash
# Vérification automatique
./check_system.sh

# macOS (Homebrew)
brew install nmap whois bind traceroute

# Ubuntu/Debian
sudo apt-get install traceroute nmap whois dnsutils net-tools

# CentOS/RHEL/Fedora
sudo dnf install traceroute nmap whois bind-utils net-tools
```

## 🚀 Installation rapide

### 1. Clone du projet
```bash
git clone https://github.com/kerbart/mcp-network-tool.git
cd mcp-network-tool
```

### 2. Lancement automatique
```bash
# Setup complet + démarrage (stdio mode)
./run.sh

# Mode HTTP
./run.sh --transport http --port 8000
```

Le script `run.sh` se charge automatiquement de :
- ✅ Vérifier Python 3.8+
- ✅ Créer l'environnement virtuel
- ✅ Installer les dépendances
- ✅ Lancer le serveur

## 📖 Installation manuelle

### 1. Environnement virtuel
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# ou venv\Scripts\activate  # Windows
```

### 2. Installation des dépendances
```bash
# Via requirements.txt
pip install -r requirements.txt

# Ou via pyproject.toml
pip install -e .
```

### 3. Vérification système
```bash
./check_system.sh
```

### 4. Lancement du serveur
```bash
# Mode stdio (défaut)
python start.py

# Mode HTTP
python start.py --transport http --port 8000
```

## 🔧 Configuration avec Claude

### Claude Desktop

Ajoutez à votre `claude_desktop_config.json` :

```json
{
  "mcpServers": {
    "network-tools": {
      "command": "python",
      "args": ["/chemin/vers/mcp-network-tools/start.py"],
      "env": {}
    }
  }
}
```

### Claude Code

```bash
# Ajout du serveur MCP
claude mcp add network-tools /chemin/vers/mcp-network-tools/start.py

# Vérification
claude mcp list
```

### Mode HTTP (optionnel)

```json
{
  "mcpServers": {
    "network-tools-http": {
      "transport": {
        "type": "http",
        "url": "http://localhost:8000"
      }
    }
  }
}
```

## 💡 Utilisation

### Exemples avec Claude

```
🧑‍💻 "Peux-tu vérifier la connectivité vers google.com ?"

🤖 Je vais utiliser ping pour tester la connectivité...
[utilise l'outil ping avec host="google.com"]

🧑‍💻 "Scanne les ports ouverts sur mon serveur 192.168.1.100"

🤖 Je vais scanner les ports courants...
[utilise l'outil nmap avec host="192.168.1.100"]

🧑‍💻 "Trace la route vers cloudflare.com"

🤖 Je vais tracer la route réseau...
[utilise l'outil traceroute avec host="cloudflare.com"]
```

### API HTTP (mode HTTP)

```bash
# Liste des outils
curl http://localhost:8000/tools

# Exécution d'un ping
curl -X POST http://localhost:8000/tools/ping \
  -H "Content-Type: application/json" \
  -d '{"arguments": {"host": "google.com", "count": 3}}'

# Health check
curl http://localhost:8000/health
```

## 📁 Structure du projet

```
mcp-network-tools/
├── src/                    # Code source principal
│   ├── tools/             # Implémentations des outils
│   │   ├── ping.py
│   │   ├── traceroute.py
│   │   ├── nmap.py
│   │   └── ...
│   └── utils/             # Utilitaires
│       ├── security.py    # Validation sécurisée
│       └── parsers.py     # Parseurs de sortie
├── start.py               # Point d'entrée principal
├── run.sh                 # Script de lancement automatique
├── check_system.sh        # Vérification des prérequis
├── requirements.txt       # Dépendances Python
├── pyproject.toml         # Configuration du projet
└── README.md              # Cette documentation
```

## 🔧 Développement

### Tests locaux

```bash
# Vérification des outils système
./check_system.sh

# Test du serveur stdio
python start.py

# Test du serveur HTTP
python start.py --transport http
curl http://localhost:8000/
```

### Ajout d'un nouvel outil

1. Créer `src/tools/mon_outil.py`
2. Implémenter la classe héritant de `BaseTool`
3. Ajouter l'outil dans `start.py`
4. Mettre à jour la documentation

### Variables d'environnement

```bash
# Logging
export MCP_LOG_LEVEL=DEBUG

# HTTP mode
export MCP_HOST=0.0.0.0
export MCP_PORT=8000
```

## 🛡️ Sécurité

### Mesures implémentées

- ✅ **Validation d'entrée** : Tous les paramètres sont validés
- ✅ **Échappement de commandes** : Protection contre l'injection
- ✅ **Limitation de privilèges** : Pas de commandes sudo
- ✅ **Timeouts** : Prévention des blocages
- ✅ **Filtrage réseau** : Blocage des adresses sensibles

### Recommandations

- Exécutez avec un utilisateur non-privilégié
- Utilisez un firewall pour limiter l'accès réseau
- Surveillez les logs pour détecter les abus
- Mettez à jour régulièrement les dépendances

## 🐛 Dépannage

### Problèmes courants

**Erreur "command not found"**
```bash
# Vérifiez les outils système
./check_system.sh

# Installez les outils manquants
brew install nmap  # macOS
sudo apt install nmap  # Ubuntu
```

**Erreur "Permission denied" pour nmap**
```bash
# Les scans SYN nécessitent sudo
sudo nmap -sS target.com

# Utilisez les scans connect (sans sudo)
nmap -sT target.com
```

**Erreur de dépendances Python**
```bash
# Réinstallation complète
rm -rf venv/
./run.sh
```

### Logs de débogage

```bash
# Mode verbose
python start.py --transport stdio --verbose

# Logs HTTP
python start.py --transport http --log-level debug
```

## 📚 Ressources

- [Documentation MCP](https://modelcontextprotocol.io/)
- [Claude Desktop Configuration](https://docs.anthropic.com/en/docs/build-with-claude/computer-use)
- [Sécurité des outils réseau](https://nmap.org/book/man-legal.html)

## 🤝 Contribution

1. Fork le projet
2. Créez une branche (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Committez vos changements (`git commit -m 'Ajout nouvelle fonctionnalité'`)
4. Poussez la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Ouvrez une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 👥 Auteurs

- **Network Tools Team** - *Développement initial*

---

**⚠️ Avertissement**: Ces outils peuvent être utilisés à des fins de diagnostic réseau légitime uniquement. L'utilisation malveillante est interdite et peut être illégale dans votre juridiction.

---

🌟 **Star ce repo si il vous a été utile !**