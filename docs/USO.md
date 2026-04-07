# Uso

## Objetivo

`SplitVideo` divide um video em duas ou mais partes sem recodificar. O app usa `ffprobe` para medir a duracao e `ffmpeg` com `-c copy` para preservar os streams originais.

## Modos de entrada

### 1. Arquivo direto

```powershell
.\splitvideo.cmd "C:\Videos\arquivo.mp4" "16:47,50%"
```

### 2. Pasta de trabalho

```powershell
.\splitvideo.cmd "C:\Videos"
```

O app lista os videos encontrados e pede a selecao.

### 3. Diretorio atual

```powershell
.\splitvideo.cmd
```

Se nenhum caminho for passado, a busca e feita no diretorio atual.

## Formatos de corte

- Tempo absoluto em segundos: `70`
- Minutos e segundos: `16:47`
- Horas, minutos e segundos: `01:16:47`
- Percentual: `50%`
- Multiplos cortes: `5:00, 16:47, 50%`

## Regras

- Os pontos sao ordenados antes da execucao.
- Pontos repetidos sao removidos.
- O valor precisa estar dentro da duracao do video.
- Percentuais usam a duracao real retornada por `ffprobe`.

## Exemplo de saida

Se o video `aula.mp4` for dividido em `10:00` e `50%`, o app gera arquivos no mesmo diretorio do original com nomes no padrao:

- `aula_001_00-00-00-00-10-00.mp4`
- `aula_002_00-10-00-00-42-30_500.mp4`
- `aula_003_00-42-30_500-01-25-01.mp4`

## Observacao tecnica

Como o corte usa `stream copy`, a divisao pode nao cair exatamente no frame solicitado. O resultado final depende de `keyframes` do arquivo de origem.
