"""
funcoes.py
Funções para transcrição de vídeo e geração de legendas SRT usando OpenAI Whisper.

Instalação:
    pip install openai-whisper
    sudo apt install ffmpeg   # Ubuntu/Debian
    brew install ffmpeg       # macOS
    # Windows: https://ffmpeg.org/download.html  (adicione o ffmpeg ao PATH)
"""

import os
import re
import shutil
import textwrap
from pathlib import Path
from dataclasses import dataclass, field


# ──────────────────────────────────────────────────────────────────────────────
# Configuração de formatação de legenda
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ConfigLegenda:
    """
    Todos os parâmetros de formatação e tempo da legenda.

    Parâmetros de TEMPO:
        duracao_minima:   Duração mínima de um bloco em segundos (evita flashes).
        duracao_maxima:   Duração máxima de um bloco em segundos (quebra segmentos longos).
        gap_entre_blocos: Silêncio mínimo (s) inserido entre blocos consecutivos.

    Parâmetros de TEXTO:
        max_chars_por_linha: Máximo de caracteres por linha de texto.
        max_linhas:          Máximo de linhas por bloco (frame). Geralmente 1 ou 2.
        uppercase:           Se True, converte todo o texto para maiúsculas.
        remover_pontuacao:   Se True, remove pontuação final (útil para legendas minimalistas).
    """
    # ── Tempo ─────────────────────────────────────────────────────────────────
    duracao_minima:   float = 1.0    # segundos
    duracao_maxima:   float = 7.0    # segundos
    gap_entre_blocos: float = 0.05   # segundos

    # ── Texto ─────────────────────────────────────────────────────────────────
    max_chars_por_linha: int  = 42   # padrão broadcast: 42 chars
    max_linhas:          int  = 2    # máximo de linhas por frame
    uppercase:           bool = False
    remover_pontuacao:   bool = False


# Perfis prontos para uso rápido
PERFIS = {
    "padrao":     ConfigLegenda(),
    "cinema":     ConfigLegenda(max_chars_por_linha=36, max_linhas=2, duracao_minima=1.5, duracao_maxima=6.0),
    "redes":      ConfigLegenda(max_chars_por_linha=28, max_linhas=1, duracao_maxima=4.0, uppercase=True),
    "broadcast":  ConfigLegenda(max_chars_por_linha=42, max_linhas=2, duracao_minima=1.0, duracao_maxima=8.0),
    "acessivel":  ConfigLegenda(max_chars_por_linha=37, max_linhas=2, duracao_minima=2.0, duracao_maxima=6.0),
}


# ──────────────────────────────────────────────────────────────────────────────
# Detecção de dispositivo (GPU / CPU)
# ──────────────────────────────────────────────────────────────────────────────

def detectar_device() -> str:
    """Retorna 'cuda' se GPU NVIDIA disponível, caso contrário 'cpu'."""
    import torch
    if torch.cuda.is_available():
        nome = torch.cuda.get_device_name(0)
        vram = torch.cuda.get_device_properties(0).total_memory / 1024 ** 3
        print(f"🚀 GPU detectada : {nome} ({vram:.1f} GB VRAM) → usando CUDA")
        return "cuda"
    print("⚠️  GPU não disponível → usando CPU (mais lento)")
    return "cpu"


# ──────────────────────────────────────────────────────────────────────────────
# Validação
# ──────────────────────────────────────────────────────────────────────────────

def verificar_dependencias() -> None:
    """Verifica se openai-whisper e ffmpeg estão disponíveis."""
    try:
        import whisper  # noqa: F401
    except ImportError:
        raise ImportError(
            "openai-whisper não instalado.\n"
            "Execute: pip install openai-whisper"
        )
    if not shutil.which("ffmpeg"):
        raise EnvironmentError(
            "ffmpeg não encontrado no PATH.\n"
            "  Windows : https://ffmpeg.org/download.html\n"
            "  Ubuntu  : sudo apt install ffmpeg\n"
            "  macOS   : brew install ffmpeg"
        )


def verificar_arquivo(caminho: str) -> None:
    """Verifica se o arquivo de vídeo existe."""
    if not os.path.isfile(caminho):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")


# ──────────────────────────────────────────────────────────────────────────────
# Formatação de timestamps
# ──────────────────────────────────────────────────────────────────────────────

def formatar_timestamp(segundos: float) -> str:
    """Converte segundos (float) para o formato SRT: HH:MM:SS,mmm"""
    total = int(segundos)
    ms = int(round((segundos - total) * 1000))
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


# ──────────────────────────────────────────────────────────────────────────────
# Pós-processamento dos segmentos
# ──────────────────────────────────────────────────────────────────────────────

