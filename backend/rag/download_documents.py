"""
RAG Document Downloader & Organizer
Downloads agricultural pest management documents for the RAG pipeline.

Run this script once to populate data/documents/ with source material.
These documents will be chunked and embedded into ChromaDB in Stage 2.

Usage:
    python download_documents.py
"""

import os
import requests
from pathlib import Path

# Where to save documents
DOCS_DIR = Path(__file__).parent.parent / "data" / "documents"
DOCS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Document Sources — Publicly available agricultural pest management guides
# ============================================================================
DOCUMENT_SOURCES = [
    # FAO Documents
    {
        "name": "FAO_Integrated_Pest_Management.pdf",
        "url": "https://www.fao.org/3/ca7749en/ca7749en.pdf",
        "source": "FAO",
        "description": "FAO guide on integrated pest management principles",
    },
    {
        "name": "FAO_Pesticide_Management_Guidelines.pdf",
        "url": "https://www.fao.org/3/a0220e/a0220e.pdf",
        "source": "FAO",
        "description": "International Code of Conduct on Pesticide Management",
    },
    {
        "name": "FAO_Plant_Health_Pest_Risk.pdf",
        "url": "https://www.fao.org/3/j0415e/j0415e.pdf",
        "source": "FAO",
        "description": "ISPM guidelines for pest risk analysis",
    },
    # Additional sources to manually download
]

# ============================================================================
# Documents that must be manually downloaded (require website navigation)
# ============================================================================
MANUAL_DOWNLOAD_INSTRUCTIONS = """
╔══════════════════════════════════════════════════════════════════╗
║           MANUAL DOWNLOAD INSTRUCTIONS                         ║
║   Save these files to: data/documents/                         ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                 ║
║  1. CABI Pest Datasheets (cabi.org/isc)                        ║
║     → Search for: Aphid, Rice Leaf Roller, Corn Borer,         ║
║       Wheat Aphid, Citrus Leaf Miner, Locust                   ║
║     → Download each pest's datasheet as PDF                    ║
║     → Save as: CABI_Aphid.pdf, CABI_Rice_Leaf_Roller.pdf, etc. ║
║                                                                 ║
║  2. PlantVillage Guides (plantvillage.psu.edu)                 ║
║     → Browse pest management section                           ║
║     → Download guides for major crops: Rice, Wheat, Corn       ║
║     → Save as: PlantVillage_Rice_Pests.pdf, etc.               ║
║                                                                 ║
║  3. Pesticide Application Manuals                              ║
║     → Search for "safe pesticide application guide" PDF        ║
║     → Focus on: application timing, safety precautions,        ║
║       environmental conditions for spraying                    ║
║     → Save as: Pesticide_Safety_Guide.pdf                      ║
║                                                                 ║
║  4. IP102 Pest Reference                                       ║
║     → Download the IP102 dataset paper and any supplementary   ║
║       material listing the 102 pest categories                 ║
║     → Save as: IP102_Reference.pdf                             ║
║                                                                 ║
║  TARGET: At least 15-20 documents total                        ║
╚══════════════════════════════════════════════════════════════════╝
"""


