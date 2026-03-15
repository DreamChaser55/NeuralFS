# NeuralFS

<p align="center">
  <img src="neuralfslogo.png" alt="NeuralFS Logo" />
</p>

NeuralFS is an AI agent framework that can write original campaigns for the Freespace Open (FSO) engine. It consists of three Roo Code/Kilo Code editor agents (LLM modes with a custom system prompt) and two specialized Python conversion scripts.

## Main Components

### FreeSpace Creative Writing Agent

This agent brainstorms and iteratively writes the campaign description in natural language, beginning with a basic idea, then writing a comprehensive reference document, plot outline and ending with detailed mission plans (scenarios).

### FSIF+FCIF Writing Agent

This agent takes the detailed mission plans written by the previous agent and converts them into an exact mission specification in a custom YAML-based intermediate mission format: *FreeSpace Intermediate File (FSIF)*. This format is much more concise than `.fs2` (the mission file format expected by FSO). `.fs2` files tend to be large, with lots of redundant fields and boilerplate. An AI agent directly creating the `.fs2` file would waste a lot of tokens and could quickly fill up its context window. Also, YAML is much more common in the LLM training data than `.fs2` files. This is why it is better to use a more concise and compact intermediate format.

The agent also writes the campaign definition file in a custom *FreeSpace Campaign Intermediate Format (FCIF)*. Similar to FSIF, FCIF is a concise YAML-based format that abstracts away the verbose `.fc2` syntax, making it easy for both humans and AI agents to define campaign structure, mission progression, starting loadouts, and branching logic.

This agent also adds FSO text coloring tags into the fiction viewer files written by the previous agent and checks them for issues using a small dedicated Python script.

### FSIF to FS2 Converter

A Python script then takes the intermediate FSIF representation of the mission and converts it into the FS2 format expected by FSO. During the conversion, the FSIF representation is extensively validated; if any errors are found, actionable error messages are printed to the console, so the AI agent can fix them and try again.

The Converter script has both command line interface suitable for use by AI agents, and GUI for use by humans.

If provided with Google Gemini or ElevenLabs API key, the Converter script can optionally generate voice files for briefings/messages/debriefings, using Gemini or ElevenLabs TTS API.

For details, see `\FSIF_to_FS2_Converter\README.md`.

### FCIF to FC2 Converter

A separate Python script converts campaign definition files from the FCIF format into the `.fc2` campaign format expected by FSO.
The converter validates the FCIF input using Pydantic, generates S-expression (SEXP) logic for mission progression (including conditional and unconditional branching), and writes the final `.fc2` file.

This converter script also has both interfaces: CLI suitable for use by AI agents and GUI for use by humans.

For details, see `\FCIF_to_FC2_Converter\README.md`.

### FSIF+FCIF Converting Agent

This agent automates the final step of the pipeline: generating the game-ready `.fs2` and `.fc2` files. It iteratively runs the FSIF to FS2 Converter on all `.fsif` mission files and the FCIF to FC2 Converter on the `.fcif` campaign file. If the converters report any errors, this agent autonomously analyzes the source files, applies the necessary fixes, and retries the conversion until all files are valid and successfully converted.

## Requirements
- Visual Studio Code
- Roo Code or Kilo Code extension
- Requirements of the FSIF to FS2 Converter: see `\FSIF_to_FS2_Converter\README.md`
- Requirements of the FCIF to FC2 Converter: see `\FCIF_to_FC2_Converter\README.md`

## Documentation
- `Documentation/index.md` — documentation home and index, navigation, and recommended reading order.
- `Freespace Bibles/` — Freespace universe Bibles (full and condensed version)

## Usage

### Phase 1: Creative Writing
1. Open the NeuralFS folder with Visual Studio Code. Roo Code or Kilo Code extension should automatically load the three AI agent definitions (defined in `.roomodes` and `.kilocodemodes` files).
2. Open the Roo Code or Kilo Code extension.
3. Select the "Freespace Creative Writing Agent" as the interaction mode.
4. Copy the initial prompt from `freespace creative writing agent prompt.txt`.
5. Add your campaign concept into the prompt. If you don't want the agent to work fully autonomously, delete the "Work autonomously." line (the agent will then ask for your approval after completing each significant phase of the work).
6. Send the prompt and wait until the FreeSpace Creative Writing Agent completes its work. Afterwards, there should be a new folder named after your campaign with the Campaign Bible and another folder inside containing detailed mission design documents in natural language. If there is any fiction viewer content, it should be in separate text files in the same folder, named according to this schema: 'missionname_story.txt'.

Note: Using AI for this phase is optional, of course. If you don't want to outsource your creativity to the AI, you can write your own Campaign Bible and mission design documents, then proceed to the next phase.

### Phase 2: FSIF and FCIF Writing
1. Start a new task in Roo Code/Kilo Code. Switch the interation mode to "FSIF+FCIF Writing Agent".
2. Copy the initial prompt from `fsif+fcif writing agent prompt.txt`.
3. Replace the "<campaign_folder>" string in the prompt with the name of the campaign folder created by the creative writing agent.
4. Send the prompt and wait until the Agent completes its work. Afterwards, there should be:
   - A new `/fsif/` folder inside your campaign folder, containing the `.fsif` files for all the missions.
   - A `.fcif` campaign definition file inside your campaign folder.

### Phase 3: Converting FSIF to FS2 and FCIF to FC2
1. Start a new task in Roo Code/Kilo Code. Switch the interation mode to "FSIF+FCIF Converting Agent".
2. Copy the initial prompt from `fsif+fcif converting agent prompt.txt`.
3. Replace the "<campaign_folder>" string in the prompt with the name of the campaign folder created by the creative writing agent.
4. Send the prompt and wait until the Agent completes its work. Afterwards, your campaign folder should contain:
   - `.fs2` mission files in the `/fsif/` subfolder (converted from the `.fsif` files).
   - A `.fc2` campaign file (converted from the `.fcif` file).
   - Optional: if you enabled voice generation, a `voice` folder will be created alongside the mission files.

Note: You can also use the GUI Converter for this phase, but then you have to copy the validator output log manually for the AI agent to fix any mistakes.

Recommended workflow: First, let the AI agent autonomously try to convert and fix the fsif files using the CLI converter (without voice generation). After all mistakes are fixed and the conversion proceeds smoothly, you can do a final conversion pass with the GUI converter and voice generation enabled.

### Phase 4: Final steps
1. Move the `.fs2` and `.fc2` files into your `/FSO/fsport-mediavps/data/missions/` folder.
2. If there are any fiction viewer files created by the first agent (located alongside the mission design documents, named as 'missionname_story.txt'), move them into your `/FSO/fsport-mediavps/data/fiction/` folder.
3. If you enabled voice generation, move the created `voice` folder to `/FSO/fsport-mediavps/data/`.
4. You can now play the campaign.

## Limitations
Currently, only FreeSpace Port (FS1 mod for FSO) is supported.

## Example missions
- `missions/Demo_missions/` — Demo missions (FSIF feature showcase).

## Example campaigns
- `campaigns/Demo_campaigns/` — Demo campaign (FCIF feature showcase).
