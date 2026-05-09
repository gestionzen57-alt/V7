#!/usr/bin/env python3
"""
POWERFLOW LAUNCHER - Démarre tout le système en une commande

Lance automatiquement :
- Dashboard serveur
- Telegram timing bot (optionnel)
- Ouvre le navigateur

Usage:
    python launcher.py                    # Dashboard seulement
    python launcher.py --with-telegram    # Dashboard + Telegram
    python launcher.py --demo             # Mode démo (sans DB)
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path
import argparse
import os
import signal


class PowerFlowLauncher:
    """Lanceur tout-en-un pour PowerFlow"""
    
    def __init__(self):
        self.processes = []
    
    def launch_dashboard_server(self, demo_mode: bool = False):
        """Lance le serveur dashboard"""
        
        if demo_mode:
            print("🎬 Lancement du serveur DEMO...")
            cmd = [sys.executable, "demo_live.py", "--duration", "600"]
        else:
            print("🌐 Lancement du serveur dashboard...")
            cmd = [sys.executable, "dashboard_server.py", "--serve"]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        self.processes.append(("Dashboard", process))
        return process
    
    def launch_telegram_bot(self):
        """Lance le bot Telegram en mode boucle"""
        
        print("📱 Lancement du bot Telegram...")
        
        # Vérifier que les variables d'environnement sont définies
        if not os.getenv("TELEGRAM_BOT_TOKEN") or not os.getenv("TELEGRAM_CHAT_ID"):
            print("⚠️  Variables Telegram non configurées (.env)")
            print("   Le bot Telegram ne sera pas lancé")
            return None
        
        cmd = [sys.executable, "telegram_timing_v6.py", "--loop"]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        self.processes.append(("Telegram", process))
        return process
    
    def open_browser(self, url: str = "http://localhost:8080/dashboard_live.html"):
        """Ouvre le dashboard dans le navigateur"""
        
        print(f"🌍 Ouverture du navigateur : {url}")
        time.sleep(2)  # Attendre que le serveur soit prêt
        
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"⚠️  Impossible d'ouvrir le navigateur : {e}")
            print(f"   Ouvre manuellement : {url}")
    
    def monitor_processes(self):
        """Surveille les processus lancés"""
        
        print("\n" + "=" * 60)
        print("✅ POWERFLOW EST EN MARCHE")
        print("=" * 60)
        print("\nProcessus actifs :")
        
        for name, process in self.processes:
            print(f"  • {name} (PID: {process.pid})")
        
        print("\n💡 Le dashboard se rafraîchit automatiquement toutes les 10s")
        print("💡 Laisse cette fenêtre ouverte")
        print("\nAppuie sur Ctrl+C pour tout arrêter\n")
        
        try:
            # Attendre indéfiniment
            while True:
                # Vérifier que les processus tournent encore
                for name, process in self.processes:
                    if process.poll() is not None:
                        print(f"\n⚠️  {name} s'est arrêté (code: {process.returncode})")
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Arrêt demandé...")
            self.stop_all()
    
    def stop_all(self):
        """Arrête tous les processus"""
        
        print("\n🛑 Arrêt des processus...")
        
        for name, process in self.processes:
            try:
                print(f"  • Arrêt de {name}...")
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"  • Force kill de {name}...")
                process.kill()
            except Exception as e:
                print(f"  • Erreur lors de l'arrêt de {name}: {e}")
        
        print("\n✅ Tous les processus sont arrêtés")
        print("À bientôt ! 👋\n")


def check_dependencies():
    """Vérifie que les fichiers nécessaires existent"""
    
    required_files = [
        "dashboard_live.html",
        "dashboard_server.py"
    ]
    
    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)
    
    if missing:
        print("❌ Fichiers manquants :")
        for file in missing:
            print(f"   • {file}")
        print("\nAssure-toi d'être dans le bon répertoire")
        return False
    
    return True


def show_banner():
    """Affiche la bannière de démarrage"""
    
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   ⚡ POWERFLOW V6 - CLARTÉ + TIMING                      ║
║                                                           ║
║   Dashboard Live + Telegram Timing Bot                   ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
"""
    print(banner)


def main():
    parser = argparse.ArgumentParser(
        description="PowerFlow Launcher - Démarre tout le système"
    )
    parser.add_argument(
        '--with-telegram',
        action='store_true',
        help='Lancer aussi le bot Telegram'
    )
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Mode démo (sans powerflow.db)'
    )
    parser.add_argument(
        '--no-browser',
        action='store_true',
        help='Ne pas ouvrir le navigateur automatiquement'
    )
    
    args = parser.parse_args()
    
    # Bannière
    show_banner()
    
    # Vérifier les dépendances
    if not check_dependencies():
        sys.exit(1)
    
    # Créer le launcher
    launcher = PowerFlowLauncher()
    
    # Lancer le dashboard
    launcher.launch_dashboard_server(demo_mode=args.demo)
    
    # Lancer Telegram si demandé
    if args.with_telegram:
        launcher.launch_telegram_bot()
    
    # Ouvrir le navigateur
    if not args.no_browser:
        launcher.open_browser()
    else:
        print("\n💡 Ouvre manuellement : http://localhost:8080/dashboard_live.html")
    
    # Surveiller
    launcher.monitor_processes()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Erreur fatale : {e}")
        sys.exit(1)
