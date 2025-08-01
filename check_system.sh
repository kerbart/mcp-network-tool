#!/bin/bash

# check_system.sh - Vérification des outils réseau requis pour MCP Network Tools
# Compatible macOS et Linux

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Compteurs
TOTAL_TOOLS=0
INSTALLED_TOOLS=0
MISSING_TOOLS=()

echo -e "${BLUE}=== Vérification des outils réseau pour MCP Network Tools ===${NC}\n"

# Détection de l'OS
OS=$(uname -s)
case "$OS" in
    Darwin)
        OS_NAME="macOS"
        PACKAGE_MANAGER="brew"
        ;;
    Linux)
        OS_NAME="Linux"
        if command -v apt-get >/dev/null 2>&1; then
            PACKAGE_MANAGER="apt"
        elif command -v yum >/dev/null 2>&1; then
            PACKAGE_MANAGER="yum"
        elif command -v dnf >/dev/null 2>&1; then
            PACKAGE_MANAGER="dnf"
        elif command -v pacman >/dev/null 2>&1; then
            PACKAGE_MANAGER="pacman"
        else
            PACKAGE_MANAGER="unknown"
        fi
        ;;
    *)
        OS_NAME="Unknown"
        PACKAGE_MANAGER="unknown"
        ;;
esac

echo -e "Système détecté: ${BLUE}$OS_NAME${NC}"
echo -e "Gestionnaire de paquets: ${BLUE}$PACKAGE_MANAGER${NC}\n"

# Fonction pour vérifier un outil
check_tool() {
    local tool=$1
    local description=$2
    
    TOTAL_TOOLS=$((TOTAL_TOOLS + 1))
    
    if command -v "$tool" >/dev/null 2>&1; then
        local version=$(get_tool_version "$tool")
        echo -e "${GREEN}✓${NC} $tool - $description ${GREEN}(installé)${NC} $version"
        INSTALLED_TOOLS=$((INSTALLED_TOOLS + 1))
    else
        echo -e "${RED}✗${NC} $tool - $description ${RED}(manquant)${NC}"
        get_install_command "$tool"
        MISSING_TOOLS+=("$tool")
    fi
}

# Fonction pour obtenir la commande d'installation
get_install_command() {
    local tool=$1
    local cmd=""
    
    case "$tool" in
        ping)
            case $PACKAGE_MANAGER in
                brew) cmd="brew install inetutils (si nécessaire)" ;;
                apt) cmd="sudo apt-get install iputils-ping" ;;
                yum|dnf) cmd="sudo $PACKAGE_MANAGER install iputils" ;;
                pacman) cmd="sudo pacman -S iputils" ;;
                *) cmd="Généralement préinstallé" ;;
            esac
            ;;
        traceroute)
            case $PACKAGE_MANAGER in
                brew) cmd="brew install traceroute" ;;
                apt) cmd="sudo apt-get install traceroute" ;;
                yum|dnf) cmd="sudo $PACKAGE_MANAGER install traceroute" ;;
                pacman) cmd="sudo pacman -S traceroute" ;;
                *) cmd="Vérifiez le gestionnaire de paquets de votre distribution" ;;
            esac
            ;;
        nmap)
            case $PACKAGE_MANAGER in
                brew) cmd="brew install nmap" ;;
                apt) cmd="sudo apt-get install nmap" ;;
                yum|dnf) cmd="sudo $PACKAGE_MANAGER install nmap" ;;
                pacman) cmd="sudo pacman -S nmap" ;;
                *) cmd="Téléchargez depuis https://nmap.org/download.html" ;;
            esac
            ;;
        whois)
            case $PACKAGE_MANAGER in
                brew) cmd="brew install whois" ;;
                apt) cmd="sudo apt-get install whois" ;;
                yum|dnf) cmd="sudo $PACKAGE_MANAGER install whois" ;;
                pacman) cmd="sudo pacman -S whois" ;;
                *) cmd="Vérifiez le gestionnaire de paquets de votre distribution" ;;
            esac
            ;;
        nslookup)
            case $PACKAGE_MANAGER in
                brew) cmd="brew install bind (si nécessaire)" ;;
                apt) cmd="sudo apt-get install dnsutils" ;;
                yum|dnf) cmd="sudo $PACKAGE_MANAGER install bind-utils" ;;
                pacman) cmd="sudo pacman -S bind-tools" ;;
                *) cmd="Généralement préinstallé" ;;
            esac
            ;;
        dig)
            case $PACKAGE_MANAGER in
                brew) cmd="brew install bind" ;;
                apt) cmd="sudo apt-get install dnsutils" ;;
                yum|dnf) cmd="sudo $PACKAGE_MANAGER install bind-utils" ;;
                pacman) cmd="sudo pacman -S bind-tools" ;;
                *) cmd="Vérifiez le gestionnaire de paquets de votre distribution" ;;
            esac
            ;;
        curl)
            case $PACKAGE_MANAGER in
                brew) cmd="brew install curl (si nécessaire)" ;;
                apt) cmd="sudo apt-get install curl" ;;
                yum|dnf) cmd="sudo $PACKAGE_MANAGER install curl" ;;
                pacman) cmd="sudo pacman -S curl" ;;
                *) cmd="Généralement préinstallé" ;;
            esac
            ;;
        netstat)
            case $PACKAGE_MANAGER in
                brew) cmd="Préinstallé sur macOS" ;;
                apt) cmd="sudo apt-get install net-tools" ;;
                yum|dnf) cmd="sudo $PACKAGE_MANAGER install net-tools" ;;
                pacman) cmd="sudo pacman -S net-tools" ;;
                *) cmd="Vérifiez le gestionnaire de paquets de votre distribution" ;;
            esac
            ;;
    esac
    
    echo -e "  ${YELLOW}Installation:${NC} $cmd"
}

