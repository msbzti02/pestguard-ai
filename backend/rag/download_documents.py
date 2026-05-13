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
    {
        "name": "FAO_Fall_Armyworm_Guide.pdf",
        "url": "https://www.fao.org/3/ca3544en/ca3544en.pdf",
        "source": "FAO",
        "description": "FAO practical guide for fall armyworm management",
    },
    {
        "name": "FAO_Locust_Watch_Guidelines.pdf",
        "url": "https://www.fao.org/3/i2952e/i2952e.pdf",
        "source": "FAO",
        "description": "Desert Locust Guidelines - Biology and behaviour",
    },
    {
        "name": "WHO_Pesticide_Hazard_Classification.pdf",
        "url": "https://www.who.int/publications/i/item/9789240005662",
        "source": "WHO",
        "description": "WHO recommended classification of pesticides by hazard",
    },
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

        "pest_management_citrus.txt": """
CITRUS PEST MANAGEMENT GUIDE
==============================
Source: Compiled from FAO and CABI references.

COMMON CITRUS PESTS:
1. Citrus Leaf Miner (Phyllocnistis citrella)
2. Citrus Psyllid (Diaphorina citri) — vector for Huanglongbing (HLB)
3. Mediterranean Fruit Fly (Ceratitis capitata)
4. Citrus Red Mite (Panonychus citri)
5. Citrus Whitefly (Dialeurodes citri)

CITRUS LEAF MINER — MANAGEMENT:
- Chemical: Abamectin, Imidacloprid (systemic)
- Biological: Ageniaspis citricola parasitoid, Cirrospilus quadristriatus
- Cultural: Remove and destroy infested leaves, avoid excess nitrogen
- Threshold: Treat when >25% of new flush leaves show serpentine mines

CITRUS PSYLLID — MANAGEMENT:
- Chemical: Dimethoate, Spirotetramat (systemic)
- Biological: Tamarixia radiata parasitoid, Diaphorencyrtus aligarhensis
- Cultural: Remove alternate hosts (e.g., Murraya paniculata), monitor regularly
- CRITICAL: Vector for HLB — zero tolerance, immediate action required

MEDITERRANEAN FRUIT FLY — MANAGEMENT:
- Chemical: Spinosad bait sprays, Malathion
- Biological: Diachasmimorpha longicaudata (parasitic wasp)
- Cultural: Strict field sanitation, collect and destroy fallen fruit, fruit bagging
- Monitoring: Pheromone traps (trimedlure) essential for detection

CITRUS RED MITE — MANAGEMENT:
- Chemical: Spirodiclofen, Propargite, Horticultural oils
- Biological: Predatory mites (Euseius tularensis), Stethorus beetles
- Cultural: Maintain adequate irrigation (drought stress exacerbates mites)
- Threshold: 5 mites per leaf

⚠️ DISCLAIMER: This information is for guidance only. Consult a certified agricultural expert before application.
""",

        "pest_management_vegetables.txt": """
VEGETABLE CROP PEST MANAGEMENT GUIDE
=======================================
Source: Compiled from various agricultural extension services.

COMMON VEGETABLE PESTS:
1. Tomato Hornworm (Manduca quinquemaculata)
2. Whitefly (Bemisia tabaci)
3. Spider Mites (Tetranychus urticae)
4. Thrips (Frankliniella occidentalis)
5. Leaf Miners (Liriomyza spp.)

TOMATO HORNWORM — MANAGEMENT:
- Chemical: Spinosad, Carbaryl (if severe)
- Biological: Bt (Bacillus thuringiensis), Trichogramma wasps, Braconid wasps
- Cultural: Hand-picking, tilling soil in fall to destroy pupae
- Threshold: Treat when defoliation exceeds 10%

WHITEFLY — MANAGEMENT:
- Chemical: Imidacloprid, Pyriproxyfen, Insecticidal soaps
- Biological: Encarsia formosa, Delphastus catalinae (ladybird beetle)
- Cultural: Reflective mulches, yellow sticky traps, weed management
- Note: High risk of resistance; rotate chemical modes of action

SPIDER MITES — MANAGEMENT:
- Chemical: Abamectin, Spiromesifen, Neem oil
- Biological: Phytoseiulus persimilis (predatory mite)
- Cultural: Reduce dust, avoid water stress, overhead irrigation can suppress
- Threshold: Treat before visible webbing occurs

⚠️ DISCLAIMER: This information is for guidance only. Consult a certified agricultural expert before application.
""",

        "ipm_principles_comprehensive.txt": """
COMPREHENSIVE INTEGRATED PEST MANAGEMENT (IPM) GUIDE
=======================================================
Source: FAO IPM Guidelines.

PRINCIPLE 1: PREVENTION AND SUPPRESSION
- Crop rotation to break pest life cycles
- Use of resistant or tolerant cultivars
- Proper seed bed preparation and sowing dates
- Balanced fertilization and irrigation
- Field sanitation and hygiene (cleaning equipment, removing infested plants)

PRINCIPLE 2: MONITORING
- Regular field scouting (at least weekly)
- Use of traps (pheromone, sticky, light)
- Keeping accurate records of pest incidence and weather
- Identifying both pests and their natural enemies

PRINCIPLE 3: DECISION MAKING (THRESHOLDS)
- Economic Threshold (ET): The pest density at which control measures should be applied to prevent an increasing pest population from reaching the Economic Injury Level.
- Economic Injury Level (EIL): The lowest population density that will cause economic damage.
- DO NOT treat if pest levels are below the threshold.

PRINCIPLE 4: NON-CHEMICAL METHODS (PRIORITY)
- Biological control: Conservation, augmentation, or introduction of natural enemies.
- Cultural control: Modifying the environment to make it less suitable for pests.
- Physical/Mechanical control: Hand-picking, netting, barriers, mulches.

PRINCIPLE 5: CHEMICAL CONTROL (AS LAST RESORT)
- Use highly selective pesticides when possible
- Target applications to specific areas (spot treatments)
- Always follow pesticide resistance management strategies
- Strictly adhere to label rates, timing, and safety precautions

PRINCIPLE 6: EVALUATION
- Assess the effectiveness of applied control measures
- Adapt future strategies based on results

⚠️ DISCLAIMER: This information is for guidance only. Consult a certified agricultural expert before application.
""",

        "pesticide_resistance_management.txt": """
PESTICIDE RESISTANCE MANAGEMENT GUIDE
========================================
Source: Insecticide Resistance Action Committee (IRAC).

WHAT IS PESTICIDE RESISTANCE?
Resistance is the heritable decrease in a pest population's susceptibility to a pesticide that previously controlled it.

MECHANISMS OF RESISTANCE:
1. Metabolic resistance: Pests detoxify or destroy the toxin faster.
2. Target-site resistance: The physical site where the toxin binds is mutated.
3. Penetration resistance: Thicker cuticles prevent the toxin from entering.
4. Behavioral resistance: Pests avoid treated areas.

CORE RESISTANCE MANAGEMENT STRATEGIES:
- Rotate Mode of Action (MoA): NEVER apply pesticides from the same IRAC group in consecutive generations of the pest.
- Use Mixtures: Combine two or more active ingredients with different MoAs, provided they are both effective against the pest.
- Follow Label Rates: Applying sub-lethal doses rapidly accelerates resistance development.
- Preserve Refuges: Leave small, untreated areas to maintain susceptible pest populations that will mate with resistant individuals.

COMMON IRAC GROUPS TO ROTATE:
- Group 1: Acetylcholinesterase inhibitors (e.g., Carbamates, Organophosphates)
- Group 3: Sodium channel modulators (e.g., Pyrethroids)
- Group 4: Nicotinic acetylcholine receptor agonists (e.g., Neonicotinoids)
- Group 5: Nicotinic acetylcholine receptor allosteric modulators (e.g., Spinosyns)
- Group 28: Ryanodine receptor modulators (e.g., Diamides)

⚠️ DISCLAIMER: This information is for guidance only. Consult a certified agricultural expert before application.
""",

        "biological_control_agents.txt": """
COMPREHENSIVE BIOLOGICAL CONTROL AGENTS REFERENCE
====================================================

PREDATORS (Consume many pests):
- Ladybird Beetles (Coccinellidae): Both adults and larvae voraciously consume aphids, scale insects, and mites.
- Lacewings (Chrysopidae): Larvae (aphid lions) feed on aphids, thrips, mites, and small caterpillars.
- Hoverflies (Syrphidae): Larvae are excellent aphid predators.
- Ground Beetles (Carabidae): Feed on soil-dwelling pests like cutworms, root maggots, and snail/slugs.
- Predatory Mites (Phytoseiidae): Crucial for controlling spider mites and thrips.

PARASITOIDS (Develop inside or on a host):
- Trichogramma wasps: Tiny wasps that parasitize the eggs of many moth/butterfly pests (e.g., corn borer, bollworm).
- Aphidius wasps: Parasitize aphids, turning them into rigid, bronzed 'mummies'.
- Encarsia formosa: Primary parasitoid used for greenhouse whitefly control.

MICROBIAL AGENTS (Pathogens):
- Bacillus thuringiensis (Bt): A bacterium toxic to specific insect orders (caterpillars, mosquito larvae, some beetles) when ingested. Safe for beneficials.
- Beauveria bassiana: A fungus that causes white muscardine disease in many insects (whiteflies, aphids, thrips). Requires high humidity.
- Metarhizium anisopliae: A fungus causing green muscardine disease, often used against soil pests and locusts.
- Nuclear Polyhedrosis Virus (NPV): Highly specific viruses used primarily against caterpillar pests like fall armyworm.

ENTOMOPATHOGENIC NEMATODES:
- Steinernema spp. and Heterorhabditis spp.: Microscopic worms applied to soil to control grubs, weevil larvae, and fungus gnats.

⚠️ DISCLAIMER: This information is for guidance only. Consult a certified agricultural expert before application.
""",

        "ip102_pest_catalog.txt": """
IP102 DATASET — COMPLETE PEST CATALOG
========================================
A reference listing major pest categories in the IP102 dataset with common names and hosts.

RICE PESTS:
Category 0: Rice Leaf Roller (Cnaphalocrocis medinalis)
Category 1: Rice Leaf Caterpillar
Category 2: Paddy Stem Maggot (Chlorops oryzae)
Category 3: Asiatic Rice Borer (Chilo suppressalis)
Category 4: Yellow Rice Borer (Scirpophaga incertulas)
Category 5: Rice Gall Midge (Orseolia oryzae)
Category 6: Rice Stemfighter
Category 7: Rice Water Weevil (Lissorhoptrus oryzophilus)

CORN PESTS:
Category 12: Corn Borer (Ostrinia furnacalis / nubilalis)
Category 13: Army worm (Mythimna separata)
Category 14: Aphid (Rhopalosiphum padi)
Category 15: Cutworm (Agrotis ipsilon)

WHEAT PESTS:
Category 20: Wheat Blossom Midge (Sitodiplosis mosellana)
Category 21: Wheat Phloeothrips
Category 22: Wheat Sawfly

BEET PESTS:
Category 30: Beet Army Worm (Spodoptera exigua)
Category 31: Beet Spot Flies
Category 32: Meadow Moth (Loxostege sticticalis)

ALFALFA PESTS:
Category 40: Alfalfa Weevil (Hypera postica)
Category 41: Alfalfa Plant Bug
Category 42: Tarnished Plant Bug (Lygus lineolaris)

CITRUS PESTS:
Category 50: Citrus Leaf Miner (Phyllocnistis citrella)
Category 51: Citrus Red Mite (Panonychus citri)
Category 52: Citrus Rust Mite (Phyllocoptruta oleivora)
Category 53: Papilio xuthus

MANGO PESTS:
Category 60: Mango Flat Beak Leafhopper
Category 61: Mango Leafhopper (Idioscopus clypealis)
Category 62: Mango Shoot Borer (Chlumetia transversa)

CABBAGE PESTS:
Category 70: Cabbage Webworm (Hellula undalis)
Category 71: Cabbage Moth (Mamestra brassicae)
Category 72: Diamondback Moth (Plutella xylostella)
Category 73: Cabbage Butterfly (Pieris rapae)
""",

        "pest_management_soybean.txt": """
SOYBEAN PEST MANAGEMENT GUIDE
===============================
Source: Compiled from Agricultural Extension Services.

COMMON SOYBEAN PESTS:
1. Soybean Aphid (Aphis glycines)
2. Bean Leaf Beetle (Cerotoma trifurcata)
3. Stink Bugs (Brown Marmorated, Green, Brown)
4. Soybean Looper (Chrysodeixis includens)
5. Spider Mites (Tetranychus urticae)

SOYBEAN APHID — MANAGEMENT:
- Chemical: Lambda-cyhalothrin, Bifenthrin, Chlorpyrifos
- Biological: Asian lady beetles (Harmonia axyridis), insidious flower bugs (Orius insidiosus)
- Cultural: Early planting, use of aphid-resistant soybean varieties (Rag genes)
- Threshold: 250 aphids per plant, with populations increasing

BEAN LEAF BEETLE — MANAGEMENT:
- Chemical: Seed treatments (Thiamethoxam, Imidacloprid) protect early stages; foliar pyrethroids for adults
- Biological: Ground beetles, parasitic tachinid flies
- Cultural: Delayed planting can reduce early colonizers
- Threshold: 20% defoliation during pod-fill stages

STINK BUGS — MANAGEMENT:
- Chemical: Acephate, Pyrethroids, Neonicotinoids (for early instars)
- Biological: Trissolcus wasps (egg parasitoids)
- Cultural: Trap crops (e.g., early-planted soybeans) to draw stink bugs away from main fields
- Threshold: 1 stink bug per foot of row during pod fill

⚠️ DISCLAIMER: This information is for guidance only. Consult a certified agricultural expert before application.
""",

        "pest_management_potato.txt": """
POTATO AND ROOT CROP PEST MANAGEMENT GUIDE
===========================================
Source: Root Crop Agricultural Extensions.

COMMON POTATO PESTS:
1. Colorado Potato Beetle (Leptinotarsa decemlineata)
2. Potato Leafhopper (Empoasca fabae)
3. Wireworms (Elateridae)
4. Potato Psyllid (Bactericerca cockerelli)

COLORADO POTATO BEETLE — MANAGEMENT:
- Chemical: Spinosad, Abamectin, Neonicotinoids (high resistance risk, rotate MoA strictly)
- Biological: Beauveria bassiana, Bt tenebrionis (specifically for beetle larvae)
- Cultural: Crop rotation (minimum 1/2 mile from previous year's field), trenching with plastic lining
- Threshold: 1 adult or 4 small larvae per plant

WIREWORM — MANAGEMENT:
- Chemical: In-furrow application of Ethoprop or Bifenthrin at planting
- Biological: Entomopathogenic nematodes (Heterorhabditis bacteriophora)
- Cultural: Avoid planting potatoes immediately after pasture or sod; cultivate fields deeply before planting
- Note: There are no effective rescue treatments once damage is observed. Preventive management is critical.

POTATO PSYLLID — MANAGEMENT:
- Chemical: Spiromesifen, Spirotetramat, Pymetrozine
- Biological: Generalist predators (lacewings, lady beetles)
- Cultural: Reflective mulches to deter landing
- Threat: Vector of Zebra Chip disease; strict management is essential.

⚠️ DISCLAIMER: This information is for guidance only. Consult a certified agricultural expert before application.
""",

        "pest_management_greenhouse.txt": """
GREENHOUSE & INDOOR PEST MANAGEMENT GUIDE
===========================================
Source: Controlled Environment Agriculture (CEA) Guidelines.

COMMON GREENHOUSE PESTS:
1. Greenhouse Whitefly (Trialeurodes vaporariorum)
2. Fungus Gnats (Bradysia spp.)
3. Western Flower Thrips (Frankliniella occidentalis)
4. Two-Spotted Spider Mite (Tetranychus urticae)

FUNGUS GNATS — MANAGEMENT:
- Chemical: Pyriproxyfen (IGR), Bacillus thuringiensis israelensis (Bti) soil drench
- Biological: Stratiolaelaps scimitus (soil predator mite), Steinernema feltiae (nematodes)
- Cultural: Avoid overwatering, improve drainage, remove algae build-up
- Threshold: Presence of adults on yellow sticky cards warrants larval treatment

WESTERN FLOWER THRIPS — MANAGEMENT:
- Chemical: Spinosad, Beauveria bassiana, Horticultural Oils
- Biological: Amblyseius swirskii (predatory mites), Orius spp. (pirate bugs)
- Cultural: Screen vents (fine mesh), strict sanitation, remove weed reservoirs
- Threat: Vector for Tomato Spotted Wilt Virus (TSWV) and Impatiens Necrotic Spot Virus (INSV).

TWO-SPOTTED SPIDER MITE — MANAGEMENT:
- Chemical: Bifenazate, Spiromesifen, Neem oil
- Biological: Phytoseiulus persimilis (highly effective predator mite in high humidity)
- Cultural: Maintain higher humidity (>60%), avoid excess nitrogen fertilizer
- Note: Mites rapidly develop resistance; rely heavily on biologicals.

⚠️ DISCLAIMER: This information is for guidance only. Consult a certified agricultural expert before application.
""",

        "pest_management_orchard_apple.txt": """
ORCHARD AND APPLE PEST MANAGEMENT GUIDE
==========================================
Source: Tree Fruit IPM Programs.

COMMON APPLE PESTS:
1. Codling Moth (Cydia pomonella)
2. Apple Maggot (Rhagoletis pomonella)
3. Plum Curculio (Conotrachelus nenuphar)
4. San Jose Scale (Quadraspidiotus perniciosus)
5. Rosy Apple Aphid (Dysaphis plantaginea)

CODLING MOTH — MANAGEMENT:
- Chemical: Chlorantraniliprole, Spinetoram, Acetamiprid
- Biological: Cydia pomonella granulovirus (CpGV), Trichogramma wasps
- Cultural: Mating disruption (pheromone ties/dispensers), trunk banding, sanitation
- Monitoring: Degree-day models coupled with pheromone trap catches

APPLE MAGGOT — MANAGEMENT:
- Chemical: Phosmet, Assail, Spinosad
- Biological: Minimal biological control options; reliance on chemical and cultural
- Cultural: Pick up and destroy dropped fruit weekly to prevent larvae from entering soil
- Monitoring: Red sphere sticky traps baited with apple volatile lures

SAN JOSE SCALE — MANAGEMENT:
- Chemical: Dormant horticultural oil sprays, Pyriproxyfen, Buprofezin
- Biological: Encarsia perniciosi (parasitic wasp), lady beetles
- Cultural: Prune out heavily infested branches to improve spray coverage
- Timing: Critical to target the "crawler" stage in early summer.

⚠️ DISCLAIMER: This information is for guidance only. Consult a certified agricultural expert before application.
""",

        "pest_management_coffee.txt": """
COFFEE CROP PEST MANAGEMENT GUIDE
===================================
Source: Global Coffee Research Institute.

COMMON COFFEE PESTS:
1. Coffee Berry Borer (Hypothenemus hampei)
2. Coffee Leaf Miner (Leucoptera coffeella)
3. Coffee White Stem Borer (Monochamus leuconotus)
4. Root-knot Nematodes (Meloidogyne spp.)

COFFEE BERRY BORER (CBB) — MANAGEMENT:
- Chemical: Cyantraniliprole, Beauveria bassiana sprays (biological/chemical hybrid)
- Biological: Cephalonomia stephanoderis, Prorops nasuta (bethylid wasps)
- Cultural: Strict harvesting hygiene (strip picking), destroying unharvested or fallen berries
- Monitoring: Broca traps baited with methanol/ethanol mixtures

COFFEE LEAF MINER — MANAGEMENT:
- Chemical: Cartap, Thiamethoxam
- Biological: Predatory wasps (Vespidae) and diverse parasitoid complexes
- Cultural: Provide adequate shade (shade-grown coffee has lower miner incidence)
- Threshold: 20-30% of leaves mined

COFFEE WHITE STEM BORER — MANAGEMENT:
- Chemical: Stem banding with Chlorpyrifos (where permitted)
- Biological: Minimal, though woodpeckers provide some natural control
- Cultural: Uprooting and burning infested trees; scrubbing stems to dislodge eggs
- Note: Chiefly a problem in Arabica coffee.

⚠️ DISCLAIMER: This information is for guidance only. Consult a certified agricultural expert before application.
""",

        "nematode_management_guide.txt": """
NEMATODE MANAGEMENT AND CONTROL GUIDE
=======================================
Source: Plant Pathology and Nematology References.

WHAT ARE PLANT-PARASITIC NEMATODES?
Microscopic roundworms that live in the soil and feed on plant roots, causing stunting, yellowing, and significant yield loss.

COMMON NEMATODES:
1. Root-Knot Nematodes (Meloidogyne spp.) - Causes galls/knots on roots.
2. Soybean Cyst Nematode (Heterodera glycines) - Cysts form on roots.
3. Lesion Nematodes (Pratylenchus spp.) - Causes dark lesions on roots and tubers.

MANAGEMENT PRINCIPLES:
1. Soil Sampling: Nematodes cannot be seen with the naked eye. Soil tests by diagnostic labs are essential to identify species and population densities.
2. Crop Rotation: The most effective cultural control. Rotate with non-host crops. For example, rotate corn (non-host) with soybeans (host for SCN).
3. Resistant Varieties: Use plant varieties bred for resistance to specific nematode strains (e.g., PI 88788 for Soybean Cyst Nematode).
4. Chemical Control (Nematicides):
   - Fumigants (e.g., 1,3-Dichloropropene, Metam sodium): Applied pre-plant to sterilize soil. Highly toxic and expensive.
   - Non-fumigants (e.g., Oxamyl, Fluopyram): Applied at planting or as seed treatments.
5. Biological Control:
   - Pasteuria penetrans (bacterial parasite of nematodes)
   - Purpureocillium lilacinum (fungus that infects nematode eggs)
6. Cultural Control: Soil solarization, planting cover crops (like marigold, which produces alpha-terthienyl that is toxic to nematodes).

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
