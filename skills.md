# Agent Skills Manifest: AI News Station

## 1. Web Researcher (`researcher`)
**Pillar: Isolate**
- **Description:** Searches for latest AI breakthroughs.
- **Strict Input:** `topic` (string).
- **Instruction:** Do not return marketing fluff. Return 3-5 technical points.

## 2. Professional Editor (`editor`)
**Pillar: Select**
- **Description:** Formats research into a LinkedIn post.
- **Strict Input:** `raw_news` (from state).
- **Instruction:** Use high-signal facts only. Avoid repetitive background info.

## 3. History Compactor (`summarizer`)
**Pillar: Compress**
- **Description:** Condenses long message history to save tokens.
- **Action:** Runs when history exceeds 5 messages.
- **Output:** Updates the `summary` field and clears the `messages` list.