"""
Compile the 10 slide PNGs into a 16:9 widescreen PowerPoint deck.
Outputs to:
  - docs/Chhaya_Phase1_Presentation.pptx
  - docs/Chhaya_Phase1_Presentation.pptx
"""
import sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches

def build_pptx():
    BASE_DIR = Path(__file__).resolve().parent
    PNG_DIR = BASE_DIR / "slides_png"
    OUT_PPTX_FINAL = BASE_DIR / "Chhaya_Phase1_Presentation.pptx"
    OUT_PPTX_P1 = BASE_DIR / "Chhaya_Phase1_Presentation.pptx"
    
    prs = Presentation()
    # Set 16:9 widescreen aspect ratio (13.333 x 7.5 inches)
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    
    blank_layout = prs.slide_layouts[6] # Blank slide layout
    
    png_files = sorted(PNG_DIR.glob("slide_*.png"))
    print(f"Found {len(png_files)} slide PNGs in {PNG_DIR}")
    
    for i, png in enumerate(png_files, start=1):
        slide = prs.slides.add_slide(blank_layout)
        # Add full-bleed image
        slide.shapes.add_picture(
            str(png),
            left=0,
            top=0,
            width=prs.slide_width,
            height=prs.slide_height
        )
        print(f"  [Slide {i}] Added {png.name}")
        
    prs.save(str(OUT_PPTX_FINAL))
    print(f"Saved PPTX deck to {OUT_PPTX_FINAL} ({OUT_PPTX_FINAL.stat().st_size} bytes)")
    
    # Also save to Phase 1 PPTX for link compatibility
    prs.save(str(OUT_PPTX_P1))
    print(f"Saved compatibility PPTX deck to {OUT_PPTX_P1} ({OUT_PPTX_P1.stat().st_size} bytes)")

if __name__ == "__main__":
    build_pptx()
