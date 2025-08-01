#!/bin/bash

# run.sh - Script de démarrage pour MCP Network Tools
# Vérifie et configure l'environnement virtuel Python, installe les dépendances et lance le serveur

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VENV_DIR="venv"
PYTHON_MIN_VERSION="3.8"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}=== MCP Network Tools - Script de démarrage ===${NC}\n"

# Fonction pour vérifier la version de Python
check_python_version() {
    local python_cmd=$1
    
    if ! command -v "$python_cmd" >/dev/null 2>&1; then
        return 1
    fi
    
    local version=$($python_cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
    if [[ -z "$version" ]]; then
        return 1
    fi
    
    # Vérification version minimale (3.8+)
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
        echo "$version"
        return 0
    else
        return 1
    fi
}

# Détection de Python
echo -e "${BLUE}1. Vérification de Python...${NC}"

PYTHON_CMD=""
for cmd in python3 python python3.11 python3.10 python3.9 python3.8; do
    if version=$(check_python_version "$cmd"); then
        PYTHON_CMD="$cmd"
        echo -e "${GREEN}✓${NC} Python trouvé: $cmd (version $version)"
        break
    fi
done

if [[ -z "$PYTHON_CMD" ]]; then
    echo -e "${RED}✗${NC} Python $PYTHON_MIN_VERSION+ requis mais non trouvé"
    echo -e "${YELLOW}Installation:${NC}"
    echo -e "  - macOS: brew install python"
    echo -e "  - Ubuntu/Debian: sudo apt-get install python3 python3-pip python3-venv"
    echo -e "  - CentOS/RHEL: sudo yum install python3 python3-pip"
    exit 1
fi

# Vérification de l'environnement virtuel
echo -e "\n${BLUE}2. Vérification de l'environnement virtuel...${NC}"

cd "$PROJECT_DIR"

if [[ ! -d "$VENV_DIR" ]]; then
    echo -e "${YELLOW}⚠${NC} Environnement virtuel non trouvé, création en cours..."
    
    # Créer l'environnement virtuel
    if ! $PYTHON_CMD -m venv "$VENV_DIR"; then
        echo -e "${RED}✗${NC} Erreur lors de la création de l'environnement virtuel"
        echo -e "${YELLOW}Vérifiez que python3-venv est installé:${NC}"
        echo -e "  - Ubuntu/Debian: sudo apt-get install python3-venv"
        exit 1
    fi
    
    echo -e "${GREEN}✓${NC} Environnement virtuel créé dans $VENV_DIR"
else
    echo -e "${GREEN}✓${NC} Environnement virtuel trouvé: $VENV_DIR"
fi

# Activation de l'environnement virtuel
echo -e "\n${BLUE}3. Activation de l'environnement virtuel...${NC}"

# Script d'activation selon l'OS
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    ACTIVATE_SCRIPT="$VENV_DIR/Scripts/activate"
else
    ACTIVATE_SCRIPT="$VENV_DIR/bin/activate"
fi

if [[ ! -f "$ACTIVATE_SCRIPT" ]]; then
    echo -e "${RED}✗${NC} Script d'activation non trouvé: $ACTIVATE_SCRIPT"
    exit 1
fi

# Activer l'environnement virtuel
source "$ACTIVATE_SCRIPT"
echo -e "${GREEN}✓${NC} Environnement virtuel activé"

# Mise à jour de pip
echo -e "\n${BLUE}4. Mise à jour de pip...${NC}"
if ! python -m pip install --upgrade pip --quiet; then
    echo -e "${YELLOW}⚠${NC} Impossible de mettre à jour pip, continuation..."
else
    echo -e "${GREEN}✓${NC} pip mis à jour"
fi

# Installation/vérification des dépendances
echo -e "\n${BLUE}5. Vérification des dépendances...${NC}"

# Fonction pour vérifier si un package est installé
is_package_installed() {
    python -c "import $1" 2>/dev/null
}

# Packages critiques à vérifier
CRITICAL_PACKAGES=("mcp" "validators" "requests" "psutil")
OPTIONAL_PACKAGES=("fastapi" "uvicorn" "aiohttp")

INSTALL_NEEDED=false

# Vérifier les packages critiques
for package in "${CRITICAL_PACKAGES[@]}"; do
    if is_package_installed "$package"; then
        echo -e "${GREEN}✓${NC} $package installé"
    else
        echo -e "${RED}✗${NC} $package manquant"
        INSTALL_NEEDED=true
    fi
done

# Vérifier les packages optionnels
for package in "${OPTIONAL_PACKAGES[@]}"; do
    if is_package_installed "$package"; then
        echo -e "${GREEN}✓${NC} $package installé (HTTP support)"
    else
        echo -e "${YELLOW}⚠${NC} $package manquant (pas de support HTTP)"
        INSTALL_NEEDED=true
    fi
done

# Installation des dépendances si nécessaire
if $INSTALL_NEEDED; then
    echo -e "\n${YELLOW}Installation des dépendances manquantes...${NC}"
    
    # Essayer d'installer depuis requirements.txt d'abord
    if [[ -f "requirements.txt" ]]; then
        echo -e "Installation depuis requirements.txt..."
        if python -m pip install -r requirements.txt --quiet; then
            echo -e "${GREEN}✓${NC} Dépendances installées depuis requirements.txt"
        else
            echo -e "${RED}✗${NC} Erreur lors de l'installation depuis requirements.txt"
            exit 1
        fi
    # Sinon installer depuis pyproject.toml
    elif [[ -f "pyproject.toml" ]]; then
        echo -e "Installation depuis pyproject.toml..."
        if python -m pip install -e . --quiet; then
            echo -e "${GREEN}✓${NC} Dépendances installées depuis pyproject.toml"
        else
            echo -e "${RED}✗${NC} Erreur lors de l'installation depuis pyproject.toml"
            exit 1
        fi
    else
        echo -e "${RED}✗${NC} Aucun fichier de dépendances trouvé (requirements.txt ou pyproject.toml)"
        exit 1
    fi
else
    echo -e "${GREEN}✓${NC} Toutes les dépendances sont installées"
fi

# Vérification des outils système (optionnel)
if [[ -f "check_system.sh" ]]; then
    echo -e "\n${BLUE}6. Vérification des outils système...${NC}"
    echo -e "${YELLOW}Conseil: Exécutez './check_system.sh' pour vérifier les outils réseau${NC}"
fi

# Démarrage du serveur
echo -e "\n${BLUE}7. Démarrage du serveur MCP Network Tools...${NC}"

# Vérifier si app.py existe
if [[ ! -f "app.py" ]]; then
    echo -e "${RED}✗${NC} Fichier app.py non trouvé"
    exit 1
fi

echo -e "${GREEN}🚀 Lancement du serveur...${NC}"
echo -e "${BLUE}Mode par défaut: stdio (compatible Claude Desktop/Code)${NC}"
echo -e "${BLUE}Pour le mode HTTP: ./run.sh --transport http${NC}"
echo -e "${BLUE}Appuyez sur Ctrl+C pour arrêter${NC}\n"

# Lancer le serveur avec les arguments passés au script
exec python app.py "$@"