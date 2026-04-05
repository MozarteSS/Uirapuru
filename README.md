# 🎬 UirapuruTranslate

**SRT subtitle generation and translation powered by local LLMs via [Ollama](https://ollama.com) and OpenAI Whisper.**

Two independent notebooks:
- **`Subtitles_Generator.ipynb`** — transcribe any video/audio into an `.srt` file using Whisper
- **`Subtitles_Translator.ipynb`** — translate any `.srt` file between languages using a local LLM

Runs entirely offline (no API keys needed) with an optional Google Translate pass for a hybrid workflow. Supports 5 translation styles and provides automatic quality review and correction.

---

## ✨ Features

### 🎙️ Subtitle Generator
- **OpenAI Whisper** transcription — all Whisper model sizes supported (`tiny` → `large`)
- **Automatic device detection** — uses CUDA if available, otherwise CPU
- **Configurable formatting** — character limits, max lines, duration ranges, uppercase, punctuation
- **5 ready-made profiles** — `padrao`, `cinema`, `redes`, `broadcast`, `acessivel`
- **Full pipeline or step-by-step** — run all steps at once or inspect intermediate results

### 🌐 Subtitle Translator
- **Any language pair** — configurable `SOURCE_LANGUAGE` and `TARGET_LANGUAGE` via ISO 639-1 codes
- **100% local inference** — no data leaves your machine (Ollama)
- **Hybrid mode** *(recommended)* — Google Translate provides the factual base; the local model naturalizes and adapts style
- **Pure-model mode** — translation and revision done entirely by the local LLM
- **5 translation styles** — Cinema, Colloquial, Formal, Casual, Academic
- **Automatic checkpoint** — interrupt and resume translation from where it left off
- **Post-translation review** — LLM audits each subtitle pair and auto-corrects flagged issues
- **Misalignment detection** — detects and corrects batch shifts/duplicates without LLM calls
- **Automatic model download** — pulls missing Ollama models automatically on first run
- **Optional quality estimation** — [TransQuest](https://github.com/TharinduDR/TransQuest) DA scores to flag semantically poor translations

---

## 🔧 Requirements

| Requirement | Notes |
|---|---|
| Python 3.11+ | |
| [Ollama](https://ollama.com/download) | Must be running (`ollama serve`) — for translation |
| [ffmpeg](https://ffmpeg.org/download.html) | Required by Whisper — for subtitle generation |
| Translation model | `translategemma:12b` *(recommended)* |
| Revision model | `translategemma:12b` *(default)* or `gemma3:12b` |
| Internet connection | Only for Google Translate (hybrid mode) and initial model download |

### 💻 Hardware Requirements

| Component |  Minimum  |  Recommended  |
|-----------|-----------|---------------|
|    RAM    |   16 GB   |     32 GB     |
| VRAM(GPU) |   8 GB    |     12 GB+    |
|  Storage  | 20GB free |   40GB+ free  |
|    CPU    |  6-core   |     8-core+   |
|    GPU    |  GTX1080  |   RTX 4070+   |

> **Note:** 12B models run on CPU (no GPU), but expect 10–30× slower speeds. With 8 GB VRAM, models run in mixed CPU+GPU mode. For best performance, a GPU with 12 GB+ VRAM is recommended.

---

## 🚀 Installation

```bash
# 1. Clone the repository
git clone https://github.com/MozarteSS/UirapuruTranslate.git
cd UirapuruTranslate

# 2. Create and activate a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Pull the recommended Ollama models (for translation)
ollama pull translategemma:12b
```

> **ffmpeg** must be installed separately on your system (it is not a Python package).  
> **TransQuest** (optional quality estimation) downloads a ~440 MB model on first use. Disable it by setting `USE_TRANSQUEST = False` in Cell 4 of the translator notebook.

> ⚠️ **PyTorch (CUDA):** the `requirements.txt` includes `torch`, `torchaudio`, and `torchvision` built for **CUDA 12.1** (`+cu121`). If you don't have an NVIDIA GPU or use a different CUDA version, install PyTorch manually:
> ```bash
> pip install torch torchaudio torchvision --index-url https://download.pytorch.org/whl/cu121
> ```
> For CPU-only or other CUDA versions, see [pytorch.org/get-started](https://pytorch.org/get-started/locally/).

---

## 📖 Usage

### 🎙️ Subtitle Generator (`Subtitles_Generator.ipynb`)

1. Open the notebook:
   ```bash
   jupyter lab Subtitles_Generator.ipynb
   ```
2. **Cell 2** — set `ARQUIVO_VIDEO`, language, Whisper model size, and formatting profile  
3. **Cell 3** — verify dependencies and file path  
4. **Cell 4** — load the Whisper model  
5. **Cell 5** — transcribe the video  
6. **Cell 6** — format segments and save the `.srt`  
7. **Cell 7** — preview the first subtitles

   > ⚡ **Shortcut:** Cell 10 runs the entire pipeline in one call via `gerar_legenda_srt()`.

### 🌐 Subtitle Translator (`Subtitles_Translator.ipynb`)

1. Make sure Ollama is running:
   ```bash
   ollama serve
   ```
2. Open the notebook:
   ```bash
   jupyter lab Subtitles_Translator.ipynb
   ```
3. **Cell 1** — checks and installs missing packages automatically  
4. **Cell 2** — set your `.srt` file path, source/target languages, model names, style, and mode  
5. **Cell 3** — runs the translation (resumes from checkpoint if interrupted)  
6. **Cell 4** *(optional)* — LLM review pass with automatic correction

The output file is saved in the same directory as the input with a style suffix (e.g., `_Cinema_pt-BR.srt`).

---

## 🎨 Translation Styles

| Code | Style | Best for |
|------|-------|----------|
| `1` | 🎬 Cinema | Movies and series in general |
| `2` | 💬 Colloquial | Everyday conversations |
| `3` | 🎓 Formal | Documentaries and educational content |
| `4` | 😄 Casual | Comedies, reality shows, vlogs |
| `5` | 🔬 Academic | Science documentaries, technical terminology |

---

## 🔄 Translation Modes

| Mode | `USE_GOOGLE_AS_BASE` | Flow |
|------|----------------------|------|
| **Hybrid** *(recommended)* | `True` | Google Translate → refinement by local model |
| **Pure model** | `False` | Translation + revision done entirely by local model |

Hybrid mode is generally more accurate and faster because the local model only needs to naturalize and fix style errors rather than translate from scratch.

---

## 🎞️ Subtitle Formatting Profiles

| Profile | Chars/line | Lines | Duration | Notes |
|---------|-----------|-------|----------|-------|
| `padrao` | 42 | 2 | 1–7 s | General purpose default |
| `cinema` | 36 | 2 | 1.5–6 s | Cinema standard |
| `redes` | 28 | 1 | up to 4 s | Social media, UPPERCASE |
| `broadcast` | 42 | 2 | 1–8 s | TV broadcast |
| `acessivel` | 37 | 2 | 2–6 s | Accessibility |

Custom profiles can be created via `ConfigLegenda` with full control over all parameters.

---

## 📁 Project Structure

```
UirapuruTranslate/
├── Subtitles_Generator.ipynb   # Notebook: video/audio → .srt (Whisper)
├── Subtitles_Translator.ipynb  # Notebook: .srt → translated .srt (Ollama)
├── functions/
│   ├── GenLeg.py               # Whisper transcription and SRT formatting logic
│   ├── translation_process.py  # Core translation, review, and correction logic
│   └── prompts.py              # Prompt templates and style definitions
└── requirements.txt            # Python dependencies
```

---

## 🤖 Recommended Models

| Model | Use | Notes |
|-------|-----|-------|
| `translategemma:12b` | Translation & revision | Best quality for subtitle translation |
| `gemma3:12b` | Revision / review | Strong general reasoning |
| `llama3.1:8b` | Translation | Faster, slightly lower quality |

Any Ollama-compatible model can be used — set `TRANSLATION_MODEL` and `REVISION_MODEL` in Cell 2.

---

## 📄 License

[MIT](LICENSE)
