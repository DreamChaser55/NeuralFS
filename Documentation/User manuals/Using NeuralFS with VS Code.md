# Using NeuralFS with VS Code

This guide will walk you through the campaign creation process with NeuralFS using the VS Code agentic AI engine.

## Phase 1: Creative Writing
1. Open the NeuralFS folder with Visual Studio Code. Roo Code or Kilo Code extension should automatically load the three AI agent definitions (defined in `.roomodes` and `.kilocodemodes` files).
2. Open the Roo Code or Kilo Code extension.
3. Select the "Freespace Creative Writing Agent" as the interaction mode.
4. Copy the initial prompt from `VS Code prompts/freespace creative writing agent.txt`.
5. Add your campaign concept into the prompt. If you don't want the agent to work fully autonomously, delete the "Work autonomously." line (the agent will then ask for your approval after completing each significant phase of the work).
6. Send the prompt and wait until the FreeSpace Creative Writing Agent completes its work. Afterwards, there should be a new folder named after your campaign with the Campaign Bible and another folder inside containing detailed mission design documents in natural language. If there is any fiction viewer content, it should be in separate text files in the same folder, named according to this schema: 'missionname_story.txt'.

Note: Using AI for this phase is optional, of course. If you don't want to outsource your creativity to the AI, you can write your own Campaign Bible and mission design documents, then proceed to the next phase.

## Phase 2: FSIF and FCIF Writing
1. Start a new task in Roo Code/Kilo Code. Switch the interation mode to "FSIF+FCIF Writing Agent".
2. Copy the initial prompt from `VS Code prompts/fsif+fcif writing agent.txt`.
3. Replace the "<campaign_folder>" string in the prompt with the name of the campaign folder created by the creative writing agent.
4. Send the prompt and wait until the Agent completes its work. Afterwards, there should be:
   - A new `/fsif/` folder inside your campaign folder, containing the `.fsif` files for all the missions.
   - A `.fcif` campaign definition file inside your campaign folder.

## Phase 3: Converting FSIF to FS2 and FCIF to FC2
1. Start a new task in Roo Code/Kilo Code. Switch the interation mode to "FSIF+FCIF Converting Agent".
2. Copy the initial prompt from `VS Code prompts/fsif+fcif converting agent.txt`.
3. Replace the "<campaign_folder>" string in the prompt with the name of the campaign folder created by the creative writing agent.
4. Send the prompt and wait until the Agent completes its work. Afterwards, your campaign folder should contain:
   - `.fs2` mission files in the `/fsif/` subfolder (converted from the `.fsif` files).
   - A `.fc2` campaign file (converted from the `.fcif` file).
   - Optional: if you enabled voice generation, a `voice` folder will be created alongside the mission files.

Note: You can also use the GUI Converter for this phase, but then you have to copy the validator output log manually for the AI agent to fix any mistakes.

Recommended workflow: First, let the AI agent autonomously try to convert and fix the fsif files using the CLI converter (without voice generation). After all mistakes are fixed and the conversion proceeds smoothly, you can do a final conversion pass with the GUI converter and voice generation enabled.

## Phase 4: Final steps
1. Move the `.fs2` and `.fc2` files into your `/FSO/fsport-mediavps/data/missions/` folder.
2. If there are any fiction viewer files created by the first agent (located alongside the mission design documents, named as 'missionname_story.txt'), move them into your `/FSO/fsport-mediavps/data/fiction/` folder.
3. If you enabled voice generation, move the created `voice` folder to `/FSO/fsport-mediavps/data/`.
4. You can now play the campaign.