def download_file(url: str, filename: str) -> bool:
    """Download a file from URL to the documents directory."""
    filepath = DOCS_DIR / filename
    if filepath.exists():
        print(f"  ✅ Already exists: {filename}")
        return True

    try:
        print(f"  ⬇️  Downloading: {filename}...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Academic Research - BAU Capstone Project)"
        }
        response = requests.get(url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        size_mb = filepath.stat().st_size / (1024 * 1024)
        print(f"  ✅ Downloaded: {filename} ({size_mb:.1f} MB)")
        return True

    except Exception as e:
        print(f"  ❌ Failed to download {filename}: {e}")
        return False


def create_sample_text_documents():
    """
    Create text-based reference documents with key pest management info.
    These supplement the PDFs and ensure the RAG pipeline has content to work with.
    """
    docs = {
        "pest_management_aphids.txt": """
APHID PEST MANAGEMENT GUIDE
============================
Source: Compiled from FAO, CABI, and PlantVillage references.

IDENTIFICATION:
- Small (1-3mm), soft-bodied insects, usually green, black, or brown.
- Found in clusters on stems, leaves, and buds.
- Produce honeydew, which attracts ants and promotes sooty mold.

DAMAGE:
- Suck plant sap, causing leaf curling, yellowing, and stunted growth.
- Vector for many plant viruses.
- Severe infestations can reduce crop yield by 20-80%.

CHEMICAL CONTROL:
- Imidacloprid (neonicotinoid) — effective but harmful to pollinators.
- Pymetrozine — selective aphicide, safer for beneficial insects.
- Lambda-cyhalothrin — broad-spectrum, use as last resort.
- ALWAYS follow label instructions. Do NOT spray during rain or high wind.

BIOLOGICAL CONTROL:
- Ladybugs (Coccinellidae) — natural predators, release 1500/acre.
- Lacewings (Chrysoperla carnea) — larvae consume ~200 aphids each.
- Parasitic wasps (Aphidius colemani) — lay eggs inside aphids.

CULTURAL CONTROL:
- Remove infested plant parts.
- Use reflective mulch to repel aphids.
- Avoid excessive nitrogen fertilization (promotes soft growth that attracts aphids).

TREATMENT TIMING:
- Best applied early morning or late evening.
- Do NOT spray when temperature exceeds 35°C.
- Do NOT spray if rain is expected within 6 hours.
- Wind speed must be below 15 km/h for effective application.

⚠️ DISCLAIMER: This information is for guidance only. Consult a certified agricultural expert before application.
""",

        "pest_management_rice_pests.txt": """
RICE PEST MANAGEMENT GUIDE
============================
Source: Compiled from FAO and IRRI (International Rice Research Institute) references.

COMMON RICE PESTS (from IP102 dataset):
1. Rice Leaf Roller (Cnaphalocrocis medinalis)
2. Rice Leaf Caterpillar
3. Paddy Stem Maggot (Chlorops oryzae)
4. Asiatic Rice Borer (Chilo suppressalis)
5. Yellow Rice Borer (Scirpophaga incertulas)

RICE LEAF ROLLER — MANAGEMENT:
- Chemical: Chlorantraniliprole, Fipronil (apply at early infestation)
- Biological: Trichogramma parasitoid release
- Cultural: Maintain field hygiene, remove weeds
- Threshold: Treat when >15% of leaves show folding damage

RICE STEM BORER — MANAGEMENT:
- Chemical: Carbofuran granules in paddy water, Cartap hydrochloride
- Biological: Release of Trichogramma japonicum egg parasitoids
- Cultural: Harvest at ground level, destroy stubble
- Threshold: Treat when >10% of tillers show dead hearts

GENERAL RICE IPM PRINCIPLES:
- Scout fields weekly during critical growth stages
- Use economic threshold levels before deciding to spray
- Rotate pesticide classes to prevent resistance
- Preserve natural enemies when possible

SPRAYING SAFETY FOR RICE PADDIES:
- Never spray when paddy water level is high (runoff contamination)
- Allow 7-14 day pre-harvest interval depending on pesticide
- Do NOT spray during flowering (harmful to pollinators)

⚠️ DISCLAIMER: This information is for guidance only. Consult a certified agricultural expert before application.
""",

        "pest_management_corn_pests.txt": """
CORN PEST MANAGEMENT GUIDE
============================
Source: Compiled from FAO and CIMMYT references.

COMMON CORN PESTS:
1. Corn Borer (Ostrinia nubilalis / Ostrinia furnacalis)
2. Fall Armyworm (Spodoptera frugiperda)
3. Corn Rootworm (Diabrotica species)

CORN BORER — MANAGEMENT:
- Chemical: Bt (Bacillus thuringiensis) sprays at early larval stage
- Chemical: Chlorantraniliprole for severe infestations
- Biological: Trichogramma ostriniae egg parasitoid
- Cultural: Destroy crop residues after harvest, rotate with non-host crops
- Threshold: Treat when 50% of plants show fresh whorl damage

FALL ARMYWORM — MANAGEMENT:
- Chemical: Spinetoram, Emamectin benzoate
- Biological: Telenomus remus parasitoid, NPV (Nuclear Polyhedrosis Virus)
- Cultural: Early planting, intercropping with legumes
- Monitoring: Use pheromone traps for early detection

⚠️ DISCLAIMER: This information is for guidance only. Consult a certified agricultural expert before application.
""",

        "pesticide_safety_guidelines.txt": """
PESTICIDE APPLICATION SAFETY GUIDELINES
==========================================
Source: Compiled from FAO International Code of Conduct on Pesticide Management.

WEATHER CONDITIONS FOR SAFE SPRAYING:
- Wind speed: Must be below 15 km/h (ideal: 3-10 km/h)
- Rain: Do NOT spray if rain expected within 6 hours
- Temperature: Avoid spraying above 35°C (increased evaporation/drift)
- Humidity: Best between 40-80% relative humidity
- Hail: NEVER spray during or immediately after hailstorm
- Snow: Do NOT apply pesticides on frozen or snow-covered crops

PERSONAL PROTECTIVE EQUIPMENT (PPE):
- Chemical-resistant gloves
- Protective eyewear or face shield
- Respiratory protection (for toxic compounds)
- Long-sleeved clothing and boots

APPLICATION TIMING:
- Early morning (before 10 AM) or late evening (after 4 PM)
- Avoid midday heat
- Apply when target pests are most active/vulnerable

ENVIRONMENTAL SAFETY:
- Maintain buffer zones near water bodies (minimum 10 meters)
- Do not contaminate water sources
- Dispose of empty containers safely
- Record all applications (date, product, rate, conditions)

PRE-HARVEST INTERVALS (PHI):
- Each pesticide has a mandatory waiting period before harvest
- Typical PHI ranges: 3 days to 21 days
- NEVER harvest before PHI expires

⚠️ DISCLAIMER: This information is for guidance only. Consult a certified agricultural expert before application.
""",

        "confidence_threshold_protocol.txt": """
CONFIDENCE THRESHOLD & PREDICTION RELIABILITY PROTOCOL
=========================================================
System Internal Document — Department 2

THRESHOLD: 0.70 (70%) Softmax Confidence

WHEN CONFIDENCE >= 0.70:
- System provides full pest identification
- LLM agent gives pesticide recommendations
- Treatment timing and alternative methods are shown
- Grad-CAM visualization is displayed

WHEN CONFIDENCE < 0.70:
- System flags prediction as UNRELIABLE
- NO specific pesticide recommendations are given
- User is warned: "Low confidence detection"
- User is prompted to upload a clearer image
- The chatbot responds with general pest identification tips only

FALSE DISCOVERY RATE (FDR) TARGET: < 10%
- The system must correctly flag at least 90% of incorrect predictions
- FDR is measured across the test set after D3 delivers the model

RATIONALE:
- Agricultural pesticide misapplication can cause crop damage, environmental harm,
  and financial loss to farmers
- A wrong diagnosis leading to wrong pesticide is worse than no diagnosis at all
- The 70% threshold was selected based on IP102 model performance literature
""",
    }

    for filename, content in docs.items():
        filepath = DOCS_DIR / filename
        if not filepath.exists():
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content.strip())
            print(f"  📝 Created: {filename}")
        else:
            print(f"  ✅ Already exists: {filename}")


def main():
    print("=" * 60)
    print("  RAG Document Collection — Stage 1")
    print("=" * 60)
    print(f"\nSaving documents to: {DOCS_DIR.resolve()}\n")

    # Download PDFs from direct URLs
    print("📥 Downloading available documents...")
    success_count = 0
    for doc in DOCUMENT_SOURCES:
        if download_file(doc["url"], doc["name"]):
            success_count += 1

    # Create text-based reference documents
    print("\n📝 Creating text reference documents...")
    create_sample_text_documents()

    # Count total documents
    total = len(list(DOCS_DIR.iterdir()))
    print(f"\n📊 Total documents in folder: {total}")

    if total < 15:
        print(f"\n⚠️  You have {total} documents. Target is 15-20.")
        print(MANUAL_DOWNLOAD_INSTRUCTIONS)
    else:
        print(f"\n✅ Document collection meets the minimum target (15+)")

    print("\n" + "=" * 60)
    print("  Next Step: Stage 2 → Build RAG pipeline with these documents")
    print("=" * 60)


if __name__ == "__main__":
    main()
