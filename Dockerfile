FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de requirements
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY *.py ./

# Copier les fichiers de configuration (optionnel, peut être monté via volume)
COPY config.yaml ./
COPY .env.example ./

# Créer un utilisateur non-root pour la sécurité
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Créer le répertoire pour les données persistantes
RUN mkdir -p /app/data

# Point d'entrée par défaut
CMD ["python", "main.py"]

# Sanity check
HEALTHCHECK --interval=5m --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('https://httpbin.org/status/200', timeout=5)" || exit 1

# Labels
LABEL maintainer="Bot Discord Mission Codeur"
LABEL description="Bot de surveillance des missions Codeur.com avec notifications Discord"
LABEL version="1.0" 