def _quebrar_texto(texto: str, max_chars: int, max_linhas: int) -> str:
    """
    Quebra o texto em linhas respeitando max_chars e max_linhas.
    Linhas excedentes são descartadas (o segmento já terá sido subdividido antes).
    """
    linhas = textwrap.wrap(texto, width=max_chars)
    return "\n".join(linhas[:max_linhas])


def _aplicar_estilo(texto: str, cfg: ConfigLegenda) -> str:
    """Aplica uppercase e remoção de pontuação se configurado."""
    if cfg.remover_pontuacao:
        texto = re.sub(r"[.,;:!?]+$", "", texto.strip())
    if cfg.uppercase:
        texto = texto.upper()
    return texto.strip()


def _subdividir_segmento(seg: dict, cfg: ConfigLegenda) -> list[dict]:
    """
    Se um segmento for muito longo (texto ou duração), subdivide em blocos menores
    distribuindo o tempo proporcionalmente pelas palavras.
    """
    texto  = seg["text"].strip()
    inicio = seg["start"]
    fim    = seg["end"]
    duracao = fim - inicio

    # Calcula quantos caracteres cabem por bloco (max_chars * max_linhas)
    capacidade = cfg.max_chars_por_linha * cfg.max_linhas

    # Se cabe num único bloco e a duração é aceitável, retorna direto
    if len(texto) <= capacidade and duracao <= cfg.duracao_maxima:
        return [seg]

    # Divide o texto em pedaços de até `capacidade` caracteres, quebrando em palavras
    palavras = texto.split()
    blocos_texto = []
    atual = []

    for palavra in palavras:
        teste = " ".join(atual + [palavra])
        if len(teste) > capacidade and atual:
            blocos_texto.append(" ".join(atual))
            atual = [palavra]
        else:
            atual.append(palavra)
    if atual:
        blocos_texto.append(" ".join(atual))

    # Distribui o tempo proporcionalmente ao número de caracteres de cada bloco
    total_chars = sum(len(b) for b in blocos_texto)
    resultado = []
    t = inicio

    for i, bloco in enumerate(blocos_texto):
        proporcao = len(bloco) / total_chars if total_chars else 1 / len(blocos_texto)
        dur_bloco = duracao * proporcao

        # Aplica limites de duração
        dur_bloco = max(cfg.duracao_minima, min(dur_bloco, cfg.duracao_maxima))

        t_fim = min(t + dur_bloco, fim)
        resultado.append({"id": seg["id"], "start": t, "end": t_fim, "text": bloco})
        t = t_fim + cfg.gap_entre_blocos

    return resultado


def formatar_segmentos(segmentos: list[dict], cfg: ConfigLegenda | None = None) -> list[dict]:
    """
    Aplica todas as regras de formatação da ConfigLegenda sobre os segmentos brutos
    retornados pelo Whisper.

    Etapas:
      1. Subdivisão de segmentos longos (duração ou texto)
      2. Aplicação de duração mínima
      3. Quebra de texto em linhas (max_chars_por_linha × max_linhas)
      4. Uppercase / remoção de pontuação
      5. Reindexação sequencial

    Args:
        segmentos: Lista bruta de segmentos do Whisper.
        cfg:       Configuração de formatação. Usa ConfigLegenda() padrão se None.

    Returns:
        Lista de segmentos formatados e prontos para exportação.
    """
    if cfg is None:
        cfg = ConfigLegenda()

    resultado = []

    for seg in segmentos:
        # 1. Subdivisão
        sub = _subdividir_segmento(seg, cfg)

        for bloco in sub:
            # 2. Duração mínima
            if bloco["end"] - bloco["start"] < cfg.duracao_minima:
                bloco["end"] = bloco["start"] + cfg.duracao_minima

            # 3 + 4. Quebra de linhas + estilo
            texto = _aplicar_estilo(bloco["text"], cfg)
            texto = _quebrar_texto(texto, cfg.max_chars_por_linha, cfg.max_linhas)
            bloco["text"] = texto

            if bloco["text"]:
                resultado.append(bloco)

    # 5. Reindexar
    for i, bloco in enumerate(resultado):
        bloco["id"] = i

    return resultado


# ──────────────────────────────────────────────────────────────────────────────
# Transcrição
# ──────────────────────────────────────────────────────────────────────────────

def carregar_modelo(modelo: str, device: str | None = None):
    """
    Carrega o modelo Whisper. Faz download automático na primeira execução.

    Args:
        modelo: 'tiny' | 'base' | 'small' | 'medium' | 'large'
        device: 'cuda', 'cpu' ou None (detecta automaticamente).
    """
    import whisper
    device = device or detectar_device()
    print(f"⏳ Carregando modelo '{modelo}' em '{device}'...")
    model = whisper.load_model(modelo, device=device)
    print(f"✅ Modelo '{modelo}' pronto.\n")
    return model


