#!/usr/bin/env python3
"""Atualiza o painel JeffersonOS com dados públicos reais da API do GitHub.

Uso local para gerar a arte inicial honesta: python scripts/update_dashboard.py --preview
Uso em GitHub Actions para obter métricas: python scripts/update_dashboard.py
Só usa Python stdlib. Nunca coleta contribuições privadas nem atribui a usuário
estatísticas fictícias. Gráfico de linguagens = bytes de código nos repos públicos.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape

USER = "kisleyj"
OUT = Path(__file__).resolve().parents[1] / "assets" / "dashboard-red.svg"
BASE = "https://api.github.com"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "jeffersonos-profile-dashboard",
    "X-GitHub-Api-Version": "2022-11-28",
}
if os.environ.get("GH_TOKEN"):
    HEADERS["Authorization"] = f"Bearer {os.environ['GH_TOKEN']}"

FEATURED_COUNT = 4  # seleção editorial no README, não métrica calculada


def api(path: str, params: dict | None = None):
    url = BASE + path + (("?" + urlencode(params)) if params else "")
    with urlopen(Request(url, headers=HEADERS), timeout=25) as response:
        return json.load(response)


def public_repos():
    repos = []
    for page in range(1, 11):
        batch = api(f"/users/{USER}/repos", {"type": "owner", "per_page": 100, "page": page})
        repos.extend(r for r in batch if not r.get("private") and
                     r.get("owner", {}).get("login", "").lower() == USER)
        if len(batch) < 100:
            return repos
    raise RuntimeError("Paginação atingiu o limite configurado: sem atualização parcial.")


def E(value):
    return escape(str(value), {'"': '&quot;', "'": '&apos;'})


def text(x, y, value, size=16, color="#f5e5e8", weight=400, extra=""):
    return (f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" '
            f'font-weight="{weight}" {extra}>{E(value)}</text>')


def metric_card(x, number, title, subtitle, color="#f26c80"):
    return "\n".join([
        f'<rect x="{x}" y="174" width="263" height="117" rx="16" fill="url(#glass)" stroke="#ab6571" stroke-opacity=".52"/>',
        f'<path d="M{x+17} 175H{x+246}" stroke="#f9bdc6" stroke-opacity=".18"/>',
        text(x+19, 204, title.upper(), 13, "#d0a5af", 600, 'letter-spacing=".6"'),
        text(x+18, 255, number, 38, color, 700),
        text(x+90, 252, subtitle, 13, "#c5a0a9") if subtitle else "",
    ])


def focus_card(x, title, subtitle, accent):
    return "\n".join([
        f'<rect x="{x}" y="355" width="263" height="87" rx="14" fill="url(#glass)" stroke="#ab6571" stroke-opacity=".4"/>',
        f'<rect x="{x+18}" y="374" width="5" height="45" rx="2.5" fill="{accent}"/>',
        text(x+36, 390, title, 19, "#fff0f1", 650),
        text(x+36, 416, subtitle, 14, "#c19da7"),
    ])


def clip(value, length=27):
    return value if len(value) <= length else value[:length-1] + "…"


def timestamp(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def worked_on(repo):
    """Repo com código e trabalho do dono.

    Entra repo próprio ou fork que recebeu push depois de criado. Fica de fora
    o repo do perfil, repo vazio (sem linguagem) e fork que nunca foi mexido.
    """
    if repo["name"].lower() == USER or not repo.get("language"):
        return False
    if not repo.get("fork"):
        return True
    created, pushed = repo.get("created_at"), repo.get("pushed_at")
    return bool(created and pushed and timestamp(pushed) > timestamp(created))


def render(repos, langs=None, ready=False):
    # São dados de repositórios, NÃO de contribuições do perfil ou experiência profissional.
    worked = [r for r in repos if worked_on(r)] if ready else []
    lang_count = str(len(langs)) if ready and langs else "—"
    code_count = str(len(worked)) if ready else "—"
    recent = sorted(worked, key=lambda r: r["pushed_at"], reverse=True)[:3]
    top = (langs or Counter()).most_common(5)

    svg = ["""<svg xmlns="http://www.w3.org/2000/svg" width="1160" height="720" viewBox="0 0 1160 720" role="img" aria-label="Painel glass JeffersonOS com estatísticas de repositórios públicos e linguagens de programação">
