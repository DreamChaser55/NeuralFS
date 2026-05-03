# fs_data.py
# Central repository for FSO token lists and allowed values.
# GENERATED FROM DOCUMENTATION. DO NOT EDIT MANUALLY.

from typing import Set

# Teams
ALLOWED_TEAMS = {'Friendly', 'Hostile', 'Unknown'}

# Message Priorities
ALLOWED_PRIORITIES = {'High', 'Low', 'Normal'}

# AI Classes
ALLOWED_AI_CLASSES = {'Captain', 'Colonel', 'Coward', 'General', 'Lieutenant', 'Major'}

# Music
ALLOWED_MUSIC_MISSION = {'1: Genesis', '2: Exodus', '3: Leviticus', '4: Numbers', '5: Deuteronomy', '6: Joshua', '7: Revelation', 'FS1-10: Darkside', 'FS1-1: Fortress', 'FS1-2: March', 'FS1-3: Chaser', 'FS1-4: Worlds Apart', 'FS1-5: Spook', 'FS1-6: Haunted', 'FS1-7: Marauder', 'FS1-8: Strike', 'FS1-9: Monolith', 'None'}

ALLOWED_MUSIC_BRIEFING = {'Brief1', 'Brief2', 'Brief3', 'Brief4', 'Brief5', 'Brief6', 'Brief7', 'FS1-BRIEF1', 'FS1-BRIEF2', 'FS1-BRIEF3', 'FS1-BRIEF4', 'FS1-BRIEF5', 'FS1-BRIEF6', 'FS1-BRIEF7', 'None'}

# Nebula Patterns (Full Nebula)
ALLOWED_NEBULA_PATTERNS = {'nbackblue', 'nbackblue1', 'nbackblue2', 'nbackcyan', 'nbackgreen', 'nbackorange', 'nbackpurp1', 'nbackpurp2', 'nbackred', 'nbackyellow', 'nblackblack'}

# Nebula Poofs (Full Nebula)
ALLOWED_NEBULA_POOFS = {'PoofGreen01', 'PoofGreen02', 'PoofPurp01', 'PoofPurp02', 'PoofRed01', 'PoofRed02'}

# Background Bitmaps - Suns
ALLOWED_SUNS = {'SunAdharaA', 'SunAdharaB', 'SunAlbireoAa', 'SunAlbireoAb', 'SunAlbireoB', 'SunAldebaranA', 'SunAldebaranB', 'SunAlphaAquilae', 'SunAlphaCentauriA', 'SunAlphaCentauriB', 'SunAlphaCrucisAa', 'SunAlphaCrucisAb', 'SunAlphardA', 'SunAlphardB', 'SunAntaresB', 'SunBetaAquilaeA', 'SunBetaAquilaeBa', 'SunBetaAquilaeBb', 'SunBetaHydri', 'SunBetelgeuse', 'SunBlue', 'SunCapellaA', 'SunCapellaB', 'SunCapellaC', 'SunDeltaSerpentis', 'SunGammaDraconis', 'SunGold', 'SunGreen', 'SunMintakaB', 'SunMintakaCa', 'SunMintakaCb', 'SunMirfak', 'SunNaos', 'SunPhiEridaniA', 'SunPhiEridaniB', 'SunPolarisAa', 'SunPolarisAb', 'SunPolarisB', 'SunProcyonA', 'SunProcyonB', 'SunRed', 'SunSiriusA', 'SunSiriusB', 'SunSol', 'SunVega', 'SunViolet', 'SunWhite'}

# Background Bitmaps - Planets
ALLOWED_PLANETS = {'Capella1', 'Capella1-1', 'Capella1-1b', 'Capella1b', 'Capella2', 'Capella2-1', 'Capella2-1b', 'Capella2b', 'Capella3', 'Capella3-1', 'Capella4', 'Capella4-1', 'planeta1', 'planetb', 'planetc', 'planetd', 'planete', 'planetf', 'planetg', 'planeth'}

# Background Bitmaps - Nebulae
ALLOWED_NEBULAE_BITMAPS = {'dneb01', 'dneb02', 'dneb03', 'dneb04', 'dneb05', 'dneb06', 'dneb07', 'dneb08', 'dneb09', 'dneb10', 'dneb11', 'dneb12', 'dneb13', 'dneb14', 'dneb15', 'dneb16', 'dneb17', 'dneb18', 'neb01', 'neb02', 'neb03', 'neb04', 'neb05', 'neb06', 'neb07', 'neb08', 'neb09', 'neb10', 'neb11', 'neb12', 'neb13', 'neb14', 'neb15', 'neb16', 'neb17', 'neb18'}

# Combined Backgrounds
ALLOWED_BACKGROUNDS = ALLOWED_SUNS | ALLOWED_PLANETS | ALLOWED_NEBULAE_BITMAPS

# Anchor Tokens (Wildcards)
ALLOWED_ANCHORS_TOKENS = {'#Command', '<any friendly player>', '<any friendly>', '<any hostile>', '<any unknown>', '<any wingman>'}

# Weapons - Primary
ALLOWED_PRIMARY_WEAPONS = {'Avenger', 'Banshee', 'D-Advanced', 'Disruptor', 'Flail', 'ML-16 Laser', 'Prometheus', 'Shivan Heavy Laser', 'Shivan Light Laser', 'Shivan Mega Laser', 'Shivan Uber Laser', 'Training', 'Vasudan Light Laser'}

# Weapons - Secondary
ALLOWED_SECONDARY_WEAPONS = {'Barracuda', 'D-Missile', 'D-Missile#Shivan', 'Enemy MX-50', 'Fang', 'Fury', 'Fury#Shivan', 'Harbinger', 'Harbinger#Shivan', 'Hornet', 'Hornet#Shivan', 'Interceptor', 'Interceptor#Shivan', 'MX-50', 'MX-50#Shivan', 'Phoenix V', 'Phoenix V#Shivan', 'Stiletto', 'Stiletto#Shivan', 'Synaptic', 'Synaptic#Shivan', 'Tsunami', 'Tsunami#Shivan', 'Unknown Bomb', 'Unknown Megabomb'}

# Combined Weapons
ALLOWED_WEAPONS = ALLOWED_PRIMARY_WEAPONS | ALLOWED_SECONDARY_WEAPONS

