# Using NeuralFS with VS Code

This guide will walk you through the campaign creation process with NeuralFS using the VS Code agentic AI engine.

## Phase 1: Creative Writing
1. Open the NeuralFS folder with Visual Studio Code. The Zoo Code extension should automatically load the three AI agent definitions (defined in the `.roomodes` file, because Zoo Code was originally called "Roo Code").
2. Open the Zoo Code extension.
3. Select the "Freespace Creative Writing Agent" as the interaction mode.
4. Copy the initial prompt from `VS Code prompts/freespace creative writing agent.txt` and paste it into Zoo Code.
5. Add your campaign concept to the prompt. If you don't want the agent to work fully autonomously, delete the "Work autonomously." line — the agent will then ask for your approval after completing each significant phase of the work.
6. Send the prompt and wait until the FreeSpace Creative Writing Agent finishes its work. When it is done, there should be a new folder named after your campaign, containing the Campaign Bible and another folder with detailed mission design documents in natural language. If there is any fiction viewer content, it will be in separate text files in the same folder, using the naming pattern `missionname_story.txt`.

Note: Using AI for this phase is optional. If you prefer to write your own Campaign Bible and mission design documents, you can skip this phase and proceed to the next one.

## Phase 2: FSIF and FCIF Writing and Converting
1. Start a new task in Zoo Code to clear the context window. Switch the interaction mode to "FSIF+FCIF Writing Agent".
2. Copy the initial prompt from `VS Code prompts/fsif+fcif writing agent.txt` and paste it into Zoo Code.
3. Replace the `<write_campaign_folder_name_here>` placeholder in the prompt with the name of the campaign folder created by the creative writing agent.
4. Send the prompt and wait until the agent finishes its work. When it is done, there should be:
   - A new `/plans/` folder inside your campaign folder, containing one per-mission implementation plan `.md` file per mission.
   - A new `/fsif/` folder inside your campaign folder, containing the `.fsif` files and converted `.fs2` files for all the missions.
   - A `.fcif` campaign definition file and a converted `.fc2` campaign file inside your campaign folder.

Note: You can optionally do a final conversion pass using the GUI converter with voice generation enabled.

## Alternative Workflow: Editing Single Missions
If you want to edit an existing FSIF mission or create a single standalone mission without going through the full campaign creation process:
1. Start a new task in Zoo Code. Switch the interaction mode to "Single FSIF Mission Editing Agent".
2. Copy the initial prompt from `VS Code prompts/single fsif mission editing agent.txt` and paste it into Zoo Code.
3. Provide your instructions (e.g. what mission to edit and how, or the details for a new mission) at the end of the prompt.
4. Send the prompt and wait until the agent finishes its work. It will write the FSIF file and run it through the converter to validate it and convert it to `.fs2`.

## Phase 3: Final Steps
1. Move the `.fs2` and `.fc2` files into your `/FSO/fsport-mediavps/data/missions/` folder.
2. If there are any fiction viewer files created by the first agent (located alongside the mission design documents, named as `missionname_story.txt`), move them into your `/FSO/fsport-mediavps/data/fiction/` folder.
3. If you enabled voice generation, move the created `voice` folder to `/FSO/fsport-mediavps/data/`.
4. You can now play the campaign.
