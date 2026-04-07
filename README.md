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

## Posso chamar de qualquer pasta do terminal?

Nao por padrao. Depois de instalar o comando global, sim.

```powershell
cd C:\Users\jairs\Codex\SplitVideo
.\install-user-command.ps1
```

Depois de abrir um novo terminal, voce pode chamar:

```powershell
splitvideo "C:\Videos\arquivo.mp4" "16:47,50%"
```

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

Opcoes uteis:

```powershell
splitvideo.cmd "C:\Videos\arquivo.mp4" "16:47,50%" --output-dir "C:\Saida"
splitvideo.cmd "C:\Videos\arquivo.mp4" "16:47,50%" --name-mode short
splitvideo.cmd "C:\Videos\arquivo.mp4" "16:47,50%" --verify --yes
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
- `--output-dir` para gravar em outra pasta
- `--name-mode short` para nomes mais curtos e seguros
- `--verify` para validar codec e duracao das saidas
- Log JSON automatico por execucao

Os pontos sao ordenados e deduplicados antes da execucao.

## Observacao tecnica

O corte usa `stream copy`, entao e rapido e nao recodifica. Em compensacao, a precisao pode depender dos `keyframes` do arquivo.
