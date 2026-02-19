"""
Adapter pour stocker les prompts dans le système de fichiers.

Structure:
prompts/
├── analyst/
│   └── system.md
├── restructurer/
│   ├── system.md
│   └── modules/
│       ├── themes.md
│       ├── vocabulary.md
│       └── ...

Supporte le lazy loading avec cache en mémoire.
"""
from pathlib import Path
from typing import Optional

from src.ports.secondary.prompt_repository_port import PromptRepositoryPort
from src.domain.exceptions import PromptNotFoundError
from src.infrastructure.logging.config import get_logger

logger = get_logger(__name__, "repository")


class FileSystemPromptRepository(PromptRepositoryPort):
    """
    Repository de prompts basé sur le système de fichiers.

    Lazy loading: les prompts sont chargés à la demande et mis en cache.
    """

    SYSTEM_PROMPT_FILE = "system.md"
    MODULES_DIR = "modules"
    SUPPORTED_EXTENSIONS = [".md", ".txt"]

    def __init__(self, prompts_path: str) -> None:
        """
        Initialise le repository.

        Args:
            prompts_path: Chemin vers le dossier racine des prompts
        """
        self._prompts_path = Path(prompts_path)
        self._prompts_path.mkdir(parents=True, exist_ok=True)

        # Cache pour lazy loading
        self._system_cache: dict[str, str] = {}
        self._module_cache: dict[str, dict[str, str]] = {}

        logger.with_extra(path=str(self._prompts_path)).debug(
            "Repository de prompts initialisé"
        )

    def get_system_prompt(self, specialist_id: str) -> str:
        """Récupère le prompt système d'un spécialiste (avec cache)."""
        # Vérifier le cache
        if specialist_id in self._system_cache:
            logger.with_extra(specialist=specialist_id).debug(
                "Prompt système récupéré depuis le cache"
            )
            return self._system_cache[specialist_id]

        # Charger depuis le fichier
        specialist_dir = self._prompts_path / specialist_id
        prompt_file = self._find_file(specialist_dir, self.SYSTEM_PROMPT_FILE)

        if prompt_file is None:
            logger.with_extra(specialist=specialist_id).warning(
                "Prompt système introuvable"
            )
            raise PromptNotFoundError(
                f"Prompt système pour '{specialist_id}' introuvable. "
                f"Attendu: {specialist_dir / self.SYSTEM_PROMPT_FILE}"
            )

        content = prompt_file.read_text(encoding="utf-8")

        # Mettre en cache
        self._system_cache[specialist_id] = content

        logger.with_extra(
            specialist=specialist_id,
            length=len(content)
        ).debug("Prompt système chargé")

        return content

    def get_module_prompt(self, specialist_id: str, module_id: str) -> str:
        """
        Récupère le prompt d'un module (avec cache).

        Supporte deux structures:
        - Standard: specialist/modules/module.md
        - Directe: specialist/module.md (pour le generator avec card_type)

        Le specialist_id peut contenir un sous-chemin (ex: "generator/basic").
        """
        # Vérifier le cache
        if specialist_id in self._module_cache:
            if module_id in self._module_cache[specialist_id]:
                logger.with_extra(
                    specialist=specialist_id,
                    module=module_id
                ).debug("Prompt module récupéré depuis le cache")
                return self._module_cache[specialist_id][module_id]

        # Charger depuis le fichier
        specialist_path = self._prompts_path / specialist_id

        # Essayer d'abord avec le sous-dossier modules/
        modules_dir = specialist_path / self.MODULES_DIR
        prompt_file = self._find_file(modules_dir, module_id)

        # Si pas trouvé, essayer directement dans le dossier specialist
        if prompt_file is None:
            prompt_file = self._find_file(specialist_path, module_id)

        if prompt_file is None:
            logger.with_extra(
                specialist=specialist_id,
                module=module_id
            ).warning("Prompt module introuvable")
            raise PromptNotFoundError(
                f"Prompt module '{module_id}' pour '{specialist_id}' introuvable. "
                f"Attendu: {modules_dir / f'{module_id}.md'} ou {specialist_path / f'{module_id}.md'}"
            )

        content = prompt_file.read_text(encoding="utf-8")

        # Mettre en cache
        if specialist_id not in self._module_cache:
            self._module_cache[specialist_id] = {}
        self._module_cache[specialist_id][module_id] = content

        logger.with_extra(
            specialist=specialist_id,
            module=module_id,
            length=len(content)
        ).debug("Prompt module chargé")

        return content

    def list_specialists(self) -> list[str]:
        """Liste tous les spécialistes (dossiers avec system.md)."""
        specialists = []

        for item in self._prompts_path.iterdir():
            if item.is_dir():
                # Vérifier qu'il y a un system.md
                if self._find_file(item, self.SYSTEM_PROMPT_FILE):
                    specialists.append(item.name)

        logger.with_extra(count=len(specialists)).debug("Spécialistes listés")
        return sorted(specialists)

    def list_modules(self, specialist_id: str) -> list[str]:
        """
        Liste tous les modules d'un spécialiste.

        Supporte deux structures:
        - Standard: specialist/modules/*.md
        - Directe: specialist/*.md (pour le generator avec card_type)
        """
        specialist_path = self._prompts_path / specialist_id
        modules_dir = specialist_path / self.MODULES_DIR

        modules = []

        # Chercher dans modules/ si existe
        if modules_dir.exists():
            for ext in self.SUPPORTED_EXTENSIONS:
                for file in modules_dir.glob(f"*{ext}"):
                    module_id = file.stem
                    if module_id not in modules:
                        modules.append(module_id)

        # Chercher aussi directement (excluant system.md)
        if specialist_path.exists():
            for ext in self.SUPPORTED_EXTENSIONS:
                for file in specialist_path.glob(f"*{ext}"):
                    module_id = file.stem
                    if module_id not in modules and module_id != "system":
                        modules.append(module_id)

        logger.with_extra(
            specialist=specialist_id,
            count=len(modules)
        ).debug("Modules listés")

        return sorted(modules)

    def save_system_prompt(self, specialist_id: str, content: str) -> None:
        """Sauvegarde le prompt système d'un spécialiste."""
        specialist_dir = self._prompts_path / specialist_id
        specialist_dir.mkdir(parents=True, exist_ok=True)

        prompt_file = specialist_dir / self.SYSTEM_PROMPT_FILE
        prompt_file.write_text(content, encoding="utf-8")

        # Invalider le cache
        self._system_cache.pop(specialist_id, None)

        logger.with_extra(
            specialist=specialist_id,
            length=len(content)
        ).info("Prompt système sauvegardé")

    def save_module_prompt(
        self,
        specialist_id: str,
        module_id: str,
        content: str
    ) -> None:
        """Sauvegarde le prompt d'un module."""
        modules_dir = self._prompts_path / specialist_id / self.MODULES_DIR
        modules_dir.mkdir(parents=True, exist_ok=True)

        prompt_file = modules_dir / f"{module_id}.md"
        prompt_file.write_text(content, encoding="utf-8")

        # Invalider le cache
        if specialist_id in self._module_cache:
            self._module_cache[specialist_id].pop(module_id, None)

        logger.with_extra(
            specialist=specialist_id,
            module=module_id,
            length=len(content)
        ).info("Prompt module sauvegardé")

    def clear_cache(self) -> None:
        """Vide le cache (utile pour les tests ou rechargement)."""
        self._system_cache.clear()
        self._module_cache.clear()
        logger.debug("Cache des prompts vidé")

    def _find_file(self, directory: Path, filename: str) -> Optional[Path]:
        """
        Trouve un fichier avec l'extension supportée.

        Args:
            directory: Dossier où chercher
            filename: Nom de base du fichier (avec ou sans extension)

        Returns:
            Path du fichier trouvé ou None
        """
        if not directory.exists():
            return None

        # Si le filename a déjà une extension supportée
        for ext in self.SUPPORTED_EXTENSIONS:
            if filename.endswith(ext):
                file_path = directory / filename
                if file_path.exists():
                    return file_path

        # Sinon, essayer chaque extension
        base_name = filename.replace(".md", "").replace(".txt", "")
        for ext in self.SUPPORTED_EXTENSIONS:
            file_path = directory / f"{base_name}{ext}"
            if file_path.exists():
                return file_path

        return None
