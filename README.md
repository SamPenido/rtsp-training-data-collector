# RTSP Frame Capture and Classification for AI Training

Este projeto contém ferramentas para conexão com streams de câmeras RTSP para capturar frames para visão computacional e treinamento de IA. Inclui uma utilidade de captura de frames e uma ferramenta de classificação manual para organizar conjuntos de dados para aprendizado de máquina.

## Sumário
- [Visão Geral](#visão-geral)
- [Funcionalidades](#funcionalidades)
- [Requisitos](#requisitos)
- [Configuração](#configuração)
- [Captura de Frames](#captura-de-frames)
  - [Execução](#execução)
- [Classificação de Frames](#classificação-de-frames)
  - [Funcionalidades de Classificação](#funcionalidades-de-classificação)
  - [Categorias e Subcategorias](#categorias-e-subcategorias)
  - [Uso](#uso)
  - [Fluxo de Classificação](#fluxo-de-classificação)
  - [Saída](#saída)
- [Licença](#licença)

## Visão Geral
Este projeto fornece ferramentas para construir conjuntos de dados de visão computacional a partir de streams de câmeras RTSP. Inclui:

1. **Coletor de Frames**: Um script que se conecta a um stream RTSP, captura frames em intervalos especificados e os salva como imagens JPEG.
2. **Classificador de Frames**: Uma ferramenta para organizar manualmente os frames capturados em categorias e subcategorias predefinidas, essencial para preparar dados de treinamento para modelos de IA.

## Funcionalidades
- **Intervalos de Captura Ajustáveis:** Modifique o tempo entre capturas de frames.
- **Qualidade JPEG Ajustável:** Configure a qualidade das imagens JPEG salvas.
- **Gerenciamento de Dados por Rodadas:** Organiza automaticamente rodadas de captura de dados com nomenclatura única para frames.
- **Classificação Manual com Subcategorias:** Interface intuitiva para categorizar frames e subcategorizar eventos em fases específicas (início, meio, fim).
- **Interface Gráfica Melhorada:** Interface sobreposta com melhor visibilidade, navegação avançada e feedback visual.
- **Persistência de Classificação:** Salva automaticamente classificações em formato JSON.
- **Reclassificação de Frames:** Suporte completo para correções de classificações anteriores.

## Requisitos
- Python 3.x
- [OpenCV](https://opencv.org/) (`cv2`)
- [python-dotenv](https://pypi.org/project/python-dotenv/)
- [NumPy](https://numpy.org/)
- [PIL/Pillow](https://pillow.readthedocs.io/en/stable/)

## Configuração
1. **Instalar Dependências:**
```bash
pip install opencv-python python-dotenv pillow numpy
```

2. **Criar Arquivo `.env`:**
```
CAMERA_USERNAME=usuario
CAMERA_PASSWORD=senha
CAMERA_IP=ip_camera
CAMERA_PORT=porta_camera
RTSP_STREAM_PATH=/stream_path
```

## Captura de Frames

### Execução
Execute o script usando:
```bash
python frame_collector.py
```

## Classificação de Frames

### Funcionalidades de Classificação
- **Categorias e Subcategorias:** Suporte para categorias principais e subcategorias que detalham fases dos eventos.
- **Interface Intuitiva:** Navegação por teclas, seleção rápida e feedback visual.
- **Persistência e Reclassificação:** Mantém histórico completo e permite correções rápidas.

### Categorias e Subcategorias
Categorias principais:
- **0: null** (sem evento)
- **1: forno_enchendo**
- **2: sinterizacao_acontecendo**
- **3: despejo_acontecendo**
- **4: panela_voltando_posicao_normal**
- **5: forno_vazio**

Subcategorias (fases dos eventos):
- **i: inicio**
- **m: meio**
- **f: fim**

### Uso
Edite o caminho do diretório de frames no script e execute:
```bash
python frame_classifier.py
```

### Fluxo de Classificação
- Navegue com teclas de seta.
- Selecione primeiro uma subcategoria (`I/M/F`) e depois uma categoria principal (`1-5`).
- Classifique como NULL com a tecla `0` (sem subcategoria).
- Pressione `H` para ajuda detalhada ou `S` para estatísticas.
- Saia pressionando `Q`.

### Saída
As classificações são armazenadas no arquivo:
- **`classifications.json`**: inclui categoria, subcategoria e metadados dos frames.

## Licença
Licença MIT

