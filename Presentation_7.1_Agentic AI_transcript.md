Summary
Agentic AI means AI that can plan, decide, and act on its own with little help.
Some popular tools for this are LangChain, AutoGen, CrewAI, and IBM Watson Orchestrate.
There are two main types: Workflows (fixed steps) and Agents (more flexible and self-directed).
Examples include a simple workflow that screens resumes versus an agent that helps someone apply for jobs.
Agentic AI often uses tricks like chaining prompts, routing tasks, running things in parallel, and reflecting on results to work better.
Transcript
Hello everyone. Welcome to Module Seven. In this module we're going to focus on a Agentic AI. Let's get started.

So let's see what, Agentic AI actually is. Agentic AI is an intelligence system that can, Perceive, Reason, Plan and Act in pursuit of a goal using an LLM as their core reasoning agent. So you going to see that mostly it's based on the multiple LLM that we're using to build these agents.

So let's look at the key features. Autonomy, which agents operate with minimal human intervention. Then we get Reasoning, they break down task decide what to do next. And then Planning; agents can plan multi-step sequences. Tool use; can call APIs access knowledge bases run functions. Self-reflection; some can evaluate and revise their own steps.

And what are the popular Agentic frameworks? You have worked with LangChain before and we have a LangChain Agent. We have, everyone currently familiar, we have Open AI Functional Calling. We have AutoGen, CrewAI, or AutoGPT. We have IBM Watson X Orchestrate. These are all kind of a prebuilt agent, or like let's say a kind of agentic framework that you can use for your specific task or use case that you have.

So using the agentic AI system represents the next evolution in LLMs, from single turn chat to dynamic and even multi-turn, goal driven agents.

Okay, let's see here how really agent AI works. Agentic AI operates in a loop of perception, reasoning and action that is powered by LLMs and tools. So let's look at the workflow and simplify it for us this workflow.

So what is Perceive? It take in input; for example user request, it can be document, it can be email. I provided an example here. For example, “summarize this PDF and find the main issue in it.” So this is getting the input, this is Perceive.

Then we have Reason and Plan. The next step that we use an LLM to analyze the input, and generate a step by step plan. So the Tool, like prompt chains, chains it can be planners or memory modules. And, you read about the prompting training in previous module.

Later we come to Act which is going to be a tool used execute each plan step by calling API or functions, querying a vector database or SQL, sending messages or completing forms. So this is the what that we really Act by, for example, calling APIs or functions to be able to use them.

Then we have Reflect and Iterate which evaluate output. If incomplete, revise the plan or retry. Optional because use a verifier model or self-critique loop.

Then we have Deliver Output which produce final response report or action.

So the workflow is Percieve, giving the input data; then Reason and Plan, use LLM to analyze the input; then Act and Tools, which is calling API or function to be able to move forward, apply the act that we want; Reflect and Iterate, which is evaluate output; and then Deliver the output at the end. These are one, two, three, four, five steps of the workflow that it says how Agentic AI works.

So let's see how the Anthropic company distinguished two types of agentic AI systems. So, Anthropic is the company that they have, developed Claude, as for example, OpenAI, developed GPT. They have developed Claude. You may familiar with that and worked with that.

They..this, distinguishes two types here. One, they are what we call Workflows, and the other Agents.

So Workflows actually are systems where LLMs and Tools are orchestrated through predefined code paths. How it works. Steps are predefined by developers already. Tools and prompts are used in a fixed linear sequence. LLM has no decision making power here.

Example use case. For example, if you say resume screening. Workflow and task is match resumes to job description. So this steps that should be taken in the workflows is: Parse the resume, which is LLM or rule-based; Extract structured info, skills, experience, etc.; Compared with a predefined job profile; Output a matching score; Like an assembly line, same steps every time. So this is the steps that it looks like in workflow.

Another type is the Agents. Agents are systems where LLMs dynamically direct their own processes and tool usage, maintaining control over how they accomplish tasks. So it's more dynamic or automatic, think of it.

How it works. LLM decides which step to take and when. Tools are in evoked dynamically based on reasoning. Supports, loops, retries, and context aware adjustments.

So let's see an example of the use case here. Intelligent job application assistant. Like, “help a user apply for a job” So, the Behavior: Read user's resume. Ask user what role are you targeting. Search job board for relevant posting. Summarize posting. And, suggest fits. Tailor tailor resume using LLM. Fill out application automatically, like a self driving assistant adopting the context and goals.

So you can see that the main difference between Workflows and Agents. Workflows LLMs and tools are orchestrated through preferred code. While Agents are more dynamically LLMs maintaining control how they accomplish the task.

And I brought here two different, examples so that you can have an idea of how these two type AI systems work.

So let's look at five workflow design patterns, five different workflow design patterns. Starting with prompt chaining. Prompt chaining means breaking it big task into smaller steps where if step is handled by different LLM prompt. For example, if you look at the diagram here, the LLM after the input, the LLM does the first part of the job. Actually the task can begin with LLM1 performing an initial step.

Then it goes to the Gate. Gate is like a traffic controller or decision maker in the middle of the process. It decides what to pass to the next model, whether the output is good enough to continue, which parts the task should follow. If they are different option, then it goes to LLM2, which continues to the next step, and then it can be awarded LLM3 which finishes the task.

