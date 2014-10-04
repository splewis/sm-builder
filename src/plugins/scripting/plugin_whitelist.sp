#pragma semicolon 1
#include <sourcemod>
#include <regex>

#define CONFIG_FILE "configs/plugin_whitelist.cfg"
#define PLUGIN_NAME_LENGTH 128

public Plugin:myinfo = {
    name = "Plugin whitelist",
    author = "splewis",
    description = "Removes plugins not found in a whitelist text file",
    version = "0.0.1",
    url = "github.com/splewis/sm-builder"
};

public OnMapEnd() {
    Handle toRemove = GetPluginsToRemove();
    char plugin[PLUGIN_NAME_LENGTH];
    for (int i = 0; i < GetArraySize(toRemove); i++) {
        GetArrayString(toRemove, i, plugin, sizeof(plugin));
        DisablePlugin(plugin);
    }
    CloseHandle(toRemove);
}

/**
 * Returns an adt array of the filenames for all plugins that should be removed,
 * according to the current contents of CONFIG_FILE.
 */
public Handle GetPluginsToRemove() {
    Handle pluginList = CreateArray(PLUGIN_NAME_LENGTH);

    char configFile[PLATFORM_MAX_PATH];
    BuildPath(Path_SM, configFile, sizeof(configFile), CONFIG_FILE);
    if (!FileExists(configFile)) {
        LogError("The plugin whitelist config file does not exist: %s", configFile);
        return pluginList;
    }

    Handle kv = CreateKeyValues("PluginWhitelist");
    if (!FileToKeyValues(kv, configFile)) {
        LogError("failed to parse keyvalues for %s", configFile);
        return pluginList;
    }


    // adds every plugin to the array
    Handle it = GetPluginIterator();
    while (MorePlugins(it)) {
        Handle plugin = ReadPlugin(it);

        // don't add "myself" to the list
        if (GetMyHandle() != plugin) {
            char buffer[PLUGIN_NAME_LENGTH];
            GetPluginFilename(plugin, buffer, sizeof(buffer));
            PushArrayString(pluginList, buffer);
        }
    }
    CloseHandle(it);


    // exact matches
    if (KvJumpToKey(kv, "Exact") && KvGotoFirstSubKey(kv, false)) {
        do {
            char name[128];
            KvGetSectionName(kv, name, sizeof(name));
            RemoveExactMatches(pluginList, name);
        } while (KvGotoNextKey(kv, false));
        KvRewind(kv);
    }

    // regex matches
    if (KvJumpToKey(kv, "Regex") && KvGotoFirstSubKey(kv, false)) {
        do {
            char name[128];
            KvGetSectionName(kv, name, sizeof(name));
            RemoveRegexMatches(pluginList, name);
        } while (KvGotoNextKey(kv, false));
        KvRewind(kv);
    }

    for (int i = 0; i < GetArraySize(pluginList); i++) {
        char buffer[PLUGIN_NAME_LENGTH];
        GetArrayString(pluginList, i, buffer, sizeof(buffer));
        LogMessage("removing plugin: %s", buffer);
    }

    CloseHandle(kv);

    return pluginList;
}

static void RemoveExactMatches(Handle pluginList, char pluginName[PLUGIN_NAME_LENGTH]) {
    for (int i = 0; i < GetArraySize(pluginList); i++) {
        char buffer[PLUGIN_NAME_LENGTH];
        GetArrayString(pluginList, i, buffer, sizeof(buffer));
        if (StrEqual(buffer, pluginName)) {
            RemoveFromArray(pluginList, i);
            i--;
        }
    }
}

static void RemoveRegexMatches(Handle pluginList, char regex[PLUGIN_NAME_LENGTH]) {
    Handle compiledRegex = CompileRegex(regex);
    if (compiledRegex == INVALID_HANDLE) {
        LogError("Failed to compile regex: %s", regex);
        return;
    }

    for (int i = 0; i < GetArraySize(pluginList); i++) {
        char pluginName[PLUGIN_NAME_LENGTH];
        GetArrayString(pluginList, i, pluginName, sizeof(pluginName));
        if (MatchRegex(compiledRegex, pluginName) > 0) {
            RemoveFromArray(pluginList, i);
            i--;
        }
    }
}

// Adapted from DarthNinja's plugin EnableDisable plugin:
// https://forums.alliedmods.net/showthread.php?t=182086
public bool DisablePlugin(char pluginFileName[PLUGIN_NAME_LENGTH]) {
    char disabledpath[256];
    char enabledpath[256];

    // add the extension if missing
    if (StrContains(pluginFileName, ".smx", false) == -1)
        Format(pluginFileName, sizeof(pluginFileName), "%s.smx", pluginFileName);

    BuildPath(Path_SM, disabledpath, sizeof(disabledpath), "plugins/disabled/%s", pluginFileName);
    BuildPath(Path_SM, enabledpath, sizeof(enabledpath), "plugins/%s", pluginFileName);

    if (!FileExists(enabledpath)) {
        return false;
    }

    if (FileExists(disabledpath)) {
        DeleteFile(disabledpath);
        LogMessage("An existing plugin file (%s) has been detected that conflicts with the one being moved. The old file has been deleted.", disabledpath);
    }

    Handle loaded = FindPluginByFile(pluginFileName);
    char PluginName[128];
    if (loaded != INVALID_HANDLE)
        GetPluginInfo(loaded, PlInfo_Name, PluginName, sizeof(PluginName));
    else
        strcopy(PluginName, sizeof(PluginName), pluginFileName);

    ServerCommand("sm plugins unload %s", pluginFileName);
    RenameFile(disabledpath, enabledpath);

    return true;
}
