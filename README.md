# Jogos do Palmeiras para a TV

Lista dos próximos jogos do Palmeiras, com data, hora e onde assistir. A tela inicial da TV
(launcher `com.gathin.tvhome`) lê o [`jogos.json`](jogos.json) para mostrar o bloco "Próximo jogo".
Perto do horário, o bloco vira um botão que abre a transmissão.

- **Fonte:** agenda do Palmeiras no ge.globo. Quando o ge ainda não tem o horário, a ESPN completa.
- **Atualização:** o GitHub Actions roda o [`gerar_jogos.py`](gerar_jogos.py) às 06h17, 12h17 e 18h17
  (horário de Brasília). Para atualizar na hora: aba **Actions** → **Atualizar jogos** → **Run workflow**.
- **Se o site do ge mudar:** o script falha sem apagar a lista, e a TV continua com a última que recebeu.
  Se a lista ficar 10 dias sem atualizar, a TV esconde o bloco.
- **Correção à mão:** é só editar o `jogos.json` aqui no GitHub. A próxima execução do job sobrescreve a edição.

Os canais só valem para os apps que a TV aceita abrir: Globoplay (Globo, SporTV e Premiere),
Prime Video, Paramount+ e YouTube (ge tv).
