# Barrinha Reels — site

Página única, sem servidor e sem instalação. Tudo roda no navegador da pessoa;
nenhum arquivo é enviado para lugar nenhum.

## Como a equipe usa

1. Abrir o link.
2. Escolher a animação na lista — já vem pronta, com posição e velocidade certas.
3. Digitar a duração do vídeo (`1:30` ou `90`).
4. `Gravar WebM com alpha` — o arquivo cai na pasta de downloads.

Quem quiser usar uma animação que não está na lista escolhe
**Enviar meus arquivos…** e arrasta a sequência PNG.

Os ajustes ficam salvos no navegador de cada pessoa.

## Publicar uma animação nova na lista

1. Exportar do After Effects: `Composição > Adicionar à fila de renderização` →
   formato **Sequência PNG** → canal **RGB + Alfa**. Só o ciclo de caminhada,
   não o vídeo inteiro — o site cuida da repetição e da duração.
2. Criar `animacoes/<nome-da-animacao>/` e jogar os PNGs lá.
3. Acrescentar um bloco em `animacoes/catalogo.json`:

```json
{
  "id": "pipoca",
  "nome": "Pipoca (cachorro)",
  "pasta": "animacoes/pipoca",
  "quadros": ["quadro_00.png", "quadro_01.png"],
  "padroes": { "fpsAnim": 12, "escala": 100, "x0": 90, "x1": 990, "y": 1700, "barraY": 1740 }
}
```

`padroes` é o que deixa a animação "pré-pronta": são os valores que o site
preenche sozinho quando alguém escolhe ela na lista.

4. Commit e push. O GitHub Pages republica em ~1 minuto.

O script aceita também o `.mov` direto (ProRes 4444 com alfa), sem precisar
exportar sequência PNG:

```bash
python preparar_animacao.py "Animacao Reels Baixo.mov" reels-baixo "Personagens"
```

Quadros idênticos em sequência são descartados — o site já repete os desenhos
na velocidade escolhida. Se uma pose precisa durar mais que as outras, passe
`--manter-repetidos`.

## Os dois botões

| Botão | O que sai | Quando usar |
|---|---|---|
| Gravar WebM com alpha | um `.webm` VP9 com transparência | uso normal — leve e rápido |
| Baixar sequência PNG (.zip) | um quadro PNG por frame | quando o editor não aceitar WebM |

A gravação do WebM acontece em tempo real: 30 s de vídeo levam 30 s.
**Não troque de aba durante a gravação** — o navegador desacelera páginas em
segundo plano e o arquivo sai com quadros repetidos. O site avisa se isso acontecer.

Sequência PNG pesa: ~1 MB por quadro, ou seja ~900 MB em 30 s a 30 fps.
Use só se for necessário.

## Hospedar de graça

O site é um arquivo só. Qualquer uma destas serve:

- **Netlify Drop** — `app.netlify.com/drop`, arraste a pasta `Barrinha Reels Web`,
  sai um link na hora. É o caminho mais curto.
- **Cloudflare Pages** — upload direto, mesma ideia.
- **GitHub Pages** — se o material já for versionado no GitHub.

Sem hospedar também funciona: mande a pasta pelo Drive/WhatsApp e a pessoa abre
o `index.html` com duplo clique.

## Navegador

Testado no Chrome (a gravação com alpha foi verificada lá). Edge deve se comportar
igual, por usar o mesmo motor. Em outros navegadores, se o WebM sair sem
transparência, use a sequência PNG.