# --- 1. Spacecraft Classes ---
ALLOWED_SHIP_CLASSES = {'GTB Athena', 'GTB Medusa', 'GTB Ursa', 'GTB Zeus', 'GTC Fenris', 'GTC Leviathan', 'GTD Hades', 'GTD Orion', 'GTDr Amazon', 'GTDr Amazon Advanced', 'GTEP Hermes', 'GTF Apollo', 'GTF Hercules', 'GTF Loki', 'GTF Ulysses', 'GTF Valkyrie', 'GTFr Chronos', 'GTFr Poseidon', 'GTI Arcadia', 'GTS Centaur', 'GTSC Faustus', 'GTSG Cerberus', 'GTSG Watchdog', 'GTT Elysium', 'PVB Amun', 'PVB Osiris', 'PVC Aten', 'PVD Typhon', 'PVEP Ra', 'PVF Anubis', 'PVF Horus', 'PVF Seth', 'PVF Thoth', 'PVFr Bast', "PVFr Ma'at", 'PVFr Satis', 'PVI Karnak', 'PVS Scarab', 'PVSG Ankh', 'PVT Isis', 'SAC 2', 'SB Nephilim', 'SB Seraphim', 'SB Shaitan', 'SC 5', 'SC Cain', 'SC Lilith', 'SD Demon', 'SD Lucifer', 'SF Basilisk', 'SF Dragon', 'SF Manticore', 'SF Scorpion', 'SFr Asmodeus', 'SFr Mephisto', 'SSG Trident', 'ST Azrael', 'TAC 1', 'TC 2', 'TSC 2', 'TTC 1', 'Terran NavBuoy', 'VAC 4', 'VC 3'}

# --- 2. Dockpoints (Mapping Class -> Set of Points) ---
ALLOWED_DOCKPOINTS = {
    'GTB Athena': {'rearming dock'},
    'GTB Medusa': {'bomber dock'},
    'GTB Ursa': {'bomber dock'},
    'GTB Zeus': {'bomber dock'},
    'GTC Fenris': {'Docking bay 1', 'Docking bay 2'},
    'GTC Leviathan': {'Docking bay 1', 'Docking bay 2'},
    'GTD Hades': {'topside docking'},
    'GTD Orion': {'front docking bay'},
    'GTDr Amazon': {'blahblah'},
    'GTDr Amazon Advanced': {'bridge dock', 'cargo dockpoint'},
    'GTEP Hermes': {'blahblah'},
    'GTF Angel': {'fighter dock'},
    'GTF Apollo': {'rearming dock'},
    'GTF Hercules': {'fighter dock'},
    'GTF Loki': {'fighter dock'},
    'GTF Ulysses': {'rearming dock'},
    'GTF Valkyrie': {'fighter dock'},
    'GTFr Chronos': {'bridge dock', 'cargo dockpoint', 'topside dock'},
    'GTFr Poseidon': {'cargo dock', 'standard dockpoint'},
    'GTI Arcadia': {'Bigship docking', 'topside docking'},
    'GTS Centaur': {'lower ring', 'upper ring'},
    'GTSC Faustus': {'port docking', 'starboard docking'},
    'GTT Elysium': {'topside docking'},
    'GTT Hunter': {'left dock', 'rearming dock', 'right dock'},
    'PVB Amun': {'rearming dock'},
    'PVB Osiris': {'dock_1', 'dock_2'},
    'PVB Sekhmet': {'Fighter Dock'},
    'PVC Aten': {'main dock'},
    'PVD Typhon': {'topside dock'},
    'PVDr Jackal': {'Rearm Dock'},
    'PVEP Ra': {'blahblah'},
    'PVF Anubis': {'Reload'},
    'PVF Horus': {'Rearming Dock'},
    'PVF Seth': {'Rearming dock'},
    'PVF Thoth': {'blahblah'},
    'PVF Ulysses': {'rearming dock'},
    'PVFr Bast': {'cargo dock', 'dock_1'},
    "PVFr Ma'at": {'bridge dock', 'cargo dock'},
    'PVFr Satis': {'docking point'},
    'PVI Karnak': {'dock-bottom1', 'dock-bottom2', 'dock-bottom3', 'dock-top1', 'dock-top2', 'dock-top3'},
    'PVS Scarab': {'lower ring'},
    'PVSC Imhotep': {'main dock'},
    'PVT Isis': {'main dock'},
    'SAC 2': {'cargo dock01'},
    'SB Nahema': {'Bomber Dock'},
    'SB Nephilim': {'dock_1'},
    'SB Seraphim': {'dock_1'},
    'SB Shaitan': {'rearming dock'},
    'SC 5': {'cargo dock'},
    'SC Cain': {'main dock'},
    'SC Lilith': {'main dock'},
    'SF Basilisk': {'fighter dock'},
    'SF Dragon': {'dock_1'},
    'SF Gorgon': {'rearming dock'},
    'SF Manticore': {'rearming dock'},
    'SF Scorpion': {'rearming dock'},
    'SFr Asmodeus': {'blahblah', 'cargo dock01', 'dock_2', 'dock_3', 'dock_4'},
    'SFr Mephisto': {'cargo dock01', 'cargo dock02', 'cargo dock03', 'cargo dock04'},
    'ST Azrael': {'dockpoint 1'},
    'TAC 1': {'cargo dockpoint'},
    'TC 2': {'cargo dock'},
    'TSC 2': {'cargo dock'},
    'TTC 1': {'cargo dock01'},
    'Terran Asteroid Base': {'blahblah'},
    'VAC 4': {'cargo dock'},
    'VC 3': {'cargo dock'},
    'Vasudan Asteroid Base': {'bottom dock', 'topside docking'},
    'Vasudan Probe': {'dock_1'},
}

