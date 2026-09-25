# Host adaptation

## Load and invoke manually

Use the same `SKILL.md` across coding agents. Do not assume that every agent has a skill importer, the same installation directory, slash commands, or delegation tools.

- If the host supports skill folders, import or place the extracted `idea-council` folder using its documented mechanism.
- If it supports attached files or file reading, attach or open `SKILL.md` and this reference, then explicitly request: `Run Idea Council on this idea: [idea].`
- If it only accepts prompts, paste the complete contents of `SKILL.md` and this reference, then add that invocation.
- Treat `$idea-council` and `@idea-council` as convenience forms only where the host recognizes them. The plain-language invocation does not require special command syntax.
- Avoid installing the full workflow as an always-on project rule. If a project-rule entry is necessary, make it a short pointer that loads the workflow only when the user explicitly says to run Idea Council. Preserve existing rules.

Use this explicit request when loading files into a host without a skill importer:

> Read idea-council/SKILL.md and idea-council/references/host-adapter.md. Run Idea Council on this idea: [describe the idea]. Check whether you can create six real subagents and send them follow-ups before starting. Keep activation manual.

## Map capabilities, not product names

Inspect tools exposed in the current session; do not infer functionality from a product name or from an example tool name in a document. Follow host instructions and permission boundaries. Do not install software, obtain credentials, launch outside model services, or modify agent configuration merely to overcome missing capabilities.

| Required operation | Acceptable host capability | Check before starting |
| --- | --- | --- |
| Create participant | Native worker, subagent, task, or isolated agent-session creation | Returns or exposes six distinct participant identities; supports focused role instructions. |
| Execute independently | Supported parallel batch, asynchronous jobs, or concurrent sessions | Can dispatch six participants without deliberate serial execution; capacity includes the chair where applicable. |
| Collect output | Task results, messages, events, or wait/status tools | Can attribute each response to a real participant and distinguish errors from completion. |
| Continue debate | Message, resume, or follow-up operation on each original participant/session | Can supply the position sheet and peer challenges after round one and collect revised positions. |
| Release capacity | Close, cancel, or host-managed completion | Can end only this meeting's work according to the host lifecycle. |

Translate these operations into actual available tools. Keep the process at one chair plus exactly six child participants. Do not create six more agents for the debate round. A resumable original session is acceptable; merely assigning the same role name to a new agent is not evidence of session continuity.

Where tools use blocking calls, use the host-supported parallel calling facility. Do not invent shell commands or use unrelated terminal processes as a substitute for real agent delegation. A host that exposes only one-shot, non-resumable workers cannot execute this complete two-round workflow as specified.

## Capability shortfalls

Distinguish portability of the instructions from availability of multi-agent execution. A text skill cannot add tools or raise concurrency limits.

If six child slots or follow-up support are missing, state the specific limitation. Offer these choices without silently switching:

1. Run **Express Council Mode (3 child slots)** using Value advocate, Constructive skeptic, and Feasibility lead.
2. Run later in an environment with six real child agents and follow-up support.
3. If the user accepts, provide a **single-agent review using multiple perspectives**. Identify it as a simulation, omit claims of independent agents or real peer debate, and label the final result accordingly.

If runtime failure occurs after startup, retry the affected existing participant once where possible. If recovery fails, report the incomplete roster and which round is missing. Summarize usable findings with that limitation; do not fabricate completion or create replacement agents beyond the allocated participant count.

## Optional metadata

`agents/openai.yaml` is optional host-specific metadata. Hosts that do not recognize it should use the Markdown instructions and manual invocation gate. Its `allow_implicit_invocation: false` setting reinforces manual activation in supporting hosts; it does not guarantee how another host discovers or loads instructions.

No external packages, API keys, or executable launcher are bundled. Native delegation must be supplied by the host. These instructions do not claim verified compatibility with every coding-agent product or version.
