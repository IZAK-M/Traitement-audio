# 🎵 Pipeline de Traitement Audio

Pipeline configurable pour appliquer des effets audio et générer des fichiers augmentés via un fichier YAML.

## 📋 Prérequis

- Python 3.12
- FFmpeg installé sur le système
- Anaconda (recommandé)

## 🚀 Installation

```bash
# Créer l'environnement avec conda
conda create -n env_audio python=3.12
conda activate env_audio

# Installer les dépendances
pip install pydub PyYAML
```

## 📁 Structure du Projet

```
audio_pipeline/
├── audio_pipeline.py      # Script principal
├── config.yaml            # Configuration
├── README.md
├── input_audio/           # Fichiers audio sources
└── output_audio/          # Fichiers générés
```

## 🎛️ Effets Disponibles

| Effet | Paramètres | Description |
|-------|-----------|-------------|
| `volume` | `gain` (dB) | Augmente/diminue le volume |
| `speed` | `factor` (1.0 = normal) | Modifie la vitesse |
| `fade` | `fade_in`, `fade_out` (ms) | Fondus entrée/sortie |
| `reverse` | - | Inverse l'audio |
| `normalize` | `headroom` (dB) | Normalise le volume |
| `repeat` | `times` | Répète l'audio |

## 🎯 Utilisation

```bash
# Avec config.yaml par défaut
python audio_pipeline.py

# Avec un fichier de config spécifique
python audio_pipeline.py config_mix.yaml
```


## 📄 Licence

MIT