So this pattern allowed to break down complex task into smaller subtypes, each handled by a different prompt or model, and then you will get the output. We call this prompt chaining workflow.

So this second workflow is that Routing. It is a pattern where the input is analyzed and sent to a specialized LLM based on its content. So as you see from the diagram, each LLM handles a different subtask or domain. So LLM Routing decides here as you see should this go to LLM1, for example, summarization. Should it go to LLM2, is a sentiment. And then should we go then to, for example, LLM doing extraction?

So, we got the final output after is collected of the correct LLM processes.

So what Routing is do is the main idea is the LLM Router because it's the one that decides what each LLM do, what task, before going to the output, and we can get the output. That is a called Routing workflow.

Another one that we call it is the Parallelization workflow. Think of a like you write a parallel code. So it's a pattern where a task is broken into smaller subtasks which are run concurrently by multiple LLMs. So you see we have here a coordinator. We have three LLM and then aggregator and then output.

So once you once each subtask is done and completed LLM concurrently, the results are combined and returned. So Coordinator split the main task into independent task which is LLM 1-2-3; process the respective subtask in parallel. And then we have Aggregator, which combine the results in the final undefined output. So this workflow is called parallelization workflow.

The other workflow is called Orchestrator-Worker. This pattern uses as central orchestrator as you are seeing here, to break down complex tasks and assign them dynamically to Worker LLM. Once process results are synthesized and combined, to for us, to get the output.

So Orchestrator dynamically analyzes the task and delegates subtask. So imagine it's like dynamically doing this. And then we have LLMs which does execute their assigned subcomponent task in parallel or in sequence. Right. And then we have Synthesizer which gathers all outputs and produce the final results.

So the Worker, or the workflow here, which we call Orchestrator-Worker, is act like a manager assigning tasks to the team. So it reads the incoming request. It breaks the text with smaller job. Assign each job to the best suited LLM, 1-2-3. So each model focused on each own task. These can run in parallel or in a worker. So depending on the job. And then after all works are done in the synthesizer. They gather their results and combine them into one final output. That's why we call it Orchestrator-Worker.

So the last one is the Evaluator and Evaluator-Otimizer workflow. This pattern introduced a second limb that acts as an evaluator. It takes the output of the first LLM generator and decides: Accept the result, it goes to output; or Reject, and some feedback for improvement. This creates a feedback loop that improves output quality iteratively.

So what it does that's LLM Generator propose a solution, and the solution goes to LLM Evaluator checks, correctness, relevance, format, etc. and if it accepted it goes to the output. If it's denied it gets rejected back with a feedback. So again the same loop is going to continue until we get the results as “accepted.”

So this is the final workflow design that I want to talk about, and it is called Evaluator-Optimizer. And based on the use case or the data that you're using, you can definitely have me. You can use different design workflow design patterns, and you can choose from these five patterns that I showed you and explained it to you.

So we talked about the five workflow design partners. Now let’s talk, about the Open-ended Agent pattern, which we call Agentic AI, it is the heart of a Agentic AI system. Unlike fixed workflow chains that we talk about, Agentic AI systems are autonomous, flexible, and adaptive.

So this pattern allows the LLM agent how to decide, how to solve a problem over time by interacting with its environment without following a fixed script. So the core idea that a link chooses its own strategy based on feedback from the world.

So let's look at the key features: First, it's open-ended, so no fixed number of steps; Flexible, adapt based on the feedback and condition; then we have Dynamic, which different actions each time depending on the situation; then Powered by Feedback, loops keeps improving to trial and error based on the feedback.

So how it works. Human, as you see from the diagram, gives an input. For example, “Find me the best investment opportunity.” Then, LLM takes action here, which decides what to do first. For example, search news, then check market trends and then environment and like web APIs, tools, responds with information or results. And then we have a LLM which updates its plan and either take another action or choose a step if the task is complete and an idea. And we have no fixed path that the agent thinks and access step by step like a human foot.

So you see how the diagram looks like. We have a human that provide input. It goes to LLM Call, decides whether to do first, what to do first. For example, take action from the take action, give feedback from the environment and then, um, choose to stop if the task is complete. So, um.

Let's say, I'm going to give you an example here. For example, like a, an investment research agent. We should start by pulling earnings report, then searches for CEO interviews, then ask follow up question if something is unclear, and then stop when he's confident in a recommendation.

So this is how Agentic AI works. And the key features is: Open-ended, Flexible, Dynamic, and Powered by Feedback loops from the environment to feedback that it gets.

Now, let's hit the next slide. So let's talk about some of the real world use cases for Agentic AI. I like one of them can be document automation like contract passing. The other research assistants like for example, the way that we do archive summarization with search agents. They can be developer copilots like but the openness is fixed generation tested. Then email triage agents which summarize, prioritize and reply.

So, common pitfalls and how to debug agents. This is very important. So we have you can have the common pitfalls like infinite loops runaway costs. So we should be able about be sure about be certain about this. That's not going to happen. It can be a cons inconsistent outputs. It can be tool misuse or hallucination propagation that we see also in most of the LLMs for hallucination that can happen.

So add, we can add best practices, like logging intermediate steps using reflection loops and then timeout plus retry policies. This is how we may think that we can address some of these common pitfalls.

This is end of the course, but I really, this module, I really encourage you to try to focus on your lab session, which is, show you a practical example end to end for Agentic AI.

Thank you all for your attendance.

