"""
Module de parsing RSS pour surveiller les nouvelles missions Codeur.com
"""

import feedparser
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class RSSParser:
    """Parser pour les flux RSS de Codeur.com"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def parse_feed(self, feed_config: Dict) -> List[Dict]:
        """
        Parse un flux RSS et retourne la liste des missions
        
        Args:
            feed_config: Configuration du flux (name, url, color)
            
        Returns:
            Liste des missions avec leurs détails
        """
        try:
            logger.info(f"Parsing flux RSS: {feed_config['name']}")
            
            # Récupérer le flux RSS
            response = self.session.get(feed_config['url'], timeout=30)
            response.raise_for_status()
            
            # Parser le flux
            feed = feedparser.parse(response.content)
            
            if feed.bozo:
                logger.warning(f"Flux RSS potentiellement malformé: {feed_config['name']}")
            
            missions = []
            for entry in feed.entries:
                mission = self._extract_mission_data(entry, feed_config)
                if mission:
                    missions.append(mission)
            
            logger.info(f"Trouvé {len(missions)} missions dans le flux {feed_config['name']}")
            return missions
            
        except Exception as e:
            logger.error(f"Erreur lors du parsing du flux {feed_config['name']}: {e}")
            return []
    
    def _extract_mission_data(self, entry, feed_config: Dict) -> Optional[Dict]:
        """
        Extrait les données d'une mission depuis une entrée RSS
        
        Args:
            entry: Entrée RSS
            feed_config: Configuration du flux
            
        Returns:
            Dictionnaire avec les données de la mission ou None si erreur
        """
        try:
            # Nettoyer la description HTML
            description = self._clean_html_description(entry.description)
            
            # Extraire le budget et les catégories
            budget, categories = self._extract_budget_and_categories(description)
            
            # Extraire le contenu principal
            content = self._extract_main_content(description)
            
            mission = {
                'id': entry.guid,
                'title': entry.title,
                'link': entry.link,
                'pub_date': entry.published,
                'pub_date_parsed': entry.published_parsed,
                'description': description,
                'budget': budget,
                'categories': categories,
                'content': content,
                'feed_name': feed_config['name'],
                'feed_color': feed_config['color']
            }
            
            return mission
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des données de mission: {e}")
            return None
    
    def _clean_html_description(self, html_description: str) -> str:
        """Nettoie la description HTML et extrait le texte"""
        try:
            soup = BeautifulSoup(html_description, 'html.parser')
            return soup.get_text(strip=True)
        except:
            return html_description
    
    def _extract_budget_and_categories(self, description: str) -> tuple:
        """
        Extrait le budget et les catégories depuis la description
        
        Returns:
            Tuple (budget, categories)
        """
        budget = "Non spécifié"
        categories = []
        
        try:
            # Pattern pour extraire budget et catégories
            # Format: "Budget : Moins de 500 € - Catégories : Développement spécifique, API"
            pattern = r"Budget\s*:\s*([^-]+)\s*-\s*Catégories\s*:\s*(.+?)(?:\s*[A-ZÀÁÂÃÄÅÆÇÈÉÊË]|\s*$)"
            match = re.search(pattern, description)
            
            if match:
                budget = match.group(1).strip()
                categories_str = match.group(2).strip()
                categories = [cat.strip() for cat in categories_str.split(',')]
            
        except Exception as e:
            logger.warning(f"Erreur lors de l'extraction budget/catégories: {e}")
        
        return budget, categories
    
    def _extract_main_content(self, description: str) -> str:
        """
        Extrait le contenu principal de la description en supprimant 
        les métadonnées (budget, catégories, lien)
        """
        try:
            # Supprimer la ligne budget/catégories
            content = re.sub(r"Budget\s*:.*?Catégories\s*:.*?\n?", "", description)
            
            # Supprimer le lien "Voir ce projet sur Codeur"
            content = re.sub(r"Voir ce projet sur Codeur.*$", "", content, flags=re.MULTILINE)
            
            # Nettoyer les espaces supplémentaires
            content = re.sub(r'\s+', ' ', content).strip()
            
            return content
            
        except:
            return description


def format_date_fr(date_tuple) -> str:
    """Formate une date en français"""
    if not date_tuple:
        return "Date inconnue"
    
    try:
        dt = datetime(*date_tuple[:6])
        months = [
            'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
            'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'
        ]
        
        return f"{dt.day} {months[dt.month-1]} {dt.year} à {dt.hour:02d}h{dt.minute:02d}"
    except:
        return "Date inconnue" 