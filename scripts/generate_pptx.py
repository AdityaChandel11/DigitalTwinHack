"""Generate high-end PowerPoint presentation for Chhaya Digital Twin hackathon submission.

Parses docs/PRESENTATION_SCRIPT_20MIN.md and outputs docs/Chhaya_Phase1_Presentation.pptx
with professional dark clinical aesthetics, embedded images, and full speaker notes.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# Root directories
REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "docs" / "PRESENTATION_SCRIPT_20MIN.md"
OUTPUT_PATH = REPO_ROOT / "docs" / "Chhaya_Phase1_Presentation.pptx"
IMAGES_DIR = REPO_ROOT / "docs" / "images"

# Color Palette (Deep Medical Dark Mode)
BG_COLOR = RGBColor(12, 18, 34)         # #0c1222 (Deep Navy)
CARD_BG = RGBColor(24, 34, 52)          # #182234 (Slate Panel)
BORDER_COLOR = RGBColor(51, 65, 85)     # #334155 (Subtle Border)
ACCENT_VIOLET = RGBColor(139, 92, 246)  # #8b5cf6 (Chhaya Purple)
ACCENT_TEAL = RGBColor(6, 182, 212)     # #06b6d4 (Clinical Cyan)
ACCENT_AMBER = RGBColor(245, 158, 11)   # #f59e0b (Excursion / Drift)
ACCENT_GREEN = RGBColor(16, 185, 129)   # #10b981 (Passed Bar)
TEXT_PRIMARY = RGBColor(248, 250, 252)  # #f8fafc (Pure White)
TEXT_MUTED = RGBColor(148, 163, 184)    # #94a3b8 (Soft Gray)
TEXT_DARK = RGBColor(15, 23, 42)

def parse_markdown_script(file_path: Path) -> list[dict]:
    """Parse the presentation markdown into structured slide dictionaries."""
    content = file_path.read_text(encoding="utf-8")
    
    # Split by slide separator
    pattern = r"═══════════════════════════════════════\s*SLIDE\s+(\d+):\s*(.*?)\s*═══════════════════════════════════════"
    matches = list(re.finditer(pattern, content))
    
    slides = []
    
    # Also find section headings
    section_pattern = r"# (SECTION [A-G]: [^\n]+)"
    section_matches = list(re.finditer(section_pattern, content))
    
    current_section = "Phase 1 Prototype & Code Submission"
    
    for i, match in enumerate(matches):
        slide_num = int(match.group(1))
        title = match.group(2).strip()
        
        # Determine section for this slide
        slide_start = match.start()
        for sm in section_matches:
            if sm.start() < slide_start:
                current_section = sm.group(1).strip()
        
        # Get content between this slide and next
        start_idx = match.end()
        end_idx = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        slide_body = content[start_idx:end_idx]
        
        # Extract visual content
        visual_match = re.search(r"VISUAL CONTENT:\s*(.*?)\s*NARRATION SCRIPT:", slide_body, re.DOTALL)
        visual_text = visual_match.group(1).strip() if visual_match else ""
        
        # Extract narration
        narration_match = re.search(r'NARRATION SCRIPT:\s*"(.*?)"\s*(?:SLIDE DURATION:|$)', slide_body, re.DOTALL)
        if not narration_match:
            narration_match = re.search(r'NARRATION SCRIPT:\s*(.*?)\s*(?:SLIDE DURATION:|$)', slide_body, re.DOTALL)
        narration_text = narration_match.group(1).strip() if narration_match else ""
        
        # Extract duration
        duration_match = re.search(r'SLIDE DURATION:\s*(~?\d+.*)', slide_body)
        duration = duration_match.group(1).strip() if duration_match else "~30 seconds"
        
        slides.append({
            "number": slide_num,
            "title": title,
            "section": current_section,
            "visual": visual_text,
            "narration": narration_text,
            "duration": duration,
        })
        
    return slides

def build_presentation(slides: list[dict], output_path: Path):
    """Build the PowerPoint presentation using python-pptx."""
    prs = Presentation()
    # 16:9 Widescreen layout
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]  # completely blank slide
    
    # Image mapping
    patient_img = IMAGES_DIR / "dashboard-patient.png"
    evidence_img = IMAGES_DIR / "dashboard-evidence.png"
    gate2_img = IMAGES_DIR / "gate2-by-group.png"

    for s_idx, s in enumerate(slides):
        slide = prs.slides.add_slide(blank_layout)
        
        # 1. Dark Background fill
        bg = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height
        )
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_COLOR
        bg.line.fill.background()
        
        # Set Speaker Notes
        notes_slide = slide.notes_slide
        notes_slide.notes_text_frame.text = f"[SLIDE {s['number']} - DURATION: {s['duration']}]\n\nNARRATION:\n{s['narration']}"
        
        # Determine if this is Slide 1 (Title)
        if s["number"] == 1:
            create_title_slide(slide, s, prs.slide_width, prs.slide_height)
            continue
            
        # Top Header Bar
        # Section pill
        section_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(8), Inches(0.4))
        stf = section_box.text_frame
        stf.word_wrap = True
        stf.margin_left = stf.margin_top = stf.margin_right = stf.margin_bottom = 0
        sp = stf.paragraphs[0]
        sp.text = f"{s['section'].upper()}  •  SLIDE {s['number']} OF {len(slides)}"
        sp.font.size = Pt(11)
        sp.font.bold = True
        sp.font.color.rgb = ACCENT_TEAL
        
        # Slide Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.7), Inches(0.8))
        ttf = title_box.text_frame
        ttf.word_wrap = True
        ttf.margin_left = ttf.margin_top = ttf.margin_right = ttf.margin_bottom = 0
        tp = ttf.paragraphs[0]
        tp.text = s["title"]
        tp.font.size = Pt(26)
        tp.font.bold = True
        tp.font.color.rgb = TEXT_PRIMARY
        
        # Subtitle accent divider line
        line = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.6), Inches(11.7), Inches(0.04)
        )
        line.fill.solid()
        line.fill.fore_color.rgb = ACCENT_VIOLET
        line.line.fill.background()
        
        # Decide if this slide gets an embedded image
        target_img = None
        if s["number"] in (37, 38, 47, 48) and patient_img.exists():
            target_img = patient_img
        elif s["number"] in (26, 46) and evidence_img.exists():
            target_img = evidence_img
        elif s["number"] in (27, 51) and gate2_img.exists():
            target_img = gate2_img
            
        if target_img:
            # 2-Column layout: Content on Left (5.8 in), Image on Right (5.7 in)
            create_content_box(slide, s["visual"], Inches(0.8), Inches(1.8), Inches(5.8), Inches(5.0))
            
            # Image card border container
            img_container = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.9), Inches(1.8), Inches(5.6), Inches(5.0)
            )
            img_container.fill.solid()
            img_container.fill.fore_color.rgb = CARD_BG
            img_container.line.color.rgb = BORDER_COLOR
            
            # Real image inside
            slide.shapes.add_picture(
                str(target_img), Inches(7.0), Inches(2.0), width=Inches(5.4)
            )
        else:
            # Full or Split Card layout
            lines = [l.strip() for l in s["visual"].split("\n") if l.strip()]
            has_subheaders = any(l.endswith(":") and not l.startswith("-") for l in lines)
            
            if has_subheaders and len(lines) > 5:
                # 2-Column Balanced Cards
                create_two_column_cards(slide, s["visual"], Inches(0.8), Inches(1.8), Inches(11.7), Inches(5.1))
            else:
                # Single Spacious Card
                create_single_card(slide, s["visual"], Inches(0.8), Inches(1.8), Inches(11.7), Inches(5.1))

        # Bottom subtle footer
        footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.05), Inches(11.7), Inches(0.3))
        ftf = footer_box.text_frame
        ftf.word_wrap = True
        ftf.margin_left = ftf.margin_top = ftf.margin_right = ftf.margin_bottom = 0
        fp = ftf.paragraphs[0]
        fp.text = "Chhaya Digital Twin  •  Team SynapseX  •  Happiest Health Challenge 2026"
        fp.font.size = Pt(10)
        fp.font.color.rgb = TEXT_MUTED

    prs.save(str(output_path))
    print(f"[SUCCESS] Wrote {len(slides)} slides to {output_path}")

def create_title_slide(slide, s: dict, width: Inches, height: Inches):
    """Render high-impact cover slide."""
    # Decorative gradient accent panel
    panel = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.2), Inches(11.7), Inches(5.2)
    )
    panel.fill.solid()
    panel.fill.fore_color.rgb = CARD_BG
    panel.line.color.rgb = ACCENT_VIOLET
    
    # Title badge
    tb = slide.shapes.add_textbox(Inches(1.4), Inches(1.7), Inches(10.5), Inches(0.5))
    p = tb.text_frame.paragraphs[0]
    p.text = "HAPPIEST HEALTH DIGITAL TWIN CHALLENGE 2026  •  PHASE 1 SUBMISSION"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = ACCENT_TEAL
    
    # Main Title
    mb = slide.shapes.add_textbox(Inches(1.4), Inches(2.3), Inches(10.5), Inches(1.2))
    p = mb.text_frame.paragraphs[0]
    p.text = "CHHAYA  (छाया)"
    p.font.size = Pt(48)
    p.font.bold = True
    p.font.color.rgb = TEXT_PRIMARY
    
    # Subtitle
    sb = slide.shapes.add_textbox(Inches(1.4), Inches(3.5), Inches(10.5), Inches(0.8))
    p = sb.text_frame.paragraphs[0]
    p.text = "A Type 2 Diabetes Digital Twin That Shows Its Work"
    p.font.size = Pt(24)
    p.font.color.rgb = ACCENT_VIOLET
    
    # Description / Hook
    db = slide.shapes.add_textbox(Inches(1.4), Inches(4.3), Inches(10.5), Inches(0.8))
    p = db.text_frame.paragraphs[0]
    p.text = "One glucose-sensor wear, turned into the patient's shadow, with a scorecard written before the results."
    p.font.size = Pt(16)
    p.font.color.rgb = TEXT_MUTED
    
    # Team Info & Badges
    ib = slide.shapes.add_textbox(Inches(1.4), Inches(5.3), Inches(10.5), Inches(0.6))
    p = ib.text_frame.paragraphs[0]
    p.text = "Team SynapseX  •  D.B.S Kanpur  •  Folder: SynapseX_D.B.S Kanpur  •  MIT Licensed Open Source"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = ACCENT_GREEN

def create_single_card(slide, text: str, left, top, width, height):
    """Render content inside a sleek container card."""
    card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height
    )
    card.fill.solid()
    card.fill.fore_color.rgb = CARD_BG
    card.line.color.rgb = BORDER_COLOR
    
    tb = slide.shapes.add_textbox(left + Inches(0.3), top + Inches(0.3), width - Inches(0.6), height - Inches(0.6))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_top = tf.margin_bottom = tf.margin_left = tf.margin_right = 0
    
    populate_text_frame(tf, text)

def create_two_column_cards(slide, text: str, left, top, width, height):
    """Split text cleanly into two balanced cards."""
    half_width = (width - Inches(0.4)) / 2
    
    lines = [l for l in text.split("\n") if l.strip()]
    midpoint = len(lines) // 2
    left_lines = lines[:midpoint]
    right_lines = lines[midpoint:]
    
    # Card 1 (Left)
    card1 = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, half_width, height)
    card1.fill.solid()
    card1.fill.fore_color.rgb = CARD_BG
    card1.line.color.rgb = BORDER_COLOR
    tb1 = slide.shapes.add_textbox(left + Inches(0.3), top + Inches(0.3), half_width - Inches(0.6), height - Inches(0.6))
    tb1.text_frame.word_wrap = True
    populate_text_frame(tb1.text_frame, "\n".join(left_lines))
    
    # Card 2 (Right)
    card2 = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left + half_width + Inches(0.4), top, half_width, height)
    card2.fill.solid()
    card2.fill.fore_color.rgb = CARD_BG
    card2.line.color.rgb = BORDER_COLOR
    tb2 = slide.shapes.add_textbox(left + half_width + Inches(0.7), top + Inches(0.3), half_width - Inches(0.6), height - Inches(0.6))
    tb2.text_frame.word_wrap = True
    populate_text_frame(tb2.text_frame, "\n".join(right_lines))

def create_content_box(slide, text: str, left, top, width, height):
    """Render text content next to an image."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = CARD_BG
    card.line.color.rgb = BORDER_COLOR
    
    tb = slide.shapes.add_textbox(left + Inches(0.3), top + Inches(0.3), width - Inches(0.6), height - Inches(0.6))
    tf = tb.text_frame
    tf.word_wrap = True
    populate_text_frame(tf, text)

