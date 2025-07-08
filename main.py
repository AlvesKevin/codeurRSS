#!/usr/bin/env python3
"""
Bot de surveillance des missions Codeur.com
Surveille les flux RSS et envoie des notifications Discord
"""

import os
import sys
import time
import yaml
import logging
import schedule
from typing import Dict, List
from dotenv import load_dotenv

from rss_parser import RSSParser
from discord_notifier import DiscordNotifier
from state_manager import StateManager


class MissionBot:
    """Bot principal de surveillance des missions"""
    
    def __init__(self, config_file: str = "config.yaml"):
        """
        Initialise le bot
        
        Args:
            config_file: Chemin vers le fichier de configuration
        """
        self.config = self._load_config(config_file)
        self.setup_logging()
        
        # Initialiser les composants
        self.rss_parser = RSSParser()
        self.state_manager = StateManager(self.config['storage']['data_file'])
        self.discord_notifier = self._setup_discord_notifier()
        
        logger.info("Bot de surveillance des missions initialisé")
    
    def _load_config(self, config_file: str) -> Dict:
        """Charge la configuration depuis le fichier YAML et les variables d'environnement"""
        # Charger les variables d'environnement
        load_dotenv()
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Override avec les variables d'environnement si présentes
            webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
            if webhook_url:
                config['discord']['webhook_url'] = webhook_url
            
            username = os.getenv('DISCORD_USERNAME')
            if username:
                config['discord']['username'] = username
            
            avatar_url = os.getenv('DISCORD_AVATAR_URL')
            if avatar_url:
                config['discord']['avatar_url'] = avatar_url
            
            check_interval = os.getenv('CHECK_INTERVAL_MINUTES')
            if check_interval:
                config['surveillance']['check_interval_minutes'] = int(check_interval)
            
            return config
            
        except Exception as e:
            print(f"Erreur lors du chargement de la configuration: {e}")
            sys.exit(1)
    
    def setup_logging(self):
        """Configure le système de logging"""
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('mission_bot.log', encoding='utf-8')
            ]
        )
        
        global logger
        logger = logging.getLogger(__name__)
    
    def _setup_discord_notifier(self) -> DiscordNotifier:
        """Configure le notificateur Discord"""
        discord_config = self.config['discord']
        
        webhook_url = discord_config.get('webhook_url')
        if not webhook_url or webhook_url == "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL":
            logger.error("URL du webhook Discord non configurée!")
            print("\n❌ ERREUR: URL du webhook Discord manquante!")
            print("Veuillez configurer DISCORD_WEBHOOK_URL dans votre fichier .env")
            print("ou modifier config.yaml avec votre URL de webhook Discord.")
            sys.exit(1)
        
        return DiscordNotifier(
            webhook_url=webhook_url,
            username=discord_config.get('username', 'Bot Missions Codeur'),
            avatar_url=discord_config.get('avatar_url')
        )
    
    def test_connection(self) -> bool:
        """Teste la connexion au webhook Discord"""
        logger.info("Test de connexion Discord...")
        return self.discord_notifier.test_webhook()
    
    def check_for_new_missions(self) -> None:
        """Vérifie tous les flux RSS pour de nouvelles missions"""
        logger.info("🔍 Vérification des nouvelles missions...")
        
        all_new_missions = []
        feeds_processed = []
        
        for feed_config in self.config['rss_feeds']:
            try:
                logger.info(f"Traitement du flux: {feed_config['name']}")
                
                # Parser le flux RSS
                missions = self.rss_parser.parse_feed(feed_config)
                
                # Filtrer les nouvelles missions
                new_missions = self.state_manager.get_new_missions(missions)
                
                if new_missions:
                    # Limiter le nombre de missions par vérification
                    max_items = self.config['surveillance']['max_items_per_check']
                    limited_missions = new_missions[:max_items]
                    
                    if len(new_missions) > max_items:
                        logger.warning(f"Limitation: {len(new_missions)} nouvelles missions trouvées, "
                                     f"seules les {max_items} premières seront traitées")
                    
                    all_new_missions.extend(limited_missions)
                    
                    # Marquer les missions comme vues
                    self.state_manager.mark_missions_seen(limited_missions)
                
                feeds_processed.append(feed_config['name'])
                
            except Exception as e:
                logger.error(f"Erreur lors du traitement du flux {feed_config['name']}: {e}")
        
        # Envoyer les notifications
        if all_new_missions:
            logger.info(f"📢 Envoi de {len(all_new_missions)} nouvelles notifications")
            success_count = self.discord_notifier.send_multiple_missions(all_new_missions)
            
            if success_count == len(all_new_missions):
                logger.info("✅ Toutes les notifications ont été envoyées avec succès")
            else:
                logger.warning(f"⚠️ Seulement {success_count}/{len(all_new_missions)} notifications envoyées")
        else:
            logger.info("ℹ️ Aucune nouvelle mission trouvée")
        
        # Sauvegarder l'état
        self.state_manager.save_state()
        
        logger.info(f"✅ Vérification terminée - {len(all_new_missions)} nouvelles missions")
    
    def run_once(self) -> None:
        """Effectue une seule vérification"""
        logger.info("🚀 Démarrage d'une vérification unique...")
        self.check_for_new_missions()
    
    def run_daemon(self) -> None:
        """Lance le bot en mode daemon avec vérifications périodiques"""
        check_interval = self.config['surveillance']['check_interval_minutes']
        
        logger.info(f"🚀 Démarrage du bot en mode daemon (vérification toutes les {check_interval} minutes)")
        
        # Programmer la vérification périodique
        schedule.every(check_interval).minutes.do(self.check_for_new_missions)
        
        # Effectuer une première vérification immédiatement
        self.check_for_new_missions()
        
        # Boucle principale
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Vérifier les tâches planifiées chaque minute
                
        except KeyboardInterrupt:
            logger.info("🛑 Arrêt du bot demandé par l'utilisateur")
        except Exception as e:
            logger.error(f"💥 Erreur fatale dans la boucle principale: {e}")
            raise
    
    def get_statistics(self) -> Dict:
        """Retourne les statistiques du bot"""
        return self.state_manager.get_statistics()
    
    def reset_state(self) -> bool:
        """Remet à zéro l'état du bot"""
        return self.state_manager.reset_state()


