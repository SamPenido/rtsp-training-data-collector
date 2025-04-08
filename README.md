# RTSP Frame Capture and Classification for AI Training

Este projeto contém ferramentas para conexão com streams de câmeras RTSP para capturar frames para visão computacional e treinamento de IA. Inclui uma utilidade de captura de frames e uma ferramenta de classificação manual para organizar conjuntos de dados para aprendizado de máquina.

## Sumário
- [Visão Geral](#visão-geral)
- [Funcionalidades](#funcionalidades)
- [Requisitos](#requisitos)
- [Configuração](#configuração)
- [Captura de Frames](#captura-de-frames)
  - [Execução](#execução)
  - [Explicação do Código](#explicação-do-código)
    - [Variáveis de Ambiente e Conexão RTSP](#variáveis-de-ambiente-e-conexão-rtsp)
    - [Gerenciamento de Rodadas](#gerenciamento-de-rodadas)
    - [Captura e Salvamento de Frames](#captura-e-salvamento-de-frames)
    - [Registro de Metadados](#registro-de-metadados)
  - [Arquivo de Saída: `test_summary.log`](#arquivo-de-saída-test_summarylog)
  - [Personalização](#personalização)
- [Classificação de Frames](#classificação-de-frames)
  - [Funcionalidades de Classificação](#funcionalidades-de-classificação)
  - [Categorias](#categorias)
  - [Uso](#uso)
  - [Fluxo de Classificação](#fluxo-de-classificação)
  - [Saída](#saída)
- [Licença](#licença)

## Visão Geral
Este projeto fornece ferramentas para construir conjuntos de dados de visão computacional a partir de streams de câmeras RTSP. Inclui:

1. **Coletor de Frames**: Um script que se conecta a um stream RTSP, captura frames em intervalos especificados e os salva como imagens JPEG.
2. **Classificador de Frames**: Uma ferramenta para organizar manualmente os frames capturados em categorias predefinidas, essencial para preparar dados de treinamento para modelos de IA.

Ambas as ferramentas trabalham juntas para otimizar a criação de conjuntos de dados rotulados para tarefas de visão computacional.

## Funcionalidades
- **Intervalos de Captura Ajustáveis:** Modifique o tempo entre capturas de frames.
- **Qualidade JPEG Ajustável:** Configure a qualidade das imagens JPEG salvas.
- **Conexão Configurável:** Ajuste facilmente os parâmetros de conexão RTSP (nome de usuário, senha, IP, porta e caminho do stream) através de um arquivo de ambiente.
- **Gerenciamento de Dados por Rodadas:** Gerencia automaticamente rodadas de captura de dados com nomenclatura única para frames.
- **Registro de Metadados:** Logs detalhados da sessão são anexados ao `test_summary.log`.
- **Classificação Manual:** Interface intuitiva para categorizar frames em classes predefinidas.
- **Rastreamento de Classificação:** Salva dados de classificação em formato JSON.
- **Reclassificação:** Suporte para corrigir classificações anteriores com atualização automática de estatísticas.

## Requisitos
- Python 3.x
- [OpenCV](https://opencv.org/) (`cv2`)
- [python-dotenv](https://pypi.org/project/python-dotenv/)
- [NumPy](https://numpy.org/)
- [PIL/Pillow](https://pillow.readthedocs.io/en/stable/)
- Bibliotecas Python padrão: `os`, `re`, `time`, `shutil`, `datetime`, `json`, `sys`

## Configuração
1. **Instalar Dependências:**
   ```bash
   pip install opencv-python python-dotenv pillow numpy
   ```

2. **Criar um Arquivo .env:**
   Na raiz do projeto, crie um arquivo chamado `.env` com as seguintes variáveis:
   ```
   CAMERA_USERNAME=seu_usuario
   CAMERA_PASSWORD=sua_senha
   CAMERA_IP=ip_da_camera
   CAMERA_PORT=porta_da_camera
   RTSP_STREAM_PATH=/caminho/do/stream
   ```
   Atualize esses valores para corresponder às configurações da sua câmera.

## Captura de Frames

### Execução
Execute o script de captura usando:
```bash
python frame_collector.py
```

O script irá:
- Conectar-se ao stream RTSP.
- Capturar frames no intervalo configurado (padrão é um frame a cada 2 segundos).
- Salvar os frames no diretório `rtsp_test_frames`.
- Registrar metadados da sessão em `test_summary.log`.

### Explicação do Código

#### Variáveis de Ambiente e Conexão RTSP
- **Variáveis de Ambiente:**
  O script usa dotenv para carregar credenciais da câmera e parâmetros do stream do arquivo `.env`.
- **Construção de URL RTSP:**
  Ele constrói o URL RTSP e mascara informações sensíveis (por exemplo, a senha) nas saídas do console.

#### Gerenciamento de Rodadas
- **Determinação do ID da Rodada:**
  A função `get_next_round_id()` determina o próximo ID de rodada:
  - Lendo a rodada atual de `test_round_state.txt`.
  - Escaneando o diretório de imagens por rodadas existentes se o arquivo de estado estiver ausente ou contiver dados inválidos.
- **Atualização de Estado:**
  Após a sessão de captura, o ID da rodada atual é salvo de volta em `test_round_state.txt` para usos futuros.

#### Captura e Salvamento de Frames
- **Conexão ao Stream RTSP:**
  O script utiliza o `cv2.VideoCapture` do OpenCV para se conectar ao stream RTSP.
- **Loop de Captura:**
  Ele continuamente lê frames por uma duração configurada (padrão é 1440 minutos ou 24 horas). Frames são salvos apenas se o intervalo definido (padrão 2 segundos) tiver passado.
- **Salvamento de Frames:**
  Cada frame é salvo como uma imagem JPEG usando um formato de nome de arquivo:
  ```
  round_<round_id>_<frame_number>_<timestamp>.jpg
  ```
  A qualidade JPEG é ajustável através dos parâmetros do script.

#### Registro de Metadados
- **Cálculo de Estatísticas:**
  Após a captura, o script calcula o número total de frames salvos, tamanho total de armazenamento e tamanho médio por frame.
- **Arquivo de Log:**
  Metadados incluindo horários de início e fim, duração configurada versus duração real, intervalo de captura, qualidade JPEG e estatísticas de armazenamento são anexados ao `test_summary.log`.

### Arquivo de Saída: `test_summary.log`
O arquivo `test_summary.log` consolida metadados detalhados da sessão, incluindo:
- **Tempo da Sessão:** Horários de início e fim.
- **Duração:** Duração do teste configurada versus o tempo de execução real.
- **Parâmetros de Captura:** Intervalo de captura e qualidade JPEG.
- **Estatísticas:** Número de frames salvos, tamanho total de dados e tamanho médio por frame.

Este log é crítico para analisar o desempenho de cada sessão de captura e fazer ajustes para execuções futuras.

### Personalização
O script de captura permite modificar facilmente parâmetros-chave:
- **Intervalo de Captura:** Altere o tempo entre capturas de frames.
- **Qualidade JPEG:** Ajuste a configuração de qualidade para o salvamento de imagens JPEG.
- **Parâmetros de Conexão RTSP:** Atualize o arquivo `.env` para modificar detalhes de conexão.
- **Duração do Teste:** Defina o tempo total de execução da sessão de captura.

## Classificação de Frames

### Funcionalidades de Classificação
- **Interface de Usuário Intuitiva:** Interface visual para classificação eficiente de frames
- **Navegação por Teclado:** Teclas de seta para navegar pelos frames e teclas numéricas para classificação
- **Navegação em Lote:** Avance rapidamente 10, 100 ou 1000 frames
- **Persistência de Classificação:** O progresso é automaticamente salvo em um arquivo JSON
- **Feedback Visual:** O display de status mostra o progresso da classificação e estatísticas
- **Carregamento Robusto de Imagens:** Usa PIL para melhor manipulação de caminhos de arquivo e formatos de imagem
- **Reclassificação:** Suporte para corrigir classificações anteriores com atualização automática de estatísticas

### Categorias
O classificador suporta as seguintes categorias predefinidas:
1. **forno_enchendo**: Fase de enchimento do forno
2. **sinterizacao_acontecendo**: Processo de sinterização em andamento
3. **despejo_acontecendo**: Descarga/despejo em progresso
4. **panela_voltando_posicao_normal**: Panela retornando à posição normal
5. **forno_vazio**: Forno vazio

### Uso
Execute a ferramenta de classificação usando:
```bash
python frame_classifier.py
```

Antes de executar, atualize a variável `frames_directory` no script para apontar para o diretório contendo seus frames capturados (padrão é o diretório `rtsp_test_frames`).

### Fluxo de Classificação
1. **Navegação:** Use as teclas de seta para navegar pelos frames
   - Setas Esquerda/Direita: Navegue um frame por vez
   - Tecla 7: Avance 10 frames
   - Tecla 8: Avance 100 frames
   - Tecla 9: Avance 1000 frames
2. **Classificação:** Pressione as teclas 1-5 para classificar frames em suas respectivas categorias
3. **Reclassificação:** Para corrigir uma classificação, basta pressionar uma tecla diferente (1-5) no mesmo frame
4. **Saída:** Pressione 'Q' para salvar e sair

A interface mostra:
- Número do frame atual e status de navegação
- Status de classificação do frame atual
- Categorias disponíveis com suas contagens atuais
- Controles de navegação

### Saída
O classificador produz um arquivo JSON:
- **`classifications.json`**: Um arquivo JSON contendo metadados para todos os frames classificados

O arquivo JSON inclui informações detalhadas para cada frame classificado:
- ID e nome da categoria
- Caminho original do arquivo
- Metadados do frame (ID da rodada, número do frame, timestamp)
- Timestamp da classificação

## Licença
Licença MIT