# --- 3. Subsystems (Mapping Class -> Set of Subsystems) ---
# Note: "Pilot" is virtual and always allowed, handled separately in logic.
# Only listing critical subsystems typically targeted by SEXPs.
ALLOWED_SUBSYSTEMS = {
    'GTB Athena': {'communications', 'engine 1', 'engine 2', 'navigation', 'sensors', 'weapons'},
    'GTB Medusa': {'communications', 'engine', 'navigation', 'sensors', 'turret01a', 'weapons'},
    'GTB Ursa': {'b05-turreta', 'communications', 'engine', 'navigation', 'sensors', 'weapons'},
    'GTB Zeus': {'communications', 'engine', 'navigation', 'sensors', 'weapons'},
    'GTC Fenris': {'communication', 'engine', 'navigation', 'radar01a-dish', 'sensors', 'turret01', 'turret02', 'turret03', 'turret04', 'turret05', 'turret06', 'turret07', 'turret08', 'turret09a-01-main', 'weapons'},
    'GTC Leviathan': {'communication', 'engine', 'navigation', 'radar01a-dish', 'sensors', 'turret01', 'turret02', 'turret03', 'turret04', 'turret05', 'turret06', 'turret07', 'turret08', 'turret09a-01-main', 'weapons'},
    'GTD Hades': {'Enginesdownright', 'communication', 'engines', 'enginesdownleft', 'enginesupleft', 'enginesupright', 'fighterbay', 'navigation', 'sensors', 'turret01a', 'turret02a', 'turret03a', 'turret04a', 'turret05a', 'turret06a', 'turret07a', 'turret08', 'turret09', 'turret10', 'turret11', 'turret12', 'turret13', 'turret14', 'turret15', 'turret16', 'turret17', 'turret18', 'turret19', 'turret20', 'turret21', 'turret22', 'weapons'},
    'GTD Orion': {'RadarDish01', 'RadarDish02', 'RadarDish03', 'communication', 'engines', 'fighterbay', 'navigation', 'sensors', 'turret01a', 'turret02a', 'turret03a', 'turret04a', 'turret05a', 'turret06', 'turret07', 'turret08', 'turret09', 'turret10', 'turret11', 'turret12', 'turret13', 'turret14', 'turret15', 'turret16', 'weapons'},
    'GTDr Amazon': {'communications', 'engine', 'navigation', 'sensors', 'weapons'},
    'GTDr Amazon Advanced': {'communication', 'engine', 'sensors', 'weapons'},
    'GTEP Hermes': {'engine'},
    'GTF Angel': {'communication', 'engine', 'navigation', 'sensors', 'weapons'},
    'GTF Apollo': {'communications', 'engine', 'navigation', 'sensors', 'weapons'},
    'GTF Hercules': {'communications', 'engine', 'navigation', 'sensors', 'weapons'},
    'GTF Loki': {'communications', 'engine', 'navigation', 'sensors', 'weapons'},
    'GTF Ulysses': {'communication', 'engines', 'navigation', 'sensors', 'weapons'},
    'GTF Valkyrie': {'communication', 'engine', 'navigation', 'sensors', 'weapons'},
    'GTFr Chronos': {'bridge', 'communication', 'engine 1', 'engine 2', 'engine 3', 'navigation', 'sensors', 'turreta', 'weapons'},
    'GTFr Poseidon': {'communication', 'engine', 'navigation', 'sensors', 'turret01', 'turret02', 'turret03', 'turret04', 'weapons'},
    'GTI Arcadia': {'RadarDish01', 'communication', 'fighterbay', 'sensors', 'turret01', 'turret02', 'turret03', 'turret04', 'turret05', 'turret06', 'turret07', 'turret08', 'turret09', 'turret10', 'turret11', 'turret12', 'turret13', 'turret14', 'turret15', 'turret16', 'turret17', 'turret18', 'turret19', 'turret20', 'turret21', 'turret22', 'turret23', 'turret24', 'weapons'},
    'GTS Centaur': {'communication', 'engines', 'sensors'},
    'GTSC Faustus': {'communication', 'engine', 'navigation', 'science01a-solar1', 'sensors', 'turret01', 'turret02', 'turret03', 'turret04', 'turret05', 'turret06', 'weapons'},
    'GTSG Cerberus': {'turret01a', 'turret02a'},
    'GTSG Watchdog': {'turret01a', 'turret02a'},
    'GTT Elysium': {'communication', 'engine', 'navigation', 'sensors', 'turret01', 'weapons'},
    'GTT Hunter': {'communication', 'engine', 'navigation', 'sensors', 'turret01', 'turret02', 'weapons'},
    'PVB Amun': {'communication', 'engine', 'navigation', 'sensors', 'turret01', 'turret02', 'weapons'},
    'PVB Osiris': {'communication', 'engine', 'navigation', 'sensors', 'turret01', 'turret02', 'weapons'},
    'PVB Sekhmet': {'communications', 'engine', 'navigation', 'sensors', 'weapons'},
    'PVC Aten': {'communications', 'engine', 'navigation', 'sensors', 'turret01a', 'turret02a', 'turret03', 'turret04', 'turret05', 'turret06', 'weapons'},
    'PVD Typhon': {'communication', 'engine', 'fighterbay 1', 'fighterbay 2', 'navigation', 'sensors', 'turret01', 'turret02', 'turret03', 'turret04', 'turret05', 'turret06', 'turret07', 'turret08', 'turret09', 'turret10', 'turret11', 'turret12', 'turret13', 'turret14', 'turret15', 'weapons'},
    'PVDr Jackal': {'communication', 'engine', 'navigation', 'sensors', 'weapons'},
    'PVEP Ra': {'engine'},
    'PVF Anubis': {'communication', 'engine', 'navigation', 'sensors', 'weapons'},
    'PVF Horus': {'communications', 'engine', 'navigation', 'sensors', 'weapons'},
    'PVF Seth': {'communications', 'engine 1', 'navigation', 'sensors', 'weapons'},
    'PVF Thoth': {'communications', 'engine', 'navigation', 'sensors', 'weapons'},
    'PVF Ulysses': {'communication', 'engines', 'navigation', 'sensors', 'weapons'},
    'PVFr Bast': {'communication', 'engines', 'navigation', 'sensors'},
    "PVFr Ma'at": {'communication', 'engine', 'navigation', 'sensors', 'turret01', 'turret02', 'turret03', 'weapons'},
    'PVFr Satis': {'communication', 'engine', 'navigation', 'sensors', 'turret01-main', 'turret02', 'turret03', 'turret04', 'turret05', 'weapons'},
    'PVI Karnak': {'Door-in1', 'Door-in2', 'Door-in3', 'Door-out1', 'Door-out2', 'Door-out3', 'bridge', 'communications', 'fighterbay01', 'fighterbay02', 'fighterbay03', 'sensors', 'turret01', 'turret02', 'turret03', 'turret04', 'turret05', 'turret06', 'turret07', 'turret08', 'turret09', 'turret10', 'turret11', 'turret12', 'turret13', 'turret14', 'turret15', 'turret16', 'turret17', 'turret18', 'turret19', 'turret20', 'turret21', 'turret22', 'turret23', 'turret24', 'turret25', 'turret26', 'turret27', 'turret28', 'turret29', 'turret30', 'turret31', 'turret32', 'turret33', 'turret34', 'turret35', 'turret36', 'turret37', 'turret38', 'weapons'},
    'PVS Scarab': {'communication', 'engines', 'sensors'},
    'PVSC Imhotep': {'communications', 'engine', 'fighterbay', 'navigation', 'sensors', 'turret01', 'turret02', 'turret03', 'turret04', 'turret05', 'weapons'},
    'PVSG Ankh': {'turret01a', 'turret02a'},
    'PVT Isis': {'communication', 'engine', 'navigation', 'sensors', 'turret01', 'turret02', 'weapons'},
    'SB Nahema': {'communications', 'engine', 'navigation', 'sensors', 'weapons'},
    'SB Nephilim': {'communication', 'engine', 'navigation', 'sensors', 'turret01', 'turret02', 'weapons'},
    'SB Seraphim': {'communication', 'engine', 'navigation', 'sensors', 'turret01', 'turret02', 'weapons'},
    'SB Shaitan': {'communication', 'engine', 'navigation', 'sensors', 'weapons'},
    'SC Cain': {'communication', 'engine', 'navigation', 'sensors', 'turret01', 'turret02', 'turret03', 'turret04', 'turret05', 'turret06', 'turret07', 'turret08', 'turret09', 'weapons'},
    'SC Lilith': {'communication', 'engine', 'navigation', 'sensors', 'turret01', 'turret02', 'turret03', 'turret04', 'turret05', 'turret06', 'turret07', 'turret08', 'turret09', 'weapons'},
    'SD Demon': {'communication', 'engine', 'fighterbay 1', 'fighterbay 2', 'navigation', 'sensors', 'turret01-base', 'turret02-base', 'turret03a-base', 'turret04-base', 'turret05-base', 'turret06a-base', 'turret07a-base', 'turret08-base', 'turret09-base', 'turret10-base', 'turret11-base', 'turret12-base', 'turret13-base', 'turret14-base', 'turret15-base', 'turret16-base', 'turret17-base', 'turret18-base', 'turret19-base', 'turret20-base', 'turret21-base', 'turret22', 'turret23', 'turret24', 'turret25', 'turret26', 'weapons'},
    'SD Lucifer': {'communication', 'engine 1', 'engine 2', 'fighterbay 1', 'fighterbay 2', 'navigation', 'reactor 1', 'reactor 2', 'reactor 3', 'reactor 4', 'reactor 5', 'sensors', 'turret01', 'turret02', 'turret03', 'turret04', 'turret05', 'turret06', 'turret07', 'turret08', 'turret09', 'turret10', 'turret11', 'turret12', 'turret13', 'turret14', 'turret15', 'turret16', 'turret17', 'weapons'},
    'SF Basilisk': {'communications', 'engine', 'navigation', 'sensors', 'weapons'},
    'SF Dragon': {'communication', 'engine', 'navigation', 'sensors', 'weapons'},
    'SF Dragon#Terrans': {'communication', 'engine', 'navigation', 'sensors', 'weapons'},
    'SF Gorgon': {'communications', 'engine', 'navigation', 'sensors', 'weapons'},
    'SF Manticore': {'communications', 'engine', 'navigation', 'sensors', 'weapons'},
    'SF Scorpion': {'communication', 'engine', 'navigation', 'sensors', 'weapons'},
    'SFr Asmodeus': {'a-turret01', 'a-turret02', 'a-turret03', 'a-turret04', 'communications', 'engine', 'navigation', 'sensors', 'weapons'},
    'SFr Mephisto': {'communication', 'engine', 'navigation', 'sensors', 'turret01', 'turret02', 'turret03', 'turret04', 'weapons'},
    'SSG Trident': {'turret01a', 'turret02a'},
    'ST Azrael': {'communications', 'engine', 'navigation', 'sensors', 'turret01a', 'turret02a', 'turret03a', 'weapons'},
    'Terran Asteroid Base': {'Asteroid01a', 'Asteroid02a', 'bunker01a', 'bunker02a', 'communications', 'comtowera', 'engine01a', 'engine02a', 'engine03', 'engine04', 'engine05', 'fighterbaya', 'navigation', 'sensors', 'turret01', 'turret02', 'turret03', 'turret04', 'turret05', 'turret06', 'turret07', 'turret08', 'turret09', 'turret10', 'turret11', 'turret12', 'turret13', 'turret14', 'turret15', 'turret16', 'turret17', 'turret18', 'turret19', 'turret20', 'turret21a', 'turret22a', 'turret23a', 'turret24a', 'turret25a', 'turret26a', 'turret27a', 'turret28', 'turret29', 'turret30', 'turret31', 'turret32', 'turret33', 'turret34', 'turret35', 'turret36', 'turret37', 'turret38', 'turret39', 'turret40', 'weapons'},
    'Vasudan Asteroid Base': {'array', 'communications', 'fighterbay', 'sensors', 'turret01', 'turret02', 'turret03', 'turret04', 'turret05', 'turret06', 'turret07', 'turret08', 'turret09', 'turret10', 'turret11', 'turret12', 'weapons'},
    'Vasudan Probe': {'communication', 'engine', 'navigation', 'sensors'},
}

