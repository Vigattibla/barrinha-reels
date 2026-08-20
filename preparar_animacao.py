# -*- coding: utf-8 -*-
"""
Prepara uma animação para o catálogo do site.

Aceita uma pasta com a sequência PNG OU um arquivo de vídeo com alpha
(ProRes 4444 .mov, WebM). Corta todos os quadros pelo mesmo retângulo — a
união do conteúdo visível de todos eles, para o personagem não tremer — e
grava em animacoes/<id>/, registrando a entrada no catalogo.json com a
posição original preservada.

    python preparar_animacao.py <origem> <id> "<Nome na lista>" [--manter-repetidos]

Exemplos:
    python preparar_animacao.py "C:\\render\\pipoca" pipoca "Pipoca (cachorro)"
    python preparar_animacao.py "Animacao Reels Baixo.mov" reels-baixo "Personagens"

Quadros idênticos em sequência são descartados por padrão: o site repete os
desenhos na velocidade escolhida, então repetição no arquivo só duplicaria
pose. Use --manter-repetidos se a repetição for intencional (uma pose que
deve durar mais que as outras).
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
CATALOGO = os.path.join(AQUI, "animacoes", "catalogo.json")
LIMIAR_ALFA = 8          # abaixo disso o pixel conta como vazio
MARGEM = 2               # folga em volta do recorte, em pixels
VIDEOS = (".mov", ".webm", ".mkv", ".avi", ".mp4")


def extrair_video(caminho, destino):
    """Quebra um vídeo com alpha em PNGs. Precisa do ffmpeg no PATH."""
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg não encontrado no PATH — necessário para ler vídeo.")
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-i", caminho, "-pix_fmt", "rgba", os.path.join(destino, "f_%03d.png")]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit("ffmpeg falhou:\n" + (r.stderr or "").strip()[-800:])


def quadros_de(pasta):
    nomes = sorted(
        n for n in os.listdir(pasta)
        if n.lower().endswith((".png", ".webp"))
    )
    if not nomes:
        raise SystemExit("Nenhum PNG encontrado em: " + pasta)
    return nomes


def sem_repetidos(pasta, nomes):
    """Remove quadros idênticos ao anterior. Devolve (lista, quantos caíram)."""
    ficam, anterior, caidos = [], None, 0
    for nome in nomes:
        with Image.open(os.path.join(pasta, nome)) as im:
            marca = hashlib.md5(im.convert("RGBA").tobytes()).hexdigest()
        if marca == anterior:
            caidos += 1
            continue
        anterior = marca
        ficam.append(nome)
    # um ciclo costuma fechar repetindo o primeiro desenho no fim
    if len(ficam) > 1:
        with Image.open(os.path.join(pasta, ficam[0])) as a, \
             Image.open(os.path.join(pasta, ficam[-1])) as b:
            if a.convert("RGBA").tobytes() == b.convert("RGBA").tobytes():
                ficam.pop()
                caidos += 1
    return ficam, caidos


def caixa_uniao(pasta, nomes):
    """Retângulo que cobre o conteúdo visível de todos os quadros."""
    caixa = None
    tamanho = None
    for nome in nomes:
        with Image.open(os.path.join(pasta, nome)) as im:
            im = im.convert("RGBA")
            if tamanho is None:
                tamanho = im.size
            elif im.size != tamanho:
                raise SystemExit(
                    "Quadros com tamanhos diferentes: %s tem %s, esperado %s"
                    % (nome, im.size, tamanho)
                )
            atual = im.getchannel("A").point(lambda v: 255 if v >= LIMIAR_ALFA else 0).getbbox()
        if atual is None:
            continue
        caixa = atual if caixa is None else (
            min(caixa[0], atual[0]), min(caixa[1], atual[1]),
            max(caixa[2], atual[2]), max(caixa[3], atual[3]),
        )
    if caixa is None:
        raise SystemExit("Todos os quadros estão vazios (só alfa zero).")

    x0 = max(0, caixa[0] - MARGEM)
    y0 = max(0, caixa[1] - MARGEM)
    x1 = min(tamanho[0], caixa[2] + MARGEM)
    y1 = min(tamanho[1], caixa[3] + MARGEM)
    return (x0, y0, x1, y1), tamanho


def main():
    argumentos = [a for a in sys.argv[1:] if not a.startswith("--")]
    opcoes = {a for a in sys.argv[1:] if a.startswith("--")}
    if len(argumentos) < 3:
        raise SystemExit(__doc__)
    origem, ident, rotulo = argumentos[0], argumentos[1], argumentos[2]

    temporaria = None
    if os.path.isfile(origem) and origem.lower().endswith(VIDEOS):
        temporaria = tempfile.mkdtemp(prefix="barrinha_")
        extrair_video(origem, temporaria)
        pasta = temporaria
    elif os.path.isdir(origem):
        pasta = origem
    else:
        raise SystemExit("Não encontrei (nem pasta, nem vídeo): " + origem)

    try:
        preparar(pasta, ident, rotulo, "--manter-repetidos" in opcoes)
    finally:
        if temporaria:
            shutil.rmtree(temporaria, ignore_errors=True)


def preparar(origem, ident, rotulo, manter_repetidos):
    nomes = quadros_de(origem)
    brutos = len(nomes)
    caidos = 0
    if not manter_repetidos:
        nomes, caidos = sem_repetidos(origem, nomes)
    caixa, tamanho = caixa_uniao(origem, nomes)
    larg, alt = caixa[2] - caixa[0], caixa[3] - caixa[1]

    destino = os.path.join(AQUI, "animacoes", ident)
    os.makedirs(destino, exist_ok=True)

    saidas = []
    for i, nome in enumerate(nomes):
        with Image.open(os.path.join(origem, nome)) as im:
            recorte = im.convert("RGBA").crop(caixa)
        saida = "quadro_%02d.png" % i
        recorte.save(os.path.join(destino, saida), optimize=True)
        saidas.append(saida)

    # centro do recorte dentro da composição original: mantém o personagem
    # na mesma altura em que foi animado.
    centro_y = round((caixa[1] + caixa[3]) / 2)
    # as pontas do trajeto recuam meia largura do desenho, senão o personagem
    # nasce e termina cortado pela borda da tela.
    margem_x = max(90, round(larg / 2))

    with open(CATALOGO, "r", encoding="utf-8") as f:
        catalogo = json.load(f)

    entrada = {
        "id": ident,
        "nome": rotulo,
        "pasta": "animacoes/" + ident,
        "quadros": saidas,
        "padroes": {
            "fpsAnim": 12,
            "escala": 100,
            "larg": tamanho[0],
            "alt": tamanho[1],
            "x0": margem_x,
            "x1": tamanho[0] - margem_x,
            "y": centro_y,
            "barraY": min(tamanho[1] - 1, centro_y + round(alt / 2) + 10),
        },
    }

    animacoes = [a for a in catalogo.get("animacoes", []) if a.get("id") != ident]
    animacoes.append(entrada)
    catalogo["animacoes"] = animacoes

    with open(CATALOGO, "w", encoding="utf-8") as f:
        json.dump(catalogo, f, indent=2, ensure_ascii=False)
        f.write("\n")

    peso = sum(os.path.getsize(os.path.join(destino, s)) for s in saidas) / 1024
    print("origem ......... %d quadros de %dx%d" % (brutos, tamanho[0], tamanho[1]))
    if caidos:
        print("repetidos ...... %d quadro(s) idêntico(s) descartado(s)" % caidos)
    print("desenhos ....... %d únicos no ciclo" % len(saidas))
    print("recorte ........ %dx%d em x=%d y=%d" % (larg, alt, caixa[0], caixa[1]))
    print("gravado em ..... animacoes/%s (%d KB)" % (ident, round(peso)))
    print("catalogo ....... '%s' registrado, y=%d" % (ident, centro_y))
    if len(saidas) < 6:
        print("\nATENÇÃO: só %d desenhos no ciclo. Se a caminhada tem mais poses,"
              "\na exportação pegou um trecho curto — confira a área de trabalho no AE."
              % len(saidas))
    print("\nConfira no site e depois: git add -A && git commit && git push")


if __name__ == "__main__":
    main()