def populate_text_frame(tf, text: str):
    """Format bullet points, headers, and highlights in text frame."""
    lines = [l for l in text.split("\n") if l.strip()]
    if not lines:
        return
        
    for i, line in enumerate(lines):
        p = tf.add_paragraph() if i > 0 else tf.paragraphs[0]
        clean = line.strip()
        
        # Check if line is a header (ends with colon or starts with bold/number)
        if clean.endswith(":") and not clean.startswith("-"):
            p.text = clean
            p.font.size = Pt(16)
            p.font.bold = True
            p.font.color.rgb = ACCENT_TEAL
            p.space_after = Pt(4)
            p.space_before = Pt(8) if i > 0 else Pt(0)
        elif clean.startswith("-") or clean.startswith("•") or clean.startswith("*"):
            # Bullet point
            clean_text = re.sub(r"^[-•*]\s*", "", clean)
            p.text = f"•  {clean_text}"
            p.font.size = Pt(13)
            p.font.color.rgb = TEXT_PRIMARY
            p.space_after = Pt(3)
            
            # Special highlighting
            if "PASSED" in clean or "✅" in clean:
                p.font.color.rgb = ACCENT_GREEN
                p.font.bold = True
            elif "MISSED" in clean or "❌" in clean or "False" in clean:
                p.font.color.rgb = ACCENT_AMBER
                p.font.bold = True
        else:
            p.text = clean
            p.font.size = Pt(13)
            p.font.color.rgb = TEXT_MUTED
            p.space_after = Pt(3)

if __name__ == "__main__":
    slides = parse_markdown_script(SCRIPT_PATH)
    build_presentation(slides, OUTPUT_PATH)
