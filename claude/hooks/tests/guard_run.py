import json, os, subprocess, sys

hook = os.path.expanduser('~/Developer/personal/settings/claude/hooks/guard-dangerous-bash.sh')
bad = n = 0
for line in open(sys.argv[1], encoding='utf-8'):
    want, cmd = line.rstrip('\n').split('\t', 1)
    cmd = cmd.replace('<NL>', '\n')
    rc = subprocess.run(['bash', hook], input=json.dumps({'tool_input': {'command': cmd}}), text=True,
                        capture_output=True).returncode
    got = '막음' if rc == 2 else '통과'
    n += 1
    if got != want:
        bad += 1
        print(f'XX [{want}→{got}] {cmd!r}')
print(f'total={n} wrong={bad}')
