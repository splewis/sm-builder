#pragma semicolon 1
#include <sourcemod>
#include "testlib.inc"

public Plugin:myinfo = {
    name = "",
    author = "splewis",
    description = "",
    version = "1.0",
    url = ""
};

public OnPluginStart() {
    PrintToServer("Plugin succesfully started");
    PrintToServer("IsPlayer(3) = %d", IsPlayer(3));
    PrintToServer("IsLessThan10(3) = %d", IsLessThan10(3));
}