# --- 4. SEXP Operators ---
# Exhaustive list of standard FSO/Retail SEXP operators.
ALLOWED_SEXP_OPERATORS = {'!=', '*', '+', '-', '/', '<', '<=', '=', '>', '>=', 'Abort rearm', 'Attack Target', 'Capture Target', 'Cover me', 'Depart', 'Destroy Subsystem', 'Disable Target', 'Disarm Target', 'Engage Enemy', 'Form on my wing', 'Ignore Target', 'Protect Target', 'Rearm me', 'abort-rearm', 'abs', 'activate-glow-maps', 'activate-glow-point-bank', 'activate-glow-points', 'add-background-bitmap', 'add-background-bitmap-new', 'add-goal', 'add-nav-ship', 'add-nav-waypoint', 'add-remove-escort', 'add-remove-hotkey', 'add-sun-bitmap', 'add-sun-bitmap-new', 'add-to-collision-group', 'add-to-collision-group-new', 'add-to-list', 'add-to-map', 'adjust-audio-volume', 'afterburner-energy-pct', 'ai-chase', 'ai-chase-any', 'ai-chase-ship-class', 'ai-chase-ship-type', 'ai-chase-wing', 'ai-destroy-subsystem', 'ai-disable-ship', 'ai-disable-ship-tactical', 'ai-disarm-ship', 'ai-disarm-ship-tactical', 'ai-dock', 'ai-evade-ship', 'ai-fly-to-ship', 'ai-form-on-wing', 'ai-guard', 'ai-ignore', 'ai-ignore-new', 'ai-keep-safe-distance', 'ai-play-dead', 'ai-play-dead-persistent', 'ai-rearm-repair', 'ai-stay-near-ship', 'ai-stay-still', 'ai-undock', 'ai-warp-out', 'ai-waypoints', 'ai-waypoints-once', 'allow-ship', 'allow-treason', 'allow-warp', 'allow-weapon', 'alter-ship-flag', 'alter-wing-flag', 'and', 'and-in-sequence', 'angle-facing-object', 'angle-vectors', 'any-of', 'apply-container-filter', 'are-ship-flags-set', 'are-waypoints-done-delay', 'are-wing-flags-set', 'avg', 'awacs-set-radius', 'bad-rearm-time', 'beam-create', 'beam-free', 'beam-free-all', 'beam-lock', 'beam-lock-all', 'beam-protect-ship', 'beam-unprotect-ship', 'bitwise-and', 'bitwise-not', 'bitwise-or', 'bitwise-xor', 'break-warp', 'call-ssm-strike', 'cancel-future-waves', 'cap-subsys-cargo-known-delay', 'cap-waypoint-speed', 'cargo-no-deplete', 'change-ai-class', 'change-background', 'change-iff', 'change-iff-color', 'change-player-score', 'change-ship-class', 'change-soundtrack', 'change-subsystem-name', 'change-team-color', 'change-team-score', 'clear-container', 'clear-debris', 'clear-goals', 'clear-subtitles', 'clear-weapons', 'close-sound-from-file', 'collide-invisible', 'config-asteroid-field', 'config-debris-field', 'config-field-targets', 'copy-container', 'copy-variable-between-indexes', 'copy-variable-from-index', 'create-bolt', 'current-speed', 'damaged-escort-priority', 'damaged-escort-priority-all', 'deactivate-glow-maps', 'deactivate-glow-point-bank', 'deactivate-glow-points', 'debug', 'del-nav', 'depart-node-delay', 'destroy-instantly', 'destroy-instantly-with-debris', 'destroy-subsys-instantly', 'destroyed-or-departed-delay', 'directive-value', 'disable-builtin-messages', 'disable-ets', 'distance', 'distance-bbox-to-subsystem', 'distance-center-to-subsystem', 'distance-to-bbox', 'distance-to-center', 'distance-to-nav', 'do-for-valid-arguments', 'do-nothing', "don't-collide-invisible", 'enable-builtin-messages', 'enable-ets', 'enable-general-orders', 'end-campaign', 'end-mission', 'engine-recharge-pct', 'every-of', 'every-time', 'every-time-argument', 'exchange-cargo', 'explosion-effect', 'facing', 'facing-waypoint', 'fade-in', 'fade-out', 'false', 'field-set-damage-type', 'fire-beam', 'fire-beam-at-coordinates', 'first-of', 'fix-warp', 'flash-hud-gauge', 'for-container-data', 'for-counter', 'for-map-container-keys', 'for-players', 'for-ship-class', 'for-ship-species', 'for-ship-team', 'for-ship-type', 'for-subsystems', 'force-glide', 'force-jump', 'force-rearm', 'free-rotating-subsystem', 'free-translating-subsystem', 'friendly-stealth-invisible', 'friendly-stealth-visible', 'functional-if-then-else', 'functional-switch', 'functional-when', 'get-collision-group', 'get-container-size', 'get-damage-caused', 'get-ets-value', 'get-fov', 'get-hotkey', 'get-map-keys', 'get-num-countermeasures', 'get-object-bank', 'get-object-heading', 'get-object-pitch', 'get-object-speed-x', 'get-object-speed-y', 'get-object-speed-z', 'get-object-x', 'get-object-y', 'get-object-z', 'get-power-output', 'get-primary-ammo', 'get-secondary-ammo', 'get-throttle-speed', 'get-variable-by-index', 'goals', 'good-primary-time', 'good-rearm-time', 'good-secondary-time', 'grant-medal', 'grant-promotion', 'has-armor-type', 'has-arrived-delay', 'has-been-tagged-delay', 'has-departed-delay', 'has-docked-delay', 'has-primary-weapon', 'has-secondary-weapon', 'has-time-elapsed', 'has-time-elapsed-msecs', 'has-undocked-delay', 'hide-jumpnode', 'hide-nav', 'hits-left', 'hits-left-subsystem', 'hits-left-subsystem-generic', 'hits-left-subsystem-specific', 'hud-activate-gauge-type', 'hud-clear-messages', 'hud-disable', 'hud-disable-except-messages', 'hud-display-gauge', 'hud-force-emp-effect', 'hud-force-sensor-static', 'hud-gauge-set-active', 'hud-set-builtin-gauge-active', 'hud-set-color', 'hud-set-coords', 'hud-set-custom-gauge-active', 'hud-set-directive', 'hud-set-frame', 'hud-set-max-targeting-range', 'hud-set-message', 'hud-set-text', 'hud-set-text-num', 'if-then-else', 'ignore-key', 'in-sequence', 'int-to-string', 'invalidate-all-arguments', 'invalidate-argument', 'invalidate-goal', 'is-ai-class', 'is-bit-set', 'is-cargo', 'is-cargo-known-delay', 'is-container-empty', 'is-destroyed-delay', 'is-disabled-delay', 'is-disarmed-delay', 'is-docked', 'is-event-false-delay', 'is-event-false-msecs-delay', 'is-event-incomplete', 'is-event-true-delay', 'is-event-true-msecs-delay', 'is-facing', 'is-friendly-stealth-visible', 'is-goal-false-delay', 'is-goal-incomplete', 'is-goal-true-delay', 'is-iff', 'is-in-box', 'is-in-mission', 'is-in-turret-fov', 'is-language', 'is-nan', 'is-nav-linked', 'is-nav-visited', 'is-player', 'is-previous-event-false', 'is-previous-event-true', 'is-previous-goal-false', 'is-previous-goal-true', 'is-primary-selected', 'is-secondary-selected', 'is-ship-class', 'is-ship-emp-active', 'is-ship-stealthy', 'is-ship-type', 'is-ship-visible', 'is-species', 'is-subsystem-destroyed-delay', 'is_tagged', 'jettison-cargo', 'jettison-cargo-delay', 'kamikaze', 'key-pressed', 'key-reset', 'key-reset-multiple', 'list-data-index', 'list-has-data', 'lock-afterburner', 'lock-perspective', 'lock-primary-weapon', 'lock-rotating-subsystem', 'lock-secondary-weapon', 'lock-translating-subsystem', 'map-has-data-item', 'map-has-key', 'max', 'min', 'missile-locked', 'mission-set-nebula', 'mission-set-subspace', 'mission-time', 'mission-time-msecs', 'mod', 'modify-variable', 'modify-variable-xstr', 'multi-eval', 'nan-to-number', 'nebula-change-fog-color', 'nebula-change-pattern', 'nebula-change-storm', 'nebula-fade-poof', 'nebula-toggle-poof', 'never-warp', 'node-targeted', 'not', 'num-players', 'num-ships-in-battle', 'num-ships-in-wing', 'num-valid-arguments', 'num-within-box', 'num_assists', 'num_class_kills', 'num_kills', 'num_type_kills', 'number-of', 'on-mission-skip', 'or', 'order', 'path-flown', 'pause-sound-from-file', 'percent-ships-arrived', 'percent-ships-departed', 'percent-ships-destroyed', 'percent-ships-disabled', 'percent-ships-disarmed', 'percent-ships-scanned', 'perform-actions-bool-first', 'perform-actions-bool-last', 'play-sound-from-file', 'play-sound-from-table', 'player-is-cheating', 'player-not-use-ai', 'player-use-ai', 'pow', 'primaries-depleted', 'primary-ammo-pct', 'primary-fired-since', 'primitive-sensors-set-range', 'protect-ship', 'query-orders', 'rand', 'rand-multiple', 'random-multiple-of', 'random-of', 'red-alert', 'remove-background-bitmap', 'remove-from-collision-group', 'remove-from-collision-group-new', 'remove-from-list', 'remove-from-map', 'remove-goal', 'remove-sun-bitmap', 'repair-subsystem', 'replace-skybox-texture', 'replace-texture', 'reset-camera', 'reset-event', 'reset-fov', 'reset-goal', 'reset-orders', 'reset-post-effects', 'reset-time-compression', 'respawns-left', 'restrict-nav', 'reverse-rotating-subsystem', 'reverse-translating-subsystem', 'rotating-subsys-set-turn-time', 'sabotage-subsystem', 'scramble-messages', 'script-eval', 'script-eval-block', 'script-eval-bool', 'script-eval-num', 'script-eval-string', 'secondaries-depleted', 'secondary-ammo-pct', 'secondary-fired-since', 'select-nav', 'self-destruct', 'send-builtin-message', 'send-message', 'send-message-chain', 'send-message-list', 'send-random-message', 'set-afterburner-energy', 'set-alpha-multiplier', 'set-ambient-light', 'set-armor-type', 'set-arrival-info', 'set-asteroid-field', 'set-bit', 'set-camera', 'set-camera-facing', 'set-camera-facing-object', 'set-camera-fov', 'set-camera-host', 'set-camera-position', 'set-camera-rotation', 'set-camera-shudder', 'set-camera-target', 'set-cargo', 'set-cutscene-bars', 'set-death-message', 'set-debriefing-persona', 'set-debriefing-toggled', 'set-debris-field', 'set-departure-info', 'set-docked', 'set-ets-values', 'set-explosion-option', 'set-fov', 'set-friendly-damage-caps', 'set-gravity-accel', 'set-hud-timer-padding', 'set-immobile', 'set-jumpnode-color', 'set-jumpnode-display-name', 'set-jumpnode-model', 'set-jumpnode-name', 'set-mission-mood', 'set-mobile', 'set-motion-debris', 'set-motion-debris-override', 'set-nav-carry', 'set-nav-color', 'set-nav-needslink', 'set-nav-visited', 'set-nav-visited-color', 'set-num-countermeasures', 'set-object-facing', 'set-object-facing-object', 'set-object-orientation', 'set-object-position', 'set-object-speed-x', 'set-object-speed-y', 'set-object-speed-z', 'set-order-allowed-for-target', 'set-persona', 'set-player-orders', 'set-player-throttle-speed', 'set-post-effect', 'set-primary-ammo', 'set-primary-weapon', 'set-respawns', 'set-scanned', 'set-secondary-ammo', 'set-secondary-weapon', 'set-shield-energy', 'set-skybox-alpha', 'set-skybox-model', 'set-skybox-orientation', 'set-sound-environment', 'set-subspace-drive', 'set-subsystem-strength', 'set-support-ship', 'set-thrusters-status', 'set-time-compression', 'set-training-context-fly-path', 'set-training-context-speed', 'set-traitor-override', 'set-unscanned', 'set-variable-by-index', 'set-weapon-energy', 'set-wing-formation', 'shield-quad-low', 'shield-recharge-pct', 'shields-left', 'shields-off', 'shields-on', 'ship-change-alt-name', 'ship-change-callsign', 'ship-copy-damage', 'ship-create', 'ship-deaths', 'ship-effect', 'ship-guardian', 'ship-guardian-threshold', 'ship-invisible', 'ship-invulnerable', 'ship-lat-maneuver', 'ship-maneuver', 'ship-no-guardian', 'ship-no-vaporize', 'ship-rot-maneuver', 'ship-set-damage-type', 'ship-set-shockwave-damage-type', 'ship-stealthy', 'ship-subsys-guardian-threshold', 'ship-subsys-ignore_if_dead', 'ship-subsys-no-live-debris', 'ship-subsys-no-replace', 'ship-subsys-targetable', 'ship-subsys-untargetable', 'ship-subsys-vanish', 'ship-tag', 'ship-targetable-as-bomb', 'ship-turret-target-order', 'ship-type-destroyed', 'ship-unstealthy', 'ship-untag', 'ship-untargetable-as-bomb', 'ship-vanish', 'ship-vaporize', 'ship-visible', 'ship-vulnerable', 'ship_score', 'show-jumpnode', 'show-subtitle', 'show-subtitle-image', 'show-subtitle-text', 'signum', 'sim-hits-left', 'skill-level-at-least', 'special-check', 'special-warp-dist', 'special-warpout-name', 'speed', 'stop-looping-animation', 'string-concatenate', 'string-concatenate-block', 'string-equals', 'string-get-length', 'string-get-substring', 'string-greater-than', 'string-less-than', 'string-set-substring', 'string-to-int', 'subsys-set-random', 'supernova-start', 'supernova-stop', 'switch', 'targeted', 'team-score', 'tech-add-intel', 'tech-add-intel-xstr', 'tech-add-ships', 'tech-add-weapons', 'tech-remove-intel', 'tech-remove-intel-xstr', 'tech-reset-to-default', 'time-docked', 'time-elapsed-last-order', 'time-ship-arrived', 'time-ship-departed', 'time-ship-destroyed', 'time-to-goal', 'time-undocked', 'time-wing-arrived', 'time-wing-departed', 'time-wing-destroyed', 'toggle-asteroid-field', 'training-msg', 'transfer-cargo', 'translating-subsys-set-speed', 'trigger-ship-animation', 'trigger-submodel-animation', 'true', 'turret-change-weapon', 'turret-clear-forced-target', 'turret-fired-since', 'turret-free', 'turret-free-all', 'turret-get-primary-ammo', 'turret-get-secondary-ammo', 'turret-has-primary-weapon', 'turret-has-secondary-weapon', 'turret-lock', 'turret-lock-all', 'turret-protect-ship', 'turret-set-direction-preference', 'turret-set-forced-subsys-target', 'turret-set-forced-target', 'turret-set-inaccuracy', 'turret-set-optimum-range', 'turret-set-primary-ammo', 'turret-set-rate-of-fire', 'turret-set-secondary-ammo', 'turret-set-target-order', 'turret-set-target-priorities', 'turret-subsys-target-disable', 'turret-subsys-target-enable', 'turret-tagged-clear', 'turret-tagged-clear-specific', 'turret-tagged-only', 'turret-tagged-specific', 'turret-unprotect-ship', 'unhide-nav', 'unlock-afterburner', 'unlock-primary-weapon', 'unlock-secondary-weapon', 'unprotect-ship', 'unrestrict-nav', 'unscramble-messages', 'unselect-nav', 'unset-bit', 'unset-cutscene-bars', 'unset-nav-carry', 'unset-nav-needslink', 'unset-nav-visited', 'update-moveable-animation', 'update-sound-environment', 'use-autopilot', 'use-nav-cinematics', 'used-cheat', 'validate-all-arguments', 'validate-argument', 'validate-general-orders', 'validate-goal', 'volumetrics-toggle', 'warp-effect', 'was-destroyed-by-delay', 'was-medal-granted', 'was-promotion-granted', 'waypoint-missed', 'waypoint-twice', 'weapon-create', 'weapon-energy-pct', 'weapon-recharge-pct', 'weapon-set-damage-type', 'when', 'when-argument', 'xor'}

