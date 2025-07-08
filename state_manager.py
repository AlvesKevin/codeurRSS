"""
Module de gestion d'état pour éviter les doublons de missions
"""

import json
import os
from typing import Set, List, Dict
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class StateManager:
    """Gestionnaire d'état pour suivre les missions déjà traitées"""
    
    def __init__(self, data_file: str = "missions_seen.json"):
        """
        Initialise le gestionnaire d'état
        
        Args:
            data_file: Chemin vers le fichier de données
        """
        self.data_file = data_file
        self.seen_missions: Set[str] = set()
        self.missions_data: Dict[str, Dict] = {}
        self.load_state()
    
    def load_state(self) -> None:
        """Charge l'état depuis le fichier de données"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Charger les IDs des missions vues
                    self.seen_missions = set(data.get('seen_missions', []))
                    
                    # Charger les données complètes des missions
                    self.missions_data = data.get('missions_data', {})
                    
                    logger.info(f"État chargé: {len(self.seen_missions)} missions vues")
            else:
                logger.info("Aucun fichier d'état trouvé, création d'un nouvel état")
                self.seen_missions = set()
                self.missions_data = {}
                
        except Exception as e:
            logger.error(f"Erreur lors du chargement de l'état: {e}")
            self.seen_missions = set()
            self.missions_data = {}
    
    def save_state(self) -> bool:
        """
        Sauvegarde l'état dans le fichier de données
        
        Returns:
            True si sauvegardé avec succès
        """
        try:
            # Nettoyer les anciennes missions (plus de 30 jours)
            self._cleanup_old_missions()
            
            data = {
                'seen_missions': list(self.seen_missions),
                'missions_data': self.missions_data,
                'last_update': datetime.now().isoformat()
            }
            
            # Créer une sauvegarde temporaire
            temp_file = f"{self.data_file}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Remplacer le fichier original
            if os.path.exists(self.data_file):
                os.replace(temp_file, self.data_file)
            else:
                os.rename(temp_file, self.data_file)
            
            logger.debug(f"État sauvegardé: {len(self.seen_missions)} missions")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de l'état: {e}")
            # Nettoyer le fichier temporaire en cas d'erreur
            if os.path.exists(f"{self.data_file}.tmp"):
                os.remove(f"{self.data_file}.tmp")
            return False
    
    def is_mission_seen(self, mission_id: str) -> bool:
        """
        Vérifie si une mission a déjà été vue
        
        Args:
            mission_id: ID unique de la mission
            
        Returns:
            True si la mission a déjà été vue
        """
        return mission_id in self.seen_missions
    
    def mark_mission_seen(self, mission: Dict) -> None:
        """
        Marque une mission comme vue
        
        Args:
            mission: Données complètes de la mission
        """
        mission_id = mission['id']
        self.seen_missions.add(mission_id)
        
        # Stocker les données essentielles de la mission
        self.missions_data[mission_id] = {
            'title': mission['title'],
            'pub_date': mission['pub_date'],
            'feed_name': mission['feed_name'],
            'seen_at': datetime.now().isoformat()
        }
        
        logger.debug(f"Mission marquée comme vue: {mission['title']}")
    
    def mark_missions_seen(self, missions: List[Dict]) -> None:
        """
        Marque plusieurs missions comme vues
        
        Args:
            missions: Liste des missions à marquer
        """
        for mission in missions:
            self.mark_mission_seen(mission)
    
    def get_new_missions(self, missions: List[Dict]) -> List[Dict]:
        """
        Filtre les missions pour ne retourner que les nouvelles
        
        Args:
            missions: Liste de toutes les missions
            
        Returns:
            Liste des missions non encore vues
        """
        new_missions = []
        
        for mission in missions:
            if not self.is_mission_seen(mission['id']):
                new_missions.append(mission)
        
        logger.info(f"Trouvé {len(new_missions)} nouvelles missions sur {len(missions)} total")
        return new_missions
    
    def get_statistics(self) -> Dict:
        """
        Retourne les statistiques de l'état
        
        Returns:
            Dictionnaire avec les statistiques
        """
        stats = {
            'total_missions_seen': len(self.seen_missions),
            'missions_by_feed': {},
            'oldest_mission': None,
            'newest_mission': None
        }
        
        # Statistiques par flux
        for mission_data in self.missions_data.values():
            feed_name = mission_data.get('feed_name', 'Unknown')
            stats['missions_by_feed'][feed_name] = stats['missions_by_feed'].get(feed_name, 0) + 1
        
        # Mission la plus ancienne et la plus récente
        if self.missions_data:
            sorted_missions = sorted(
                self.missions_data.values(),
                key=lambda x: x.get('seen_at', '1970-01-01')
            )
            stats['oldest_mission'] = sorted_missions[0].get('title')
            stats['newest_mission'] = sorted_missions[-1].get('title')
        
        return stats
    
    def _cleanup_old_missions(self, days_to_keep: int = 30) -> None:
        """
        Nettoie les missions anciennes pour éviter que le fichier devienne trop volumineux
        
        Args:
            days_to_keep: Nombre de jours à conserver
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        missions_to_remove = []
        
        for mission_id, mission_data in self.missions_data.items():
            try:
                seen_at = datetime.fromisoformat(mission_data.get('seen_at', '1970-01-01'))
                if seen_at < cutoff_date:
                    missions_to_remove.append(mission_id)
            except ValueError:
                # Date invalide, on garde la mission par sécurité
                continue
        
        # Supprimer les missions anciennes
        for mission_id in missions_to_remove:
            self.seen_missions.discard(mission_id)
            self.missions_data.pop(mission_id, None)
        
        if missions_to_remove:
            logger.info(f"Nettoyage: {len(missions_to_remove)} anciennes missions supprimées")
    
    def reset_state(self) -> bool:
        """
        Remet à zéro l'état (utile pour les tests ou reset manuel)
        
        Returns:
            True si réinitialisé avec succès
        """
        try:
            self.seen_missions.clear()
            self.missions_data.clear()
            
            if os.path.exists(self.data_file):
                os.remove(self.data_file)
            
            logger.info("État réinitialisé")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la réinitialisation: {e}")
            return False 