# Arquitetura

## Resumo

O projeto foi mantido como uma CLI simples em Python para reduzir atrito operacional no Windows e permitir empacotamento rapido com `PyInstaller`.

## Componentes

### `splitvideo.py`

Arquivo principal do projeto. Responsavel por:

- interpretar argumentos da linha de comando
- localizar `ffmpeg` e `ffprobe`
- selecionar video por arquivo, pasta ou diretorio atual
- converter tempos absolutos e percentuais
- montar segmentos
- executar os cortes
- gerar log JSON por execucao
- verificar saidas com `ffprobe` quando solicitado

## Fluxo interno

1. Resolver binarios externos.
2. Resolver o alvo de trabalho.
3. Detectar a duracao com `ffprobe`.
4. Normalizar os pontos de corte.
5. Gerar a lista de segmentos.
6. Executar `ffmpeg` para cada segmento com `-c copy`.
7. Verificar as saidas quando `--verify` estiver ativo.
8. Gravar um log estruturado na pasta de saida.

## Dependencias

### Runtime

- Python 3.14 ou compativel
- `ffmpeg`
- `ffprobe`

### Build

- `PyInstaller`

## Empacotamento

O build gera um diretorio `dist\SplitVideo` com:

- `SplitVideo.exe`
- pasta `tools` com os binarios auxiliares

O codigo usa `app_root()` para localizar os executaveis corretamente tanto no modo fonte quanto no modo empacotado.
