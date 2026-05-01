# Using NeuralFS with VS Code

This guide will walk you through the campaign creation process with NeuralFS using the VS Code agentic AI engine.

## Phase 1: Creative Writing
1. Open the NeuralFS folder with Visual Studio Code. Roo Code extension should automatically load the three AI agent definitions (defined in the `.roomodes` file).
2. Open the Roo Code extension.
3. Select the "Freespace Creative Writing Agent" as the interaction mode.
4. Copy the initial prompt from `VS Code prompts/freespace creative writing agent.txt` and paste it into Roo Code.
5. Add your campaign concept into the prompt. If you don't want the agent to work fully autonomously, delete the "Work autonomously." line (the agent will then ask for your approval after completing each significant phase of the work).
6. Send the prompt and wait until the FreeSpace Creative Writing Agent completes its work. Afterwards, there should be a new folder named after your campaign with the Campaign Bible and another folder inside containing detailed mission design documents in natural language. If there is any fiction viewer content, it should be in separate text files in the same folder, named according to this schema: 'missionname_story.txt'.

Note: Using AI for this phase is optional, of course. If you don't want to outsource your creativity to the AI, you can write your own Campaign Bible and mission design documents, then proceed to the next phase.

## Phase 2: FSIF and FCIF Writing and Converting
1. Start a new task in Roo Code. Switch the interation mode to "FSIF+FCIF Writing Agent".
2. Copy the initial prompt from `VS Code prompts/fsif+fcif writing agent.txt` and paste it into Roo Code.
3. Replace the "<campaign_folder>" string in the prompt with the name of the campaign folder created by the creative writing agent.
4. Send the prompt and wait until the Agent completes its work. Afterwards, there should be:
   - A new `/fsif/` folder inside your campaign folder, containing the `.fsif` files and converted `.fs2` files for all the missions.
   - A `.fcif` campaign definition file and a converted `.fc2` campaign file inside your campaign folder.

Note: You can optionally do a final conversion pass with the GUI Converter and voice generation enabled.

## Alternative Workflow: Editing Single Missions
If you want to edit an existing FSIF mission or create a single standalone mission without going through the full campaign creation process:
1. Start a new task in Roo Code. Switch the interaction mode to "Single FSIF Mission Editing Agent".
2. Copy the initial prompt from `VS Code prompts/single fsif mission editing agent.txt` and paste it into Roo Code.
3. Provide your instructions (e.g. what mission to edit and how, or the details for a new mission) at the end of the prompt.
4. Send the prompt and wait until the Agent completes its work. It will write the FSIF file and run it through the converter to validate it and convert it into `.fs2`.

## Phase 3: Final steps
1. Move the `.fs2` and `.fc2` files into your `/FSO/fsport-mediavps/data/missions/` folder.
2. If there are any fiction viewer files created by the first agent (located alongside the mission design documents, named as 'missionname_story.txt'), move them into your `/FSO/fsport-mediavps/data/fiction/` folder.
3. If you enabled voice generation, move the created `voice` folder to `/FSO/fsport-mediavps/data/`.
4. You can now play the campaign.