# --- 5. Voices ---
ALLOWED_VOICES_GOOGLE = {'Achernar', 'Achird', 'Algenib', 'Algieba', 'Alnilam', 'Aoede', 'Autonoe', 'Callirrhoe', 'Charon', 'Despina', 'Enceladus', 'Erinome', 'Fenrir', 'Gacrux', 'Iapetus', 'Kore', 'Laomedeia', 'Leda', 'Orus', 'Puck', 'Pulcherrima', 'Rasalgethi', 'Sadachbia', 'Sadaltager', 'Schedar', 'Sulafat', 'Umbriel', 'Vindemiatrix', 'Zephyr', 'Zubenelgenubi'}
ALLOWED_VOICES_ELEVENLABS = {'Adam', 'Arnold', 'Bella', 'Brian', 'Callum', 'Charlie', 'Charlotte', 'Daniel', 'Dorothy', 'Elli', 'Emily', 'Freya', 'George', 'Harry', 'James', 'Josh', 'Lily', 'Matilda', 'Nicole', 'Rachel', 'Ryan', 'Sam', 'Sarah', 'Serena', 'Thomas'}
ALLOWED_VOICES_INWORLD = {'Abby', 'Alex', 'Amina', 'Anjali', 'Arjun', 'Ashley', 'Avery', 'Bianca', 'Blake', 'Brandon', 'Brian', 'Callum', 'Carter', 'Cedric', 'Celeste', 'Chloe', 'Claire', 'Clive', 'Conrad', 'Craig', 'Damon', 'Darlene', 'Deborah', 'Dennis', 'Derek', 'Dominus', 'Duncan', 'Edward', 'Eleanor', 'Elizabeth', 'Elliot', 'Ethan', 'Evan', 'Evelyn', 'Felix', 'Gareth', 'Graham', 'Grant', 'Hades', 'Hamish', 'Hana', 'Hank', 'Jake', 'James', 'Jason', 'Jessica', 'Jonah', 'Julia', 'Kayla', 'Kelsey', 'Lauren', 'Levi', 'Liam', 'Loretta', 'Lucian', 'Luna', 'Malcolm', 'Marcus', 'Mark', 'Marlene', 'Mia', 'Miranda', 'Mortimer', 'Nadia', 'Naomi', 'Nate', 'Oliver', 'Olivia', 'Pippa', 'Pixie', 'Priya', 'Reed', 'Riley', 'Ronald', 'Rupert', 'Saanvi', 'Sarah', 'Sebastian', 'Selene', 'Serena', 'Shaun', 'Simon', 'Snik', 'Sophie', 'Tessa', 'Theodore', 'Timothy', 'Trevor', 'Tristan', 'Tyler', 'Veronica', 'Victor', 'Victoria', 'Vinny', 'Wendy'}