<defs>
  <linearGradient id="base" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#08090c"/><stop offset=".52" stop-color="#140a0e"/><stop offset="1" stop-color="#230d13"/></linearGradient>
  <linearGradient id="edge" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#f16a7c"/><stop offset=".48" stop-color="#c94e64"/><stop offset="1" stop-color="#74303c"/></linearGradient>
  <linearGradient id="glass" x1="0" y1="0" x2=".7" y2="1"><stop stop-color="#352126" stop-opacity=".79"/><stop offset=".54" stop-color="#26151b" stop-opacity=".65"/><stop offset="1" stop-color="#180d13" stop-opacity=".85"/></linearGradient>
  <linearGradient id="shine" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#ffe2e5" stop-opacity=".18"/><stop offset=".45" stop-color="#ffe2e5" stop-opacity=".025"/><stop offset="1" stop-color="#ffe2e5" stop-opacity="0"/></linearGradient>
  <linearGradient id="aurora" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#8b2838" stop-opacity=".04"/><stop offset=".65" stop-color="#a12c44" stop-opacity=".12"/><stop offset="1" stop-color="#5d1827" stop-opacity=".13"/></linearGradient>
  <filter id="blur"><feGaussianBlur stdDeviation="44"/></filter>
  <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0H0V32" fill="none" stroke="#da7c89" stroke-opacity=".04"/></pattern>
  <clipPath id="clip"><rect x="8" y="8" width="1144" height="704" rx="27"/></clipPath>
</defs>
<g font-family="Inter,Segoe UI,Arial,sans-serif">
<rect x="6" y="6" width="1148" height="708" rx="28" fill="url(#base)"/>
<g clip-path="url(#clip)">
  <circle cx="1090" cy="120" r="190" fill="#9d2641" opacity=".29" filter="url(#blur)"/>
  <circle cx="70" cy="620" r="200" fill="#731427" opacity=".25" filter="url(#blur)"/>
  <rect x="6" y="6" width="1148" height="708" fill="url(#aurora)"/>
  <rect x="6" y="6" width="1148" height="708" fill="url(#grid)"/>
  <path d="M470 6H855L455 712H150Z" fill="url(#shine)" opacity=".6"/>
  <path d="M0 543Q210 506 423 550T845 552T1180 519V727H0Z" fill="#11080d" opacity=".55"/>
