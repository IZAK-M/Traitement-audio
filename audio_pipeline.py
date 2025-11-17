"""
Pipeline de traitement audio configurable
Permet d'appliquer des effets audio et de générer des fichiers augmentés
"""

import yaml
import os
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range
from pydub.playback import play
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AudioPipeline:
    """Classe principale pour le pipeline de traitement audio"""
    
    def __init__(self, config_file='config.yaml'):
        """
        Initialise le pipeline avec un fichier de configuration
        
        Args:
            config_file (str): Chemin vers le fichier YAML de configuration
        """
        self.config = self.load_config(config_file)
        self.audio_segments = []
        self.mix_segments = []
        self.concatenate_segments = []
        self.result = None
        
    def load_config(self, config_file):
        """
        Charge la configuration depuis un fichier YAML
        
        Args:
            config_file (str): Chemin vers le fichier YAML
            
        Returns:
            dict: Configuration chargée
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                logger.info(f"Configuration chargée depuis {config_file}")
                return config
        except FileNotFoundError:
            logger.error(f"Fichier de configuration {config_file} introuvable")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Erreur lors du parsing YAML: {e}")
            raise
    
    def load_audio_files(self):
        """
        Charge tous les fichiers audio spécifiés dans la configuration
        Supporte mix_files, concatenate_files, et audio_files (legacy)
        """
        input_folder = self.config.get('input_folder', 'input_audio')
        
        if not os.path.exists(input_folder):
            logger.error(f"Le dossier {input_folder} n'existe pas")
            raise FileNotFoundError(f"Dossier {input_folder} introuvable")
        
        # Charger les fichiers à mixer
        mix_files = self.config.get('mix_files', [])
        for audio_file in mix_files:
            file_path = os.path.join(input_folder, audio_file)
            try:
                audio = AudioSegment.from_file(file_path)
                self.mix_segments.append(audio)
                logger.info(f"Fichier pour mixage chargé: {audio_file} ({len(audio)}ms, {audio.frame_rate}Hz)")
            except Exception as e:
                logger.error(f"Erreur lors du chargement de {audio_file}: {e}")
        
        # Charger les fichiers à concaténer
        concatenate_files = self.config.get('concatenate_files', [])
        for audio_file in concatenate_files:
            file_path = os.path.join(input_folder, audio_file)
            try:
                audio = AudioSegment.from_file(file_path)
                self.concatenate_segments.append(audio)
                logger.info(f"Fichier pour concaténation chargé: {audio_file} ({len(audio)}ms, {audio.frame_rate}Hz)")
            except Exception as e:
                logger.error(f"Erreur lors du chargement de {audio_file}: {e}")
        
        # Support de l'ancien format (audio_files) pour compatibilité
        audio_files = self.config.get('audio_files', [])
        if audio_files and not mix_files and not concatenate_files:
            for audio_file in audio_files:
                file_path = os.path.join(input_folder, audio_file)
                try:
                    audio = AudioSegment.from_file(file_path)
                    self.audio_segments.append(audio)
                    logger.info(f"Fichier chargé: {audio_file} ({len(audio)}ms, {audio.frame_rate}Hz)")
                except Exception as e:
                    logger.error(f"Erreur lors du chargement de {audio_file}: {e}")
    
    def apply_volume_effect(self, audio, params):
        """
        Applique un changement de volume
        
        Args:
            audio (AudioSegment): Segment audio à modifier
            params (dict): Paramètres (gain en dB)
            
        Returns:
            AudioSegment: Audio modifié
        """
        gain = params.get('gain', 0)
        logger.info(f"Application de l'effet volume: {gain}dB")
        return audio + gain
    
    def apply_speed_effect(self, audio, params):
        """
        Modifie la vitesse de lecture
        
        Args:
            audio (AudioSegment): Segment audio à modifier
            params (dict): Paramètres (factor: 1.0 = normal, 2.0 = 2x plus rapide)
            
        Returns:
            AudioSegment: Audio modifié
        """
        factor = params.get('factor', 1.0)
        logger.info(f"Application de l'effet vitesse: x{factor}")
        
        # Modifier la vitesse en changeant le frame_rate
        sound_with_altered_frame_rate = audio._spawn(audio.raw_data, 
                                                      overrides={'frame_rate': int(audio.frame_rate * factor)})
        # Reconvertir au frame_rate original pour maintenir la compatibilité
        return sound_with_altered_frame_rate.set_frame_rate(audio.frame_rate)
    
    def apply_fade_effect(self, audio, params):
        """
        Applique un fondu en entrée et/ou sortie
        
        Args:
            audio (AudioSegment): Segment audio à modifier
            params (dict): Paramètres (fade_in, fade_out en ms)
            
        Returns:
            AudioSegment: Audio modifié
        """
        fade_in = params.get('fade_in', 0)
        fade_out = params.get('fade_out', 0)
        
        result = audio
        if fade_in > 0:
            result = result.fade_in(fade_in)
            logger.info(f"Fade in appliqué: {fade_in}ms")
        if fade_out > 0:
            result = result.fade_out(fade_out)
            logger.info(f"Fade out appliqué: {fade_out}ms")
        
        return result
    
    def apply_reverse_effect(self, audio, params):
        """
        Inverse l'audio
        
        Args:
            audio (AudioSegment): Segment audio à modifier
            params (dict): Paramètres (non utilisés)
            
        Returns:
            AudioSegment: Audio inversé
        """
        logger.info("Application de l'effet reverse")
        return audio.reverse()
    
    def apply_normalize_effect(self, audio, params):
        """
        Normalise le volume audio
        
        Args:
            audio (AudioSegment): Segment audio à modifier
            params (dict): Paramètres (headroom en dB)
            
        Returns:
            AudioSegment: Audio normalisé
        """
        headroom = params.get('headroom', 0.1)
        logger.info(f"Normalisation avec headroom: {headroom}dB")
        return normalize(audio, headroom=headroom)
    
    def apply_repeat_effect(self, audio, params):
        """
        Répète l'audio un certain nombre de fois
        
        Args:
            audio (AudioSegment): Segment audio à modifier
            params (dict): Paramètres (times: nombre de répétitions)
            
        Returns:
            AudioSegment: Audio répété
        """
        times = params.get('times', 1)
        logger.info(f"Répétition de l'audio: {times} fois")
        return audio * times
    
    def mix_audio_files(self):
        """
        Mélange tous les fichiers audio chargés
        
        Returns:
            AudioSegment: Audio mixé
        """
        if not self.audio_segments:
            logger.warning("Aucun fichier audio à mixer")
            return None
        
        logger.info(f"Mixage de {len(self.audio_segments)} fichiers audio")
        
        # Prendre le premier fichier comme base
        mixed = self.audio_segments[0]
        
        # Superposer les autres fichiers
        for audio in self.audio_segments[1:]:
            mixed = mixed.overlay(audio)
        
        return mixed
    
    def concatenate_audio_files(self):
        """
        Concatène tous les fichiers audio chargés bout à bout
        
        Returns:
            AudioSegment: Audio concaténé
        """
        if not self.audio_segments:
            logger.warning("Aucun fichier audio à concaténer")
            return None
        
        logger.info(f"Concaténation de {len(self.audio_segments)} fichiers audio")
        
        result = self.audio_segments[0]
        for audio in self.audio_segments[1:]:
            result += audio
        
        return result
    
    def apply_effects(self, audio):
        """
        Applique tous les effets spécifiés dans la configuration
        
        Args:
            audio (AudioSegment): Segment audio à traiter
            
        Returns:
            AudioSegment: Audio avec effets appliqués
        """
        effects = self.config.get('effects', [])
        result = audio
        
        # Dictionnaire des effets disponibles
        effect_functions = {
            'volume': self.apply_volume_effect,
            'speed': self.apply_speed_effect,
            'fade': self.apply_fade_effect,
            'reverse': self.apply_reverse_effect,
            'normalize': self.apply_normalize_effect,
            'repeat': self.apply_repeat_effect,
        }
        
        for effect in effects:
            effect_type = effect.get('type')
            if effect_type in effect_functions:
                result = effect_functions[effect_type](result, effect)
            else:
                logger.warning(f"Effet inconnu: {effect_type}")
        
        return result
    
    def save_audio(self, audio, output_name='result'):
        """
        Sauvegarde l'audio dans les formats spécifiés
        
        Args:
            audio (AudioSegment): Audio à sauvegarder
            output_name (str): Nom de base du fichier de sortie
        """
        output_folder = self.config.get('output_folder', 'output_audio')
        output_formats = self.config.get('output_formats', ['mp3', 'wav'])
        
        # Créer le dossier de sortie s'il n'existe pas
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            logger.info(f"Dossier de sortie créé: {output_folder}")
        
        for fmt in output_formats:
            output_path = os.path.join(output_folder, f"{output_name}.{fmt}")
            try:
                # Paramètres d'export selon le format
                if fmt == 'mp3':
                    audio.export(output_path, format='mp3', bitrate='192k')
                elif fmt == 'wav':
                    audio.export(output_path, format='wav')
                else:
                    audio.export(output_path, format=fmt)
                
                logger.info(f"Fichier sauvegardé: {output_path}")
            except Exception as e:
                logger.error(f"Erreur lors de la sauvegarde en {fmt}: {e}")
    
    def run(self):
        """
        Execute le pipeline complet
        """
        logger.info("=" * 50)
        logger.info("Démarrage du pipeline audio")
        logger.info("=" * 50)
        
        # 1. Charger les fichiers audio
        self.load_audio_files()
        
        # 2. Traiter selon la nouvelle configuration (mix_files + concatenate_files)
        if self.mix_segments or self.concatenate_segments:
            # Nouveau format: mix_files et/ou concatenate_files
            mixed_audio = None
            concatenated_audio = None
            
            # Mixer les fichiers si présents
            if self.mix_segments:
                logger.info(f"Mixage de {len(self.mix_segments)} fichiers")
                mixed_audio = self.mix_segments[0]
                for audio in self.mix_segments[1:]:
                    mixed_audio = mixed_audio.overlay(audio)
            
            # Concaténer les fichiers si présents
            if self.concatenate_segments:
                logger.info(f"Concaténation de {len(self.concatenate_segments)} fichiers")
                concatenated_audio = self.concatenate_segments[0]
                for audio in self.concatenate_segments[1:]:
                    concatenated_audio += audio
            
            # Combiner mix et concatenate si les deux existent
            if mixed_audio and concatenated_audio:
                # Déterminer comment combiner (par défaut: concaténer le mix puis le reste)
                final_combine = self.config.get('final_combine_method', 'concatenate')
                if final_combine == 'overlay':
                    self.result = mixed_audio.overlay(concatenated_audio)
                else:  # concatenate
                    self.result = mixed_audio + concatenated_audio
            elif mixed_audio:
                self.result = mixed_audio
            elif concatenated_audio:
                self.result = concatenated_audio
        
        # 3. Support de l'ancien format (audio_files avec combine_method)
        elif self.audio_segments:
            combine_method = self.config.get('combine_method', 'concatenate')
            if combine_method == 'mix':
                self.result = self.mix_audio_files()
            else:
                self.result = self.concatenate_audio_files()
        else:
            logger.error("Aucun fichier audio chargé. Arrêt du pipeline.")
            return
        
        # 4. Appliquer les effets
        if self.result:
            self.result = self.apply_effects(self.result)
        
        # 5. Sauvegarder le résultat
        if self.result:
            output_name = self.config.get('output_name', 'result')
            self.save_audio(self.result, output_name)
        
        logger.info("=" * 50)
        logger.info("Pipeline terminé avec succès!")
        logger.info("=" * 50)


def main():
    """Fonction principale"""
    import sys
    
    try:
        # Vérifier si un fichier de config est passé en argument
        config_file = 'config.yaml'
        if len(sys.argv) > 1:
            config_file = sys.argv[1]
            logger.info(f"Utilisation du fichier de configuration: {config_file}")
        
        # Créer et exécuter le pipeline
        pipeline = AudioPipeline(config_file)
        pipeline.run()
        
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        raise


if __name__ == "__main__":
    main()