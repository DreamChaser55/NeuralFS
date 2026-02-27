# sexp_argument_logic.py
# Auto-generated from FSO sexp.cpp. Do not edit manually.

from opf_definitions import *
from sexp_definitions import INT_MAX


def get_argument_type(op, arg_index):
    if op in ["OP_TRUE", "OP_FALSE", "OP_MISSION_TIME", "OP_MISSION_TIME_MSECS", "OP_NOP", "OP_WAYPOINT_MISSED", "OP_WAYPOINT_TWICE", "OP_PATH_FLOWN", "OP_GRANT_PROMOTION", "OP_WAS_PROMOTION_GRANTED", "OP_RED_ALERT", "OP_FORCE_JUMP", "OP_RESET_ORDERS", "OP_INVALIDATE_ALL_ARGUMENTS", "OP_VALIDATE_ALL_ARGUMENTS", "OP_NUM_VALID_ARGUMENTS", "OP_SUPERNOVA_STOP", "OP_GET_SUPERNOVA_STAGE", "OP_NAV_UNSELECT", "OP_PLAYER_IS_CHEATING_BASTARD", "OP_RESET_POST_EFFECTS", "OP_FOR_PLAYERS"]:
        return OPF_NONE
    if op in ["OP_AND", "OP_AND_IN_SEQUENCE", "OP_OR", "OP_NOT", "OP_XOR"]:
        return OPF_BOOL
    if op in ["OP_PLUS", "OP_MINUS", "OP_MOD", "OP_MUL", "OP_DIV", "OP_EQUALS", "OP_GREATER_THAN", "OP_LESS_THAN", "OP_NOT_EQUAL", "OP_GREATER_OR_EQUAL", "OP_LESS_OR_EQUAL", "OP_RAND", "OP_RAND_MULTIPLE", "OP_ABS", "OP_MIN", "OP_MAX", "OP_AVG", "OP_SIGNUM", "OP_IS_NAN", "OP_NAN_TO_NUMBER", "OP_ANGLE_VECTORS"]:
        return OPF_NUMBER
    if op == "OP_POW":
        if arg_index == 0:
            return OPF_NUMBER
        else:
            return OPF_POSITIVE
    if op in ["OP_STRING_EQUALS", "OP_STRING_GREATER_THAN", "OP_STRING_LESS_THAN", "OP_STRING_TO_INT", "OP_STRING_GET_LENGTH"]:
        return OPF_STRING
    if op == "OP_STRING_CONCATENATE":
        if arg_index == 0 or arg_index == 1:
            return OPF_STRING
        elif arg_index == 2:
            return OPF_VARIABLE_NAME
        else:
            return OPF_NONE
    if op == "OP_STRING_CONCATENATE_BLOCK":
        if arg_index == 0:
            return OPF_VARIABLE_NAME
        else:
            return OPF_STRING
    if op == "OP_INT_TO_STRING":
        if arg_index == 0:
            return OPF_NUMBER
        elif arg_index == 1:
            return OPF_VARIABLE_NAME
        else:
            return OPF_NONE
    if op == "OP_STRING_GET_SUBSTRING":
        if arg_index == 0:
            return OPF_STRING
        elif arg_index == 1 or arg_index == 2:
            return OPF_POSITIVE
        elif arg_index == 3:
            return OPF_VARIABLE_NAME
        else:
            return OPF_NONE
    if op == "OP_STRING_SET_SUBSTRING":
        if arg_index == 0:
            return OPF_STRING
        elif arg_index == 1 or arg_index == 2:
            return OPF_POSITIVE
        elif arg_index == 3:
            return OPF_STRING
        elif arg_index == 4:
            return OPF_VARIABLE_NAME
        else:
            return OPF_NONE
    if op == "OP_DEBUG":
        if arg_index == 0:
            return OPF_BOOL
        else:
            return OPF_MESSAGE_OR_STRING
    if op == "OP_IS_TRUE_FOR_DURATION":
        if arg_index == 0:
            return OPF_POSITIVE
        else:
            return OPF_BOOL
    if op in ["OP_HAS_TIME_ELAPSED", "OP_HAS_TIME_ELAPSED_MSECS", "OP_SPEED", "OP_SET_TRAINING_CONTEXT_SPEED", "OP_SPECIAL_CHECK", "OP_AI_WARP_OUT", "OP_TEAM_SCORE", "OP_HUD_SET_MAX_TARGETING_RANGE", "OP_MISSION_SET_NEBULA", "OP_MISSION_SET_SUBSPACE", "OP_SET_BIT", "OP_UNSET_BIT", "OP_IS_BIT_SET", "OP_BITWISE_AND", "OP_BITWISE_OR", "OP_BITWISE_NOT", "OP_BITWISE_XOR"]:
        return OPF_POSITIVE
    if op in ["OP_AI_WARP", "OP_SET_TRAINING_CONTEXT_FLY_PATH"]:
        if  not arg_index :
            return OPF_WAYPOINT_PATH
        else:
            return OPF_NUMBER
    if op in ["OP_AI_WAYPOINTS", "OP_AI_WAYPOINTS_ONCE"]:
        if arg_index == 0:
            return OPF_WAYPOINT_PATH
        elif arg_index == 1 or arg_index == 3:
            return OPF_POSITIVE
        elif arg_index == 2 or arg_index == 4:
            return OPF_BOOL
        else:
            return OPF_NONE
    if op in ["OP_TURRET_PROTECT_SHIP", "OP_TURRET_UNPROTECT_SHIP"]:
        if arg_index == 0:
            return OPF_TURRET_TYPE
        else:
            return OPF_SHIP
    if op in ["OP_IS_DISABLED", "OP_IS_DISARMED", "OP_TIME_SHIP_DESTROYED", "OP_TIME_SHIP_ARRIVED", "OP_TIME_SHIP_DEPARTED", "OP_AFTERBURNER_LEFT", "OP_WEAPON_ENERGY_LEFT", "OP_SHIELDS_LEFT", "OP_HITS_LEFT", "OP_SIM_HITS_LEFT", "OP_CLEAR_SHIP_GOALS", "OP_PROTECT_SHIP", "OP_UNPROTECT_SHIP", "OP_BEAM_PROTECT_SHIP", "OP_BEAM_UNPROTECT_SHIP", "OP_TRANSFER_CARGO", "OP_EXCHANGE_CARGO", "OP_SHIP_INVISIBLE", "OP_SHIP_VISIBLE", "OP_SHIP_INVULNERABLE", "OP_SHIP_VULNERABLE", "OP_SHIP_BOMB_TARGETABLE", "OP_SHIP_BOMB_UNTARGETABLE", "OP_SHIP_GUARDIAN", "OP_SHIP_NO_GUARDIAN", "OP_SHIP_VANISH", "OP_DESTROY_INSTANTLY", "OP_DESTROY_INSTANTLY_WITH_DEBRIS", "OP_SHIELDS_ON", "OP_SHIELDS_OFF", "OP_SHIP_STEALTHY", "OP_SHIP_UNSTEALTHY", "OP_FRIENDLY_STEALTH_INVISIBLE", "OP_FRIENDLY_STEALTH_VISIBLE", "OP_PRIMARIES_DEPLETED", "OP_SECONDARIES_DEPLETED", "OP_SPECIAL_WARP_DISTANCE", "OP_SET_SPECIAL_WARPOUT_NAME", "OP_IS_SHIP_VISIBLE", "OP_IS_SHIP_STEALTHY", "OP_IS_FRIENDLY_STEALTH_VISIBLE", "OP_GET_DAMAGE_CAUSED", "OP_GET_THROTTLE_SPEED", "OP_FORCE_REARM", "OP_ABORT_REARM"]:
        return OPF_SHIP
    if op == "OP_ALTER_SHIP_FLAG":
        if(arg_index == 0):
            return OPF_SHIP_FLAG
        if(arg_index == 1 or arg_index == 2):
            return OPF_BOOL
        else:
            return OPF_SHIP_WING_WHOLETEAM
    if op == "OP_ALTER_WING_FLAG":
        if(arg_index == 0):
            return OPF_WING_FLAG
        if(arg_index == 1):
            return OPF_BOOL
        else:
            return OPF_WING
    if op == "OP_CANCEL_FUTURE_WAVES":
        return OPF_WING
    if op == "OP_SET_PLAYER_THROTTLE_SPEED":
        if(arg_index == 0):
            return OPF_SHIP
        else:
            return OPF_POSITIVE
    if op == "OP_SHIP_CREATE":
        if arg_index == 0:
            return OPF_STRING
        elif arg_index == 1:
            return OPF_SHIP_CLASS_NAME
        elif arg_index == 8:
            return OPF_IFF
        elif arg_index == 9:
            return OPF_BOOL
        else:
            return OPF_NUMBER
    if op == "OP_WEAPON_CREATE":
        if arg_index == 0:
            return OPF_SHIP_OR_NONE
        elif arg_index == 1:
            return OPF_WEAPON_NAME
        elif arg_index == 8:
            return OPF_SHIP
        elif arg_index == 9:
            return OPF_SUBSYSTEM
        else:
            return OPF_NUMBER
    if op == "OP_CLEAR_WEAPONS":
        return OPF_WEAPON_NAME
    if op == "OP_CLEAR_DEBRIS":
        return OPF_SHIP_CLASS_NAME
    if op == "OP_SHIP_GUARDIAN_THRESHOLD":
        if arg_index == 0:
            return OPF_POSITIVE
        else:
            return OPF_SHIP
    if op == "OP_SHIP_SUBSYS_GUARDIAN_THRESHOLD":
        if arg_index == 0:
            return OPF_POSITIVE
        elif arg_index == 1:
            return OPF_SHIP
        else:
            return OPF_SUBSYS_OR_GENERIC
    if op in ["OP_SHIP_SUBSYS_TARGETABLE", "OP_SHIP_SUBSYS_UNTARGETABLE"]:
        if arg_index == 0:
            return OPF_SHIP
        else:
            return OPF_SUBSYS_OR_GENERIC
    if op in ["OP_SHIP_SUBSYS_NO_REPLACE", "OP_SHIP_SUBSYS_NO_LIVE_DEBRIS", "OP_SHIP_SUBSYS_VANISHED", "OP_SHIP_SUBSYS_IGNORE_IF_DEAD"]:
        if arg_index == 0:
            return OPF_SHIP
        elif arg_index == 1:
            return OPF_BOOL
        else:
            return OPF_SUBSYS_OR_GENERIC
    if op in ["OP_IS_DESTROYED", "OP_HAS_ARRIVED", "OP_HAS_DEPARTED", "OP_CLEAR_GOALS"]:
        return OPF_SHIP_WING
    if op in ["OP_IS_DISABLED_DELAY", "OP_IS_DISARMED_DELAY"]:
        if  arg_index == 0 :
            return OPF_POSITIVE
        else:
            return OPF_SHIP
    if op == "OP_SHIP_TAG":
        if arg_index == 0:
            return OPF_SHIP
        elif arg_index == 3:
            return OPF_SSM_CLASS
        elif arg_index == 7:
            return OPF_IFF
        elif arg_index > 3:
            return OPF_NUMBER
        else:
            return OPF_POSITIVE
    if op == "OP_SHIP_UNTAG":
        return OPF_SHIP
    if op == "OP_FACING":
        if arg_index == 0:
            return OPF_SHIP
        else:
            return OPF_POSITIVE
    if op == "OP_FACING2":
        if arg_index == 0:
            return OPF_WAYPOINT_PATH
        else:
            return OPF_POSITIVE
    if op == "OP_ORDER":
        if arg_index == 1:
            return OPF_AI_ORDER
        else:
            return OPF_SHIP_WING
    if op == "OP_QUERY_ORDERS":
        if arg_index == 0:
            return OPF_ORDER_RECIPIENT
        if arg_index == 1:
            return OPF_AI_ORDER
        if arg_index == 2:
            return OPF_POSITIVE
        if arg_index == 5:
            return OPF_SUBSYSTEM
        else:
            return OPF_SHIP_WING
    if op == "OP_TIME_TO_GOAL":
        return OPF_SHIP
    if op == "OP_SET_HUD_TIME_PAD":
        return OPF_NUMBER
    if op == "OP_WAS_DESTROYED_BY_DELAY":
        if arg_index == 0:
            return OPF_POSITIVE
        else:
            return OPF_SHIP
    if op in ["OP_IS_DESTROYED_DELAY", "OP_HAS_ARRIVED_DELAY", "OP_HAS_DEPARTED_DELAY", "OP_LAST_ORDER_TIME"]:
        if  arg_index == 0 :
            return OPF_POSITIVE
        else:
            return OPF_SHIP_WING
    if op == "OP_SHIP_CHANGE_ALT_NAME":
        if arg_index == 0:
            return OPF_STRING
        else:
            return OPF_SHIP_WING
    if op == "OP_SHIP_CHANGE_CALLSIGN":
        if arg_index == 0:
            return OPF_STRING
        else:
            return OPF_SHIP
    if op == "OP_SHIP_CHANGE_DISPLAY_NAME":
        if arg_index == 0:
            return OPF_STRING
        else:
            return OPF_SHIP_WING
    if op == "OP_SET_DEATH_MESSAGE":
        return OPF_MESSAGE_OR_STRING
    if op in ["OP_DISTANCE", "OP_DISTANCE_CENTER", "OP_DISTANCE_BBOX"]:
        return OPF_SHIP_WING_SHIPONTEAM_POINT
    if op in ["OP_SET_OBJECT_SPEED_X", "OP_SET_OBJECT_SPEED_Y", "OP_SET_OBJECT_SPEED_Z"]:
        if arg_index == 0:
            return OPF_SHIP_WING
        elif arg_index == 1:
            return OPF_NUMBER
        else:
            return OPF_BOOL
    if op in ["OP_GET_OBJECT_SPEED_X", "OP_GET_OBJECT_SPEED_Y", "OP_GET_OBJECT_SPEED_Z"]:
        if arg_index == 0:
            return OPF_SHIP_WING
        else:
            return OPF_BOOL
    if op in ["OP_GET_OBJECT_X", "OP_GET_OBJECT_Y", "OP_GET_OBJECT_Z"]:
        if arg_index == 0:
            return OPF_SHIP_WING_POINT
        elif arg_index == 1:
            return OPF_SUBSYSTEM_OR_NONE
        else:
            return OPF_NUMBER
    if op in ["OP_GET_OBJECT_PITCH", "OP_GET_OBJECT_BANK", "OP_GET_OBJECT_HEADING"]:
        return OPF_SHIP_WING
    if op == "OP_ANGLE_FVEC_TARGET":
        if arg_index == 0:
            return OPF_SHIP
        else:
            return OPF_SHIP_WING_POINT
    if op == "OP_SET_OBJECT_POSITION":
        if(arg_index == 0):
            return OPF_SHIP_WING_POINT
        else:
            return OPF_NUMBER
    if op == "OP_SET_OBJECT_ORIENTATION":
        if arg_index == 0:
            return OPF_SHIP_WING
        else:
            return OPF_NUMBER
    if op == "OP_SET_OBJECT_FACING":
        if arg_index == 0:
            return OPF_SHIP_WING
        elif arg_index < 4:
            return OPF_NUMBER
        else:
            return OPF_POSITIVE
    if op == "OP_SET_OBJECT_FACING_OBJECT":
        if arg_index == 0:
            return OPF_SHIP_WING
        elif arg_index == 1:
            return OPF_SHIP_WING_POINT
        else:
            return OPF_POSITIVE
    if op == "OP_SHIP_MANEUVER":
        if arg_index == 0:
            return OPF_SHIP_WING
        elif arg_index == 1:
            return OPF_POSITIVE
        elif arg_index < 5:
            return OPF_NUMBER
        elif arg_index == 5:
            return OPF_BOOL
        elif arg_index < 9:
            return OPF_NUMBER
        elif arg_index == 9:
            return OPF_BOOL
        else:
            return OPF_POSITIVE
    if op in ["OP_SHIP_ROT_MANEUVER", "OP_SHIP_LAT_MANEUVER"]:
        if arg_index == 0:
            return OPF_SHIP_WING
        elif arg_index == 1:
            return OPF_POSITIVE
        elif arg_index < 5:
            return OPF_NUMBER
        elif arg_index == 5:
            return OPF_BOOL
        else:
            return OPF_POSITIVE
    if op == "OP_MODIFY_VARIABLE":
        if arg_index == 0:
            return OPF_VARIABLE_NAME
        else:
            return OPF_AMBIGUOUS
    if op == "OP_MODIFY_VARIABLE_XSTR":
        if arg_index == 0:
            return OPF_VARIABLE_NAME
        elif arg_index == 1:
            return OPF_STRING
        elif arg_index == 2:
            return OPF_NUMBER
        else:
            return OPF_NONE
    if op in ["OP_GET_VARIABLE_BY_INDEX", "OP_COPY_VARIABLE_BETWEEN_INDEXES"]:
        return OPF_POSITIVE
    if op == "OP_COPY_VARIABLE_FROM_INDEX":
        if arg_index == 0:
            return OPF_POSITIVE
        else:
            return OPF_VARIABLE_NAME
    if op == "OP_SET_VARIABLE_BY_INDEX":
        if arg_index == 0:
            return OPF_POSITIVE
        else:
            return OPF_AMBIGUOUS
    if op == "OP_CONTAINER_ADD_TO_LIST":
        if arg_index == 0:
            return OPF_LIST_CONTAINER_NAME
        elif arg_index == 1:
            return OPF_BOOL
        else:
            return OPF_CONTAINER_VALUE
    if op == "OP_CONTAINER_REMOVE_FROM_LIST":
        if arg_index == 0:
            return OPF_LIST_CONTAINER_NAME
        else:
            return OPF_CONTAINER_VALUE
    if op in ["OP_CONTAINER_ADD_TO_MAP", "OP_CONTAINER_REMOVE_FROM_MAP"]:
        if arg_index == 0:
            return OPF_MAP_CONTAINER_NAME
        else:
            return OPF_CONTAINER_VALUE
    if op == "OP_CONTAINER_GET_MAP_KEYS":
        if arg_index == 0:
            return OPF_MAP_CONTAINER_NAME
        elif arg_index == 1:
            return OPF_LIST_CONTAINER_NAME
        elif arg_index == 2:
            return OPF_BOOL
        else:
            return OPF_NONE
    if op == "OP_CLEAR_CONTAINER":
        return OPF_CONTAINER_NAME
    if op == "OP_COPY_CONTAINER":
        if arg_index == 0 or arg_index == 1:
            return OPF_CONTAINER_NAME
        elif arg_index == 2:
            return OPF_BOOL
        else:
            return OPF_NONE
    if op == "OP_APPLY_CONTAINER_FILTER":
        if arg_index == 0:
            return OPF_CONTAINER_NAME
        elif arg_index == 1:
            return OPF_LIST_CONTAINER_NAME
        else:
            return OPF_NONE
    if op in ["OP_HAS_DOCKED", "OP_HAS_UNDOCKED", "OP_HAS_DOCKED_DELAY", "OP_HAS_UNDOCKED_DELAY", "OP_TIME_DOCKED", "OP_TIME_UNDOCKED"]:
        if  arg_index < 2 :
            return OPF_SHIP
        else:
            return OPF_POSITIVE
    if op in ["OP_TIME_WING_DESTROYED", "OP_TIME_WING_ARRIVED", "OP_TIME_WING_DEPARTED", "OP_CLEAR_WING_GOALS"]:
        return OPF_WING
    if op in ["OP_SET_SCANNED", "OP_SET_UNSCANNED", "OP_IS_SUBSYSTEM_DESTROYED"]:
        if not arg_index:
            return OPF_SHIP
        else:
            return OPF_SUBSYSTEM
    if op == "OP_HITS_LEFT_SUBSYSTEM":
        if arg_index == 0:
            return OPF_SHIP
        elif arg_index == 1:
            return OPF_SUBSYSTEM
        else:
            return OPF_BOOL
    if op == "OP_HITS_LEFT_SUBSYSTEM_GENERIC":
        if arg_index == 0:
            return OPF_SHIP
        else:
            return OPF_SUBSYSTEM_TYPE
    if op == "OP_HITS_LEFT_SUBSYSTEM_SPECIFIC":
        if arg_index == 0:
            return OPF_SHIP
        elif arg_index == 1:
            return OPF_SUBSYSTEM
        else:
            return OPF_NONE
    if op in ["OP_DISTANCE_CENTER_SUBSYSTEM", "OP_DISTANCE_BBOX_SUBSYSTEM"]:
        if arg_index == 0:
            return OPF_SHIP_WING_SHIPONTEAM_POINT
        elif arg_index == 1:
            return OPF_SHIP
        elif arg_index == 2:
            return OPF_SUBSYSTEM
        else:
            return OPF_NONE
    if op == "OP_NUM_WITHIN_BOX":
        if(arg_index < 3):
            return OPF_NUMBER
        elif(arg_index < 6):
            return OPF_POSITIVE
        else:
            return OPF_SHIP_WING
    if op == "OP_IS_IN_BOX":
        if arg_index == 0:
            return OPF_SHIP_WING_POINT
        elif arg_index <= 6:
            return OPF_NUMBER
        else:
            return OPF_SHIP
    if op == "OP_IS_IN_MISSION":
        return OPF_STRING
    if op == "OP_HAS_ARMOR_TYPE":
        if arg_index == 0:
            return OPF_SHIP
        elif arg_index == 1:
            return OPF_ARMOR_TYPE
        else:
            return OPF_SUBSYSTEM
    if op == "OP_IS_DOCKED":
        return OPF_SHIP
    if op == "OP_MISSILE_LOCKED":
        if arg_index == 0:
            return OPF_POSITIVE
        elif arg_index == 1:
            return OPF_SHIP
        else:
            return OPF_SUBSYSTEM
    if op == "OP_TARGETED":
        if not arg_index:
            return OPF_SHIP
        elif arg_index == 1:
            return OPF_POSITIVE
        else:
            return OPF_SUBSYSTEM
    if op == "OP_NODE_TARGETED":
        if not arg_index:
            return OPF_JUMP_NODE_NAME
        elif arg_index == 1:
            return OPF_POSITIVE
        else:
            return OPF_NONE
    if op == "OP_IS_SUBSYSTEM_DESTROYED_DELAY":
        if  arg_index == 0 :
            return OPF_SHIP
        elif  arg_index == 1 :
            return OPF_SUBSYSTEM
        else:
            return OPF_POSITIVE
    if op == "OP_IS_IFF":
        if not arg_index:
            return OPF_IFF
        else:
            return OPF_SHIP_WING
    if op == "OP_CHANGE_IFF":
        if not arg_index:
            return OPF_IFF
        else:
            return OPF_SHIP_WING_WHOLETEAM
    if op == "OP_IS_SPECIES":
        if not arg_index:
            return OPF_SPECIES
        else:
            return OPF_SHIP_WING
    if op == "OP_ADD_SHIP_GOAL":
        if not arg_index:
            return OPF_SHIP
        else:
            return OPF_AI_GOAL
    if op == "OP_ADD_WING_GOAL":
        if not arg_index:
            return OPF_WING
        else:
            return OPF_AI_GOAL
    if op == "OP_ADD_GOAL":
        if  arg_index == 0 :
            return OPF_SHIP_WING
        else:
            return OPF_AI_GOAL
    if op == "OP_REMOVE_GOAL":
        if  arg_index == 0 :
            return OPF_SHIP_WING
        elif  arg_index == 1 :
            return OPF_AI_GOAL
        else:
            return OPF_BOOL
    if op in ["OP_COND", "OP_WHEN", "OP_EVERY_TIME", "OP_IF_THEN_ELSE", "OP_PERFORM_ACTIONS_BOOL_FIRST", "OP_PERFORM_ACTIONS_BOOL_LAST"]:
        if not arg_index:
            return OPF_BOOL
        else:
            return OPF_NULL
    if op == "OP_SWITCH":
        if not arg_index:
            return OPF_NUMBER
        else:
            return OPF_NULL
    if op in ["OP_WHEN_ARGUMENT", "OP_EVERY_TIME_ARGUMENT"]:
        if arg_index == 0:
            return OPF_FLEXIBLE_ARGUMENT
        elif arg_index == 1:
            return OPF_BOOL
        else:
            return OPF_NULL
    if op in ["OP_DO_FOR_VALID_ARGUMENTS", "OP_ON_MISSION_SKIP"]:
        return OPF_NULL
    if op in ["OP_RANDOM_OF", "OP_IN_SEQUENCE"]:
        return OPF_ANYTHING
    if op in ["OP_ANY_OF", "OP_EVERY_OF", "OP_RANDOM_MULTIPLE_OF"]:
        return OPF_DATA_OR_STR_CONTAINER
    if op in ["OP_NUMBER_OF", "OP_FIRST_OF"]:
        if arg_index == 0:
            return OPF_POSITIVE
        else:
            return OPF_DATA_OR_STR_CONTAINER
    if op == "OP_FOR_COUNTER":
        return OPF_NUMBER
    if op == "OP_FOR_SHIP_CLASS":
        return OPF_SHIP_CLASS_NAME
    if op == "OP_FOR_SHIP_TYPE":
        return OPF_SHIP_TYPE
    if op == "OP_FOR_SHIP_TEAM":
        return OPF_IFF
    if op == "OP_FOR_SHIP_SPECIES":
        return OPF_SPECIES
    if op == "OP_FOR_SUBSYSTEMS":
        if arg_index == 0:
            return OPF_SHIP
        else:
            return OPF_SUBSYSTEM_TYPE
    if op == "OP_FOR_CONTAINER_DATA":
        return OPF_CONTAINER_NAME
    if op == "OP_FOR_MAP_CONTAINER_KEYS":
        return OPF_MAP_CONTAINER_NAME
    if op in ["OP_INVALIDATE_ARGUMENT", "OP_VALIDATE_ARGUMENT"]:
        return OPF_ANYTHING
    if op == "OP_FUNCTIONAL_IF_THEN_ELSE":
        if arg_index == 0:
            return OPF_BOOL
        else:
            return OPF_NUMBER
    if op == "OP_FUNCTIONAL_SWITCH":
        return OPF_NUMBER
    if op == "OP_FUNCTIONAL_WHEN":
        if arg_index == 0 or arg_index == 2:
            return OPF_BOOL
        elif arg_index == 1:
            return OPF_FUNCTIONAL_WHEN_EVAL_TYPE
        else:
            return OPF_NULL
    if op in ["OP_AI_DISABLE_SHIP", "OP_AI_DISABLE_SHIP_TACTICAL", "OP_AI_DISARM_SHIP", "OP_AI_DISARM_SHIP_TACTICAL"]:
        if arg_index == 0:
            return OPF_SHIP
        elif arg_index == 1:
            return OPF_POSITIVE
        else:
            return OPF_BOOL
    if op in ["OP_AI_EVADE_SHIP", "OP_AI_IGNORE", "OP_AI_IGNORE_NEW", "OP_AI_REARM_REPAIR"]:
        if arg_index == 0:
            return OPF_SHIP
        elif arg_index == 1:
            return OPF_POSITIVE
        else:
            return OPF_BOOL
    if op in ["OP_AI_FLY_TO_SHIP", "OP_AI_STAY_NEAR_SHIP"]:
        if arg_index == 0:
            return OPF_SHIP
        elif arg_index == 1 or arg_index == 2:
            return OPF_POSITIVE
        else:
            return OPF_BOOL
    if op == "OP_AI_CHASE":
        if arg_index == 0:
            return OPF_SHIP_WING
        elif arg_index == 1:
            return OPF_POSITIVE
        else:
            return OPF_BOOL
    if op == "OP_AI_CHASE_WING":
        if arg_index == 0:
            return OPF_WING
        elif arg_index == 1:
            return OPF_POSITIVE
        else:
            return OPF_BOOL
    if op == "OP_AI_CHASE_SHIP_CLASS":
        if arg_index == 0:
            return OPF_SHIP_CLASS_NAME
        elif arg_index == 1:
            return OPF_POSITIVE
        else:
            return OPF_BOOL
    if op == "OP_AI_CHASE_SHIP_TYPE":
        if arg_index == 0:
            return OPF_SHIP_TYPE
        elif arg_index == 1:
            return OPF_POSITIVE
        else:
            return OPF_BOOL
    if op == "OP_AI_GUARD":
        if arg_index == 0:
            return OPF_SHIP_WING
        elif arg_index == 1:
            return OPF_POSITIVE
        else:
            return OPF_BOOL
    if op == "OP_AI_GUARD_WING":
        if arg_index == 0:
            return OPF_WING
        elif arg_index == 1:
            return OPF_POSITIVE
        else:
            return OPF_BOOL
    if op == "OP_AI_KEEP_SAFE_DISTANCE":
        return OPF_POSITIVE
    if op == "OP_AI_DOCK":
        if not arg_index:
            return OPF_SHIP
        elif arg_index == 1:
            return OPF_DOCKER_POINT
        elif arg_index == 2:
            return OPF_DOCKEE_POINT
        elif(arg_index == 3):
            return OPF_POSITIVE
        else:
            return OPF_BOOL
    if op == "OP_AI_UNDOCK":
        if arg_index == 0:
            return OPF_POSITIVE
        else:
            return OPF_SHIP
    if op == "OP_AI_DESTROY_SUBSYS":
        if not arg_index:
            return OPF_SHIP
        elif arg_index == 1:
            return OPF_SUBSYSTEM
        elif arg_index == 2:
            return OPF_POSITIVE
        else:
            return OPF_BOOL
    if op == "OP_GOALS_ID":
        return OPF_AI_GOAL
    if op in ["OP_SET_CARGO", "OP_IS_CARGO"]:
        if arg_index == 0:
            return OPF_CARGO
        elif arg_index == 1:
            return OPF_SHIP
        else:
            return OPF_SUBSYSTEM
    if op in ["OP_CHANGE_AI_CLASS", "OP_IS_AI_CLASS"]:
        if arg_index == 0:
            return OPF_AI_CLASS
        elif arg_index == 1:
            return OPF_SHIP
        else:
            return OPF_SUBSYS_OR_GENERIC
    if op == "OP_IS_SHIP_TYPE":
        if arg_index == 0:
            return OPF_SHIP_TYPE
        else:
            return OPF_SHIP
    if op == "OP_IS_SHIP_CLASS":
        if arg_index == 0:
            return OPF_SHIP_CLASS_NAME
        else:
            return OPF_SHIP
    if op == "OP_CHANGE_SOUNDTRACK":
        return OPF_SOUNDTRACK_NAME
    if op == "OP_PLAY_SOUND_FROM_TABLE":
        if arg_index == 3:
            return OPF_GAME_SND
        else:
            return OPF_NUMBER
    if op == "OP_PLAY_SOUND_FROM_FILE":
        if arg_index == 0:
            return OPF_STRING
        elif arg_index == 3:
            return OPF_VARIABLE_NAME
        else:
            return OPF_NUMBER
    if op in ["OP_CLOSE_SOUND_FROM_FILE", "OP_PAUSE_SOUND_FROM_FILE"]:
        if arg_index == 0:
            return OPF_BOOL
        else:
            return OPF_VARIABLE_NAME
    if op == "OP_SET_FRIENDLY_DAMAGE_CAPS":
        return OPF_NUMBER
    if op in ["OP_ALLOW_TREASON", "OP_END_MISSION", "OP_SET_DEBRIEFING_TOGGLED"]:
        return OPF_BOOL
    if op == "OP_SET_DEBRIEFING_PERSONA":
        return OPF_POSITIVE
    if op == "OP_SET_TRAITOR_OVERRIDE":
        return OPF_TRAITOR_OVERRIDE
    if op in ["OP_SET_PLAYER_ORDERS", "OP_SET_ORDER_ALLOWED_TARGET"]:
        if arg_index==0:
            return OPF_SHIP
        if arg_index==1:
            return OPF_BOOL
        else:
            return OPF_AI_ORDER
    if op in ["OP_ENABLE_GENERAL_ORDERS", "OP_VALIDATE_GENERAL_ORDERS"]:
        if arg_index == 0:
            return OPF_BOOL
        else:
            return OPF_LUA_GENERAL_ORDER
    if op == "OP_SET_SOUND_ENVIRONMENT":
        if arg_index == 0:
            return OPF_SOUND_ENVIRONMENT
        arg_index -= 1
        # FALLTHROUGH
    if op in ["OP_UPDATE_SOUND_ENVIRONMENT", "OP_SET_SOUND_ENVIRONMENT"]:
        a_mod = arg_index % 2
        if a_mod == 0:
            return OPF_SOUND_ENVIRONMENT_OPTION
        else:
            return OPF_POSITIVE
    if op == "OP_ADJUST_AUDIO_VOLUME":
        if arg_index == 0:
            return OPF_AUDIO_VOLUME_OPTION
        else:
            return OPF_POSITIVE
    if op == "OP_SET_EXPLOSION_OPTION":
        if arg_index == 0:
            return OPF_SHIP
        a_mod = (arg_index - 1) % 2
        if a_mod == 0:
            return OPF_EXPLOSION_OPTION
        else:
            return OPF_POSITIVE
    if op in ["OP_HUD_DISABLE", "OP_HUD_DISABLE_EXCEPT_MESSAGES"]:
        return OPF_POSITIVE
    if op == "OP_HUD_SET_TEXT":
        if arg_index == 0:
            return OPF_CUSTOM_HUD_GAUGE
        else:
            return OPF_STRING
    if op == "OP_HUD_SET_XSTR":
        if arg_index == 0:
            return OPF_CUSTOM_HUD_GAUGE
        if arg_index == 1:
            return OPF_STRING
        else:
            return OPF_NUMBER
    if op == "OP_HUD_SET_MESSAGE":
        if arg_index == 0:
            return OPF_CUSTOM_HUD_GAUGE
        else:
            return OPF_MESSAGE
    if op == "OP_HUD_SET_TEXT_NUM":
        if arg_index == 0:
            return OPF_CUSTOM_HUD_GAUGE
        else:
            return OPF_POSITIVE
    if op in ["OP_HUD_SET_COORDS", "OP_HUD_SET_FRAME", "OP_HUD_SET_COLOR"]:
        if arg_index == 0:
            return OPF_ANY_HUD_GAUGE
        else:
            return OPF_POSITIVE
    if op == "OP_HUD_RESET_COLOR":
        return OPF_ANY_HUD_GAUGE
    if op == "OP_HUD_CLEAR_MESSAGES":
        return OPF_NONE
    if op == "OP_HUD_FORCE_SENSOR_STATIC":
        return OPF_BOOL
    if op == "OP_HUD_FORCE_EMP_EFFECT":
        if arg_index < 2:
            return OPF_NUMBER
        else:
            return OPF_MESSAGE_OR_STRING
    if op == "OP_SET_SQUADRON_WINGS":
        return OPF_WING
    if op in ["OP_PLAYER_USE_AI", "OP_PLAYER_NOT_USE_AI"]:
        return OPF_NONE
    if op == "OP_CREATE_BOLT":
        if arg_index == 0:
            return OPF_BOLT_TYPE
        elif arg_index == 7:
            return OPF_BOOL
        else:
            return OPF_NUMBER
    if op == "OP_EXPLOSION_EFFECT":
        if arg_index <= 2:
            return OPF_NUMBER
        elif arg_index == 9:
            return OPF_FIREBALL
        elif arg_index == 10:
            return OPF_GAME_SND
        else:
            return OPF_POSITIVE
    if op == "OP_WARP_EFFECT":
        if arg_index <= 5:
            return OPF_NUMBER
        elif arg_index == 8 or arg_index == 9:
            return OPF_GAME_SND
        elif arg_index == 10:
            return OPF_FIREBALL
        else:
            return OPF_POSITIVE
    if op in ["OP_SEND_MESSAGE", "OP_SEND_RANDOM_MESSAGE"]:
        if  arg_index == 0 :
            return OPF_WHO_FROM
        elif  arg_index == 1 :
            return OPF_PRIORITY
        else:
            return OPF_MESSAGE
    if op == "OP_SEND_BUILTIN_MESSAGE":
        # switch detected
        if arg_index == 0 :
            return OPF_MESSAGE_TYPE
        if arg_index == 1 :
            return OPF_SHIP_OR_NONE
        if arg_index == 2 :
            return OPF_BOOL
        else:
            return OPF_WHO_FROM
    if op in ["OP_SEND_MESSAGE_LIST", "OP_SEND_MESSAGE_CHAIN", "OP_SEND_BUILTIN_MESSAGE"]:
        if op == "OP_SEND_MESSAGE_CHAIN":
            if arg_index == 0:
                return OPF_EVENT_NAME
            arg_index -= 1
        a_mod = arg_index % 4
        if(a_mod == 0):
            return OPF_WHO_FROM
        elif(a_mod == 1):
            return OPF_PRIORITY
        elif(a_mod == 2):
            return OPF_MESSAGE
        elif(a_mod == 3):
            return OPF_POSITIVE
        else:
            return OPF_NONE
    if op == "OP_TRAINING_MSG":
        if arg_index < 2:
            return OPF_MESSAGE
        else:
            return OPF_POSITIVE
    if op in ["OP_ENABLE_BUILTIN_MESSAGES", "OP_DISABLE_BUILTIN_MESSAGES"]:
        return OPF_WHO_FROM
    if op == "OP_SET_PERSONA":
        if arg_index == 0:
            return OPF_PERSONA
        else:
            return OPF_SHIP
    if op == "OP_SET_MISSION_MOOD":
        return OPF_MISSION_MOOD
    if op == "OP_CHANGE_TEAM_COLOR":
        if arg_index == 0:
            return OPF_TEAM_COLOR
        elif arg_index == 1:
            return OPF_NUMBER
        else:
            return OPF_SHIP
    if op == "OP_CALL_SSM_STRIKE":
        if arg_index == 0:
            return OPF_SSM_CLASS
        elif arg_index == 1:
            return OPF_IFF
        else:
            return OPF_SHIP
    if op == "OP_SELF_DESTRUCT":
        return OPF_SHIP
    if op == "OP_NEXT_MISSION":
        return OPF_MISSION_NAME
    if op == "OP_END_CAMPAIGN":
        return OPF_BOOL
    if op == "OP_END_OF_CAMPAIGN":
        return OPF_NONE
    if op in ["OP_PREVIOUS_GOAL_TRUE", "OP_PREVIOUS_GOAL_FALSE"]:
        if  arg_index == 0 :
            return OPF_MISSION_NAME
        elif arg_index == 1 :
            return OPF_GOAL_NAME
        else:
            return OPF_BOOL
    if op == "OP_PREVIOUS_GOAL_INCOMPLETE":
        return OPF_GOAL_NAME
    if op in ["OP_PREVIOUS_EVENT_TRUE", "OP_PREVIOUS_EVENT_FALSE", "OP_PREVIOUS_EVENT_INCOMPLETE"]:
        if not arg_index:
            return OPF_MISSION_NAME
        elif  arg_index == 1 :
            return OPF_EVENT_NAME
        else:
            return OPF_BOOL
    if op == "OP_SABOTAGE_SUBSYSTEM":
        if not arg_index:
            return OPF_SHIP
        elif arg_index == 1 :
            return OPF_SUBSYS_OR_GENERIC
        else:
            return OPF_POSITIVE
    if op in ["OP_REPAIR_SUBSYSTEM", "OP_SET_SUBSYSTEM_STRNGTH"]:
        if not arg_index:
            return OPF_SHIP
        elif arg_index == 1 :
            return OPF_SUBSYS_OR_GENERIC
        elif arg_index == 2:
            return OPF_POSITIVE
        else:
            return OPF_BOOL
    if op == "OP_DESTROY_SUBSYS_INSTANTLY":
        if arg_index == 0:
            return OPF_SHIP
        else:
            return OPF_SUBSYS_OR_GENERIC
    if op == "OP_WAYPOINTS_DONE":
        if  arg_index == 0 :
            return OPF_SHIP_WING
        else:
            return OPF_WAYPOINT_PATH
    if op == "OP_WAYPOINTS_DONE_DELAY":
        if  arg_index == 0 :
            return OPF_SHIP_WING
        elif  arg_index == 1 :
            return OPF_WAYPOINT_PATH
        else:
            return OPF_POSITIVE
    if op in ["OP_INVALIDATE_GOAL", "OP_VALIDATE_GOAL"]:
        return OPF_GOAL_NAME
    if op == "OP_SHIP_TYPE_DESTROYED":
        if  arg_index == 0 :
            return OPF_POSITIVE
        else:
            return OPF_SHIP_TYPE
    if op == "OP_KEY_PRESSED":
        if not arg_index:
            return OPF_KEYPRESS
        else:
            return OPF_POSITIVE
    if op in ["OP_KEY_RESET", "OP_KEY_RESET_MULTIPLE"]:
        return OPF_KEYPRESS
    if op in ["OP_EVENT_TRUE", "OP_EVENT_FALSE"]:
        return OPF_EVENT_NAME
    if op in ["OP_EVENT_INCOMPLETE", "OP_EVENT_TRUE_DELAY", "OP_EVENT_FALSE_DELAY", "OP_EVENT_TRUE_MSECS_DELAY", "OP_EVENT_FALSE_MSECS_DELAY"]:
        if arg_index == 0:
            return OPF_EVENT_NAME
        elif arg_index == 1:
            return OPF_POSITIVE
        elif arg_index == 2:
            return OPF_BOOL
        else:
            return OPF_NONE
    if op in ["OP_GOAL_INCOMPLETE", "OP_GOAL_TRUE_DELAY", "OP_GOAL_FALSE_DELAY"]:
        if not arg_index:
            return OPF_GOAL_NAME
        else:
            return OPF_POSITIVE
    if op == "OP_RESET_EVENT":
        return OPF_EVENT_NAME
    if op == "OP_RESET_GOAL":
        return OPF_GOAL_NAME
    if op == "OP_AI_CHASE_ANY":
        if not arg_index:
            return OPF_POSITIVE
        else:
            return OPF_BOOL
    if op in ["OP_AI_PLAY_DEAD", "OP_AI_PLAY_DEAD_PERSISTENT"]:
        return OPF_POSITIVE
    if op == "OP_AI_STAY_STILL":
        if arg_index == 0:
            return OPF_SHIP_POINT
        elif arg_index == 1:
            return OPF_POSITIVE
        else:
            return OPF_BOOL
    if op == "OP_AI_FORM_ON_WING":
        if arg_index == 0:
            return OPF_SHIP
        elif arg_index == 1:
            return OPF_POSITIVE
        else:
            return OPF_BOOL
    if op in ["OP_GOOD_REARM_TIME", "OP_BAD_REARM_TIME"]:
        if  arg_index == 0 :
            return OPF_IFF
        else:
            return OPF_POSITIVE
    if op == "OP_NUM_PLAYERS":
        return OPF_NONE
    if op == "OP_SKILL_LEVEL_AT_LEAST":
        return OPF_SKILL_LEVEL
    if op in ["OP_GRANT_MEDAL", "OP_WAS_MEDAL_GRANTED"]:
        return OPF_MEDAL_NAME
    if op == "OP_IS_CARGO_KNOWN":
        return OPF_SHIP
    if op == "OP_CARGO_KNOWN_DELAY":
        if  arg_index == 0 :
            return OPF_POSITIVE
        else:
            return OPF_SHIP
    if op == "OP_HAS_BEEN_TAGGED_DELAY":
        if  arg_index == 0 :
            return OPF_POSITIVE
        else:
            return OPF_SHIP
    if op == "OP_ARE_SHIP_FLAGS_SET":
        if arg_index == 0:
            return OPF_SHIP
        else:
            return OPF_SHIP_FLAG
    if op == "OP_ARE_WING_FLAGS_SET":
        if arg_index == 0:
            return OPF_WING
        else:
            return OPF_WING_FLAG
    if op == "OP_IS_SHIP_EMP_ACTIVE":
        return OPF_SHIP
    if op == "OP_CAP_SUBSYS_CARGO_KNOWN_DELAY":
        if  arg_index == 0 :
            return OPF_POSITIVE
        elif  arg_index == 1 :
            return OPF_SHIP
        else:
            return OPF_SUBSYSTEM
    if op in ["OP_ALLOW_SHIP", "OP_TECH_ADD_SHIP"]:
        return OPF_SHIP_CLASS_NAME
    if op in ["OP_ALLOW_WEAPON", "OP_TECH_ADD_WEAPON"]:
        return OPF_WEAPON_NAME
    if op in ["OP_TECH_ADD_INTEL", "OP_TECH_REMOVE_INTEL"]:
        return OPF_INTEL_NAME
    if op in ["OP_TECH_ADD_INTEL_XSTR", "OP_TECH_REMOVE_INTEL_XSTR"]:
        return OPF_INTEL_NAME if not (arg_index % 2) else OPF_NUMBER
    if op == "OP_TECH_RESET_TO_DEFAULT":
        return OPF_NONE
    if op == "OP_CHANGE_PLAYER_SCORE":
        if arg_index == 0:
            return OPF_NUMBER
        else:
            return OPF_SHIP
    if op == "OP_CHANGE_TEAM_SCORE":
        return OPF_NUMBER
    if op in ["OP_SHIP_VAPORIZE", "OP_SHIP_NO_VAPORIZE"]:
        return OPF_SHIP
    if op in ["OP_DONT_COLLIDE_INVISIBLE", "OP_COLLIDE_INVISIBLE"]:
        return OPF_SHIP
    if op in ["OP_SET_MOBILE", "OP_SET_IMMOBILE"]:
        return OPF_SHIP
    if op == "OP_IGNORE_KEY":
        if arg_index == 0:
            return OPF_NUMBER
        else:
            return OPF_KEYPRESS
    if op in ["OP_WARP_BROKEN", "OP_WARP_NOT_BROKEN", "OP_WARP_NEVER", "OP_WARP_ALLOWED"]:
        return OPF_SHIP
    if op == "OP_SET_SUBSPACE_DRIVE":
        if arg_index == 0:
            return OPF_BOOL
        else:
            return OPF_SHIP
    if op == "OP_FLASH_HUD_GAUGE":
        return OPF_BUILTIN_HUD_GAUGE
    if op == "OP_GOOD_PRIMARY_TIME":
        if arg_index == 0 or arg_index == 2:
            return OPF_SHIP_WING_WHOLETEAM
        elif arg_index == 1:
            return OPF_WEAPON_NAME
        else:
            return OPF_BOOL
    if op == "OP_GOOD_SECONDARY_TIME":
        if  arg_index == 0 :
            return OPF_IFF
        elif  arg_index == 1 :
            return OPF_POSITIVE
        elif  arg_index == 2 :
            return OPF_HUGE_WEAPON
        else:
            return OPF_SHIP
    if op in ["OP_PERCENT_SHIPS_ARRIVED", "OP_PERCENT_SHIPS_DEPARTED", "OP_PERCENT_SHIPS_DESTROYED"]:
        if  arg_index == 0 :
            return OPF_POSITIVE
        else:
            return OPF_SHIP_WING
    if op in ["OP_PERCENT_SHIPS_DISARMED", "OP_PERCENT_SHIPS_DISABLED", "OP_PERCENT_SHIPS_SCANNED"]:
        if  arg_index == 0 :
            return OPF_POSITIVE
        else:
            return OPF_SHIP
    if op == "OP_DEPART_NODE_DELAY":
        if  arg_index == 0 :
            return OPF_POSITIVE
        elif  arg_index == 1 :
            return OPF_JUMP_NODE_NAME
        else:
            return OPF_SHIP
    if op == "OP_DESTROYED_DEPARTED_DELAY":
        if  arg_index == 0 :
            return OPF_POSITIVE
        else:
            return OPF_SHIP_WING
    if op in ["OP_JETTISON_CARGO_DELAY", "OP_JETTISON_CARGO_NEW"]:
        if(arg_index == 1):
            return OPF_POSITIVE
        else:
            return OPF_SHIP
    if op == "OP_SET_DOCKED":
        if arg_index == 0:
            return OPF_SHIP
        elif arg_index == 1:
            return OPF_DOCKER_POINT
        elif arg_index == 2:
            return OPF_SHIP
        else:
            return OPF_DOCKEE_POINT
    if op == "OP_CARGO_NO_DEPLETE":
        if arg_index == 0:
            return OPF_SHIP
        else:
            return OPF_NUMBER
    if op == "OP_BEAM_FIRE":
        # switch detected
        if arg_index == 0:
            return OPF_SHIP
        if arg_index == 1:
            return OPF_SUBSYSTEM
        if arg_index == 2:
            return OPF_SHIP
        if arg_index == 3:
            return OPF_SUBSYSTEM
        if arg_index == 4:
            return OPF_BOOL
        else:
            # UNREACHABLE
            return OPF_NULL
    if op == "OP_BEAM_FIRE_COORDS":
        # switch detected
        if arg_index == 0:
            return OPF_SHIP
        if arg_index == 1:
            return OPF_SUBSYSTEM
        if arg_index == 5:
            return OPF_BOOL
        else:
            return OPF_NUMBER
    if op == "OP_BEAM_FLOATING_FIRE":
        # switch detected
        if arg_index == 0:
            return OPF_WEAPON_NAME
        if arg_index == 1:
            if arg_index == 6:
                return OPF_SHIP_OR_NONE
            if arg_index == 2:
                return OPF_IFF
            if arg_index == 7:
                return OPF_SUBSYSTEM_OR_NONE
        else:
            return OPF_NUMBER
    if op == "OP_IS_TAGGED":
        return OPF_SHIP
    if op == "OP_IS_PLAYER":
        if arg_index == 0:
            return OPF_BOOL
        else:
            return OPF_SHIP
    if op in ["OP_NUM_KILLS", "OP_NUM_ASSISTS", "OP_SHIP_SCORE", "OP_SHIP_DEATHS", "OP_RESPAWNS_LEFT"]:
        return OPF_SHIP
    if op == "OP_SET_RESPAWNS":
        if arg_index == 0 :
            return OPF_POSITIVE
        else:
            return OPF_SHIP
    if op == "OP_ADD_REMOVE_HOTKEY":
        if arg_index == 0:
            return OPF_BOOL
        if arg_index == 1:
            return OPF_POSITIVE
        else:
            return OPF_SHIP_WING
    if op == "OP_NUM_TYPE_KILLS":
        if(arg_index == 0):
            return OPF_SHIP
        else:
            return OPF_SHIP_TYPE
    if op == "OP_NUM_CLASS_KILLS":
        if(arg_index == 0):
            return OPF_SHIP
        else:
            return OPF_SHIP_CLASS_NAME
    if op in ["OP_BEAM_FREE", "OP_BEAM_LOCK", "OP_TURRET_FREE", "OP_TURRET_LOCK", "OP_TURRET_TAGGED_SPECIFIC", "OP_TURRET_TAGGED_CLEAR_SPECIFIC"]:
        if(arg_index == 0):
            return OPF_SHIP
        else:
            return OPF_SUBSYSTEM
    if op in ["OP_TURRET_SUBSYS_TARGET_DISABLE", "OP_TURRET_SUBSYS_TARGET_ENABLE"]:
        if(arg_index == 0):
            return OPF_SHIP
        else:
            return OPF_SUBSYS_OR_GENERIC
    if op == "OP_TURRET_CHANGE_WEAPON":
        if(arg_index == 0):
            return OPF_SHIP
        elif(arg_index == 1):
            return OPF_SUBSYSTEM
        elif(arg_index == 2):
            return OPF_WEAPON_NAME
        elif(arg_index > 2):
            return OPF_POSITIVE
        else:
            return OPF_NONE
    if op == "OP_TURRET_SET_DIRECTION_PREFERENCE":
        if(arg_index == 0):
            return OPF_SHIP
        elif(arg_index == 1):
            return OPF_NUMBER
        else:
            return OPF_SUBSYSTEM
    if op == "OP_TURRET_SET_RATE_OF_FIRE":
        if(arg_index == 0):
            return OPF_SHIP
        elif(arg_index == 1):
            return OPF_NUMBER
        else:
            return OPF_SUBSYSTEM
    if op == "OP_TURRET_SET_OPTIMUM_RANGE":
        if(arg_index == 0):
            return OPF_SHIP
        elif(arg_index == 1):
            return OPF_NUMBER
        else:
            return OPF_SUBSYSTEM
    if op == "OP_TURRET_SET_FORCED_TARGET":
        if arg_index == 0:
            return OPF_SHIP
        elif arg_index == 1:
            return OPF_SHIP
        else:
            return OPF_SUBSYSTEM
    if op == "OP_TURRET_SET_FORCED_SUBSYS_TARGET":
        if arg_index == 0:
            return OPF_SHIP
        elif arg_index == 1:
            return OPF_SUBSYSTEM
        elif arg_index == 2:
            return OPF_SHIP
        else:
            return OPF_SUBSYSTEM
    if op == "OP_TURRET_CLEAR_FORCED_TARGET":
        if arg_index == 0:
            return OPF_SHIP
        else:
            return OPF_SUBSYSTEM
    if op == "OP_TURRET_SET_INACCURACY":
        if arg_index == 0:
            return OPF_SHIP
        elif arg_index == 1:
            return OPF_NUMBER
        else:
            return OPF_SUBSYSTEM
    if op == "OP_TURRET_SET_TARGET_PRIORITIES":
        if(arg_index == 0):
            return OPF_SHIP
        elif(arg_index == 1):
            return OPF_SUBSYSTEM
        elif(arg_index == 2):
            return OPF_BOOL
        else:
            return OPF_TARGET_PRIORITIES
    if op == "OP_SET_ARMOR_TYPE":
        if(arg_index == 0):
            return OPF_SHIP
        elif(arg_index == 1):
            return OPF_BOOL
        elif(arg_index == 2):
            return OPF_ARMOR_TYPE
        else:
            return OPF_SUBSYS_OR_GENERIC
    if op == "OP_WEAPON_SET_DAMAGE_TYPE":
        if(arg_index == 0):
            return OPF_BOOL
        elif(arg_index == 1):
            return OPF_DAMAGE_TYPE
        elif(arg_index == 2):
            return OPF_BOOL
        else:
            return OPF_WEAPON_NAME
    if op == "OP_SHIP_SET_DAMAGE_TYPE":
        if(arg_index == 0):
            return OPF_BOOL
        elif(arg_index == 1):
            return OPF_DAMAGE_TYPE
        elif(arg_index == 2):
            return OPF_BOOL
        else:
            return OPF_SHIP
    if op == "OP_SHIP_SHOCKWAVE_SET_DAMAGE_TYPE":
        if(arg_index == 0):
            return OPF_DAMAGE_TYPE
        elif(arg_index == 1):
            return OPF_BOOL
        else:
            return OPF_SHIP_CLASS_NAME
    if op == "OP_FIELD_SET_DAMAGE_TYPE":
        if(arg_index == 0):
            return OPF_DAMAGE_TYPE
        else:
            return OPF_BOOL
    if op == "OP_TURRET_SET_TARGET_ORDER":
        if(arg_index == 0):
            return OPF_SHIP
        elif(arg_index == 1):
            return OPF_SUBSYSTEM
        else:
            return OPF_TURRET_TARGET_ORDER
    if op == "OP_SHIP_TURRET_TARGET_ORDER":
        if(arg_index == 0):
            return OPF_SHIP
        else:
            return OPF_TURRET_TARGET_ORDER
    if op in ["OP_LOCK_ROTATING_SUBSYSTEM", "OP_FREE_ROTATING_SUBSYSTEM", "OP_REVERSE_ROTATING_SUBSYSTEM"]:
        if arg_index == 0:
            return OPF_SHIP
        else:
            return OPF_ROTATING_SUBSYSTEM
    if op in ["OP_LOCK_TRANSLATING_SUBSYSTEM", "OP_FREE_TRANSLATING_SUBSYSTEM", "OP_REVERSE_TRANSLATING_SUBSYSTEM"]:
        if arg_index == 0:
            return OPF_SHIP
        else:
            return OPF_TRANSLATING_SUBSYSTEM
    if op == "OP_ROTATING_SUBSYS_SET_TURN_TIME":
        if arg_index == 0:
            return OPF_SHIP
        elif arg_index == 1:
            return OPF_ROTATING_SUBSYSTEM
        elif arg_index == 2:
            return OPF_NUMBER
        else:
            return OPF_POSITIVE
    if op == "OP_TRANSLATING_SUBSYS_SET_SPEED":
        if arg_index == 0:
            return OPF_SHIP
        elif arg_index == 1:
            return OPF_TRANSLATING_SUBSYSTEM
        elif arg_index == 2:
            return OPF_NUMBER
        else:
            return OPF_POSITIVE
    if op == "OP_TRIGGER_SUBMODEL_ANIMATION":
        if arg_index == 0:
            return OPF_SHIP
        elif arg_index == 1:
            return OPF_ANIMATION_TYPE
        elif arg_index == 2 or arg_index == 3:
            return OPF_NUMBER
        elif arg_index == 4:
            return OPF_BOOL
        elif arg_index == 5:
            return OPF_SUBSYSTEM
        else:
            return OPF_NONE
    if op in ["OP_BEAM_FREE_ALL", "OP_BEAM_LOCK_ALL", "OP_TURRET_FREE_ALL", "OP_TURRET_LOCK_ALL", "OP_TURRET_TAGGED_ONLY_ALL", "OP_TURRET_TAGGED_CLEAR_ALL"]:
        return OPF_SHIP
    if op == "OP_ADD_REMOVE_ESCORT":
        if(arg_index == 0):
            return OPF_SHIP
        else:
            return OPF_NUMBER
    if op == "OP_AWACS_SET_RADIUS":
        if(arg_index == 0):
            return OPF_SHIP
        elif(arg_index == 1):
            return OPF_AWACS_SUBSYSTEM
        else:
            return OPF_NUMBER
    if op == "OP_PRIMITIVE_SENSORS_SET_RANGE":
        if not arg_index:
            return OPF_SHIP
        else:
            return OPF_NUMBER
    if op == "OP_CAP_WAYPOINT_SPEED":
        if arg_index == 0:
            return OPF_SHIP
        else:
            return OPF_NUMBER
    if op == "OP_SET_WING_FORMATION":
        if arg_index == 0:
            return OPF_WING_FORMATION
        elif arg_index == 1:
            return OPF_NUMBER
        else:
            return OPF_WING
    if op == "OP_SUBSYS_SET_RANDOM":
        if arg_index == 0:
            return OPF_SHIP
        elif arg_index == 1 or arg_index == 2:
            return OPF_NUMBER
        else:
            return OPF_SUBSYSTEM
    if op == "OP_SUPERNOVA_START":
        return OPF_POSITIVE
    if op in ["OP_SHIELD_RECHARGE_PCT", "OP_WEAPON_RECHARGE_PCT", "OP_ENGINE_RECHARGE_PCT"]:
        return OPF_SHIP
    if op == "OP_GET_ETS_VALUE":
        if arg_index == 0:
            return OPF_STRING
        else:
            return OPF_SHIP
    if op == "OP_GET_POWER_OUTPUT":
        return OPF_SHIP
    if op == "OP_SET_ETS_VALUES":
        if arg_index < 3:
            return OPF_POSITIVE
        else:
            return OPF_SHIP
    if op == "OP_SHIELD_QUAD_LOW":
        if(arg_index == 0):
            return OPF_SHIP
        else:
            return OPF_NUMBER
    if op in ["OP_PRIMARY_AMMO_PCT", "OP_SECONDARY_AMMO_PCT"]:
        if(arg_index == 0):
            return OPF_SHIP
        else:
            return OPF_NUMBER
    if op in ["OP_GET_PRIMARY_AMMO", "OP_SET_PRIMARY_AMMO", "OP_GET_SECONDARY_AMMO", "OP_SET_SECONDARY_AMMO"]:
        if(arg_index == 0):
            return OPF_SHIP
        else:
            return OPF_NUMBER
    if op in ["OP_SET_PRIMARY_WEAPON", "OP_SET_SECONDARY_WEAPON"]:
        if(arg_index == 0):
            return OPF_SHIP
        elif arg_index == 2:
            return OPF_WEAPON_NAME
        else:
            return OPF_NUMBER
    if op in ["OP_TURRET_GET_PRIMARY_AMMO", "OP_TURRET_GET_SECONDARY_AMMO", "OP_TURRET_SET_PRIMARY_AMMO", "OP_TURRET_SET_SECONDARY_AMMO"]:
        if arg_index == 0:
            return OPF_SHIP
        elif arg_index == 1:
            return OPF_SUBSYSTEM
        else:
            return OPF_NUMBER
    if op == "OP_IS_IN_TURRET_FOV":
        if arg_index == 0 or arg_index == 1:
            return OPF_SHIP
        elif arg_index == 2:
            return OPF_SUBSYSTEM
        else:
            return OPF_POSITIVE
    if op == "OP_GET_NUM_COUNTERMEASURES":
        return OPF_SHIP
    if op == "OP_SET_NUM_COUNTERMEASURES":
        if arg_index == 0:
            return OPF_SHIP
        else:
            return OPF_POSITIVE
    if op in ["OP_LOCK_PRIMARY_WEAPON", "OP_UNLOCK_PRIMARY_WEAPON", "OP_LOCK_SECONDARY_WEAPON", "OP_UNLOCK_SECONDARY_WEAPON"]:
        pass
    if op in ["OP_LOCK_AFTERBURNER", "OP_UNLOCK_AFTERBURNER", "OP_LOCK_PRIMARY_WEAPON", "OP_UNLOCK_PRIMARY_WEAPON", "OP_LOCK_SECONDARY_WEAPON", "OP_UNLOCK_SECONDARY_WEAPON"]:
        return OPF_SHIP
    if op in ["OP_SET_AFTERBURNER_ENERGY", "OP_SET_WEAPON_ENERGY", "OP_SET_SHIELD_ENERGY"]:
        if arg_index == 0:
            return OPF_POSITIVE
        else:
            return OPF_SHIP
    if op == "OP_SET_AMBIENT_LIGHT":
        return OPF_POSITIVE
    if op == "OP_SET_POST_EFFECT":
        if arg_index == 0:
            return OPF_POST_EFFECT
        else:
            return OPF_POSITIVE
    if op == "OP_CHANGE_SUBSYSTEM_NAME":
        if arg_index == 0:
            return OPF_SHIP
        elif arg_index == 1:
            return OPF_STRING
        else:
            return OPF_SUBSYSTEM
    if op in ["OP_IS_SECONDARY_SELECTED", "OP_IS_PRIMARY_SELECTED"]:
        if(arg_index == 0):
            return OPF_SHIP
        else:
            return OPF_NUMBER
    if op == "OP_DAMAGED_ESCORT_LIST":
        if arg_index < 2:
            return OPF_NUMBER
        else:
            return OPF_SHIP
    if op == "OP_DAMAGED_ESCORT_LIST_ALL":
        return OPF_POSITIVE
    if op == "OP_CHANGE_SHIP_CLASS":
        if not arg_index:
            return OPF_SHIP_CLASS_NAME
        else:
            return OPF_SHIP
    if op == "OP_SHIP_COPY_DAMAGE":
        return OPF_SHIP
    if op in ["OP_DEACTIVATE_GLOW_POINTS", "OP_ACTIVATE_GLOW_POINTS", "OP_DEACTIVATE_GLOW_MAPS", "OP_ACTIVATE_GLOW_MAPS"]:
        return OPF_SHIP
    if op in ["OP_DEACTIVATE_GLOW_POINT_BANK", "OP_ACTIVATE_GLOW_POINT_BANK"]:
        if not arg_index:
            return OPF_SHIP
        else:
            return OPF_POSITIVE
    if op == "OP_SET_SKYBOX_MODEL":
        if arg_index == 0:
            return OPF_SKYBOX_MODEL_NAME
        elif arg_index == 1:
            return OPF_BOOL
        else:
            return OPF_SKYBOX_FLAGS
    if op == "OP_SET_SKYBOX_ORIENT":
        return OPF_NUMBER
    if op == "OP_SET_SKYBOX_ALPHA":
        return OPF_NUMBER
    if op == "OP_SET_SUPPORT_SHIP":
        if (arg_index == 0) or (arg_index == 2):
            return OPF_DEPARTURE_LOCATION
        if (arg_index == 1) or (arg_index == 3):
            return OPF_SHIP_WITH_BAY
        if arg_index == 4:
            return OPF_SUPPORT_SHIP_CLASS
        if arg_index == 5:
            return OPF_NUMBER
        if arg_index == 6:
            return OPF_NUMBER
    if op == "OP_SET_ARRIVAL_INFO":
        if arg_index == 0:
            return OPF_SHIP_WING
        elif arg_index == 1:
            return OPF_ARRIVAL_LOCATION
        elif arg_index == 2:
            return OPF_ARRIVAL_ANCHOR_ALL
        elif arg_index == 3:
            return OPF_NUMBER
        elif arg_index == 4 or arg_index == 5:
            return OPF_POSITIVE
        elif arg_index == 6:
            return OPF_BOOL
    if op == "OP_SET_DEPARTURE_INFO":
        if arg_index == 0:
            return OPF_SHIP_WING
        elif arg_index == 1:
            return OPF_DEPARTURE_LOCATION
        elif arg_index == 2:
            return OPF_SHIP_WITH_BAY
        elif arg_index == 3 or arg_index == 4:
            return OPF_NUMBER
        elif arg_index == 5:
            return OPF_BOOL
    if op == "OP_KAMIKAZE":
        if arg_index==0:
            return OPF_POSITIVE
        else:
            return OPF_SHIP_WING
    if op == "OP_NUM_SHIPS_IN_BATTLE":
        return OPF_SHIP_WING_WHOLETEAM
    if op == "OP_NUM_SHIPS_IN_WING":
        return OPF_WING
    if op == "OP_CURRENT_SPEED":
        return OPF_SHIP_WING
    if op == "OP_TURRET_FIRED_SINCE":
        if arg_index == 0:
            return OPF_SHIP
        elif arg_index == 1:
            return OPF_SUBSYSTEM
        else:
            return OPF_POSITIVE
    if op in ["OP_PRIMARY_FIRED_SINCE", "OP_SECONDARY_FIRED_SINCE"]:
        if arg_index == 0:
            return OPF_SHIP
        else:
            return OPF_POSITIVE
    if op in ["OP_HAS_PRIMARY_WEAPON", "OP_HAS_SECONDARY_WEAPON"]:
        if arg_index == 0:
            return OPF_SHIP
        elif arg_index == 1:
            return OPF_WEAPON_BANK_NUMBER
        else:
            return OPF_WEAPON_NAME
    if op in ["OP_TURRET_HAS_PRIMARY_WEAPON", "OP_TURRET_HAS_SECONDARY_WEAPON"]:
        if arg_index == 0:
            return OPF_SHIP
        elif arg_index == 1:
            return OPF_SUBSYSTEM
        elif arg_index == 2:
            return OPF_WEAPON_BANK_NUMBER
        else:
            return OPF_WEAPON_NAME
    if op == "OP_DIRECTIVE_VALUE":
        if arg_index == 0:
            return OPF_NUMBER
        else:
            return OPF_BOOL
    if op == "OP_GET_HOTKEY":
        return OPF_SHIP_WING
    if op in ["OP_NAV_IS_VISITED", "OP_NAV_DISTANCE", "OP_NAV_DEL", "OP_NAV_HIDE", "OP_NAV_RESTRICT", "OP_NAV_UNHIDE", "OP_NAV_UNRESTRICT", "OP_NAV_SET_VISITED", "OP_NAV_UNSET_VISITED", "OP_NAV_SELECT"]:
        return OPF_STRING
    if op in ["OP_NAV_SET_CARRY", "OP_NAV_UNSET_CARRY"]:
        return OPF_SHIP_WING
    if op in ["OP_NAV_SET_NEEDSLINK", "OP_NAV_UNSET_NEEDSLINK", "OP_NAV_ISLINKED"]:
        return OPF_SHIP
    if op in ["OP_NAV_USECINEMATICS", "OP_NAV_USEAP"]:
        return OPF_BOOL
    if op == "OP_NAV_ADD_WAYPOINT":
        if arg_index==0:
            return OPF_STRING
        elif arg_index==1:
            return OPF_WAYPOINT_PATH
        elif arg_index==2:
            return OPF_POSITIVE
        else:
            return OPF_SHIP_WING_WHOLETEAM
    if op == "OP_NAV_ADD_SHIP":
        if arg_index==0:
            return OPF_STRING
        else:
            return OPF_SHIP
    if op in ["OP_NAV_SET_COLOR", "OP_NAV_SET_VISITED_COLOR"]:
        if arg_index >= 0 and arg_index <= 2:
            return OPF_POSITIVE
        else:
            return OPF_STRING
    if op in ["OP_SCRAMBLE_MESSAGES", "OP_UNSCRAMBLE_MESSAGES"]:
        return OPF_SHIP
    if op == "OP_CUTSCENES_GET_FOV":
        return OPF_NONE
    if op in ["OP_CUTSCENES_SET_CUTSCENE_BARS", "OP_CUTSCENES_UNSET_CUTSCENE_BARS", "OP_CUTSCENES_FADE_IN", "OP_CUTSCENES_FADE_OUT", "OP_CUTSCENES_SET_TIME_COMPRESSION"]:
        return OPF_POSITIVE
    if op == "OP_CUTSCENES_SET_FOV":
        return OPF_NUMBER
    if op == "OP_CUTSCENES_SET_CAMERA":
        return OPF_STRING
    if op in ["OP_CUTSCENES_SET_CAMERA_POSITION", "OP_CUTSCENES_SET_CAMERA_FACING", "OP_CUTSCENES_SET_CAMERA_ROTATION"]:
        if(arg_index < 3):
            return OPF_NUMBER
        else:
            return OPF_POSITIVE
    if op == "OP_CUTSCENES_SET_CAMERA_FACING_OBJECT":
        if(arg_index < 1):
            return OPF_SHIP_WING_POINT
        else:
            return OPF_POSITIVE
    if op == "OP_CUTSCENES_SET_CAMERA_FOV":
        return OPF_POSITIVE
    if op in ["OP_CUTSCENES_SET_CAMERA_HOST", "OP_CUTSCENES_SET_CAMERA_TARGET"]:
        if(arg_index < 1):
            return OPF_SHIP_WING_POINT_OR_NONE
        else:
            return OPF_SUBSYSTEM_OR_NONE
    if op == "OP_CUTSCENES_RESET_CAMERA":
        return OPF_BOOL
    if op in ["OP_CUTSCENES_RESET_FOV", "OP_CUTSCENES_RESET_TIME_COMPRESSION"]:
        return OPF_NONE
    if op == "OP_CUTSCENES_FORCE_PERSPECTIVE":
        if arg_index == 1:
            return OPF_NUMBER
        else:
            return OPF_BOOL
    if op == "OP_SET_CAMERA_SHUDDER":
        if arg_index == 0 or arg_index == 1:
            return OPF_POSITIVE
        else:
            return OPF_BOOL
    if op == "OP_CUTSCENES_SHOW_SUBTITLE":
        if arg_index < 2:
            return OPF_NUMBER
        elif arg_index == 2:
            return OPF_STRING
        elif arg_index == 3:
            return OPF_POSITIVE
        elif arg_index == 4:
            return OPF_STRING
        elif arg_index == 5:
            return OPF_POSITIVE
        elif arg_index < 8:
            return OPF_BOOL
        elif arg_index < 12:
            return OPF_POSITIVE
        elif arg_index == 12:
            return OPF_BOOL
        elif arg_index == 13:
            return OPF_NUMBER
        else:
            return OPF_NONE
    if op == "OP_CUTSCENES_SHOW_SUBTITLE_TEXT":
        if arg_index == 0:
            return OPF_MESSAGE_OR_STRING
        elif arg_index == 1 or arg_index == 2:
            return OPF_NUMBER
        elif arg_index == 3 or arg_index == 4:
            return OPF_BOOL
        elif arg_index >= 5 and arg_index <= 10:
            return OPF_POSITIVE
        elif arg_index == 11:
            return OPF_FONT
        elif arg_index == 12:
            return OPF_BOOL
        elif arg_index == 13:
            return OPF_NUMBER
        elif arg_index == 14:
            return OPF_BOOL
        else:
            return OPF_NONE
    if op == "OP_CUTSCENES_SHOW_SUBTITLE_IMAGE":
        if arg_index == 0:
            return OPF_STRING
        elif arg_index == 1 or arg_index == 2:
            return OPF_NUMBER
        elif arg_index == 3 or arg_index == 4:
            return OPF_BOOL
        elif arg_index >= 5 and arg_index <= 8:
            return OPF_POSITIVE
        elif arg_index == 9 or arg_index == 10:
            return OPF_BOOL
        else:
            return OPF_NONE
    if op in ["OP_JUMP_NODE_SET_JUMPNODE_NAME", "OP_JUMP_NODE_SET_JUMPNODE_DISPLAY_NAME"]:
        if(arg_index==0):
            return OPF_JUMP_NODE_NAME
        elif arg_index==1:
            return OPF_STRING
        else:
            return OPF_NONE
    if op == "OP_JUMP_NODE_SET_JUMPNODE_COLOR":
        if(arg_index==0):
            return OPF_JUMP_NODE_NAME
        else:
            return OPF_POSITIVE
    if op == "OP_JUMP_NODE_SET_JUMPNODE_MODEL":
        if(arg_index==0):
            return OPF_JUMP_NODE_NAME
        elif arg_index == 1:
            return OPF_STRING
        else:
            return OPF_BOOL
    if op in ["OP_JUMP_NODE_SHOW_JUMPNODE", "OP_JUMP_NODE_HIDE_JUMPNODE"]:
        return OPF_JUMP_NODE_NAME
    if op == "OP_CHANGE_BACKGROUND":
        return OPF_POSITIVE
    if op in ["OP_ADD_BACKGROUND_BITMAP", "OP_ADD_BACKGROUND_BITMAP_NEW"]:
        if arg_index == 0:
            return OPF_BACKGROUND_BITMAP
        elif arg_index == 8:
            return OPF_VARIABLE_NAME
        else:
            return OPF_POSITIVE
    if op == "OP_REMOVE_BACKGROUND_BITMAP":
        return OPF_POSITIVE
    if op in ["OP_ADD_SUN_BITMAP", "OP_ADD_SUN_BITMAP_NEW"]:
        if arg_index == 0:
            return OPF_SUN_BITMAP
        elif arg_index == 5:
            return OPF_VARIABLE_NAME
        else:
            return OPF_POSITIVE
    if op == "OP_REMOVE_SUN_BITMAP":
        return OPF_POSITIVE
    if op == "OP_NEBULA_CHANGE_STORM":
        return OPF_NEBULA_STORM_TYPE
    if op == "OP_NEBULA_CHANGE_PATTERN":
        return OPF_NEBULA_PATTERN
    if op == "OP_NEBULA_TOGGLE_POOF":
        if not arg_index:
            return OPF_NEBULA_POOF
        else:
            return OPF_BOOL
    if op == "OP_NEBULA_SET_POOFS":
        if arg_index == 0:
            return OPF_BOOL
        else:
            return OPF_NEBULA_POOF
    if op == "OP_NEBULA_FADE_POOF":
        if arg_index == 0:
            return OPF_NEBULA_POOF
        elif arg_index == 1:
            return OPF_POSITIVE
        else:
            return OPF_BOOL
    if op == "OP_NEBULA_FADE_POOFS":
        if arg_index == 0:
            return OPF_BOOL
        elif arg_index == 1:
            return OPF_POSITIVE
        else:
            return OPF_NEBULA_POOF
    if op in ["OP_NEBULA_CHANGE_FOG_COLOR", "OP_NEBULA_SET_RANGE"]:
        return OPF_POSITIVE
    if op == "OP_VOLUMETRICS_TOGGLE":
        return OPF_BOOL
    if op == "OP_TOGGLE_ASTEROID_FIELD":
        return OPF_BOOL
    if op == "OP_SET_ASTEROID_FIELD":
        if arg_index <= 2:
            return OPF_POSITIVE
        elif arg_index <= 5:
            return OPF_BOOL
        elif arg_index <= 11:
            return OPF_NUMBER
        elif arg_index == 12:
            return OPF_BOOL
        elif arg_index <= 18:
            return OPF_NUMBER
        else:
            return OPF_SHIP
    if op == "OP_SET_DEBRIS_FIELD":
        if arg_index <= 1:
            return OPF_POSITIVE
        elif arg_index <= 4:
            return OPF_DEBRIS_TYPES
        elif arg_index <= 10:
            return OPF_NUMBER
        else:
            return OPF_BOOL
    if op == "OP_CONFIG_ASTEROID_FIELD":
        if arg_index <= 2:
            return OPF_POSITIVE
        elif arg_index <= 8:
            return OPF_NUMBER
        elif arg_index == 9:
            return OPF_BOOL
        elif arg_index <= 15:
            return OPF_NUMBER
        else:
            return OPF_ASTEROID_TYPES
    if op == "OP_CONFIG_DEBRIS_FIELD":
        if arg_index <= 1:
            return OPF_POSITIVE
        elif arg_index <= 7:
            return OPF_NUMBER
        elif arg_index <= 8:
            return OPF_BOOL
        else:
            return OPF_DEBRIS_TYPES
    if op == "OP_CONFIG_FIELD_TARGETS":
        if arg_index == 0:
            return OPF_BOOL
        else:
            return OPF_SHIP
    if op == "OP_SET_MOTION_DEBRIS":
        return OPF_MOTION_DEBRIS
    if op in ["OP_SCRIPT_EVAL_BOOL", "OP_SCRIPT_EVAL_NUM", "OP_SCRIPT_EVAL_BLOCK", "OP_SCRIPT_EVAL"]:
        return OPF_STRING
    if op == "OP_SCRIPT_EVAL_STRING":
        if not arg_index:
            return OPF_STRING
        else:
            return OPF_VARIABLE_NAME
    if op == "OP_SCRIPT_EVAL_MULTI":
        if arg_index == 0:
            return OPF_STRING
        elif arg_index == 1:
            return OPF_BOOL
        else:
            return OPF_SHIP
    if op == "OP_CHANGE_IFF_COLOR":
        if (arg_index == 0) or (arg_index == 1):
            return OPF_IFF
        elif (arg_index >= 2) and (arg_index <=4):
            return OPF_POSITIVE
        else:
            return OPF_SHIP_WING
    if op == "OP_HUD_DISPLAY_GAUGE":
        if  arg_index == 0 :
            return OPF_POSITIVE
        else:
            return OPF_HUD_ELEMENT
    if op in ["OP_DISABLE_ETS", "OP_ENABLE_ETS"]:
        return OPF_SHIP
    if op == "OP_IS_FACING":
        if arg_index == 0:
            return OPF_SHIP
        elif arg_index == 1:
            return OPF_SHIP_POINT
        else:
            return OPF_POSITIVE
    if op == "OP_FORCE_GLIDE":
        if arg_index == 0:
            return OPF_SHIP
        else:
            return OPF_BOOL
    if op == "OP_HUD_SET_DIRECTIVE":
        if arg_index == 0:
            return OPF_CUSTOM_HUD_GAUGE
        else:
            return OPF_STRING
    if op == "OP_HUD_GAUGE_SET_ACTIVE":
        if arg_index == 0:
            return OPF_ANY_HUD_GAUGE
        else:
            return OPF_BOOL
    if op == "OP_HUD_ACTIVATE_GAUGE_TYPE":
        if arg_index == 0:
            return OPF_BUILTIN_HUD_GAUGE
        else:
            return OPF_BOOL
    if op == "OP_HUD_SET_CUSTOM_GAUGE_ACTIVE":
        if arg_index == 0:
            return OPF_BOOL
        else:
            return OPF_CUSTOM_HUD_GAUGE
    if op == "OP_HUD_SET_BUILTIN_GAUGE_ACTIVE":
        if arg_index == 0:
            return OPF_BOOL
        else:
            return OPF_BUILTIN_HUD_GAUGE
    if op == "OP_GET_COLGROUP_ID":
        return OPF_SHIP
    if op in ["OP_ADD_TO_COLGROUP", "OP_REMOVE_FROM_COLGROUP"]:
        if arg_index == 0:
            return OPF_SHIP
        else:
            return OPF_POSITIVE
    if op in ["OP_ADD_TO_COLGROUP_NEW", "OP_REMOVE_FROM_COLGROUP_NEW"]:
        if arg_index == 0:
            return OPF_POSITIVE
        else:
            return OPF_SHIP
    if op == "OP_SHIP_EFFECT":
        if arg_index == 0:
            return OPF_SHIP_EFFECT
        elif arg_index == 1:
            return OPF_NUMBER
        else:
            return OPF_SHIP_WING
    if op == "OP_CLEAR_SUBTITLES":
        return OPF_NONE
    if op == "OP_SET_THRUSTERS":
        if arg_index == 0:
            return OPF_BOOL
        else:
            return OPF_SHIP
    if op == "OP_OVERRIDE_MOTION_DEBRIS":
        return OPF_BOOL
    if op == "OP_REPLACE_TEXTURE":
        if arg_index == 0 or arg_index == 1:
            return OPF_STRING
        else:
            return OPF_SHIP_WING
    if op == "OP_REPLACE_TEXTURE_SKYBOX":
        return OPF_STRING
    if op == "OP_SET_ALPHA_MULT":
        if arg_index == 0:
            return OPF_POSITIVE
        else:
            return OPF_SHIP_WING
    if op == "OP_IS_LANGUAGE":
        return OPF_LANGUAGE
    if op == "OP_USED_CHEAT":
        return OPF_STRING
    if op in ["OP_TRIGGER_ANIMATION_NEW", "OP_STOP_LOOPING_ANIMATION"]:
        if arg_index == 0:
            return OPF_SHIP
        elif arg_index == 1:
            return OPF_ANIMATION_TYPE
        elif arg_index == 2:
            return OPF_ANIMATION_NAME
        else:
            return OPF_BOOL
    if op == "OP_UPDATE_MOVEABLE":
        if arg_index == 0:
            return OPF_SHIP
        elif(arg_index == 1):
            return OPF_ANIMATION_NAME
        else:
            return OPF_NUMBER
    if op in ["OP_IS_CONTAINER_EMPTY", "OP_GET_CONTAINER_SIZE"]:
        if arg_index == 0:
            return OPF_CONTAINER_NAME
        else:
            return OPF_NONE
    if op == "OP_LIST_HAS_DATA":
        if arg_index == 0:
            return OPF_LIST_CONTAINER_NAME
        else:
            return OPF_CONTAINER_VALUE
    if op == "OP_LIST_DATA_INDEX":
        if arg_index == 0:
            return OPF_LIST_CONTAINER_NAME
        elif arg_index == 1:
            return OPF_CONTAINER_VALUE
        else:
            return OPF_NONE
    if op == "OP_MAP_HAS_KEY":
        if arg_index == 0:
            return OPF_MAP_CONTAINER_NAME
        else:
            return OPF_CONTAINER_VALUE
    if op == "OP_MAP_HAS_DATA_ITEM":
        if arg_index == 0:
            return OPF_MAP_CONTAINER_NAME
        elif arg_index == 1:
            return OPF_CONTAINER_VALUE
        elif arg_index == 2:
            return OPF_VARIABLE_NAME
        else:
            return OPF_NONE
    if op == "OP_SET_GRAVITY_ACCEL":
        return OPF_POSITIVE
    # Default/Fallback
    return OPF_NONE