def transcrever(model, arquivo: str, idioma: str | None = None) -> tuple[list[dict], str]:
    """
    Transcreve o áudio de um vídeo usando o modelo Whisper.

    Args:
        model:   Modelo Whisper já carregado.
        arquivo: Caminho do arquivo de vídeo ou áudio.
        idioma:  Código do idioma ('pt', 'en'…) ou None para detecção automática.

    Returns:
        (segmentos_brutos, idioma_detectado)
    """
    print(f"🔊 Transcrevendo '{os.path.basename(arquivo)}'... aguarde.")
    opts = {"verbose": False}
    if idioma:
        opts["language"] = idioma

    resultado = model.transcribe(arquivo, **opts)
    segmentos = resultado.get("segments", [])
    idioma_detectado = resultado.get("language", "desconhecido")

    print(f"✅ Transcrição concluída!")
    print(f"   Idioma detectado : {idioma_detectado}")
    print(f"   Segmentos brutos : {len(segmentos)}\n")

    return segmentos, idioma_detectado


# ──────────────────────────────────────────────────────────────────────────────
# Exportação
# ──────────────────────────────────────────────────────────────────────────────

def salvar_srt(segmentos: list[dict], caminho_saida: str) -> str:
    """
    Salva os segmentos em um arquivo .srt.

    Args:
        segmentos:     Lista de segmentos (já formatados).
        caminho_saida: Caminho do arquivo .srt a ser criado.

    Returns:
        Caminho absoluto do arquivo gerado.
    """
    blocos = []
    for i, seg in enumerate(segmentos, start=1):
        inicio = formatar_timestamp(seg["start"])
        fim    = formatar_timestamp(seg["end"])
        texto  = seg["text"].strip()
        blocos.append(f"{i}\n{inicio} --> {fim}\n{texto}")

    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write("\n\n".join(blocos) + "\n")

    caminho_abs = os.path.abspath(caminho_saida)
    print(f"💾 Legenda salva em: {caminho_abs}")
    return caminho_abs


# ──────────────────────────────────────────────────────────────────────────────
# Prévia
# ──────────────────────────────────────────────────────────────────────────────

def exibir_previa(segmentos: list[dict], n: int = 10) -> None:
    """Imprime os primeiros N segmentos com timestamps formatados."""
    print(f"{'#':<4} {'INÍCIO':<13} {'FIM':<13} TEXTO")
    print("-" * 80)
    for seg in segmentos[:n]:
        inicio = formatar_timestamp(seg["start"])
        fim    = formatar_timestamp(seg["end"])
        texto  = seg["text"].strip().replace("\n", " / ")[:55]
        print(f"{seg['id']:<4} {inicio:<13} {fim:<13} {texto}")


# ──────────────────────────────────────────────────────────────────────────────
# Pipeline completo (atalho)
# ──────────────────────────────────────────────────────────────────────────────

def gerar_legenda_srt(
    arquivo_video: str,
    idioma: str | None = "pt",
    modelo: str = "small",
    arquivo_saida: str | None = None,
    device: str | None = None,
    cfg: ConfigLegenda | None = None,
) -> str:
    """
    Pipeline completo: valida → carrega modelo → transcreve → formata → salva .srt.

    Args:
        arquivo_video: Caminho do vídeo ou áudio.
        idioma:        Código do idioma ou None para detecção automática.
        modelo:        Tamanho do modelo Whisper.
        arquivo_saida: Caminho do .srt. Se None, usa o mesmo nome do vídeo.
        device:        'cuda', 'cpu' ou None (detecta automaticamente).
        cfg:           ConfigLegenda com os parâmetros de formatação.

    Returns:
        Caminho absoluto do arquivo .srt gerado.
    """
    verificar_dependencias()
    verificar_arquivo(arquivo_video)

    cfg   = cfg or ConfigLegenda()
    saida = arquivo_saida or str(Path(arquivo_video).with_suffix(".srt"))

    print(f"📂 Vídeo  : {arquivo_video}")
    print(f"🤖 Modelo : {modelo}")
    print(f"🌎 Idioma : {idioma or 'detecção automática'}")
    print(f"💾 Saída  : {saida}\n")

    model = carregar_modelo(modelo, device=device)
    segmentos_brutos, _ = transcrever(model, arquivo_video, idioma)

    if not segmentos_brutos:
        print("⚠️  Nenhuma fala detectada no vídeo.")
        return ""

    segmentos = formatar_segmentos(segmentos_brutos, cfg)
    print(f"   Segmentos formatados: {len(segmentos)}\n")

    return salvar_srt(segmentos, saida)