# --- 6. Hardpoints ---
# Mapping Class -> {'primary': N, 'secondary': M}
NUM_OF_HARDPOINTS = {
    'GTB Athena': {'primary': 2, 'secondary': 2},
    'GTB Medusa': {'primary': 1, 'secondary': 3},
    'GTB Ursa': {'primary': 2, 'secondary': 3},
    'GTB Zeus': {'primary': 2, 'secondary': 3},
    'GTDr Amazon': {'primary': 1, 'secondary': 0},
    'GTF Angel': {'primary': 1, 'secondary': 1},
    'GTF Apollo': {'primary': 2, 'secondary': 2},
    'GTF Hercules': {'primary': 2, 'secondary': 2},
    'GTF Loki': {'primary': 2, 'secondary': 1},
    'GTF Loki#stealth': {'primary': 2, 'secondary': 1},
    'GTF Ulysses': {'primary': 2, 'secondary': 1},
    'GTF Valkyrie': {'primary': 2, 'secondary': 1},
    'PVB Amun': {'primary': 2, 'secondary': 3},
    'PVB Osiris': {'primary': 1, 'secondary': 3},
    'PVB Sekhmet': {'primary': 1, 'secondary': 3},
    'PVDr Jackal': {'primary': 1, 'secondary': 0},
    'PVF Anubis': {'primary': 1, 'secondary': 1},
    'PVF Horus': {'primary': 2, 'secondary': 2},
    'PVF Seth': {'primary': 2, 'secondary': 2},
    'PVF Thoth': {'primary': 1, 'secondary': 1},
    'PVF Ulysses': {'primary': 2, 'secondary': 1},
    'SB Nahema': {'primary': 2, 'secondary': 3},
    'SB Nephilim': {'primary': 1, 'secondary': 4},
    'SB Seraphim': {'primary': 3, 'secondary': 4},
    'SB Shaitan': {'primary': 2, 'secondary': 1},
    'SF Basilisk': {'primary': 2, 'secondary': 2},
    'SF Dragon': {'primary': 2, 'secondary': 1},
    'SF Dragon#Terrans': {'primary': 2, 'secondary': 1},
    'SF Dragon#weakened': {'primary': 2, 'secondary': 1},
    'SF Gorgon': {'primary': 2, 'secondary': 2},
    'SF Manticore': {'primary': 1, 'secondary': 2},
    'SF Scorpion': {'primary': 2, 'secondary': 1},
}

