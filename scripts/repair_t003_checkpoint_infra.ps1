param(
    [string]$RepoPath = (Get-Location).Path,
    [switch]$RunCheckpoint,
    [switch]$CleanupT003Temp,
    [switch]$NoSync
)

$ErrorActionPreference = 'Stop'

function Write-Step([string]$Message) {
    Write-Host "[T003-RECOVER] $Message"
}

$RepoPath = (Resolve-Path $RepoPath).Path
$CheckpointScript = Join-Path $RepoPath 'scripts\auto_checkpoint_claude.ps1'
$SyncScript = Join-Path $RepoPath 'scripts\auto_git_sync.ps1'

if (-not (Test-Path $CheckpointScript)) {
    throw "auto_checkpoint_claude.ps1 not found: $CheckpointScript"
}

Write-Step "RepoPath = $RepoPath"
Write-Step "Target = $CheckpointScript"

# Avoid repeated PowerShell security prompts for local project scripts already approved by the operator.
try { Unblock-File -Path $CheckpointScript -ErrorAction SilentlyContinue } catch {}
try { if (Test-Path $SyncScript) { Unblock-File -Path $SyncScript -ErrorAction SilentlyContinue } } catch {}

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$backup = "$CheckpointScript.bak_T003_recover_$stamp"
Copy-Item $CheckpointScript $backup -Force
Write-Step "Backup created: $backup"

# Python patcher: replaces ambiguous PowerShell '-replace' usages on $content with [regex]::Replace
# and converts array replacement values into plain text. This targets the observed failure:
# "The -ireplace operator allows only two elements to follow it, not 3."
$py = Join-Path $RepoPath '.t003_repair_auto_checkpoint.py'
@'
import pathlib
import re
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding='utf-8-sig')
if 'T003_SAFE_REGEX_REPLACE_PATCH' in text:
    print('{"patched": false, "reason": "already patched"}')
    raise SystemExit(0)

lines = text.splitlines(keepends=True)
helper = [
"\n",
"# T003_SAFE_REGEX_REPLACE_PATCH: normalize replacement text before regex replacement.\n",
"function Convert-ToCheckpointText {\n",
"    param([AllowNull()][object]$Value)\n",
"    if ($null -eq $Value) { return \"\" }\n",
"    if ($Value -is [array]) { return ($Value -join [Environment]::NewLine) }\n",
"    return [string]$Value\n",
"}\n",
"\n",
]

def find_operator_comma(expr: str) -> int:
    in_single = False
    in_double = False
    escape = False
    paren = 0
    bracket = 0
    brace = 0
    for i, ch in enumerate(expr):
        if escape:
            escape = False
            continue
        if ch == '`':
            escape = True
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            continue
        if in_single or in_double:
            continue
        if ch == '(':
            paren += 1
        elif ch == ')' and paren > 0:
            paren -= 1
        elif ch == '[':
            bracket += 1
        elif ch == ']' and bracket > 0:
            bracket -= 1
        elif ch == '{':
            brace += 1
        elif ch == '}' and brace > 0:
            brace -= 1
        elif ch == ',' and paren == 0 and bracket == 0 and brace == 0:
            return i
    return -1

patched = 0
out = []
helper_inserted = False
line_re = re.compile(r'^(?P<indent>\s*)\$content\s*=\s*\$content\s+-replace\s+(?P<rhs>.+?)(?P<eol>\r?\n)?$')

for line in lines:
    m = line_re.match(line)
    if not m or 'T003_SAFE_REGEX_REPLACE_PATCH' in line:
        out.append(line)
        continue

    rhs = m.group('rhs').strip()
    comma = find_operator_comma(rhs)
    if comma < 0:
        out.append(line)
        continue

    pattern = rhs[:comma].strip()
    repl = rhs[comma+1:].strip()
    # Refuse unsafe cases where the line seems to contain a second operator-level comma.
    if find_operator_comma(repl) >= 0:
        out.append(line)
        continue

    if not helper_inserted:
        out.extend(helper)
        helper_inserted = True

    indent = m.group('indent')
    eol = m.group('eol') or '\n'
    new_line = f"{indent}$content = [regex]::Replace($content, {pattern}, (Convert-ToCheckpointText -Value ({repl})))  # T003_SAFE_REGEX_REPLACE_PATCH{eol}"
    out.append(new_line)
    patched += 1

if patched == 0:
    context = []
    for idx, l in enumerate(lines, 1):
        if '$content' in l and '-replace' in l:
            context.append(f'{idx}: {l.rstrip()}')
    print('{"patched": false, "reason": "no safe one-line $content -replace pattern found"}')
    if context:
        print('Candidate lines:')
        print('\n'.join(context))
    raise SystemExit(2)

path.write_text(''.join(out), encoding='utf-8')
print('{"patched": true, "lines_patched": %d}' % patched)
'@ | Set-Content -Path $py -Encoding UTF8

python $py $CheckpointScript
if ($LASTEXITCODE -ne 0) {
    throw "Python patcher failed with exit code $LASTEXITCODE"
}

Write-Step "PowerShell parse check"
$tokens = $null
$parseErrors = $null
[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw $CheckpointScript), [ref]$parseErrors) | Out-Null
if ($parseErrors -and $parseErrors.Count -gt 0) {
    Write-Host "[T003-RECOVER][FAIL] Parse errors detected; restoring backup"
    Copy-Item $backup $CheckpointScript -Force
    $parseErrors | Format-List | Out-String | Write-Host
    throw "auto_checkpoint_claude.ps1 parse failed after patch"
}
Write-Step "Parse OK"

if ($CleanupT003Temp) {
    Write-Step "Cleaning T003 temporary artifacts committed by first hotfix"
    $paths = @()
    $paths += Join-Path $RepoPath '.t003_patch_pf_normalizer.py'
    $paths += Join-Path $RepoPath '.t003_repair_auto_checkpoint.py'
    $paths += Get-ChildItem -Path (Join-Path $RepoPath 'Core') -Filter 'pf_normalizer.py.bak_T003_*' -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName }
    $paths += Get-ChildItem -Path (Join-Path $RepoPath 'Docs') -Filter 'DISPATCH_STATUS.json.bak_T003_*' -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName }
    foreach ($p in $paths) {
        if ($p -and (Test-Path $p)) {
            Remove-Item $p -Force
            Write-Step "Removed: $p"
        }
    }
}

Write-Step "Git status after repair"
git -C $RepoPath status --short

if ($RunCheckpoint) {
    Write-Step "Running repaired checkpoint script"
    if ($NoSync) {
        & $CheckpointScript -Focus "T003 pf_normalizer signature hotfix / checkpoint repair" -NoGit
    } else {
        & $CheckpointScript -Focus "T003 pf_normalizer signature hotfix / checkpoint repair"
    }
} elseif (-not $NoSync) {
    if (Test-Path $SyncScript) {
        Write-Step "Syncing repair commit through auto_git_sync"
        & $SyncScript -Message "fix(infra): repair auto_checkpoint replace operator after T003"
    } else {
        Write-Step "auto_git_sync.ps1 not found; leaving changes local"
    }
}

Write-Step "Done"
