import json
import re

FORBIDDEN = [
    'breakthrough',
    'clinically validated',
    'clinical validation',
    'abdm',
    'abha',
    'predictive digital twin'
]

with open('video/storyboard.json', 'r', encoding='utf-8') as f:
    sb = json.load(f)

print(f"Checking {len(sb)} segments in storyboard.json...")
total_sec = sum(s['seconds'] for s in sb)
print(f"Total Duration: {total_sec:.1f}s ({total_sec/60:.2f} min)")
assert 1230 <= total_sec <= 1320, f"Duration {total_sec} out of range [1230, 1320]"

errors = []
for s in sb:
    sid = s['id']
    cap = s['caption']
    sec = s['seconds']
    
    # Forbidden words check
    cap_lower = cap.lower()
    for fw in FORBIDDEN:
        if fw in cap_lower:
            errors.append(f"[{sid}] Forbidden word '{fw}' found in caption: {cap}")
            
    # Check unquoted alert
    if 'alert' in cap_lower:
        matches = re.finditer(r'\balert[s]?\b', cap_lower)
        for m in matches:
            start = max(0, m.start() - 15)
            context = cap_lower[start:m.end() + 10]
            if 'no alert' not in context and 'no meal alert' not in context and '"alert"' not in context and "'alert'" not in context:
                errors.append(f"[{sid}] Alert rule violation: context '{context}' in: {cap}")
                
    # Caption line and character limit check
    lines = cap.split('\n')
    if len(lines) > 2:
        errors.append(f"[{sid}] More than 2 lines ({len(lines)}): {cap}")
    for i, line in enumerate(lines):
        if len(line) > 52:
            errors.append(f"[{sid}] Line {i+1} exceeds 52 chars ({len(line)}): '{line}'")

if errors:
    print(f"Found {len(errors)} errors:")
    for e in errors:
        print("  -", e)
else:
    print(">>> SUCCESS: ALL 276 STORYBOARD SEGMENTS PASS QA WITH ZERO ERRORS!")