# --- 7. Secondary Bank Capacities ---
# Mapping Class -> [cap1, cap2, ...]
SHIP_SBANK_CAPACITIES = {
    'GTB Athena': [80, 80],
    'GTB Medusa': [40, 80, 80],
    'GTB Ursa': [80, 80, 80],
    'GTB Zeus': [40, 40, 40],
    'GTF Angel': [40],
    'GTF Apollo': [40, 40],
    'GTF Hercules': [60, 60],
    'GTF Loki': [20],
    'GTF Loki#stealth': [20],
    'GTF Ulysses': [40],
    'GTF Valkyrie': [60],
    'PVB Amun': [60, 60, 80],
    'PVB Osiris': [40, 40, 20],
    'PVB Sekhmet': [60, 60, 80],
    'PVDr Jackal': [],
    'PVF Anubis': [60],
    'PVF Horus': [40, 40],
    'PVF Seth': [40, 80],
    'PVF Thoth': [80],
    'PVF Ulysses': [40],
    'SB Nahema': [40, 40, 20],
    'SB Nephilim': [40, 40, 40, 40],
    'SB Seraphim': [40, 40, 80, 80],
    'SB Shaitan': [40],
    'SF Basilisk': [80, 80],
    'SF Dragon': [20],
    'SF Dragon#Terrans': [20],
    'SF Dragon#weakened': [20],
    'SF Gorgon': [80, 80],
    'SF Manticore': [40, 40],
    'SF Scorpion': [40],
}

