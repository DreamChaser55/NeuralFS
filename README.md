# NeuralFS

<p align="center">
  <img src="neuralfslogo.png" alt="NeuralFS Logo" />
</p>

NeuralFS is an agentic AI framework that can create fully playable original campaigns for the FreeSpace Open (FSO) engine from text descriptions. It consists of three AI agents (LLMs with tool calling and custom system prompts) and two specialized Python conversion and validation scripts. NeuralFS supports two agentic AI engines:
- Visual Studio Code (using the Zoo Code extension)
- OpenCode

## Main Components

### AI Agents

#### FreeSpace Creative Writing Agent

This agent brainstorms and iteratively writes the campaign description in natural language, beginning with a basic idea, then producing a comprehensive reference document and a plot outline, and ending with detailed mission plans (scenarios).

#### FSIF+FCIF Writing Agent

This agent takes the detailed mission plans written by the previous agent and converts them into an exact mission specification in a custom YAML-based intermediate mission format: *FreeSpace Intermediate Format (FSIF)*. Why do we need an intermediate format?
- FSIF is much more concise than `.fs2` (the mission file format expected by FSO). `.fs2` files tend to be large, with many redundant fields and boilerplate sections; an AI agent directly creating the `.fs2` file would waste a lot of tokens and could quickly fill up its context window.
- YAML files are much more common in LLM training data than `.fs2` files.

This agent also writes the campaign definition file in a custom *FreeSpace Campaign Intermediate Format (FCIF)*. Similar to FSIF, FCIF is a concise YAML-based format that abstracts away the verbose `.fc2` syntax, making it easy for AI agents to define campaign structure, mission progression, starting loadouts, and mission success/failure logic.

The agent also adds FSO text-coloring tags to the fiction viewer files written by the previous agent and checks them for issues using a small dedicated Python script (Fiction Viewer Validator).

The agent follows a **Plan → Act** workflow that improves the performance of AI agents compared to simple immediate implementation workflows: for each mission, it first writes an implementation plan into the `<campaign_folder>/plans/` directory before writing the corresponding `.fsif` file. The plan captures mission metadata, entity lists, mission flow, SEXP strategy, and known risks, and serves as the implementation checklist while authoring the FSIF. After writing each `.fsif` or `.fcif` file, the agent runs it through the respective Python converter script to validate it. If the converter reports any errors or warnings, the agent autonomously analyzes the file, applies the necessary fixes, and retries the conversion until the file is valid and successfully converted to game-ready `.fs2` or `.fc2` formats.

#### Single FSIF Mission Editing Agent

This agent is intended to write or edit single FSIF missions or FCIF campaign files outside the existing NeuralFS campaign creation workflow. It allows users to quickly make changes to existing missions or create standalone missions without going through the full campaign authoring process. Similar to the FSIF+FCIF Writing Agent, it works with the FSIF and FCIF formats and runs the converter scripts to validate its work. You can think of this agent as a NeuralFS FRED alternative: for the first time, you can create a playable FreeSpace mission just by talking to your editor in plain English!

### Conversion Scripts

#### FSIF to FS2 Converter

A Python script that takes the intermediate FSIF representation of the mission and converts it into the FS2 format expected by FSO. During the conversion, the FSIF file is extensively validated; if any errors are found, actionable error messages are printed to the console so the AI agent can fix them and try again.

The converter provides both a command-line interface suitable for use by AI agents and a GUI for human users.

If provided with a Google Gemini, ElevenLabs, or Inworld API key, the converter can optionally generate voice files for briefings, messages, and debriefings using the respective TTS API.

For details, see `FSIF_to_FS2_Converter/README.md`.

#### FCIF to FC2 Converter

This Python script converts campaign definition files from the FCIF format into the `.fc2` campaign format expected by FSO.
The converter validates the FCIF input, generates S-expression (SEXP) logic for mission progression (success/failure conditions), and writes the final `.fc2` file.

This converter also provides both interfaces: a command-line interface suitable for use by AI agents and a GUI for human users.

For details, see `FCIF_to_FC2_Converter/README.md`.

## Requirements
- Python 3.9+
- One of these agentic AI engines:
  - Visual Studio Code with Zoo Code extension
  - OpenCode
- PyYAML
- pydantic

Optional (for TTS):
- `google-genai`
- `elevenlabs`
- `requests` (for Inworld TTS)

If you want to use TTS, you need to provide an API key for your chosen provider. The simplest option is to place a file named `Gemini_API_key.txt`, `Elevenlabs_API_key.txt`, or `Inworld_API_key.txt` (containing only your key) into the `API_keys` directory.

## Developer setup and tests

See `developer_setup.md` for virtual environment setup, dependency installation, test execution, and Python syntax checks.

## Documentation for AI agents
- `Documentation/index.md` — documentation home, index, navigation, and recommended reading order.
- `Freespace Bibles/` — FreeSpace universe Bibles (full and condensed version)

## Manuals for human users

Read the manual for your chosen agentic AI engine:
- `Documentation/User manuals/Using NeuralFS with VS Code.md`
- `Documentation/User manuals/Using NeuralFS with OpenCode.md`

## Limitations
- Currently, only FreeSpace Port (FS1 mod for FSO) is supported.
- Some FreeSpace mission features are unsupported, simplified, or abstracted away:
  - Wings are defined using a single position argument; wing formation is fixed. All ships in a wing are defined by a single ship template.
  - Turret weapons cannot be changed.
  - Briefing icon placement is simplified and uses a top-down 2D grid with automatic camera placement.
  - Event chaining is not supported.
  - only two ships can be docked to each other (daisy chained (multiple) ship docking is not supported)
  - Branched campaigns are not supported.
- I don't recommend creating campaigns longer than around 8 missions: this results in excessive token consumption and fills a large fraction of the agents' context windows, which reduces their intelligence. I recommend 6 missions as the default length.

## Example missions
- `missions/Demo_missions/` — Demo missions (FSIF feature showcase).

## Example campaigns
- `campaigns/Demo_campaigns/` — Demo campaign (FCIF feature showcase).
