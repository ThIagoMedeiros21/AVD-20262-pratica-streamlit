# Justificativa das métricas — Dashboard 2

**Dataset:** Electric Vehicle Charging Dataset (sintético), amostra de 100 mil sessões de recarga.

**Público-alvo comum às métricas:** gestor(a) de uma rede de estações de recarga, que não precisa ler histogramas nem boxplots, mas decide horário de equipe, tarifas e investimento em carregadores.

**Widgets que controlam o dashboard:**
- **Período do dia** (`st.pills`, múltipla escolha: Madrugada, Manhã, Tarde, Noite): filtra todas as métricas e gráficos.
- **Crossfilter no gráfico de sessões por hora:** arrastar uma faixa de horário recalcula as métricas e o gráfico de energia para as sessões daquele intervalo.

Os números citados abaixo são da amostra completa, sem filtro.

## Métrica 1: Volume de sessões e energia entregue
- **Variável:** contagem de sessões (linhas) e `energia_kwh` (energia entregue por sessão, kWh)
- **O que mede:** quantas sessões caem no filtro e quanta energia elas entregaram no total (em MWh), com a fatia que isso representa do total da amostra (ex.: a tarde concentra 54,9% das sessões).
- **Por que foi escolhida:** métricas de **contagem** e **soma** são a base da Teoria de Métricas Básicas: respondem "quanto?" antes de qualquer outra pergunta. A EDA mostrou uma demanda muito desigual ao longo do dia (pico às 16h, só 1,6% das sessões de manhã), e a fatia do total deixa isso visível em um número.
- **Público-alvo:** gestor(a) da rede de recarga.
- **Qual decisão pode ser apoiada por essa métrica?** Em quais períodos reforçar a equipe e a manutenção, e quando a rede fica ociosa (por exemplo, para tarifas mais baratas de manhã e atrair demanda).
- **O que comunica ao público-alvo:** o tamanho da operação no recorte escolhido: "a tarde responde por mais da metade das recargas e da energia entregue".

## Métrica 2: Distribuição da energia em relação à mediana
- **Variável:** `energia_kwh` (energia entregue por sessão, kWh)
- **O que mede:** a proporção de sessões **abaixo**, **em torno** e **acima** da mediana de energia, junto da média, da mediana, do mínimo, do máximo e do desvio padrão no recorte. "Em torno" = dentro de ±10% da mediana. A mediana de referência é fixa, a da amostra completa (9,21 kWh), para que os recortes sejam comparáveis entre si.
- **Por que foi escolhida:** a EDA mostrou que `energia_kwh` é assimétrica (skew 1,28, não normal pelo Shapiro-Wilk). Por isso a **mediana** é uma medida de tendência central mais confiável que a média, e a divisão em três faixas resume a distribuição sem exigir a leitura de um histograma.
- **Público-alvo:** gestor(a) da rede de recarga.
- **Qual decisão pode ser apoiada por essa métrica?** Se um período tem mais sessões "acima da mediana", ele é o que mais pesa no consumo de energia e no contrato com a distribuidora. Isso ajuda a planejar a potência contratada e os preços por kWh.
- **O que comunica ao público-alvo:** um resumo direto: "metade das recargas entrega mais de 9,2 kWh". No recorte filtrado, mostra se as sessões daquele período são maiores ou menores que o normal da rede.

## Métrica 3: Sessões longas (mais de 8 horas)
- **Variável:** `duracao_carga_h` (duração da sessão, em horas) e `energia_kwh`
- **O que mede:** a porcentagem de sessões com duração acima de 8 h, a fatia das **horas de vaga ocupada** que essas sessões consomem e a fatia da **energia** que elas entregam.
- **Por que foi escolhida:** é uma métrica de **proporção** que expõe um desequilíbrio que a média esconde. Na amostra, as sessões longas são só 11,9% do total, mas ocupam 33,3% das horas de vaga e entregam apenas 17,5% da energia. Ou seja, são carros que ficam parados no carregador muito depois de terem carregado o suficiente. A EDA já indicava isso: `duracao_carga_h` é a variável mais assimétrica (skew 2,18), com cauda longa, e os outliers foram mantidos por serem plausíveis.
- **Público-alvo:** gestor(a) da rede de recarga.
- **Qual decisão pode ser apoiada por essa métrica?** Criar uma tarifa de ociosidade (cobrança por tempo parado após a carga) ou um limite de tempo, liberando vagas para mais usuários sem precisar instalar novos carregadores.
- **O que comunica ao público-alvo:** "uma em cada oito recargas prende a vaga por mais de 8 h e ocupa um terço do tempo dos carregadores, entregando pouca energia por isso".
