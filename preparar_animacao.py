# -*- coding: utf-8 -*-
"""
Prepara uma animação para o catálogo do site.

Recebe a sequência PNG exportada do After Effects em 1080x1920 (ou qualquer
tamanho), corta todos os quadros pelo mesmo retângulo — a união do conteúdo
visível de todos eles, para o personagem não tremer — e grava em
animacoes/<id>/, já registrando a entrada no catalogo.json com a posição
original preservada.

    python preparar_animacao.py <pasta-de-origem> <id> "<Nome na lista>"

Exemplo:
    python preparar_animacao.py "C:\\render\\pipoca" pipoca "Pipoca (cachorro)"
"""

import json
import os
import sys

from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
CATALOGO = os.path.join(AQUI, "animacoes", "catalogo.json")
LIMIAR_ALFA = 8          # abaixo disso o pixel conta como vazio
MARGEM = 2               # folga em volta do recorte, em pixels


def quadros_de(pasta):
    nomes = sorted(
        n for n in os.listdir(pasta)
        if n.lower().endswith((".png", ".webp"))
    )
    if not nomes:
        raise SystemExit("Nenhum PNG encontrado em: " + pasta)
    return nomes


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
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    origem, ident, rotulo = sys.argv[1], sys.argv[2], sys.argv[3]
    if not os.path.isdir(origem):
        raise SystemExit("Pasta não encontrada: " + origem)

    nomes = quadros_de(origem)
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
            "x0": 90,
            "x1": tamanho[0] - 90,
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
    print("origem ......... %d quadros de %dx%d" % (len(nomes), tamanho[0], tamanho[1]))
    print("recorte ........ %dx%d em x=%d y=%d" % (larg, alt, caixa[0], caixa[1]))
    print("gravado em ..... animacoes/%s (%d KB)" % (ident, round(peso)))
    print("catalogo ....... '%s' registrado, y=%d" % (ident, centro_y))
    print("\nConfira no site e depois: git add -A && git commit && git push")


if __name__ == "__main__":
    main()
