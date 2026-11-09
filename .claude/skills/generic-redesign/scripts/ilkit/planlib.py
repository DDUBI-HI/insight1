import json
from datetime import date


def slide(n, role, family, title, core, takeaway, why, blocks, page="body", table=None, must=None, ev=("src_01",), chart=None, chart_take=None):
    return {
        "slide_number": n, "slide_role": role, "page_family": page,
        "working_title": title, "core_message": core, "audience_takeaway": takeaway,
        "why_here": why, "recommended_layout_family": family,
        "content_blocks": [{"block_type": b[0], "purpose": b[1], "content_instruction": b[2]} for b in blocks],
        "chart_strategy": chart, "chart_takeaway": chart_take,
        "table_strategy": "table" if table else None, "table_takeaway": table,
        "content_constraints": {"must_include": must or [], "must_not_include": [], "evidence_to_use": list(ev)},
        "evidence_sources": list(ev), "priority": "must",
    }


def write_plan(path, meta, arc, inventory, slides, notes=None, fact=None):
    d = {
        "deck_meta": meta,
        "design_dependency": {
            "preset_name": "insightlearning",
            "design_md_path": ".claude/skills/slide/templates/layouts/insightlearning/DESIGN.md",
            "allowed_layout_families": ["structure", "insight", "breakdown", "compare", "data", "process", "visual"],
            "consistency_notes": ["generic-redesign 표준: 03_content 라이트 셸, 섹션 라벨 'NN | 이름', 표지·엔딩 네이비 셸"],
        },
        "story_arc": arc,
        "content_inventory": inventory,
        "slides": slides,
        "ordering_notes": notes or {"split_topics": [], "merged_topics": [], "deferred_topics": [], "appendix_candidates": []},
        "fact_check_log": fact or [{"claim": "자사·고객사 내부 자료(강사 이력, 시간, 금액)", "slide_number": 1, "priority": "MEDIUM", "status": "unverified", "source": None, "original": "내부 자료 — 웹 검증 불가", "corrected_to": None, "checked_at": date.today().isoformat()}],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def write_spec(project_dir, name, audience, images, icons):
    plan = json.load(open(f"{project_dir}/slide_plan.json", encoding="utf-8"))
    sl = plan["slides"]
    out = [f"# {name} - Design Spec\n\n> Plan-Consuming mode. `slide_plan.json` is the per-slide SSOT; §IX is its transcription. Active theme: Insightlearning (locked).\n",
           "## I. Project Information\n\n| Item | Value |\n| ---- | ----- |",
           f"| **Project Name** | {name} — {plan['deck_meta']['working_title']} |",
           "| **Canvas Format** | PPT 16:9 (1280×720) |", f"| **Page Count** | {len(sl)} |",
           "| **Design Style** | Insightlearning |", f"| **Target Audience** | {audience} |",
           "| **Use Case** | 범용 교육 프로그램 소개서 (고객사 제안서 범용화 + 리디자인) |", f"| **Created Date** | {date.today().isoformat()} |\n",
           "## II. Canvas Specification\n\n| Property | Value |\n| -------- | ----- |\n| **Format** | PPT 16:9 |\n| **Dimensions** | 1280×720 |\n| **viewBox** | `0 0 1280 720` |\n| **Margins** | left/right 56px |\n| **Content Area** | x=56, y=168, w=1168, h=472 |\n",
           "## III. Visual Theme\n\n- **Style**: Insightlearning\n- **Theme**: Light content shell; navy cover / ending\n- **Tone**: confident, consultative, formal 합니다체\n\n| Role | HEX | Purpose |\n| ---- | --- | ------- |\n| **Background** | `#FFFFFF` | page |\n| **Secondary bg** | `#F8F8F8` | filled cards |\n| **Primary** | `#012281` | navy blocks, icons |\n| **Accent** | `#E0EDF3` | one highlight |\n| **Body text** | `#1A1A1A` | text |\n| **Secondary text** | `#595959` | descriptors, GM |\n| **Tertiary text** | `#666666` | captions |\n| **Border/divider** | `#DFDFDF` | hairlines |\n",
           "## IV. Typography System\n\n**Font stack**: `Pretendard, 'Apple SD Gothic Neo', 'Malgun Gothic', Arial, sans-serif`\n\n**Baseline**: Body 15.2px · Headline 29.6/800 · Title 17.6/700 · Caption 12.8 · Cover 52/700 · Closing 56/800\n",
           "## V. Layout Principles\n\n- **Header area**: section label y=62, navy split rule y=72–78, centered headline y=128\n- **Content area**: y=168–640\n- **Footer area**: GM y=680, page number y=696\n",
           "## VI. Icon Usage Specification\n\n| Purpose | Icon Path | Page |\n| ------- | --------- | ---- |"]
    out += [f"| {p} | `tabler-outline/{i}` | {pg} |" for p, i, pg in icons]
    out += ["\n## VII. Visualization Reference List\n\n| Visualization Type | Reference Template | Used In |\n| --- | --- | --- |\n| navy-label-table / chevron-step-band / filled-card-stack (DESIGN §5.1) | custom | see §IX |\n",
            "## VIII. Image Resource List\n\n| Filename | Dimensions | Ratio | Purpose | Type | Status | Generation Description |\n| --- | --- | --- | --- | --- | --- | --- |"]
    out += [f"| {f} | {d} | {r} | {p} | {t} | Existing | - |" for f, d, r, p, t in images]
    out += ["\n## IX. Content Outline\n"]
    for s in sl:
        out.append(f"#### Slide {s['slide_number']:02d} - {s['working_title']}\n\n- **Layout**: {s['recommended_layout_family']} ({s['page_family']})\n- **Core**: {s['core_message']}\n- **Content**:")
        out += [f"  - {b['block_type']}: {b['content_instruction']}" for b in s["content_blocks"]]
        out.append("")
    out += ["## X. Speaker Notes Requirements\n\n- File naming matches SVG names; `[전환]` markers; formal 합니다체; no 여러분/당신\n",
            "## XI. Technical Constraints Reminder\n\n1. viewBox `0 0 1280 720`\n2. Background `<rect>`\n3. `<tspan>` for wrapping, no `<foreignObject>`\n4. `fill-opacity` instead of rgba\n5. No `mask`, `<style>`, `class`\n6. No `textPath`, `animate*`, `script`\n7. Markers only per shared-standards §1.1\n\n- No `<g opacity>`; inline styles only\n"]
    open(f"{project_dir}/design_spec.md", "w", encoding="utf-8").write("\n".join(out))
