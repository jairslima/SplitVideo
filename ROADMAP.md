# Roadmap

## Melhorias sugeridas

### Interface grafica

Uma GUI simples com selecao de arquivo, lista de cortes e barra de progresso reduziria o atrito para uso recorrente.

### Drag and drop

Aceitar arrastar um arquivo para o `.exe` ou para a janela da futura GUI melhoraria o fluxo no Windows.

### Perfil de nomes

Adicionar opcoes para controlar o nome das saidas, como sufixos curtos, prefixos numericos ou subpasta de destino.

### Log persistente

Gravar um log por execucao com entrada, duracao, cortes calculados e comandos executados facilitaria auditoria.

### Validacao por streams

Adicionar verificacao opcional pos-corte com `ffprobe` para confirmar codecs, duracao e streams presentes em cada parte.

### Corte mais preciso

Oferecer um modo opcional com recodificacao parcial ou total para quem quiser mais precisao de frame.
