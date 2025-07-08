"""
Module de notification Discord pour les nouvelles missions Codeur.com
"""

import requests
import json
from typing import Dict, List
import logging
from rss_parser import format_date_fr

logger = logging.getLogger(__name__)


class DiscordNotifier:
    """Gestionnaire des notifications Discord via webhook"""
    
    def __init__(self, webhook_url: str, username: str = "Bot Missions Codeur", 
                 avatar_url: str = None):
        """
        Initialise le notificateur Discord
        
        Args:
            webhook_url: URL du webhook Discord
            username: Nom d'utilisateur du bot
            avatar_url: URL de l'avatar du bot
        """
        self.webhook_url = webhook_url
        self.username = username
        self.avatar_url = avatar_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'RSSBot/1.0'
        })
    
    def send_mission_notification(self, mission: Dict) -> bool:
        """
        Envoie une notification pour une nouvelle mission
        
        Args:
            mission: Dictionnaire contenant les données de la mission
            
        Returns:
            True si envoyé avec succès, False sinon
        """
        try:
            embed = self._create_mission_embed(mission)
            payload = self._create_webhook_payload([embed])
            
            response = self.session.post(self.webhook_url, json=payload, timeout=30)
            response.raise_for_status()
            
            logger.info(f"Notification envoyée pour la mission: {mission['title']}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de notification: {e}")
            return False
    
    def send_multiple_missions(self, missions: List[Dict]) -> int:
        """
        Envoie des notifications pour plusieurs missions (max 10 embeds par message)
        
        Args:
            missions: Liste des missions
            
        Returns:
            Nombre de notifications envoyées avec succès
        """
        if not missions:
            return 0
        
        success_count = 0
        
        # Discord limite à 10 embeds par message
        for i in range(0, len(missions), 10):
            batch = missions[i:i+10]
            
            try:
                embeds = [self._create_mission_embed(mission) for mission in batch]
                payload = self._create_webhook_payload(embeds)
                
                response = self.session.post(self.webhook_url, json=payload, timeout=30)
                response.raise_for_status()
                
                success_count += len(batch)
                logger.info(f"Envoyé {len(batch)} notifications de missions")
                
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi du batch de missions: {e}")
        
        return success_count
    
    def send_summary_notification(self, total_new: int, feeds_processed: List[str]) -> bool:
        """
        Envoie un résumé des nouvelles missions trouvées
        
        Args:
            total_new: Nombre total de nouvelles missions
            feeds_processed: Liste des flux traités
            
        Returns:
            True si envoyé avec succès
        """
        try:
            embed = {
                "title": "📊 Résumé de surveillance",
                "color": 0x3498db,
                "fields": [
                    {
                        "name": "Nouvelles missions trouvées",
                        "value": str(total_new),
                        "inline": True
                    },
                    {
                        "name": "Flux surveillés",
                        "value": ", ".join(feeds_processed),
                        "inline": True
                    }
                ],
                "timestamp": self._get_current_timestamp(),
                "footer": {
                    "text": "Bot Surveillance Codeur.com"
                }
            }
            
            payload = self._create_webhook_payload([embed])
            response = self.session.post(self.webhook_url, json=payload, timeout=30)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du résumé: {e}")
            return False
    
    def _create_mission_embed(self, mission: Dict) -> Dict:
        """
        Crée un embed Discord pour une mission
        
        Args:
            mission: Données de la mission
            
        Returns:
            Dictionnaire représentant l'embed Discord
        """
        # Limiter la longueur du contenu pour l'embed
        content = mission['content']
        if len(content) > 300:
            content = content[:300] + "..."
        
        # Créer la liste des catégories
        categories_str = ", ".join(mission['categories']) if mission['categories'] else "Non spécifiées"
        
        embed = {
            "title": mission['title'],
            "url": mission['link'],
            "color": mission['feed_color'],
            "description": content,
            "fields": [
                {
                    "name": "💰 Budget",
                    "value": mission['budget'],
                    "inline": True
                },
                {
                    "name": "🏷️ Catégories",
                    "value": categories_str,
                    "inline": True
                },
                {
                    "name": "📡 Source",
                    "value": mission['feed_name'],
                    "inline": True
                },
                {
                    "name": "📅 Publié le",
                    "value": format_date_fr(mission['pub_date_parsed']),
                    "inline": False
                }
            ],
            "footer": {
                "text": "Codeur.com • Nouvelle mission disponible",
                "icon_url": "https://www.codeur.com/favicon.ico"
            },
            "timestamp": self._get_current_timestamp()
        }
        
        return embed
    
    def _create_webhook_payload(self, embeds: List[Dict]) -> Dict:
        """
        Crée le payload pour le webhook Discord
        
        Args:
            embeds: Liste des embeds à inclure
            
        Returns:
            Payload pour le webhook
        """
        payload = {
            "embeds": embeds
        }
        
        if self.username:
            payload["username"] = self.username
        
        if self.avatar_url:
            payload["avatar_url"] = self.avatar_url
        
        return payload
    
    def _get_current_timestamp(self) -> str:
        """Retourne le timestamp actuel au format ISO"""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
    
    def test_webhook(self) -> bool:
        """
        Teste la connexion au webhook Discord
        
        Returns:
            True si le webhook fonctionne
        """
        try:
            embed = {
                "title": "🧪 Test de connexion",
                "description": "Le bot de surveillance des missions Codeur.com est opérationnel !",
                "color": 0x00ff00,
                "timestamp": self._get_current_timestamp(),
                "footer": {
                    "text": "Test de configuration"
                }
            }
            
            payload = self._create_webhook_payload([embed])
            response = self.session.post(self.webhook_url, json=payload, timeout=30)
            response.raise_for_status()
            
            logger.info("Test webhook Discord réussi")
            return True
            
        except Exception as e:
            logger.error(f"Échec du test webhook Discord: {e}")
            return False 