import subprocess
import sys
import tempfile
from pathlib import Path


def obter_duracao_video(video_path):
    resultado = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(resultado.stdout.strip())


def executar(comando):
    resultado = subprocess.run(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if resultado.returncode != 0:
        raise RuntimeError(
            "Erro no FFmpeg:\n" + resultado.stderr
        )


def juntar_video_foto(
    video_path,
    fotos_paths,
    saida_path,
    duracao_foto=5,
    trilha_path=None,
):
    video = Path(video_path)
    fotos = [Path(f) for f in fotos_paths]
    saida = Path(saida_path)

    if not video.exists():
        raise FileNotFoundError(f"Vídeo não encontrado: {video}")

    if not fotos:
        raise FileNotFoundError("Nenhuma foto foi informada.")

    for foto in fotos:
        if not foto.exists():
            raise FileNotFoundError(f"Foto não encontrada: {foto}")

    if trilha_path is None:
        trilha_path = Path(__file__).parent / "busca" / "trilha_padrao.mp3"
    else:
        trilha_path = Path(trilha_path)

    if not trilha_path.exists():
        raise FileNotFoundError(
            f"Trilha não encontrada: {trilha_path}"
        )

    saida.parent.mkdir(parents=True, exist_ok=True)

    duracao_video = obter_duracao_video(video)
    duracao_total_fotos = len(fotos) * duracao_foto
    duracao_total = duracao_video + duracao_total_fotos

    with tempfile.TemporaryDirectory(
        prefix="montagem_",
        dir=str(saida.parent),
    ) as tmp:
        tmp = Path(tmp)

        video_sem_audio = tmp / "video_sem_audio.mp4"
        audio_original = tmp / "audio_original.wav"
        audio_trilha = tmp / "audio_trilha.wav"
        audio_final = tmp / "audio_final.wav"

        # ==========================================================
        # 1. NORMALIZA O VÍDEO E MONTA COM AS FOTOS
        # ==========================================================

        video_normalizado = tmp / "video_normalizado.mp4"
        video_sem_audio = tmp / "video_sem_audio.mp4"

        # Primeiro transforma o vídeo original em exatamente 30 FPS.
        executar(
            [
                "ffmpeg",
                "-y",
                "-fflags", "+genpts",
                "-i", str(video),
                "-an",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                str(video_normalizado),
            ]
        )

        comandos = [
            "ffmpeg",
            "-y",
            "-i", str(video_normalizado),
        ]

        for foto in fotos:
            comandos += [
                "-loop", "1",
                "-framerate", "30",
                "-i", str(foto),
            ]

        filtros = []

        filtros.append(
            "[0:v]"
            "setpts=PTS-STARTPTS,"
            "scale=720:1280:force_original_aspect_ratio=decrease,"
            "pad=720:1280:(ow-iw)/2:(oh-ih)/2,"
            "fps=30,"
            "format=yuv420p,"
            f"trim=duration={duracao_video},"
            "setpts=N/30/TB"
            "[v0]"
        )

        primeiro_indice_foto = 1

        for i, _foto in enumerate(fotos):
            indice = primeiro_indice_foto + i

            filtros.append(
                f"[{indice}:v]"
                "scale=720:1280:force_original_aspect_ratio=increase,"
                "crop=720:1280,"
                "boxblur=25:2,"
                "fps=30,"
                "format=yuv420p,"
                f"trim=duration={duracao_foto},"
                "setpts=N/30/TB"
                f"[bg{i}]"
            )

            filtros.append(
                f"[{indice}:v]"
                "scale=720:720:force_original_aspect_ratio=decrease,"
                "pad=720:720:(ow-iw)/2:(oh-ih)/2,"
                "fps=30,"
                "format=yuv420p,"
                f"trim=duration={duracao_foto},"
                "setpts=N/30/TB"
                f"[fg{i}]"
            )

            if i == len(fotos) - 1:
                filtros.append(
                    f"[bg{i}][fg{i}]"
                    "overlay=0:(H-h)/2,"
                    f"fade=t=out:st={duracao_foto - 1}:d=1:color=black,"
                    "setpts=N/30/TB"
                    f"[v{i + 1}]"
                )
            else:
                filtros.append(
                    f"[bg{i}][fg{i}]"
                    "overlay=0:(H-h)/2,"
                    "setpts=N/30/TB"
                    f"[v{i + 1}]"
                )

        entradas_video = "[v0]" + "".join(
            f"[v{i + 1}]"
            for i in range(len(fotos))
        )

        filtros.append(
            entradas_video
            + f"concat=n={len(fotos) + 1}:v=1:a=0,"
            "setpts=N/30/TB"
            "[outv]"
        )

        filtro_video = ";".join(filtros)

        executar(
            comandos
            + [
                "-filter_complex", filtro_video,
                "-map", "[outv]",
                "-an",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                "-r", "30",
                "-movflags", "+faststart",
                str(video_sem_audio),
            ]
        )

        # ==========================================================
        # 2. NORMALIZA O ÁUDIO ORIGINAL PARA A DURAÇÃO DO VÍDEO
        # ==========================================================

        executar(
            [
                "ffmpeg",
                "-y",
                "-i", str(video),
                "-vn",
                "-af",
                (
                    "aresample=48000,"
                    "aformat=sample_fmts=s16:sample_rates=48000:"
                    "channel_layouts=stereo,"
                    "apad,"
                    f"atrim=duration={duracao_video},"
                    "asetpts=PTS-STARTPTS"
                ),
                "-t", str(duracao_video),
                "-ac", "2",
                "-ar", "48000",
                "-c:a", "pcm_s16le",
                str(audio_original),
            ]
        )

        # ==========================================================
        # 3. PREPARA A TRILHA PARA TODAS AS FOTOS
        # ==========================================================

        executar(
            [
                "ffmpeg",
                "-y",
                "-stream_loop", "-1",
                "-i", str(trilha_path),
                "-vn",
                "-af",
                (
                    "aresample=48000,"
                    "aformat=sample_fmts=s16:sample_rates=48000:"
                    "channel_layouts=stereo,"
                    f"atrim=duration={duracao_total_fotos},"
                    "asetpts=PTS-STARTPTS,"
                    f"afade=t=in:st=0:d=2," "afade=t=out:st={max(0, duracao_total_fotos - 1)}:d=1"
                ),
                "-t", str(duracao_total_fotos),
                "-ac", "2",
                "-ar", "48000",
                "-c:a", "pcm_s16le",
                str(audio_trilha),
            ]
        )

        # ==========================================================
        # 4. JUNTA ÁUDIO ORIGINAL + TRILHA
        # ==========================================================

        executar(
            [
                "ffmpeg",
                "-y",
                "-i", str(audio_original),
                "-i", str(audio_trilha),
                "-filter_complex",
                "[0:a][1:a]concat=n=2:v=0:a=1[outa]",
                "-map", "[outa]",
                "-ac", "2",
                "-ar", "48000",
                "-c:a", "pcm_s16le",
                str(audio_final),
            ]
        )

        # ==========================================================
        # 5. JUNTA VÍDEO + ÁUDIO FINAL
        # ==========================================================

        executar(
            [
                "ffmpeg",
                "-y",
                "-i", str(video_sem_audio),
                "-i", str(audio_final),
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "128k",
                "-t", str(duracao_total),
                "-movflags", "+faststart",
                str(saida),
            ]
        )

    print(f"✅ Vídeo final criado: {saida}")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(
            "Uso: python juntar_video_foto.py "
            "video.mp4 foto1.jpg [foto2.jpg ...] saida.mp4"
        )
        sys.exit(1)

    juntar_video_foto(
        sys.argv[1],
        sys.argv[2:-1],
        sys.argv[-1],
    )
