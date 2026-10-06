"""Point d'entrée CLI : commande `vector` (contracts/cli-contract.md)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from vectorizator import checkpoint  # module : save / load / remove
from vectorizator.config import (
    DEFAULT_MODEL,
    MODELS,
    ConfigError,
    load_api_key,
    model_dimension,
)
from vectorizator.counter import CounterError, next_occurrence
from vectorizator.embedder import EmbeddingError, embed_texts
from vectorizator.inputs import InputsError, collect_inputs
from vectorizator.output import save_matrix
from vectorizator.schema import SchemaError, validate_index

EXIT_OK = 0
EXIT_CONFIG = 1
EXIT_DOC_FAILURE = 2


class CliError(Exception):
    """Erreur de configuration ou de validation des options."""


def build_parser() -> argparse.ArgumentParser:
    """Construit le parseur d'arguments de la commande `vector`."""
    parser = argparse.ArgumentParser(
        prog="vector",
        description=(
            "Vectorise les chunks de JSON d'index (schéma 1.0) en "
            "matrices NumPy via l'API Mistral Embeddings."
        ),
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        metavar="INPUT",
        help="Chemin(s) de fichier(s) .json ou de dossier(s).",
    )
    parser.add_argument(
        "--choix-techno",
        default=DEFAULT_MODEL,
        help=f"Modèle d'embedding (défaut : {DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--taille-batch",
        type=int,
        default=25,
        help="Chunks par lot, 0 à 100 ; 0 = requête simple (défaut : 25).",
    )
    parser.add_argument(
        "--retry-occurences",
        type=int,
        default=3,
        help="Nombre de retry par échec, 0 à 10 (défaut : 3).",
    )
    parser.add_argument(
        "--retry-time",
        type=int,
        default=3,
        help="Premier délai de retry en secondes, 1 à 10 (défaut : 3).",
    )
    parser.add_argument(
        "--output-folder",
        default="output",
        help="Dossier de sortie, créé si absent (défaut : output).",
    )
    return parser


def validate_args(args: argparse.Namespace) -> None:
    """Valide les bornes des options ; échoue vite et clairement (FR-016)."""
    if args.choix_techno not in MODELS:
        accepted = ", ".join(sorted(MODELS))
        msg = f"--choix-techno : {args.choix_techno!r} inconnu (acceptés : {accepted})."
        raise CliError(msg)
    if not 0 <= args.taille_batch <= 100:
        raise CliError("--taille-batch doit être compris entre 0 et 100.")
    if not 0 <= args.retry_occurences <= 10:
        raise CliError("--retry-occurences doit être compris entre 0 et 10.")
    if not 1 <= args.retry_time <= 10:
        raise CliError("--retry-time doit être compris entre 1 et 10.")


def make_client(api_key: str):
    """Crée le client SDK Mistral (import paresseux : les tests l'injectent).

    Forme d'import de la documentation officielle Mistral
    (embedders : `from mistralai.client import Mistral`).
    """
    from mistralai.client import Mistral

    return Mistral(api_key=api_key)


def process_document(
    client,
    model: str,
    dimension: int,
    source: Path,
    output_dir: Path,
    batch_size: int,
    retry_occurrences: int,
    retry_time: int,
) -> Path:
    """Traite un JSON : valider -> reprendre -> vectoriser -> sauvegarder.

    Reprise (FR-009) : les vecteurs des lots déjà réussis sont rechargés
    depuis le checkpoint ; seuls les lots restants sont renvoyés à
    l'API. Un checkpoint lié à un autre modèle (ou taille de lot) est
    invalidé avec avertissement (clarification Q3). Le checkpoint est
    supprimé après écriture de la matrice (clarification Q4).

    Le numéro d'occurrence est consommé et persisté juste avant
    l'écriture de la matrice : jamais réutilisé, même si l'écriture est
    interrompue (FR-011, R-07).
    """
    data = json.loads(source.read_text(encoding="utf-8"))
    _title, texts = validate_index(data, str(source))
    stored, invalidated = checkpoint.load(output_dir, source, model, batch_size)
    if invalidated:
        print(
            f"[AVERTISSEMENT] {source} : état de reprise ignoré "
            "(modèle ou taille de lot différent, ou fichier corrompu) ; "
            "re-vectorisation depuis le premier lot."
        )
        stored = []
    size = batch_size if batch_size > 0 else 1
    skip_batches = len(stored) // size

    def _persist(vectors_so_far: list[list[float]]) -> None:
        checkpoint.save(output_dir, source, model, batch_size, vectors_so_far)

    fresh_vectors = embed_texts(
        client,
        model,
        texts,
        dimension,
        batch_size,
        retry_occurrences,
        retry_time,
        skip_batches=skip_batches,
        on_batch_done=_persist,
    )
    vectors = stored + fresh_vectors
    occurrence = next_occurrence(Path.cwd())
    path = save_matrix(output_dir, Path(source).stem, occurrence, vectors)
    checkpoint.remove(output_dir, source)
    print(f"[OK] {source} -> {path}")
    return path


def run(args: argparse.Namespace) -> int:
    """Exécute le traitement des inputs ; retourne le code de sortie.

    Chaque JSON est traité indépendamment : l'échec d'un document
    n'interrompt pas les suivants (FR-003). Un compteur corrompu est le
    seul arrêt global : fail-fast sans écrire de sortie (FR-013).
    """
    try:
        api_key = load_api_key()
    except ConfigError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return EXIT_CONFIG
    model = args.choix_techno
    try:
        dimension = model_dimension(model)
    except ConfigError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return EXIT_CONFIG
    try:
        sources = collect_inputs(args.inputs)
    except InputsError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return EXIT_CONFIG
    if not sources:
        print(
            "Erreur : aucun fichier .json traitable n'a été trouvé "
            "dans les inputs donnés.",
            file=sys.stderr,
        )
        return EXIT_CONFIG
    client = make_client(api_key)
    output_dir = Path(args.output_folder)
    failures = 0
    try:
        for source in sources:
            try:
                process_document(
                    client,
                    model,
                    dimension,
                    source,
                    output_dir,
                    args.taille_batch,
                    args.retry_occurences,
                    args.retry_time,
                )
            except (
                SchemaError,
                EmbeddingError,
                OSError,
                json.JSONDecodeError,
            ) as exc:
                failures += 1
                print(f"Erreur : {exc}", file=sys.stderr)
    except CounterError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return EXIT_CONFIG
    if failures:
        print(f"{failures} document(s) en échec.", file=sys.stderr)
        return EXIT_DOC_FAILURE
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    """Point d'entrée console `vector` ; retourne le code de sortie."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        validate_args(args)
    except CliError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return EXIT_CONFIG
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
