#!/usr/bin/env python3
"""Gera jogos.json com os próximos jogos do Palmeiras e onde assistir, para o bloco da tela inicial da TV.

Fonte principal: a agenda do Palmeiras no ge.globo (traz data, hora, campeonato e canais de cada jogo).
Horário que o ge ainda não publicou é completado pela ESPN, quando ela já tiver.
Só biblioteca padrão do Python. Uso: python3 -I gerar_jogos.py [saida.json]
"""
import json
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

GE_AGENDA = "https://ge.globo.com/futebol/times/palmeiras/agenda-de-jogos-do-palmeiras/"
ESPN = "https://site.api.espn.com/apis/site/v2/sports/soccer/{liga}/teams/2029/schedule?fixture=true"
ESPN_LIGAS = ["bra.1", "bra.copa_do_brazil", "conmebol.libertadores", "bra.camp.paulista"]
BRT = timezone(timedelta(hours=-3))  # Brasília, sem horário de verão desde 2019
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"

GLOBOPLAY = "com.globo.globotv"
# Canal do ge -> (nome na tela, app, tipo de vídeo do ge com o link ao vivo no Globoplay). Ordem = preferência.
# Só entram serviços que os avós assinam; os outros (Disney+, Cartola...) ficam de fora.
CANAIS = {
    "globo": ("Globo", GLOBOPLAY, "tvg"),
    "globoplay": ("Globo", GLOBOPLAY, "tvg"),
    "sportv": ("SporTV", GLOBOPLAY, "sportv"),
    "premiere": ("Premiere", GLOBOPLAY, "premiere"),
    "prime vídeo": ("Prime Video", "com.amazon.amazonvideo.livingroom", None),
    "prime video": ("Prime Video", "com.amazon.amazonvideo.livingroom", None),
    "paramount+": ("Paramount+", "com.cbs.ca", None),
    "ge tv": ("ge tv (YouTube)", "com.google.android.youtube.tv", None),
}
ORDEM = ["Globo", "SporTV", "Premiere", "Prime Video", "Paramount+", "ge tv (YouTube)"]


def baixar(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def agenda_ge():
    html = baixar(GE_AGENDA)
    i = html.find('"teamAgenda":')
    if i < 0:
        raise RuntimeError("ge: agenda não encontrada na página (o site mudou?)")
    agenda, _ = json.JSONDecoder().raw_decode(html, i + len('"teamAgenda":'))
    return agenda.get("future") or []


def horarios_espn():
    """{(data BRT, adversário em minúsculas): datetime} para completar horários que faltam no ge."""
    achados = {}
    for liga in ESPN_LIGAS:
        try:
            d = json.loads(baixar(ESPN.format(liga=liga)))
        except Exception as e:  # a ESPN é só complemento: sem ela, o jogo fica "horário a definir"
            print(f"aviso: ESPN {liga}: {e}", file=sys.stderr)
            continue
        for ev in d.get("events", []):
            quando = datetime.fromisoformat(ev["date"].replace("Z", "+00:00")).astimezone(BRT)
            for t in ev["competitions"][0]["competitors"]:
                nome = t["team"]["displayName"].lower()
                if "palmeiras" not in nome:
                    achados[(quando.date().isoformat(), nome)] = quando
    return achados


def mesmo_time(ge, espn):
    a, b = ge.lower(), espn.lower()
    return a in b or b in a


def montar():
    espn = None
    jogos = []
    for ev in agenda_ge():
        m = ev.get("match") or {}
        casa = (m.get("firstContestant") or {}).get("popularName")
        fora = (m.get("secondContestant") or {}).get("popularName")
        data = m.get("startDate")
        if not (casa and fora and data and re.fullmatch(r"\d{4}-\d{2}-\d{2}", data)):
            continue
        adversario = fora if casa == "Palmeiras" else casa

        inicio = None
        if m.get("startHour"):
            inicio = datetime.fromisoformat(f"{data}T{m['startHour']}").replace(tzinfo=BRT)
        else:
            if espn is None:
                espn = horarios_espn()
            for (dia, nome), quando in espn.items():
                if dia == data and mesmo_time(adversario, nome):
                    inicio = quando
                    break

        videos = {}
        for gv in ((m.get("transmission") or {}).get("gameVideos") or []):
            vid = (gv.get("video") or {}).get("id")
            if isinstance(vid, int):
                videos[gv.get("mediaType")] = vid
        canais = {}
        for fonte in m.get("liveWatchSources") or []:
            info = CANAIS.get((fonte.get("name") or "").strip().lower())
            if not info or info[0] in canais:
                continue
            nome, app, tipo = info
            canal = {"nome": nome, "app": app}
            if tipo and tipo in videos:
                canal["link"] = f"https://globoplay.globo.com/v/{videos[tipo]}/"
            canais[nome] = canal

        fase = m.get("phase") or {}
        camp = ((fase.get("championshipEdition") or {}).get("championship") or {}).get("name")
        jogos.append({
            "data": data,
            "inicio": inicio.isoformat() if inicio else None,
            "mandante": casa,
            "visitante": fora,
            "campeonato": camp,
            "fase": fase.get("name"),
            "estadio": (m.get("location") or {}).get("popularName"),
            "canais": [canais[n] for n in ORDEM if n in canais],
        })
    jogos.sort(key=lambda j: j["inicio"] or j["data"] + "T23:59")
    return jogos


def main():
    saida = sys.argv[1] if len(sys.argv) > 1 else "jogos.json"
    jogos = montar()
    if not jogos:
        # Melhor manter o arquivo anterior do que publicar uma lista vazia por causa de uma falha do site
        raise SystemExit("nenhum jogo encontrado; jogos.json não foi alterado")
    doc = {"time": "Palmeiras", "gerado": datetime.now(BRT).isoformat(timespec="seconds"), "jogos": jogos}
    with open(saida, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    print(f"{len(jogos)} jogos -> {saida}")


if __name__ == "__main__":
    main()
