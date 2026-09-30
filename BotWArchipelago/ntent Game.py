[1mdiff --git a/Locations.py b/Locations.py[m
[1mindex d2ee209..eb539cb 100644[m
[1m--- a/Locations.py[m
[1m+++ b/Locations.py[m
[36m@@ -1,4 +1,4 @@[m
[31m-from BaseClasses import Location[m
[32m+[m[32mfrom BaseClasses import Location #type: ignore[m
 from .Data import location_table, event_table[m
 from .Game import starting_index, game_name[m
 from typing import Any[m
[1mdiff --git a/Rules.py b/Rules.py[m
[1mindex 29633df..09df467 100644[m
[1m--- a/Rules.py[m
[1m+++ b/Rules.py[m
[36m@@ -7,10 +7,10 @@[m [mfrom .hooks import Rules[m
 from .Helpers import clamp, is_item_enabled, is_option_enabled, get_option_value, convert_string_to_type,\[m
     format_to_valid_identifier, format_state_prog_items_key, ProgItemsCat[m
 [m
[31m-from BaseClasses import MultiWorld, CollectionState[m
[31m-from worlds.AutoWorld import World[m
[31m-from worlds.generic.Rules import set_rule, add_rule[m
[31m-from Options import Choice, Toggle, Range, NamedRange, NumericOption[m
[32m+[m[32mfrom BaseClasses import MultiWorld, CollectionState # type: ignore[m
[32m+[m[32mfrom worlds.AutoWorld import World # type: ignore[m
[32m+[m[32mfrom worlds.generic.Rules import set_rule, add_rule # type: ignore[m
[32m+[m[32mfrom Options import Choice, Toggle, Range, NamedRange, NumericOption # type: ignore[m
 [m
 import re[m
 import math[m
[36m@@ -94,10 +94,10 @@[m [mdef evaluate_postfix(expr: str, location: str) -> bool:[m
                 op = stack.pop()[m
                 stack.append(not op)[m
     except Exception:[m
[31m-        raise construct_logic_error(location, LogicErrorSource.EVALUATE_POSTFIX)[m
[32m+[m[32m        raise construct_logic_error(location, LogicErrorSource.EVALUATE_POSTFIX) # type: ignore[m
 [m
     if len(stack) != 1:[m
[31m-        raise construct_logic_error(location, LogicErrorSource.EVALUATE_STACK_SIZE)[m
[32m+[m[32m        raise construct_logic_error(location, LogicErrorSource.EVALUATE_STACK_SIZE) # type: ignore[m
 [m
     return stack.pop()[m
 [m
[36m@@ -216,14 +216,14 @@[m [mdef set_rules(world: "ManualWorld", multiworld: MultiWorld, player: int):[m
                 if total >= item_count:[m
                     requires_list = requires_list.replace(item_base, "1")[m
 [m
[31m-            if total <= item_count:[m
[32m+[m[32m            if total <= item_count: # type: ignore[m
                 requires_list = requires_list.replace(item_base, "0")[m
 [m
         requires_list = re.sub(r'\s?\bAND\b\s?', '&', requires_list, count=0, flags=re.IGNORECASE)[m
         requires_list = re.sub(r'\s?\bOR\b\s?', '|', requires_list, count=0, flags=re.IGNORECASE)[m
 [m
         requires_string = infix_to_postfix("".join(requires_list), area)[m
[31m-        return (evaluate_postfix(requires_string, area))[m
[32m+[m[32m        return (evaluate_postfix(requires_string, area)) # type: ignore[m
 [m
     # this is only called when the area (think, location or region) has a "requires" field that is a dict[m
     def checkRequireDictForArea(state: CollectionState, area: dict):[m
[36m@@ -254,7 +254,7 @@[m [mdef set_rules(world: "ManualWorld", multiworld: MultiWorld, player: int):[m
                     canAccess = True[m
                     break[m
             else:[m
[31m-                item_parts = item.split(":")[m
[32m+[m[32m                item_parts = item.split(":") # type: ignore[m
                 item_name = item[m
                 item_count = 1[m
 [m
[36m@@ -288,7 +288,7 @@[m [mdef set_rules(world: "ManualWorld", multiworld: MultiWorld, player: int):[m
         used_location_names.extend([l.name for l in multiworld.get_region(region, player).locations])[m
         if region != "Menu":[m
             for exitRegion in multiworld.get_region(region, player).entrances:[m
[31m-                def fullRegionCheck(state: CollectionState, region=regionMap[region], region_name=exitRegion.name):[m
[32m+[m[32m                def fullRegionCheck(state: CollectionState, region=regionMap[region], region_name=exitRegion.name):  # type: ignore[m
                     region['name'] = region_name[m
                     region['is_region'] = True[m
 [m
[36m@@ -334,7 +334,7 @@[m [mdef set_rules(world: "ManualWorld", multiworld: MultiWorld, player: int):[m
             set_rule(locFromWorld, checkBothLocationAndRegion)[m
         elif "region" in location: # Only region access required, check the location's region's requires[m
             def fullRegionCheck(state, region=locationRegion):[m
[31m-                return fullLocationOrRegionCheck(state, region)[m
[32m+[m[32m                return fullLocationOrRegionCheck(state, region) # type: ignore[m
 [m
             set_rule(locFromWorld, fullRegionCheck)[m
         else: # No location region and no location requires? It's accessible.[m
[36m@@ -362,7 +362,7 @@[m [mdef set_rules(world: "ManualWorld", multiworld: MultiWorld, player: int):[m
                     args.insert(index, state)[m
                 continue[m
             if parameter.name.lower() == "player":[m
[31m-                args.insert(index, player)[m
[32m+[m[32m                args.insert(index, player) # type: ignore[m
                 continue[m
 [m
             if index < len(args) and args[index] != "":[m
[36m@@ -569,16 +569,16 @@[m [mdef YamlCompare(world: "ManualWorld", multiworld: MultiWorld, state: CollectionS[m
         if not hasattr(world, 'yaml_compare_rule_cache'):[m
             world.yaml_compare_rule_cache = dict[str,bool]()[m
 [m
[31m-    if skipCache or world.yaml_compare_rule_cache.get(cacheindex, None) is None:[m
[32m+[m[32m    if skipCache or world.yaml_compare_rule_cache.get(cacheindex, None) is None: # type: ignore[m
         try:[m
             if issubclass(type(option), Choice):[m
[31m-                value = convert_string_to_type(value, str|int)[m
[32m+[m[32m                value = convert_string_to_type(value, str|int) # type: ignore[m
                 if isinstance(value, str):[m
                     value = option.from_text(value).value[m
 [m
             elif issubclass(type(option), Range):[m
                 if type(option).__base__ == NamedRange:[m
[31m-                    value = convert_string_to_type(value, str|int)[m
[32m+[m[32m                    value = convert_string_to_type(value, str|int) # type: ignore[m
                     if isinstance(value, str):[m
                         value = option.from_text(value).value[m
 [m
[36m@@ -608,10 +608,10 @@[m [mdef YamlCompare(world: "ManualWorld", multiworld: MultiWorld, state: CollectionS[m
         result = comp_symbols[comparator](option.value, value)[m
 [m
         if not skipCache:[m
[31m-            world.yaml_compare_rule_cache[cacheindex] = result[m
[32m+[m[32m            world.yaml_compare_rule_cache[cacheindex] = result # type: ignore[m
 [m
     else: #if exists and not skipCache[m
[31m-        result = world.yaml_compare_rule_cache[cacheindex][m
[32m+[m[32m        result = world.yaml_compare_rule_cache[cacheindex] # type: ignore[m
 [m
     return not result if reverse_result else result[m
 [m
[1mdiff --git a/update_apworld.ps1 b/update_apworld.ps1[m
[1mindex 1d1da14..6f423a7 100644[m
[1m--- a/update_apworld.ps1[m
[1m+++ b/update_apworld.ps1[m
[36m@@ -1,122 +1,122 @@[m
[31m-[m
[31m-$ErrorActionPreference = "Stop"[m
[31m-[m
[31m-$ProjectDir = "C:\Projects\BotWArchipelago"[m
[31m-$ArchivePath = Join-Path $ProjectDir "botw.apworld"[m
[31m-$ZipPath = Join-Path $ProjectDir "botw.zip"[m
[31m-$CustomWorldsDir = "C:\ProgramData\Archipelago\custom_worlds"[m
[31m-$InstalledPath = Join-Path $CustomWorldsDir "botw.apworld"[m
[31m-[m
[31m-$StageRoot = Join-Path $env:TEMP "BotW_APWorld_Build"[m
[31m-$PackageDir = Join-Path $StageRoot "botw"[m
[31m-[m
[31m-try {[m
[31m-    Write-Host ""[m
[31m-    Write-Host "=== BotW Archipelago World Updater ===" -ForegroundColor Cyan[m
[31m-    Write-Host ""[m
[31m-[m
[31m-    # Verify the Manual repository files.[m
[31m-    $RequiredFiles = @([m
[31m-        "__init__.py",[m
[31m-        "Game.py",[m
[31m-        "Data.py",[m
[31m-        "Items.py",[m
[31m-        "Locations.py",[m
[31m-        "Regions.py",[m
[31m-        "Rules.py",[m
[31m-        "data\game.json"[m
[31m-    )[m
[31m-[m
[31m-    foreach ($File in $RequiredFiles) {[m
[31m-        if (-not (Test-Path (Join-Path $ProjectDir $File))) {[m
[31m-            throw "Required repository file not found: $ProjectDir\$File"[m
[31m-        }[m
[31m-    }[m
[31m-[m
[31m-    # Create a clean staging directory.[m
[31m-    Remove-Item $StageRoot -Recurse -Force -ErrorAction SilentlyContinue[m
[31m-    New-Item -ItemType Directory -Path $PackageDir -Force |[m
[31m-        Out-Null[m
[31m-[m
[31m-    # Copy the repository into one package directory.[m
[31m-    # Exclude Git metadata, editor settings, caches, and old archives.[m
[31m-    & robocopy $ProjectDir $PackageDir /E `[m
[31m-        /XD ".git" ".vscode" "__pycache__" `[m
[31m-        /XF "*.apworld" "*.zip" "update_apworld.ps1" `[m
[31m-        /NFL /NDL /NJH /NJS /NP[m
[31m-[m
[31m-    $RobocopyExitCode = $LASTEXITCODE[m
[31m-    if ($RobocopyExitCode -ge 8) {[m
[31m-        throw "Failed to stage repository files. Robocopy exit code: $RobocopyExitCode"[m
[31m-    }[m
[31m-[m
[31m-    if (-not (Test-Path (Join-Path $PackageDir "__init__.py"))) {[m
[31m-        throw "Staged package is missing __init__.py."[m
[31m-    }[m
[31m-[m
[31m-    # Ensure the custom worlds directory exists.[m
[31m-    if (-not (Test-Path $CustomWorldsDir)) {[m
[31m-        New-Item -ItemType Directory -Path $CustomWorldsDir -Force |[m
[31m-            Out-Null[m
[31m-    }[m
[31m-[m
[31m-    Remove-Item $ArchivePath, $ZipPath -Force -ErrorAction SilentlyContinue[m
[31m-[m
[31m-    # Archive the botw directory itself, preserving the botw/ prefix.[m
[31m-    Compress-Archive -Path $PackageDir -DestinationPath $ZipPath -Force[m
[31m-    Move-Item $ZipPath $ArchivePath -Force[m
[31m-[m
[31m-    # Verify the APWorld archive structure.[m
[31m-    Add-Type -AssemblyName System.IO.Compression.FileSystem[m
[31m-    $Zip = [System.IO.Compression.ZipFile]::OpenRead($ArchivePath)[m
[31m-[m
[31m-    try {[m
[31m-        $Entries = @([m
[31m-            $Zip.Entries | ForEach-Object {[m
[31m-                $_.FullName.Replace("\", "/")[m
[31m-            }[m
[31m-        )[m
[31m-[m
[31m-        if ($Entries -notcontains "botw/__init__.py") {[m
[31m-            throw "Archive is missing botw/__init__.py."[m
[31m-        }[m
[31m-[m
[31m-        if ($Entries -notcontains "botw/Game.py") {[m
[31m-            throw "Archive is missing botw/Game.py."[m
[31m-        }[m
[31m-[m
[31m-        if ($Entries -notcontains "botw/data/game.json") {[m
[31m-            throw "Archive is missing botw/data/game.json."[m
[31m-        }[m
[31m-[m
[31m-        $TopLevelEntries = @([m
[31m-            $Entries |[m
[31m-                Where-Object { $_ -and $_ -notmatch "^botw/" }[m
[31m-        )[m
[31m-[m
[31m-        if ($TopLevelEntries.Count -gt 0) {[m
[31m-            throw "Unexpected files outside the botw directory: $($TopLevelEntries -join ', ')"[m
[31m-        }[m
[31m-    }[m
[31m-    finally {[m
[31m-        $Zip.Dispose()[m
[31m-    }[m
[31m-[m
[31m-    # Install the verified archive.[m
[31m-    Copy-Item $ArchivePath $InstalledPath -Force[m
[31m-[m
[31m-    Write-Host "SUCCESS!" -ForegroundColor Green[m
[31m-    Write-Host "Built:     $ArchivePath"[m
[31m-    Write-Host "Installed: $InstalledPath"[m
[31m-    Write-Host "Archive contains one top-level botw/ directory."[m
[31m-    Write-Host ""[m
[31m-    Write-Host "Restart Archipelago before testing changes."[m
[31m-}[m
[31m-catch {[m
[31m-    Write-Host ""[m
[31m-    Write-Host "UPDATE FAILED:" -ForegroundColor Red[m
[31m-    Write-Host $_.Exception.Message -ForegroundColor Red[m
[31m-}[m
[31m-finally {[m
[31m-    Remove-Item $StageRoot -Recurse -Force -ErrorAction SilentlyContinue[m
[32m+[m[41m[m
[32m+[m[32m$ErrorActionPreference = "Stop"[m[41m[m
[32m+[m[41m[m
[32m+[m[32m$ProjectDir = "C:\Projects\BotWArchipelago"[m[41m[m
[32m+[m[32m$ArchivePath = Join-Path $ProjectDir "botw.apworld"[m[41m[m
[32m+[m[32m$ZipPath = Join-Path $ProjectDir "botw.zip"[m[41m[m
[32m+[m[32m$CustomWorldsDir = "C:\ProgramData\Archipelago\custom_worlds"[m[41m[m
[32m+[m[32m$InstalledPath = Join-Path $CustomWorldsDir "botw.apworld"[m[41m[m
[32m+[m[41m[m
[32m+[m[32m$StageRoot = Join-Path $env:TEMP "BotW_APWorld_Build"[m[41m[m
[32m+[m[32m$PackageDir = Join-Path $StageRoot "botw"[m[41m[m
[32m+[m[41m[m
[32m+[m[32mtry {[m[41m[m
[32m+[m[32m    Write-Host ""[m[41m[m
[32m+[m[32m    Write-Host "=== BotW Archipelago World Updater ===" -ForegroundColor Cyan[m[41m[m
[32m+[m[32m    Write-Host ""[m[41m[m
[32m+[m[41m[m
[32m+[m[32m    # Verify the Manual repository files.[m[41m[m
[32m+[m[32m    $RequiredFiles = @([m[41m[m
[32m+[m[32m        "__init__.py",[m[41m[m
[32m+[m[32m        "Game.py",[m[41m[m
[32m+[m[32m        "Data.py",[m[41m[m
[32m+[m[32m        "Items.py",[m[41m[m
[32m+[m[32m        "Locations.py",[m[41m[m
[32m+[m[32m        "Regions.py",[m[41m[m
[32m+[m[32m        "Rules.py",[m[41m[m
[32m+[m[32m        "data\game.json"[m[41m[m
[32m+[m[32m    )[m[41m[m
[32m+[m[41m[m
[32m+[m[32m    foreach ($File in $RequiredFiles) {[m[41m[m
[32m+[m[32m        if (-not (Test-Path (Join-Path $ProjectDir $File))) {[m[41m[m
[32m+[m[32m            throw "Required repository file not found: $ProjectDir\$File"[m[41m[m
[32m+[m[32m        }[m[41m[m
[32m+[m[32m    }[m[41m[m
[32m+[m[41m[m
[32m+[m[32m    # Create a clean staging directory.[m[41m[m
[32m+[m[32m    Remove-Item $StageRoot -Recurse -Force -ErrorAction SilentlyContinue[m[41m[m
[32m+[m[32m    New-Item -ItemType Directory -Path $PackageDir -Force |[m[41m[m
[32m+[m[32m        Out-Null[m[41m[m
[32m+[m[41m[m
[32m+[m[32m    # Copy the repository into one package directory.[m[41m[m
[32m+[m[32m    # Exclude Git metadata, editor settings, caches, and old archives.[m[41m[m
[32m+[m[32m    & robocopy $ProjectDir $PackageDir /E `[m[41m[m
[32m+[m[32m        /XD ".git" ".vscode" "__pycache__" `[m[41m[m
[32m+[m[32m        /XF "*.apworld" "*.zip" "update_apworld.ps1" `[m[41m[m
[32m+[m[32m        /NFL /NDL /NJH /NJS /NP[m[41m[m
[32m+[m[41m[m
[32m+[m[32m    $RobocopyExitCode = $LASTEXITCODE[m[41m[m
[32m+[m[32m    if ($RobocopyExitCode -ge 8) {[m[41m[m
[32m+[m[32m        throw "Failed to stage repository files. Robocopy exit code: $RobocopyExitCode"[m[41m[m
[32m+[m[32m    }[m[41m[m
[32m+[m[41m[m
[32m+[m[32m    if (-not (Test-Path (Join-Path $PackageDir "__init__.py"))) {[m[41m[m
[32m+[m[32m        throw "Staged package is missing __init__.py."[m[41m[m
[32m+[m[32m    }[m[41m[m
[32m+[m[41m[m
[32m+[m[32m    # Ensure the custom worlds directory exists.[m[41m[m
[32m+[m[32m    if (-not (Test-Path $CustomWorldsDir)) {[m[41m[m
[32m+[m[32m        New-Item -ItemType Directory -Path $CustomWorldsDir -Force |[m[41m[m
[32m+[m[32m            Out-Null[m[41m[m
[32m+[m[32m    }[m[41m[m
[32m+[m[41m[m
[32m+[m[32m    Remove-Item $ArchivePath, $ZipPath -Force -ErrorAction SilentlyContinue[m[41m[m
[32m+[m[41m[m
[32m+[m[32m    # Archive the botw directory itself, preserving the botw/ prefix.[m[41m[m
[32m+[m[32m    Compress-Archive -Path $PackageDir -DestinationPath $ZipPath -Force[m[41m[m
[32m+[m[32m    Move-Item $ZipPath $ArchivePath -Force[m[41m[m
[32m+[m[41m[m
[32m+[m[32m    # Verify the APWorld archive structure.[m[41m[m
[32m+[m[32m    Add-Type -AssemblyName System.IO.Compression.FileSystem[m[41m[m
[32m+[m[32m    $Zip = [System.IO.Compression.ZipFile]::OpenRead($ArchivePath)[m[41m[m
[32m+[m[41m[m
[32m+[m[32m    try {[m[41m[m
[32m+[m[32m        $Entries = @([m[41m[m
[32m+[m[32m            $Zip.Entries | ForEach-Object {[m[41m[m
[32m+[m[32m                $_.FullName.Replace("\", "/")[m[41m[m
[32m+[m[32m            }[m[41m[m
[32m+[m[32m        )[m[41m[m
[32m+[m[41m[m
[32m+[m[32m        if ($Entries -notcontains "botw/__init__.py") {[m[41m[m
[32m+[m[32m            throw "Archive is missing botw/__init__.py."[m[41m[m
[32m+[m[32m        }[m[41m[m
[32m+[m[41m[m
[32m+[m[32m        if ($Entries -notcontains "botw/Game.py") {[m[41m[m
[32m+[m[32m            throw "Archive is missing botw/Game.py."[m[41m[m
[32m+[m[32m        }[m[41m[m
[32m+[m[41m[m
[32m+[m[32m        if ($Entries -notcontains "botw/data/game.json") {[m[41m[m
[32m+[m[32m            throw "Archive is missing botw/data/game.json."[m[41m[m
[32m+[m[32m        }[m[41m[m
[32m+[m[41m[m
[32m+[m[32m        $TopLevelEntries = @([m[41m[m
[32m+[m[32m            $Entries |[m[41m[m
[32m+[m[32m                Where-Object { $_ -and $_ -notmatch "^botw/" }[m[41m[m
[32m+[m[32m        )[m[41m[m
[32m+[m[41m[m
[32m+[m[32m        if ($TopLevelEntries.Count -gt 0) {[m[41m[m
[32m+[m[32m            throw "Unexpected files outside the botw directory: $($TopLevelEntries -join ', ')"[m[41m[m
[32m+[m[32m        }[m[41m[m
[32m+[m[32m    }[m[41m[m
[32m+[m[32m    finally {[m[41m[m
[32m+[m[32m        $Zip.Dispose()[m[41m[m
[32m+[m[32m    }[m[41m[m
[32m+[m[41m[m
[32m+[m[32m    # Install the verified archive.[m[41m[m
[32m+[m[32m    Copy-Item $ArchivePath $InstalledPath -Force[m[41m[m
[32m+[m[41m[m
[32m+[m[32m    Write-Host "SUCCESS!" -ForegroundColor Green[m[41m[m
[32m+[m[32m    Write-Host "Built:     $ArchivePath"[m[41m[m
[32m+[m[32m    Write-Host "Installed: $InstalledPath"[m[41m[m
[32m+[m[32m    Write-Host "Archive contains one top-level botw/ directory."[m[41m[m
[32m+[m[32m    Write-Host ""[m[41m[m
[32m+[m[32m    Write-Host "Restart Archipelago before testing changes."[m[41m[m
[32m+[m[32m}[m[41m[m
[32m+[m[32mcatch {[m[41m[m
[32m+[m[32m    Write-Host ""[m[41m[m
[32m+[m[32m    Write-Host "UPDATE FAILED:" -ForegroundColor Red[m[41m[m
[32m+[m[32m    Write-Host $_.Exception.Message -ForegroundColor Red[m[41m[m
[32m+[m[32m}[m[41m[m
[32m+[m[32mfinally {[m[41m[m
[32m+[m[32m    Remove-Item $StageRoot -Recurse -Force -ErrorAction SilentlyContinue[m[41m[m
 }[m
\ No newline at end of file[m
