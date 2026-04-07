# Publicacao

## Repositorio

Este projeto foi preparado para publicacao publica no GitHub com licenca MIT.

## Estrategia adotada

- versionar apenas codigo-fonte e documentacao
- ignorar `build` e `dist`
- ignorar `tools`, porque os binarios de `ffmpeg` e `ffprobe` podem ser restaurados localmente

## Build local

```powershell
cd C:\Users\jairs\Codex\SplitVideo
.\build.ps1 -Clean
```

## Resultado esperado

- `dist\SplitVideo\SplitVideo.exe`

## Passos recomendados para release futura

1. Gerar o build local.
2. Validar o `.exe` com um arquivo real.
3. Criar uma release no GitHub.
4. Anexar o zip da pasta `dist\SplitVideo`.
