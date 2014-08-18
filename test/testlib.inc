#include "testlib_extras.inc"

public bool:IsPlayer(client) {
    return client >= 1 && client <= MaxClients
          && IsClientConnected(client) && IsClientInGame(client)
          && !IsFakeClient(client);
}
