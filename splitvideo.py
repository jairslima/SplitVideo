from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


VIDEO_EXTENSIONS = {
    ".avi",
    ".m4v",
    ".mkv",
    ".mov",
    ".mp4",
    ".mpeg",
    ".mpg",
    ".ts",
    ".webm",
    ".wmv",
}


class SplitVideoError(Exception):
    pass


@dataclass(frozen=True)
class Segment:
    index: int
    start_seconds: float
    end_seconds: float
    output_path: Path


@dataclass(frozen=True)
class StreamInfo:
    codec_name: str
    codec_type: str


@dataclass
class ExecutionLog:
    started_at: str
    input_path: str
    output_dir: str
    duration_seconds: float
    cuts_requested: list[str]
    cuts_resolved: list[float]
    name_mode: str
    segments: list[dict]
    verification: list[dict]


def setup_console_output() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None:
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
        except (AttributeError, ValueError):
            pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Divide um video em varias partes sem recodificar. "
            "Aceita tempos absolutos como 16:47 e percentuais como 50%."
        )
    )
    parser.add_argument(
        "target",
        nargs="?",
        help="Arquivo de video ou pasta de trabalho. Se omitido, usa o diretorio atual.",
    )
    parser.add_argument(
        "cuts",
        nargs="*",
        help="Pontos de corte. Pode passar varios valores ou uma lista separada por virgula.",
    )
    parser.add_argument(
        "--ffmpeg",
        help="Caminho para ffmpeg.exe. Se omitido, tenta PATH, pasta atual e tools.",
    )
    parser.add_argument(
        "--ffprobe",
        help="Caminho para ffprobe.exe. Se omitido, tenta PATH, pasta atual e tools.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Apenas lista os videos encontrados e encerra.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Monta os cortes e exibe os comandos sem executar ffmpeg.",
    )
    parser.add_argument(
        "--output-dir",
        help="Pasta de saida. Se omitido, grava ao lado do video original.",
    )
    parser.add_argument(
        "--name-mode",
        choices=("verbose", "short"),
        default="verbose",
        help="Padrao dos nomes de arquivo gerados.",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verifica codec e duracao das saidas com ffprobe apos cada corte.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Executa sem pedir confirmacao interativa.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    setup_console_output()
    args = build_parser().parse_args(argv)

    try:
        ffmpeg_path, ffprobe_path = resolve_binaries(args.ffmpeg, args.ffprobe)
        target_path = Path(args.target).expanduser() if args.target else Path.cwd()
        selected_video = resolve_video_target(target_path, list_only=args.list)
        if args.list:
            return 0

        output_dir = resolve_output_dir(selected_video, args.output_dir)
        duration_seconds = probe_duration(selected_video, ffprobe_path)
        original_streams = probe_streams(selected_video, ffprobe_path)
        print(
            f"Arquivo: {selected_video}\n"
            f"Duracao detectada: {format_seconds(duration_seconds)}\n"
            f"Saida: {output_dir}"
        )

        raw_cuts = collect_cut_tokens(args.cuts)
        if not raw_cuts:
            raw_cuts = prompt_cut_tokens()

        cut_points = normalize_cut_points(raw_cuts, duration_seconds)
        segments = build_segments(
            selected_video=selected_video,
            output_dir=output_dir,
            cut_points=cut_points,
            duration_seconds=duration_seconds,
            name_mode=args.name_mode,
        )

        execution_log = ExecutionLog(
            started_at=datetime.now().isoformat(timespec="seconds"),
            input_path=str(selected_video),
            output_dir=str(output_dir),
            duration_seconds=duration_seconds,
            cuts_requested=raw_cuts,
            cuts_resolved=cut_points,
            name_mode=args.name_mode,
            segments=[
                {
                    "index": segment.index,
                    "start_seconds": segment.start_seconds,
                    "end_seconds": segment.end_seconds,
                    "output_path": str(segment.output_path),
                }
                for segment in segments
            ],
            verification=[],
        )

        print("\nPartes planejadas:")
        for segment in segments:
            print(
                f"{segment.index:02d}. {format_seconds(segment.start_seconds)} -> "
                f"{format_seconds(segment.end_seconds)}"
            )
            print(f"    {segment.output_path}")

        if args.dry_run:
            print("\nDry run: nenhum arquivo foi gerado.")
            return 0

        if not args.yes:
            confirm = input("\nExecutar cortes? [s/N]: ").strip().lower()
            if confirm not in {"s", "sim", "y", "yes"}:
                print("Operacao cancelada.")
                return 1

        for segment in segments:
            run_split_command(selected_video, segment, ffmpeg_path)
            if args.verify:
                execution_log.verification.append(
                    verify_segment(segment, ffprobe_path, original_streams)
                )

        log_path = write_execution_log(execution_log, output_dir)
        print(f"\nConcluido.\nLog: {log_path}")
        return 0
    except SplitVideoError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nOperacao interrompida.", file=sys.stderr)
        return 130


def resolve_binaries(
    ffmpeg_override: str | None, ffprobe_override: str | None
) -> tuple[Path, Path]:
    ffmpeg_path = resolve_binary("ffmpeg", ffmpeg_override)
    ffprobe_path = resolve_binary("ffprobe", ffprobe_override)
    return ffmpeg_path, ffprobe_path


def resolve_binary(name: str, override: str | None) -> Path:
    candidates: list[Path] = []

    if override:
        candidates.append(Path(override).expanduser())

    if env_value := os.environ.get(name.upper()):
        candidates.append(Path(env_value))

    if found := shutil.which(name):
        candidates.append(Path(found))

    root = app_root()
    candidates.extend(
        [
            root / f"{name}.exe",
            root / name,
            root / "tools" / f"{name}.exe",
            root / "tools" / name,
        ]
    )

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    raise SplitVideoError(
        f"{name} nao encontrado. Use --{name} ou coloque {name}.exe no PATH ou em "
        f"{root}\\tools."
    )


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def resolve_video_target(target_path: Path, list_only: bool) -> Path:
    if target_path.is_file():
        if not is_video_file(target_path):
            raise SplitVideoError(f"Arquivo nao parece video suportado: {target_path}")
        return target_path.resolve()

    working_dir = target_path if target_path.exists() else Path.cwd() / target_path
    if not working_dir.exists():
        raise SplitVideoError(f"Caminho nao encontrado: {working_dir}")
    if not working_dir.is_dir():
        raise SplitVideoError(f"Caminho invalido: {working_dir}")

    videos = find_videos(working_dir)
    if not videos:
        raise SplitVideoError(f"Nenhum video encontrado em: {working_dir}")

    print(f"Local de trabalho: {working_dir}")
    for index, video in enumerate(videos, start=1):
        print(f"{index:02d}. {video.name}")

    if list_only:
        return videos[0]

    if len(videos) == 1:
        print("Video unico encontrado; usando automaticamente.")
        return videos[0]

    selection = input("Selecione o video pelo numero: ").strip()
    try:
        selected_index = int(selection)
    except ValueError as exc:
        raise SplitVideoError("Selecao invalida.") from exc

    if not 1 <= selected_index <= len(videos):
        raise SplitVideoError("Selecao fora da lista.")

    return videos[selected_index - 1]


def resolve_output_dir(selected_video: Path, output_dir_value: str | None) -> Path:
    if output_dir_value:
        output_dir = Path(output_dir_value).expanduser()
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir.resolve()
    return selected_video.parent.resolve()


def find_videos(directory: Path) -> list[Path]:
    return sorted(
        [
            item
            for item in directory.iterdir()
            if item.is_file() and is_video_file(item)
        ],
        key=lambda item: item.name.lower(),
    )


def is_video_file(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTENSIONS


def probe_duration(video_path: Path, ffprobe_path: Path) -> float:
    completed = run_ffprobe(
        ffprobe_path,
        [
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ],
    )
    output = completed.stdout.strip().replace(",", ".")
    try:
        duration = float(output)
    except ValueError as exc:
        raise SplitVideoError(f"Duracao invalida retornada por ffprobe: {output!r}") from exc

    if duration <= 0:
        raise SplitVideoError("Duracao do video nao pode ser zero.")
    return duration


def probe_streams(video_path: Path, ffprobe_path: Path) -> list[StreamInfo]:
    completed = run_ffprobe(
        ffprobe_path,
        [
            "-show_entries",
            "stream=codec_name,codec_type",
            "-of",
            "json",
            str(video_path),
        ],
    )
    data = json.loads(completed.stdout)
    streams = [
        StreamInfo(
            codec_name=stream.get("codec_name", ""),
            codec_type=stream.get("codec_type", ""),
        )
        for stream in data.get("streams", [])
    ]
    if not streams:
        raise SplitVideoError("Nenhum stream detectado no video.")
    return streams


def run_ffprobe(ffprobe_path: Path, arguments: list[str]) -> subprocess.CompletedProcess[str]:
    command = [str(ffprobe_path), "-v", "error", *arguments]
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        raise SplitVideoError(
            "ffprobe falhou.\n"
            f"Comando: {' '.join(command)}\n"
            f"Saida: {completed.stderr.strip() or completed.stdout.strip()}"
        )
    return completed


def collect_cut_tokens(cuts: list[str]) -> list[str]:
    tokens: list[str] = []
    for raw_cut in cuts:
        tokens.extend(split_cut_list(raw_cut))
    return tokens


def prompt_cut_tokens() -> list[str]:
    raw_value = input(
        "Informe um ou mais pontos de corte (ex.: 16:47, 50%, 1:10:30): "
    ).strip()
    tokens = split_cut_list(raw_value)
    if not tokens:
        raise SplitVideoError("Nenhum ponto de corte informado.")
    return tokens


def split_cut_list(raw_value: str) -> list[str]:
    return [token.strip() for token in raw_value.split(",") if token.strip()]


def normalize_cut_points(raw_cuts: Iterable[str], duration_seconds: float) -> list[float]:
    resolved_points = [parse_cut_token(raw_cut, duration_seconds) for raw_cut in raw_cuts]
    sorted_unique = sorted({round(point, 6) for point in resolved_points})
    if not sorted_unique:
        raise SplitVideoError("Nenhum ponto de corte valido foi gerado.")
    return sorted_unique


def parse_cut_token(raw_cut: str, duration_seconds: float) -> float:
    value = raw_cut.strip()
    if not value:
        raise SplitVideoError("Ponto de corte vazio.")

    if value.endswith("%"):
        percentage_text = value[:-1].strip().replace(",", ".")
        try:
            percentage = float(percentage_text)
        except ValueError as exc:
            raise SplitVideoError(f"Percentual invalido: {raw_cut}") from exc
        if not 0 < percentage < 100:
            raise SplitVideoError(f"Percentual fora do intervalo: {raw_cut}")
        seconds = duration_seconds * (percentage / 100.0)
    else:
        seconds = parse_time_value(value)

    if not 0 < seconds < duration_seconds:
        raise SplitVideoError(
            f"Ponto de corte fora do intervalo do video: {raw_cut} "
            f"(duracao {format_seconds(duration_seconds)})"
        )
    return seconds


def parse_time_value(value: str) -> float:
    sanitized = value.strip().replace(",", ".")

    if ":" in sanitized:
        parts = sanitized.split(":")
    elif sanitized.count(".") == 1 and all(chunk.isdigit() for chunk in sanitized.split(".")):
        parts = sanitized.split(".")
    else:
        parts = [sanitized]

    if not parts or len(parts) > 3:
        raise SplitVideoError(f"Tempo invalido: {value}")

    try:
        numbers = [
            float(part) if index == len(parts) - 1 else int(part)
            for index, part in enumerate(parts)
        ]
    except ValueError as exc:
        raise SplitVideoError(f"Tempo invalido: {value}") from exc

    if any(number < 0 for number in numbers):
        raise SplitVideoError(f"Tempo invalido: {value}")

    if len(parts) == 1:
        return float(numbers[0])
    if len(parts) == 2:
        minutes, seconds = numbers
        if seconds >= 60:
            raise SplitVideoError(f"Tempo invalido: {value}")
        return minutes * 60 + seconds

    hours, minutes, seconds = numbers
    if minutes >= 60 or seconds >= 60:
        raise SplitVideoError(f"Tempo invalido: {value}")
    return hours * 3600 + minutes * 60 + seconds


def build_segments(
    selected_video: Path,
    output_dir: Path,
    cut_points: list[float],
    duration_seconds: float,
    name_mode: str,
) -> list[Segment]:
    boundaries = [0.0, *cut_points, duration_seconds]
    segments: list[Segment] = []

    for index, (start, end) in enumerate(zip(boundaries, boundaries[1:]), start=1):
        output_name = build_output_name(selected_video, index, start, end, name_mode)
        segments.append(
            Segment(
                index=index,
                start_seconds=start,
                end_seconds=end,
                output_path=(output_dir / output_name).resolve(),
            )
        )
    return segments


def build_output_name(
    selected_video: Path, index: int, start_seconds: float, end_seconds: float, name_mode: str
) -> str:
    stem = selected_video.stem if name_mode == "verbose" else sanitize_basename(selected_video.stem)
    suffix = selected_video.suffix
    start_slug = slugify_timestamp(start_seconds)
    end_slug = slugify_timestamp(end_seconds)
    if name_mode == "short":
        return f"{stem}_{index:03d}_{start_slug}_{end_slug}{suffix}"
    return f"{stem}_{index:03d}_{start_slug}-{end_slug}{suffix}"


def sanitize_basename(value: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", value)
    sanitized = re.sub(r"_+", "_", sanitized).strip("._-")
    return sanitized or "video"


def run_split_command(video_path: Path, segment: Segment, ffmpeg_path: Path) -> None:
    duration = segment.end_seconds - segment.start_seconds
    if duration <= 0:
        raise SplitVideoError("Segmento com duracao invalida.")

    command = [
        str(ffmpeg_path),
        "-y",
        "-v",
        "error",
        "-ss",
        format_ffmpeg_timestamp(segment.start_seconds),
        "-i",
        str(video_path),
        "-t",
        format_ffmpeg_timestamp(duration),
        "-c",
        "copy",
        str(segment.output_path),
    ]
    print(f"\nExecutando parte {segment.index:02d}:")
    print(" ".join(quote_if_needed(item) for item in command))

    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        raise SplitVideoError(f"ffmpeg falhou ao gerar: {segment.output_path}")


def verify_segment(
    segment: Segment, ffprobe_path: Path, original_streams: list[StreamInfo]
) -> dict:
    duration = probe_duration(segment.output_path, ffprobe_path)
    streams = probe_streams(segment.output_path, ffprobe_path)
    verification = {
        "output_path": str(segment.output_path),
        "duration_seconds": duration,
        "expected_duration_seconds": round(segment.end_seconds - segment.start_seconds, 6),
        "streams_match": [(s.codec_type, s.codec_name) for s in streams]
        == [(s.codec_type, s.codec_name) for s in original_streams],
        "streams": [asdict(stream) for stream in streams],
    }
    print(
        "Verificacao:"
        f" duracao={format_seconds(duration)}"
        f", codecs_ok={'sim' if verification['streams_match'] else 'nao'}"
    )
    return verification


def write_execution_log(execution_log: ExecutionLog, output_dir: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = output_dir / f"splitvideo_log_{timestamp}.json"
    log_path.write_text(
        json.dumps(asdict(execution_log), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return log_path


def format_seconds(seconds: float) -> str:
    total_milliseconds = int(round(seconds * 1000))
    total_seconds, milliseconds = divmod(total_milliseconds, 1000)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if milliseconds:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_ffmpeg_timestamp(seconds: float) -> str:
    total_milliseconds = int(round(seconds * 1000))
    hours, remainder = divmod(total_milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, milliseconds = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"


def slugify_timestamp(seconds: float) -> str:
    formatted = format_seconds(seconds)
    return formatted.replace(":", "-").replace(".", "_")


def quote_if_needed(value: str) -> str:
    return f'"{value}"' if " " in value else value


if __name__ == "__main__":
    raise SystemExit(main())