def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Bot de surveillance des missions Codeur.com")
    parser.add_argument('--config', '-c', default='config.yaml',
                       help='Fichier de configuration (défaut: config.yaml)')
    parser.add_argument('--once', action='store_true',
                       help='Effectuer une seule vérification puis quitter')
    parser.add_argument('--test', action='store_true',
                       help='Tester la connexion Discord puis quitter')
    parser.add_argument('--stats', action='store_true',
                       help='Afficher les statistiques puis quitter')
    parser.add_argument('--reset', action='store_true',
                       help='Remettre à zéro l\'état puis quitter')
    
    args = parser.parse_args()
    
    try:
        # Initialiser le bot
        bot = MissionBot(args.config)
        
        if args.test:
            # Test de connexion
            print("🧪 Test de connexion Discord...")
            if bot.test_connection():
                print("✅ Connexion Discord réussie!")
                sys.exit(0)
            else:
                print("❌ Échec de la connexion Discord!")
                sys.exit(1)
        
        elif args.stats:
            # Afficher les statistiques
            stats = bot.get_statistics()
            print("\n📊 Statistiques du bot:")
            print(f"Total missions vues: {stats['total_missions_seen']}")
            print(f"Missions par flux: {stats['missions_by_feed']}")
            if stats['newest_mission']:
                print(f"Dernière mission: {stats['newest_mission']}")
            sys.exit(0)
        
        elif args.reset:
            # Reset de l'état
            print("🔄 Remise à zéro de l'état...")
            if bot.reset_state():
                print("✅ État remis à zéro avec succès!")
                sys.exit(0)
            else:
                print("❌ Erreur lors de la remise à zéro!")
                sys.exit(1)
        
        elif args.once:
            # Vérification unique
            bot.run_once()
        
        else:
            # Mode daemon
            bot.run_daemon()
    
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du programme")
    except Exception as e:
        print(f"\n💥 Erreur fatale: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 