# SplitVideo

CLI para dividir um video em duas ou mais partes sem recodificar, preservando audio e video com `-c copy`.

Licenca: MIT

## Requisitos

- Windows com `python`
- `ffmpeg.exe`
- `ffprobe.exe`

O script procura `ffmpeg` e `ffprobe` nesta ordem:

1. `--ffmpeg` e `--ffprobe`
2. variaveis de ambiente `FFMPEG` e `FFPROBE`
3. `PATH`
4. a propria pasta do projeto
5. `tools\ffmpeg.exe` e `tools\ffprobe.exe`

## Uso

Sem parametro, usa a pasta atual:

```powershell
splitvideo.cmd
```

Com pasta:

```powershell
splitvideo.cmd "C:\Videos"
```

Com arquivo:

```powershell
splitvideo.cmd "C:\Videos\arquivo.mp4"
```

Tambem aceita cortes direto na linha de comando:

```powershell
splitvideo.cmd "C:\Videos\arquivo.mp4" 16:47 50%
splitvideo.cmd "C:\Videos" "5:00, 16:47, 50%"
```

## Executavel

Para gerar o `.exe`:

```powershell
cd C:\Users\jairs\Codex\SplitVideo
.\build.ps1 -Clean
```

Saida esperada:

- `dist\SplitVideo\SplitVideo.exe`
- `dist\SplitVideo\tools\ffmpeg.exe`
- `dist\SplitVideo\tools\ffprobe.exe`

Exemplo:

```powershell
.\dist\SplitVideo\SplitVideo.exe "C:\Videos\arquivo.mp4" "16:47,50%"
```

## Documentacao

- [Uso](docs/USO.md)
- [Arquitetura](docs/ARQUITETURA.md)
- [Publicacao](docs/PUBLICACAO.md)
- [Roadmap](ROADMAP.md)

## Regras de corte

- Tempo absoluto: `16:47`, `01:16:47`, `70`
- Percentual: `50%`
- Multiplos cortes: `5:00, 16:47, 50%`

Os pontos sao ordenados e deduplicados antes da execucao.

## Observacao tecnica

O corte usa `stream copy`, entao e rapido e nao recodifica. Em compensacao, a precisao pode depender dos `keyframes` do arquivo.
