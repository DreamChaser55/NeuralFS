# NeuralFS

<p align="center">
  <img src="neuralfslogo.png" alt="NeuralFS Logo" />
</p>

NeuralFS is an agentic AI framework that can write original campaigns for the Freespace Open (FSO) engine. It consists of two AI agents (LLMs with a custom system prompt) and two specialized Python conversion scripts. NeuralFS supports two agentic AI engines:
- Visual Studio Code (by using the Roo Code extension)
- OpenCode

## Main Components

### FreeSpace Creative Writing Agent

This agent brainstorms and iteratively writes the campaign description in natural language, beginning with a basic idea, then writing a comprehensive reference document, plot outline and ending with detailed mission plans (scenarios).

### FSIF+FCIF Writing Agent

This agent takes the detailed mission plans written by the previous agent and converts them into an exact mission specification in a custom YAML-based intermediate mission format: *FreeSpace Intermediate File (FSIF)*. This format is much more concise than `.fs2` (the mission file format expected by FSO). `.fs2` files tend to be large, with lots of redundant fields and boilerplate. An AI agent directly creating the `.fs2` file would waste a lot of tokens and could quickly fill up its context window. Also, YAML is much more common in the LLM training data than `.fs2` files. This is why it is better to use a more concise and compact intermediate format.

The agent also writes the campaign definition file in a custom *FreeSpace Campaign Intermediate Format (FCIF)*. Similar to FSIF, FCIF is a concise YAML-based format that abstracts away the verbose `.fc2` syntax, making it easy for both humans and AI agents to define campaign structure, mission progression, starting loadouts, and mission success/failure logic.

This agent also adds FSO text coloring tags into the fiction viewer files written by the previous agent and checks them for issues using a small dedicated Python script.

After writing each `.fsif` or `.fcif` file, this agent immediately runs it through the respective Python converter script to validate it. If the converter reports any errors or warnings, the agent autonomously analyzes the file, applies the necessary fixes, and retries the conversion until the file is valid and successfully converted to game-ready `.fs2` or `.fc2` formats.

### FSIF to FS2 Converter

A Python script that takes the intermediate FSIF representation of the mission and converts it into the FS2 format expected by FSO. During the conversion, the FSIF representation is extensively validated; if any errors are found, actionable error messages are printed to the console, so the AI agent can fix them and try again.

The Converter script has both command line interface suitable for use by AI agents, and GUI for use by humans.

If provided with Google Gemini or ElevenLabs API key, the Converter script can optionally generate voice files for briefings/messages/debriefings, using Gemini or ElevenLabs TTS API.

For details, see `\FSIF_to_FS2_Converter\README.md`.

### FCIF to FC2 Converter

This Python script converts campaign definition files from the FCIF format into the `.fc2` campaign format expected by FSO.
The converter validates the FCIF input, generates S-expression (SEXP) logic for mission progression (success/failure conditions), and writes the final `.fc2` file.

This converter script also has both interfaces: CLI suitable for use by AI agents and GUI for use by humans.

For details, see `\FCIF_to_FC2_Converter\README.md`.

## Requirements
- One of these agentic AI engines:
  - Visual Studio Code with Roo Code extension
  - Opencode
- PyYAML
- pydantic

## Documentation for AI agents
- `Documentation/index.md` — documentation home and index, navigation, and recommended reading order.
- `Freespace Bibles/` — Freespace universe Bibles (full and condensed version)

## Manuals for human users

Read the manual based on your chosen agentic AI engine:
- `Documentation/User manuals/Using NeuralFS with VS Code.md`.
- `Documentation/User manuals/Using NeuralFS with OpenCode.md`.

## Limitations
- Currently, only FreeSpace Port (FS1 mod for FSO) is supported.
- Some FS mission features are unsupported, simplified or abstracted away:
  - Wings are defined using a single position argument; wing formation is fixed.
  - Turret weapons cannot be changed.
  - Briefing icon placement is simplified and uses top-down 2D grid and automatic camera placement.
  - Event chaining is not supported.
  - Branched campaigns are not supported.

## Example missions
- `missions/Demo_missions/` — Demo missions (FSIF feature showcase).

## Example campaigns
- `campaigns/Demo_campaigns/` — Demo campaign (FCIF feature showcase).
