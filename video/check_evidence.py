import json

with open('src/chhaya/dashboard/demo/evidence.json') as f:
    ev = json.load(f)
print('Tally:', ev['tally'])
print('Fusion:', ev['fusion'])
print('\nResults:')
for r in ev['results']:
    print(f"ID: {r['id']}, Grade: {r['grade']}, Title: {r['title']}, Bars: {r.get('bars')}")
    print(f"  Claim: {r['claim']}")
    for b in r.get('bar_text', []):
        print(f"    Bar text: {b}")
    print()
