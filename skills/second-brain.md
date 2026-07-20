---
name: second-brain
description: "Access and update the Obsidian Vault as the long-term memory for the project. Use before answering complex architectural questions or after resolving significant issues."
risk: safe
source: custom
date_added: "2026-04-22"
---

# Second Brain: Obsidian Knowledge Vault

## Vault Location
```
(Local Obsidian Vault Path)
```

---

## Vault Structure

Strict division into main areas. Each note **must** be located in the appropriate subfolder and link to its local or root index.

Vault/
│
├── 01_Architecture/              ← System architecture, databases, core logic
│   └── Architecture_Index.md     ← 🔗 Sub-index
├── 02_Features/                  ← Business logic, user flows, specific features
│   └── Features_Index.md         ← 🔗 Sub-index
├── 03_Infrastructure/            ← DevOps, CI/CD, deployment, servers
│   └── Infrastructure_Index.md   ← 🔗 Sub-index
├── 04_Meetings_and_Logs/         ← Daily notes, meeting summaries, work statuses
│   └── Meetings_Index.md         ← 🔗 Sub-index
├── _Assets/                      ← ONLY images and media files
│                                    (Pasted images always go here!)
│
└── Main_Index.md                 ← 💻 Central hub connecting all indices

## Graph Architecture (Hierarchical MOC)

The graph should look like a **system of clear clusters**, where `Main_Index` acts as the central hub.

### Linking Rules (mandatory for each note)

- **Central Hub Rule**: `Main_Index` is the core. All sub-indexes connect directly to it.
- **Leaf Notes**: Leaf notes connect ONLY to their local sub-index (e.g., a note in `01_Architecture` connects only to `Architecture_Index`).
- **No Direct Links to Main**: Leaf notes should never link directly to `Main_Index`.
- **No Cross-Cluster Linking**: Notes from one cluster should not link directly to notes in another cluster unless necessary, prefer routing through indexes.

---

## Assets Rules (Images)

- **ALWAYS** save images in `_Assets/`
- **NEVER** leave `Pasted image XXXXXXXXXX.png` in the root of the Vault or in note folders
- Link format in notes: `![[_Assets/filename.png]]`
- When creating notes with embedded images, specify the path explicitly.

---

## Use this skill when
- Asked about the system architecture or core features
- Before a complex debug session — check the vault for known issues
- After resolving a significant bug — record it in the vault
- After making an architectural decision — update the relevant Index
- At the end of a productive session — record a note in `04_Meetings_and_Logs/`

## Do not use this skill when
- The question is trivial and does not require persistent context
- The task is a one-line fix without architectural consequences

---

## Instructions

### After resolving an issue or making a decision:
1. Determine the correct folder based on the topic.
2. Naming convention: `YYYY-MM-DD_topic.md`
3. The first link in the note should be to the **sub-index of the folder** (e.g., `[[Architecture_Index]]`), and **not** directly to `[[Main_Index]]`.
4. Mandatory frontmatter:
```yaml
---
date: YYYY-MM-DD
tags: [relevant, tags]
project: Current Project
---
```
5. Include: **What happened**, **Root cause**, **Fix applied**, **Lessons learned**

---

## Note Quality Rules
- Each note must have **frontmatter** with `date`, `tags`, `project`
- The first line of the body is a link to the parent Index
- Architectural notes should contain a **Mermaid diagram** (if there are data flows)
- Bug notes should contain **steps to reproduce**
- Atomic notes: one topic — one note, link instead of duplicating

---

## Limitations
- Always verify the vault against the real code — the vault might be outdated.
- Do not store sensitive credentials or keys in Obsidian notes.
- If the vault and code contradict each other — trust the code, update the vault.
