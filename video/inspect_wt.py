import json

with open("video/storyboard.json", "r", encoding="utf-8") as f:
    sb = json.load(f)

wt = [s for s in sb if s["chapter"] == "Live Walkthrough"]
for s in wt:
    print(f"{s['id']}|{s['visual']}|{s['caption']}")
