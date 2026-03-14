# 🎬 UirapuruTranslate — SRT Subtitle Translator

**English → Brazilian Portuguese subtitle translation powered by local LLMs via [Ollama](https://ollama.com).**

Runs entirely offline (no API keys needed) with an optional Google Translate pass for a hybrid workflow. Supports 5 translation styles and provides automatic quality review and correction.

---

## ✨ Features

- **100% local inference** — no data leaves your machine (Ollama)
- **Hybrid mode** *(recommended)* — Google Translate provides the factual base; the local model naturalizes and adapts style
- **Pure-model mode** — translation and revision done entirely by the local LLM
- **5 translation styles** — Cinema, Colloquial, Formal, Casual, Academic
- **Automatic checkpoint** — interrupt and resume translation from where it left off
- **Post-translation review** — LLM audits each subtitle pair and auto-corrects flagged issues
- **Misalignment detection** — detects and corrects batch shifts/duplicates without LLM calls
- **Optional quality estimation** — [TransQuest](https://github.com/TharinduDR/TransQuest) DA scores to flag semantically poor translations

---

## 🔧 Requirements

| Requirement | Notes |
|---|---|
| Python 3.11+ | |
| [Ollama](https://ollama.com/download) | Must be running (`ollama serve`) |
| Translation model | `translategemma:12b` *(recommended)* |
| Revision model | `gemma3:12b` *(recommended)* |
| Internet connection | Only for Google Translate (hybrid mode) and model download |

### 💻 Hardware Requirements

| Component | Minimum | Recommended |
|---|---|---|
| RAM | 16 GB | 32 GB |
| VRAM (GPU) | 8 GB | 12 GB+ |
| GPU | NVIDIA GTX 1080 / AMD RX 6600 | NVIDIA RTX 3080 / RTX 4070+ |
| Storage | 20 GB free | 40 GB+ free |
| CPU | 6-core | 8-core+ |

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

# 4. Pull the recommended Ollama models
ollama pull translategemma:12b
ollama pull gemma3:12b
```

> **TransQuest** (optional quality estimation) is listed in `requirements.txt` but downloads a ~440 MB model on first use. Skip it if not needed by setting `USE_TRANSQUEST = False` in Cell 4.

---

## 📖 Usage

1. Make sure Ollama is running:
   ```bash
   ollama serve
   ```
2. Open the notebook:
   ```bash
   jupyter lab tradutor_legendas_ollama.ipynb
   ```
3. **Cell 1** — checks and installs missing packages automatically  
4. **Cell 2** — set your `.srt` file path, model names, style, and mode  
5. **Cell 3** — runs the translation (resumes from checkpoint if interrupted)  
6. **Cell 4** *(optional)* — LLM review pass with automatic correction

The output file is saved in the same directory as the input with the suffix `_<Style>_pt-BR.srt`.

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

## 📁 Project Structure

```
UirapuruTranslate/
├── tradutor_legendas_ollama.ipynb  # Main notebook (user interface)
├── translation_process.py          # Core translation and processing logic
├── prompts.py                      # Prompt templates and style definitions
└── requirements.txt                # Python dependencies
```

---

## 🤖 Recommended Models

| Model | Use | Notes |
|-------|-----|-------|
| `translategemma:12b` | Translation | Best EN→PT-BR quality |
| `gemma3:12b` | Revision / review | Strong general reasoning |
| `llama3.1:8b` | Translation | Faster, slightly lower quality |

Any Ollama-compatible model can be used — set `TRANSLATION_MODEL` and `REVISION_MODEL` in Cell 2.

---

## 📄 License

[MIT](LICENSE)