# --- 8. Secondary Weapon Sizes ---
# Mapping Weapon -> float
WEAPON_CARGO_SIZES = {
    'Barracuda': 10.0,
    'Cluster Baby': 2.0,
    'Cluster Baby Weak': 2.0,
    'Cluster Bomb': 15.0,
    'Cluster Bomb Baby': 2.0,
    'Cluster Bomb#Shivan': 15.0,
    'D-Missile': 8.0,
    'D-Missile#Shivan': 8.0,
    'EM Pulse': 4.0,
    'EM Pulse#Shivan': 4.0,
    'Enemy MX-50': 4.0,
    'Enemy MX-50#Shivan': 4.0,
    'Fang': 0.25,
    'FighterKiller': 4.0,
    'FighterKiller#Shivan': 4.0,
    'Fury': 0.5,
    'Fury#Shivan': 0.5,
    'Fusion Mortar': 1.0,
    'Harbinger': 40.0,
    'Harbinger#End': 40.0,
    'Harbinger#Shivan': 40.0,
    'Havoc': 2.0,
    'Hornet': 1.0,
    'Hornet#Shivan': 1.0,
    'Hornet#Weak': 1.0,
    'Hornet#Weak#Shivan': 1.0,
    'Interceptor': 4.0,
    'Interceptor#Shivan': 4.0,
    'Interceptor#Weak': 2.66,
    'Interceptor#Weak#Shivan': 2.66,
    'MX-50': 4.0,
    'MX-50#Shivan': 4.0,
    'Phoenix V': 8.0,
    'Phoenix V#Shivan': 8.0,
    'S_Cluster Baby': 2.0,
    'S_Cluster Baby Weak': 2.0,
    'S_Cluster Bomb Baby': 2.0,
    'Serkr': 15.0,
    'Serkr#short': 15.0,
    'Shivan Cluster': 15.0,
    'Shrapnel': 2.0,
    'Stiletto': 8.0,
    'Stiletto#Shivan': 8.0,
    'Swarmer': 4.0,
    'Synaptic': 15.0,
    'Synaptic#Shivan': 15.0,
    'Tsunami': 15.0,
    'Tsunami#Shivan': 15.0,
    'Unknown Bomb': 15.0,
    'Unknown Megabomb': 40.0,
    'Vasudan Flux Cannon': 1.0,
}

# --- 9. Ship Bounding Boxes ---
# Mapping Class -> {'min': [x, y, z], 'max': [x, y, z]}
SHIP_BOUNDING_BOXES = {
    'GTB Athena': {'min': [-8.6, -2.6, -15.0], 'max': [8.6, 4.6, 8.5]},
    'GTC Fenris': {'min': [-35.1, -99.8, -115.5], 'max': [35.2, 79.5, 132.4]},
    'GTC Leviathan': {'min': [-35.1, -99.8, -115.5], 'max': [35.2, 79.5, 132.4]},
    'GTD Hades': {'min': [-609.7, -836.8, -1691.8], 'max': [609.7, 893.1, 1691.8]},
    'GTD Orion': {'min': [-249.9, -362.6, -819.9], 'max': [357.2, 372.2, 1194.2]},
    'GTF Apollo': {'min': [-7.5, -2.7, -9.4], 'max': [7.5, 4.1, 12.0]},
    'GTFr Chronos': {'min': [-24.2, -6.6, -92.0], 'max': [24.2, 35.6, 67.5]},
    'GTI Arcadia': {'min': [-1299.8, -996.2, -917.0], 'max': [1402.0, 942.1, 924.3]},
    'GTS Centaur': {'min': [-3.7, -5.6, -12.6], 'max': [3.7, 6.2, 11.8]},
    'GTSC Faustus': {'min': [-64.3, -64.5, -74.9], 'max': [62.3, 62.8, 86.3]},
    'GTT Elysium': {'min': [-9.1, -14.0, -16.3], 'max': [9.1, 17.0, 10.4]},
    'PVB Amun': {'min': [-9.5, -5.2, -17.5], 'max': [9.5, 5.2, 14.9]},
    'PVC Aten': {'min': [-60.2, -25.9, -123.0], 'max': [60.2, 35.0, 106.9]},
    'PVD Typhon': {'min': [-504.0, -263.4, -1086.5], 'max': [504.0, 269.1, 1065.9]},
    'PVFr Bast': {'min': [-5.7, -5.7, -21.5], 'max': [5.7, 5.7, 14.9]},
    'PVFr Satis': {'min': [-24.8, -18.7, -57.3], 'max': [24.8, 11.4, 39.8]},
    'PVI Karnak': {'min': [-2090.2, -1395.7, -2632.1], 'max': [3006.2, 1395.7, 2636.6]},
    'PVSC Imhotep': {'min': [-40.3, -46.8, -92.5], 'max': [40.3, 36.1, 108.7]},
    'PVT Isis': {'min': [-6.5, -3.0, -15.1], 'max': [6.4, 2.6, 9.8]},
    'SB Shaitan': {'min': [-10.5, -2.0, -14.1], 'max': [7.5, 4.1, 12.3]},
    'SC Cain': {'min': [-42.3, -42.7, -96.0], 'max': [42.1, 36.9, 97.9]},
    'SC Lilith': {'min': [-42.3, -42.7, -96.0], 'max': [42.1, 36.9, 97.9]},
    'SD Demon': {'min': [-504.5, -573.6, -1044.0], 'max': [504.5, 625.8, 1052.6]},
    'SD Lucifer': {'min': [-621.9, -537.9, -1475.8], 'max': [623.7, 306.6, 1263.9]},
    'SFr Asmodeus': {'min': [-33.7, -47.9, -56.9], 'max': [33.7, 12.9, 56.4]},
    'SFr Mephisto': {'min': [-8.4, -8.2, -24.6], 'max': [8.4, 9.2, 24.5]},
    'ST Azrael': {'min': [-12.8, -12.5, -19.1], 'max': [12.8, 8.6, 19.8]},
    'Subspace Node': {'min': [-669.6, -669.6, -669.6], 'max': [669.6, 669.6, 669.6]},
    'Terran Asteroid Base': {'min': [-461.6, -332.6, -708.9], 'max': [467.5, 896.2, 858.8]},
    'Vasudan Asteroid Base': {'min': [-908.4, -460.1, -1025.4], 'max': [895.0, 457.4, 1029.9]},
}

# --- 10. Player Wing Names ---
PLAYER_WING_NAMES = {"Alpha", "Beta", "Gamma", "Delta", "Epsilon"}

