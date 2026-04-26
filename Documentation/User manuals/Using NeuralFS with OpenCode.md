# Using NeuralFS with OpenCode

This guide will walk you through the campaign creation process with NeuralFS using the OpenCode agentic AI engine.

### Phase 1: Creative Writing
1. Open your terminal and navigate to the NeuralFS folder.
2. Start an OpenCode session by running `opencode`. OpenCode will automatically load the three AI agent definitions (defined in `opencode.json`).
3. Use the **Tab** key to switch to the "Freespace Creative Writing Agent".
4. Tell the agent about your campaign concept. If you want the agent to work fully autonomously, tell it to do so. The agent will then not ask for your approval after completing each significant phase of the work.
5. Send the prompt and wait until the FreeSpace Creative Writing Agent completes its work. Afterwards, there should be a new folder named after your campaign with the Campaign Bible and another folder inside containing detailed mission design documents in natural language. If there is any fiction viewer content, it should be in separate text files in the same folder, named according to this schema: 'missionname_story.txt'.

Note: Using AI for this phase is optional, of course. If you don't want to outsource your creativity to the AI, you can write your own Campaign Bible and mission design documents, then proceed to the next phase.

### Phase 2: FSIF and FCIF Writing and Converting
1. Start a new OpenCode session. Use the **Tab** key to switch to the "FSIF+FCIF Writing Agent".
2. Point the agent to the campaign folder created by the creative writing agent by mentioning it with '@' and ask it to write the fsif and fcif files based on the existing documents.
3. Send the prompt and wait until the Agent completes its work. Afterwards, there should be:
   - A new `/fsif/` folder inside your campaign folder, containing the `.fsif` files and converted `.fs2` files for all the missions.
   - A `.fcif` campaign definition file and a converted `.fc2` campaign file inside your campaign folder.

Note: You can optionally do a final conversion pass with the GUI Converter and voice generation enabled.

### Alternative Workflow: Editing Single Missions
If you want to edit an existing FSIF mission or create a single standalone mission without going through the full campaign creation process:
1. Start a new OpenCode session. Use the **Tab** key to switch to the "Single FSIF Mission Editing Agent".
2. Provide your instructions (e.g. what mission to edit and how, or the details for a new mission). You can point the agent to your notes using the `@` mention feature.
3. Send the prompt and wait until the Agent completes its work. It will write the FSIF file and run it through the converter to validate it.

### Phase 3: Final steps
1. Move the `.fs2` and `.fc2` files into your `/FSO/fsport-mediavps/data/missions/` folder.
2. If there are any fiction viewer files created by the first agent (located alongside the mission design documents, named as 'missionname_story.txt'), move them into your `/FSO/fsport-mediavps/data/fiction/` folder.
3. If you enabled voice generation, move the created `voice` folder to `/FSO/fsport-mediavps/data/`.
4. You can now play the campaign.
