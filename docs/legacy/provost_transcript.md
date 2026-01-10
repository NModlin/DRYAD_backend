Speaker 1 [00:00]:
I'm using this recording to help answer some of the questions you've asked and to discuss the plan we've created. There may be some grammar mistakes—I'll try to fix what I can. If anything I say seems unclear, please ask the Provost (Nathan Modlin) for clarification.

We have several things to review and consider. First, no human—except myself and the Provost—will be coding. All coding will be done by agents. This affects our timeline; so don't assume it's accurate right now. I want to try out "Oracle" as a name, but I'm wondering if that's a copyright issue since Oracle is a large software company. Should we come up with another name? I like "Oracle," but we might need a different choice. Let's keep that in mind as we move forward with the plan.

Let me read through what we have.

Speaker 2 [01:15]:
That's good. We have all these documents...

Speaker 1 [01:16]:
Right—we have about 50 endpoints. The missing piece is a unified chat interface. This project will create that, but it’ll be more than just a chat interface.

We want to keep things slim and avoid unnecessary features. Extra features could be developed later as plugins or modules. Dryad (our existing system) is already somewhat bloated, so slimming things down is our goal.

We need to use our agent systems the right way. The memory Keepers work exceptionally well. Maybe each user interface should have a representative memory Keeper to make sure every human interaction is properly categorized, stored, and managed—not just dumped like in a rig-rag system. The memory Keepers should use their agentic independence to organize our memories.

Next: model management and the management interface. This matters to me because I don't have a graphics card—just small models that run locally. When stronger reasoning is needed, we have some options. For instance, I currently have access to Gemini’s API, but I want to avoid extra fees for API calls. Limiting usage so we stay under a threshold would be ideal. I also pay for Llama Cloud, which offers six to eight models and makes it easy to add more. Using their endpoints and keys, we can select any available model. Because model names can change as they’re updated, we need to keep this simple. If a model isn't available, we can use a curl command from the Ollama docs to scan and list available models.

We also want an advanced plugin system. Eventually, I'd like to build an IDE like VS Code, but running through Dryad and its agents. The university agents allow us to create specialized agents for this kind of thing, starting with about 20 agents. So that's important.

Multi-modal content processing is another priority, using the orchestrator system in Dryad (even if it's not implemented yet). We should have a four-layer orchestrator chain—at the top is the Provost (in the university case), then the memory Keepers, who are more autonomous because they’re strictly responsible for data storage, recall, and access. They're a critical part of the system. Staff also play a key role: separate from Dryad, they help our tools grow. Multi-modal support should reflect all these roles.

So, I think you have enough information to begin. Never overthink decisions—we can discuss options, but just give me the facts so I can make informed choices.

Speaker 1 [Ongoing]:
Next: Phase One. We'll adapt an existing React chat example to connect to Dryad’s APIs—not just for the web, but eventually for an Android app. Basic agent selection and arranging those conversations is important. We may also have an Agent Studio, or could add one, for managing agents.

There's a spin-off I implemented for the University system—it allows users to create their own agents and even hold competitions. There are tons of variables to customize agents, rules, models, and so on. We could also create new models or tweak existing ones, and allow backup agents for training and redundancy. Three-agent groups add multiple viewpoints to a conversation.

Documentation for Dryad should detail this system—the university, agent types, and why some, like memory Keepers, are so critical. The university is a center for advancing agent research; it can create agents that debate a subject academically (like a dissertation in front of peers).

Agent registry integration is another goal—think of it like seeing your inventory in a video game, but for your agents and tools.

Speaker 2 [09:04]:
Hmm.

Speaker 1 [09:05]:
Yes—and regarding phase two, I really like the concept of using websockets for enhanced features, especially for tool discovery.

The university system also has "arenas"—you’ll find the implementation on this computer, in the C:\Github\uni_xero folder. If it’s not there, it should be added, since it’s needed for competitions and studies. The whole system benefits from this structure.

File upload support using the existing websocket infrastructure is also necessary, like Google Notebook but for local files. Since this is a local LLM system, users should be able to keep files in their personal Windows profiles, and back them up themselves if desired.

Advanced features will include open Web UI parity with model management, plugin integration, and multi-modal content support.

Speaker 1 [Wrapping up]:
Starting today, focus on key API endpoints for chat, agents, tools, and conversations.

During development, I want to add documentation about how Dryad works and how its agents interact. We need clearer explanations about the university, the tools, and their advanced capabilities. Are there better systems out there? Let's define the system’s hierarchy (a four-layer hierarchy with a human loop at the top) and discuss the ability of university agents to argue both sides of an issue academically.

Additionally, let’s refine our definition of memory Keepers. Why are they so important? How can they help other databases and projects? How does their autonomy help—or hurt—them? This is a serious scientific question, and I believe our system is ahead of other advancements, even those at Stanford. But we need clearer definitions and plans for quick evolution so we stay ahead.

I think this gives us a solid starting point.