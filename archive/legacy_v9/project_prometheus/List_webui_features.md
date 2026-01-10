Here is a complete reference of **Open WebUI’s features, forks, and enhancement projects** as of October 2025 — ideal for designing your own advanced self-hosted LLM interface inspired by it.  

***

## Core Features

Open WebUI is an **extensible, self‑hosted AI WebUI** that supports local and remote models like **Ollama**, **OpenAI**, and other OpenAI-compatible APIs. Its feature set spans setup, model integration, UX, and extensibility layers.[1][2][3]

### Platform and Deployment
- Seamless installation through **Docker**, **Kubernetes**, **Helm**, **Podman**, or **native installers**.  
- Bundled images with **Ollama** runtime or **CUDA** acceleration.  
- Persistent **SQLite (`webui.db`)** configuration for multi-instance sync and load balancing.  
- Built-in **import/export** to migrate or clone configurations easily.  
- Guided setup wizard for admin and role initialization.[3][1]

### Core Capabilities
- Works **offline**, fully self-contained.  
- **API Compatibility:** Integrates any OpenAI-format API endpoint for multi-backend chat handling.  
- **RBAC (Role-Based Access Control):** Per-user permissions and secured admin privileges.  
- **Multiple Models per Chat:** Parallel or comparative model usage within a single session.  
- **Pipelines Plugin Framework:** Extensible Python-based pipeline hooks enabling function calling, filters, and rate-limiting.[4][3]

### Chat, UX, and User Tools
- Bi-directional (LTR/RTL) chat UI; multilingual interface (i18n-ready).  
- **Responsive Design** across desktop, PWA mobile (offline-capable).  
- **Haptic feedback** for mobile users.  
- Built-in **Swagger API docs** (offline).  
- **Chat export** to PDF and plain text.  
- **Keyboard shortcuts panel** and in-app documentation.[5][1]

### Advanced Integrations
- **Web browsing inside chats** using the `#URL` command.  
- **Image generation:** via AUTOMATIC1111, **ComfyUI**, or **DALL‑E**.  
- **OAuth/SSO** (e.g., Feishu integration).  
- **OpenTelemetry Metrics & Logging** for observability.  
- Multi‑language date/time formatting and better UI state persistence.[3][5]

### Performance
- Lazy-loaded JS components (jsPDF, Leaflet, etc.) reduce bundle size by 1.4 MB.  
- Optimized code block rendering and markdown parsing.  
- Dynamic memory-efficient message processing pipeline.[5]

***

## Known Open WebUI Forks

There are numerous community forks extending the base project for specialized use cases.[6][7][8]

| Fork Name | Description | Enhancements |
|------------|--------------|---------------|
| **OpenLLM-France / `open-webui-lucie`** | Integrated with **Lucie** (LINAGORA’s enterprise LLM). | Distributed backend, French NLP pipeline integration. [8] |
| **acceleratorlastorder / open-webui-fork** | Full offline fork with LLM runner integrations. | Backend agnostic (Ollama, LM Studio, KoboldCPP). [6] |
| **Haervwe / open-webui-tools** | Modular toolkit to extend base capabilities. | Adds tools (arXiv, Perplexica, Pexels, YouTube, image/audio generation, Hugging Face integration). [9] |

***

## Major Enhancement Projects and Toolkits

### Haervwe’s Open‑WebUI Tools Collection[9]
**15+ custom tools, pipes, and filters**, designed to extend any Open WebUI installation:
- **Tools:** arXiv search, YouTube embed, Pexels media retrieval, Hugging Face image generator.
- **Function Pipes:** Planner Agent v2, arXiv MCTS, Resume Analyzer, Mopidy control.
- **Filters:** Semantic Router, Prompt Enhancer, Clean Thinking Tags, Document Parser.

### Pipelines Framework (Official)[4]
Modular plugin system providing:
- Function calling, context filtering, and middleware hooks.
- Realtime translation, rate-limiting, Langfuse analytics, and proxy routing.

***

## Notable Features Added in 2025 Releases

Recent GitHub updates (October 2025) added :[5]
- On‑demand library loading to improve load times.
- Per‑chat **PDF export tool**.
- Enhanced **auth reliability** and **function validation** routines.
- **Notification drag-to-dismiss** and **keyboard navigation**.
- Refined localization layers and **SSO expansions**.

***

## For Inspiration in Your Custom LLM Interface

Combining all community innovations, a modern Open WebUI‑style platform could support:
- Real‑time plugin execution (Python & JS sandboxes).  
- Multi‑LLM threaded orchestration (composable backends).  
- Persistent chat graphing and entropy-based memory trimming.  
- Fine-grained OpenTelemetry telemetry and cost tracking.  
- Autonomous pipeline execution (Planner/MCP agent integration).  
- In-app ComfyUI-style canvas for multimodal chains.

Each of these is already explored or prototyped in forks and plugin toolsets under Open WebUI’s expanding GitHub ecosystem.[7][6][9][3][4]

[1](https://docs.openwebui.com/features/)
[2](https://docs.openwebui.com)
[3](https://github.com/open-webui/open-webui)
[4](https://github.com/open-webui/pipelines)
[5](https://github.com/open-webui/open-webui/releases)
[6](https://github.com/acceleratorlastorder/open-webui-fork)
[7](https://github.com/open-webui)
[8](https://github.com/OpenLLM-France/open-webui-lucie)
[9](https://github.com/Haervwe/open-webui-tools)
[10](https://www.youtube.com/watch?v=CDiVq3mPZc8)
[11](https://www.youtube.com/watch?v=dLEG1LqX4Qg)
[12](https://docs.openwebui.com/tutorials/tips/contributing-tutorial/)
[13](https://hostkey.com/blog/74-10-tips-for-open-webui-to-enhance-your-work-with-ai/)
[14](https://docs.openwebui.com/getting-started/)
[15](https://github.com/open-webui/open-webui/discussions/16530)
[16](https://www.pondhouse-data.com/blog/introduction-to-open-web-ui)
[17](https://www.reddit.com/r/opensource/comments/1kfhkal/open_webui_is_no_longer_open_source/)
[18](https://github.com/open-webui/open-webui/discussions/9334)
[19](https://github.com/open-webui/open-webui/discussions/13458)
[20](https://www.reddit.com/r/OpenWebUI/comments/1gjziqm/im_the_sole_maintainer_of_open_webui_ama/)