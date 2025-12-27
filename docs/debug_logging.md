CRITICAL: Debug logging system:
* Use the configurable debug system with levels (0-3+) and per-Action filtering
* Level 0: off (default), Level 1: summary counts, Level 2: lifecycle events, Level 3+: verbose details
* Programmatic API: `set_debug_options(level=2, include=["MoveUntil"])` or `observe_actions(MoveUntil)`
* Environment variables: `ARCADEACTIONS_DEBUG=2`, `ARCADEACTIONS_DEBUG_ALL=1`, `ARCADEACTIONS_DEBUG_INCLUDE=MoveUntil,CallbackUntil`
* Level 1 summary shows ALL action counts (not filtered) - filters only apply to Level 2+ detailed logging