</g>
<rect x="7" y="7" width="1146" height="706" rx="27" fill="none" stroke="url(#edge)" stroke-width="2.5" stroke-opacity=".87"/>
<path d="M32 8H440" stroke="#e17f90" stroke-opacity=".6" stroke-width="2"/>
<path d="M860 712H1131" stroke="#8d3344" stroke-opacity=".54" stroke-width="2"/>
<circle cx="38" cy="39" r="6" fill="#ff655e"/><circle cx="59" cy="39" r="6" fill="#ffd166"/><circle cx="80" cy="39" r="6" fill="#f16a7c"/>
"""]
    svg += [text(105, 45, "jefferson@github:~ / painel", 17, "#e8c7cd", 500),
            text(36, 101, "JeffersonOS", 35, "#fff2f3", 750),
            text(283, 101, "// atividade pública", 16, "#e0788b", 500),
            text(36, 134, "Tecnologia que funciona fora do tutorial.", 18, "#d0abb3"),
            text(1123, 101, "SUPORTE  /  INFRA  /  DEV", 13, "#be9099", 600, 'text-anchor="end"'),
            '<path d="M36 153H1124" stroke="#c37585" stroke-opacity=".27"/>',
            metric_card(36, str(len(repos)), "Repositórios públicos", "conta GitHub"),
            metric_card(317, code_count, "Projetos com código", "próprios e forks", "#f5a1aa"),
            metric_card(598, lang_count, "Linguagens", "nos projetos", "#dc7587"),
            metric_card(879, str(FEATURED_COUNT), "Projetos destacados", "seleção pessoal", "#ea7185"),
            text(36, 333, "›_  ONDE EU ATUO", 17, "#d9556a", 700),
            focus_card(36, "Suporte & sistemas", "Clipp · fiscal · diagnóstico", "#d9556a"),
            focus_card(317, "Infraestrutura", "Linux · Docker · redes", "#c94e64"),
            focus_card(598, "Desenvolvimento", "Web · mobile · automação", "#b8455c"),
            focus_card(879, "Homelab", "NAS · VPN · aprendizado", "#e3909d"),
            '<rect x="36" y="469" width="1087" height="199" rx="16" fill="url(#glass)" stroke="#ab6571" stroke-opacity=".48"/>',
            text(55, 503, "LINGUAGENS NOS REPOSITÓRIOS", 17, "#f9e5e9", 700),
            text(55, 525, "Distribuição por bytes de código públicos", 12, "#bd97a0"),
            '<path d="M586 487V650" stroke="#9b5e69" stroke-opacity=".45"/>',
            text(611, 503, "ÚLTIMOS PROJETOS ATUALIZADOS", 17, "#f9e5e9", 700),
            text(611, 525, "Ordenados pelo último push público", 12, "#bd97a0"),
            ]
    palette = ["#f06a88", "#cd445c", "#e391a0", "#a73b53", "#f4a3ae"]
    if top:
        max_b = max(v for _, v in top)
        total = sum(langs.values()) or 1
        for idx, (language, count) in enumerate(top):
            yy = 551 + idx * 24
            w = max(3, round(count / max_b * 225))
            svg += [text(56, yy+11, clip(language, 12), 14, "#f5e5e8"),
                    f'<rect x="196" y="{yy-1}" width="225" height="13" rx="5" fill="#27151c"/>',
                    f'<rect x="196" y="{yy-1}" width="{w}" height="13" rx="5" fill="{palette[idx]}"/>',
                    text(490, yy+11, f"{100*count/total:.1f}%".replace(".", ","), 14, "#e9c5cc", 500)]
    else:
        svg += [text(56, 564, "Aguardando a primeira execução do workflow.", 15, "#d4adb7"),
                text(56, 591, "Sem números de linguagens inventados.", 14, "#a87b86")]
    if recent:
        for idx, r in enumerate(recent):
            yy = 548 + idx*43
            svg += [f'<rect x="608" y="{yy-16}" width="486" height="35" rx="8" fill="#1d0e14" stroke="#995568" stroke-opacity=".54"/>',
                    text(622, yy+6, clip(r["name"], 29), 15, "#fceef0", 600),
                    text(1083, yy+6, r["pushed_at"][:10], 13, "#c39aa5", 400, 'text-anchor="end"')]
    else:
        svg += [text(614, 564, "Aguardando a primeira execução do workflow.", 15, "#d4adb7"),
                text(614, 591, "Projetos não são ordenados por dados fictícios.", 14, "#a87b86")]
    svg += ['<path d="M35 684H1125" stroke="#ba6978" stroke-opacity=".35"/>',
            text(38, 702, "Fonte: API pública do GitHub · sem contribuições privadas", 12, "#c39aa5"),
            text(1120, 702, "JEFFERSONOS  /  RED EDITION", 12, "#e16e82", 600, 'text-anchor="end"'),
            '</g></svg>']
    return "\n".join(svg) + "\n"


def main(preview=False):
    if preview:
        # Nomes/conteúdo público previamente conferidos no GitHub; outros dados ficam em espera.
        names = ["primeiro-app-android", "server-mine", "readme-template", "kisleyj",
                 "proffy-mobile", "app-fundamento-web", "dio-lab-open-source",
                 "avaliacao-app-mobile", "aprenda-kotlin-com-exemplos-lab"]
        repos = [{"name": name} for name in names]
        svg = render(repos, ready=False)
    else:
        repos = public_repos()
        if not repos:
            raise RuntimeError("Nenhum repositório público retornado; painel antigo preservado")
        langs = Counter()
        for repo in repos:
            if not worked_on(repo):
                continue
            bytes_by_lang = api(f"/repos/{USER}/{repo['name']}/languages")
            langs.update({name: int(value) for name, value in bytes_by_lang.items()})
        svg = render(repos, langs, ready=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if not OUT.exists() or OUT.read_text(encoding="utf-8") != svg:
        OUT.write_text(svg, encoding="utf-8")
        print(f"Painel gerado: {len(repos)} repositórios públicos; preview={preview}")
    else:
        print("Dados iguais: não é necessário criar outro commit.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true", help="Gera painel inicial sem métricas não confirmadas")
    args = parser.parse_args()
    try:
        main(args.preview)
    except Exception as exc:
        sys.exit(f"Falha na API/dados; SVG anterior preservado: {exc}")
