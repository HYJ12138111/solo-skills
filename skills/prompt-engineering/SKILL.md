---
name: prompt-engineering
description: "Structured prompt engineering following the ICIO framework. Use when the user asks to craft, improve, or review a prompt — or when their instructions to AI are vague and need tightening. Applies modular thinking (Context/Instruction/Input/Output blocks), three-level evolution (chat → precise NL → structured engineering), and entropy-reduction principles."
---

# Prompt Engineering (ICIO Framework)

Apply structured prompt engineering based on the principle that **prompting is natural-language programming**. The goal is entropy reduction: constraining the LLM's infinite probability space down to a deterministic, high-quality output.

## When to Apply

- User asks to "write a prompt", "improve this prompt", "why did the AI give bad results"
- User's instruction to AI is vague (weak verbs, no constraints, no format specified)
- User needs to turn a one-off prompt into a reusable template
- Any time you're about to send a prompt to an AI and the task is non-trivial

## Core Framework: ICIO

Every prompt needs these four elements. Scale the detail to match the task — not every block needs equal weight:

| Block | Role | Check |
|-------|------|-------|
| **I**nput | Raw material to process | Is the data clearly separated from the instruction? Use `"""` to wrap long inputs |
| **C**ontext | Cognitive water level | Does the AI know its role, the audience, and the scenario? |
| **I**nstruction | Action + constraints | Strong verbs only. "Critically analyze" not "look at". Constraints converge, don't scatter |
| **O**utput | Delivery format | Specify format only when it matters. "Output JSON" / "Markdown table" / "Code only, no explanation" |

**Overriding principle: information density > character count.** A 30-word ICIO prompt beats 60 words of pleasantries.

## Three-Level Escalation

Match the prompt complexity to the task. Don't over-engineer.

### Level 1 — Chat Mode (skip ICIO)
For trivia, simple Q&A, translations of single words. No structure needed.

### Level 2 — Precise Natural Language (light ICIO)
For 90% of real-world tasks. Use natural language but add constraints: who you are, what you want, how you want it.
> "I have 20 minutes at home, no equipment, want to lose fat. Give me a plan."

### Level 3 — Structured Engineering (full ICIO, Markdown blocks)
For complex, multi-step, reusable tasks. Separate Role / Rules / Workflow sections.
```
# Profile
- Role: [expert identity]
- Ability: [specific capability]

# Rules
- [constraint 1]
- [constraint 2]

# Workflow
1. [step 1]
2. [step 2]
```

## Modular Thinking: Cut What You Don't Need

The four blocks are Lego pieces, not a form to fill. Cut based on scenario:

| Mode | Scenario | Keep | Cut | Why |
|------|----------|------|-----|-----|
| **Flash** | Fix a bug, quick code question | Instruction + Input | Context + Output | The code IS the context. No pleasantries. |
| **Creative** | Write copy, generate ideas | Context + Instruction | Input | No raw material. Thicken Context to supply style. |
| **Format** | Meeting notes → table | Input + Output | Context | AI's persona doesn't matter. Lock the output format. |

## Tactical Cheatsheet

1. **Separate input from instruction** — wrap raw text in `"""` so the AI knows what's material vs. command
2. **Strong verbs** — "Refactor", "Extract", "Critique", "Compare". Never "look at", "handle", "fix"
3. **Examples beat adjectives** — can't describe a style? Show one input-output pair (Few-Shot)
4. **"Think step by step"** — the magic phrase that forces System 2 reasoning for math/logic tasks
5. **Negative constraints** — "Do NOT include greetings", "Exclude the term 'marginal utility'" — these are powerful
6. **Add, don't pad** — every word should carry signal. If a sentence doesn't constrain or specify, delete it

## Review Checklist

When reviewing a user's prompt before they send it:

- [ ] Is the input clearly separated from the instruction?
- [ ] Does the instruction use a strong verb?
- [ ] Are there concrete constraints (length, style, what to avoid)?
- [ ] Is the output format specified (if it matters)?
- [ ] Can any words be cut without losing meaning?
- [ ] Would an example help more than another sentence of description?

## Anti-Patterns

- **Over-structuring trivial tasks** — don't write a 20-line Markdown prompt to ask "what's 2+2"
- **Pleasantries as padding** — "Could you please maybe..." is noise. Cut it.
- **Open-ended invitations** — "Write me something about AI" is not a prompt, it's a wish
- **Missing output format when it matters** — if you need JSON, say so. The AI can't read your mind.
