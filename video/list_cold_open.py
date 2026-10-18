import json

with open('video/storyboard.json', encoding='utf-8') as f:
    sb = json.load(f)

cold_open = [s for s in sb if s['chapter'] == 'Cold Open']
print(f"Cold Open segments: {len(cold_open)}")
tot = sum(s['seconds'] for s in cold_open)
print(f"Total Cold Open seconds: {tot}")
for s in cold_open:
    print(f"{s['id']} ({s['seconds']}s): visual='{s['visual'][:60]}' | caption='{s['caption'][:40]}'")
