# AI QA Academy

Independent learning dashboard for QA tools — each tool is an **on-site course**
with clickable guides. Official vendor docs are linked as reference only.

## Routes

- `/` — category dashboard  
- `/tools/[category]` — tools in a category  
- `/tools/[category]/[tool]` — course outline (clickable guides)  
- `/tools/[category]/[tool]/[guide]` — full on-site lesson  
- `/learn/[slug]` — deeper academy curriculum tracks  

See `DESIGN.md` for milestones.

## Develop

```bash
npm install
npm run dev
npm run build
```