# Fonction pour obtenir la version d'un outil
get_tool_version() {
    local tool=$1
    case "$tool" in
        ping)
            echo ""
            ;;
        traceroute)
            if [[ "$OS" == "Darwin" ]]; then
                echo ""
            else
                traceroute --version 2>&1 | head -1 | grep -o '[0-9]\+\.[0-9]\+' | head -1 || echo ""
            fi
            ;;
        nmap)
            nmap --version 2>&1 | head -1 | grep -o '[0-9]\+\.[0-9]\+' | head -1 || echo ""
            ;;
        whois)
            echo ""
            ;;
        nslookup)
            echo ""
            ;;
        dig)
            dig -v 2>&1 | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+' | head -1 || echo ""
            ;;
        curl)
            curl --version 2>&1 | head -1 | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+' | head -1 || echo ""
            ;;
        netstat)
            echo ""
            ;;
        *)
            echo ""
            ;;
    esac
}

# Vérification des outils réseau
echo -e "${BLUE}Outils réseau requis:${NC}"

# Vérification de tous les outils
check_tool "ping" "Test de connectivité"
check_tool "traceroute" "Traçage de route réseau"
check_tool "nmap" "Scanner de ports et réseau"
check_tool "whois" "Informations sur les domaines"
check_tool "nslookup" "Résolution DNS"
check_tool "dig" "Outil DNS avancé"
check_tool "curl" "Client HTTP/HTTPS"
check_tool "netstat" "Statistiques réseau"

# Résumé
echo -e "\n${BLUE}=== Résumé ===${NC}"
echo -e "Outils installés: ${GREEN}$INSTALLED_TOOLS${NC}/$TOTAL_TOOLS"

if [ ${#MISSING_TOOLS[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ Tous les outils réseau sont installés!${NC}"
    echo -e "\nVous pouvez maintenant utiliser MCP Network Tools sans problème."
else
    echo -e "${YELLOW}⚠ Outils manquants:${NC} ${MISSING_TOOLS[*]}"
    echo -e "\n${YELLOW}Pour installer tous les outils manquants d'un coup:${NC}"
    
    case $PACKAGE_MANAGER in
        brew)
            echo "brew install nmap whois bind traceroute"
            ;;
        apt)
            echo "sudo apt-get update && sudo apt-get install traceroute nmap whois dnsutils net-tools curl iputils-ping"
            ;;
        yum)
            echo "sudo yum install traceroute nmap whois bind-utils net-tools curl iputils"
            ;;
        dnf)
            echo "sudo dnf install traceroute nmap whois bind-utils net-tools curl iputils"
            ;;
        pacman)
            echo "sudo pacman -S traceroute nmap whois bind-tools net-tools curl iputils"
            ;;
        *)
            echo "Consultez la documentation de votre distribution Linux."
            ;;
    esac
fi

# Vérification des permissions pour nmap
if command -v nmap >/dev/null 2>&1; then
    echo -e "\n${BLUE}=== Notes importantes ===${NC}"
    echo -e "${YELLOW}⚠ nmap:${NC} Certains scans nécessitent des privilèges root."
    echo -e "  Pour les scans SYN, utilisez: ${YELLOW}sudo${NC}"
    echo -e "  Les scans 'connect' fonctionnent sans privilèges spéciaux."
fi

echo -e "\n${BLUE}=== Python Dependencies ===${NC}"
echo -e "N'oubliez pas d'installer les dépendances Python:"
echo -e "${YELLOW}pip install -r requirements.txt${NC}"
echo -e "ou"
echo -e "${YELLOW}pip install -e .${NC}"

exit 0