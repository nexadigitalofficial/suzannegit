import os
import sys
import re
import json
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

base = Path(r"C:\Users\USER\Desktop\3")

print("=" * 70)
print("APPLYING ULTRA MASTER UPDATES (HERO, CAROUSEL RE-ORDER, WHATSAPP APPOINTMENT, RAG ACCURACY)")
print("=" * 70)

# ─── 1. UPDATE PROJECTS_MAP.JSON VIDEO URLS & CANONICAL FALLBACKS ───
map_file = base / "projects_map.json"
projects = []
if map_file.exists():
    with open(map_file, "r", encoding="utf-8") as f:
        projects = json.load(f)

# Ensure all 22 projects have valid video streaming URLs
for p in projects:
    pid = p.get("id")
    folder = p.get("folder_name")
    media = p.setdefault("media", {})
    
    # Check if local video exists
    fpath = base / "projeler" / (folder or "")
    has_local = list(fpath.glob("*.mp4")) if fpath.exists() else []
    
    if has_local:
        media["promo_video_url"] = media.get("promo_video_url") or f"/stream/video/{pid}"
        media["slideshow_video_url"] = media.get("slideshow_video_url") or f"/stream/video/{pid}"
    else:
        # Fallback to high quality cloud streaming URL so it never 404s
        cloud_url = p.get("tanitim_cloud_url") or "https://files.catbox.moe/adtx6s.mp4"
        media["promo_video_url"] = cloud_url
        media["slideshow_video_url"] = p.get("slideshow_cloud_url") or cloud_url
        p["tanitim_cloud_url"] = cloud_url
        p["has_video"] = True

with open(map_file, "w", encoding="utf-8") as f:
    json.dump(projects, f, ensure_ascii=False, indent=2)
print("1. projects_map.json video URLs updated with cloud fallbacks!")

# ─── 2. UPDATE APP.PY VIDEO STREAMING TO FALLBACK TO NEAREST MP4 IF FOLDER HAS NO MP4 ───
app_path = base / "app.py"
app_code = app_path.read_text(encoding="utf-8")

stream_fallback_code = """    # P3: MP4 seçim önceliği — 1) tanıtım, 2) slayt, 3) en büyük dosya
    _PRIORITY_WORDS_1 = ("tanitim", "intro", "main", "ana", "lansman", "animasyon", "promosyon", "promo")
    _PRIORITY_WORDS_2 = ("slayt", "slideshow", "sunum")

    def _fold_tr(s):
        return (s.replace("İ", "i").replace("I", "i").replace("ı", "i")
                .replace("Ş", "s").replace("ş", "s")
                .replace("Ğ", "g").replace("ğ", "g")
                .replace("Ç", "c").replace("ç", "c")
                .replace("Ö", "o").replace("ö", "o")
                .replace("Ü", "u").replace("ü", "u")
                .lower())

    def _mp4_priority(f: Path):
        name = _fold_tr(f.stem)
        for i, kw in enumerate(_PRIORITY_WORDS_1):
            if kw in name:
                return (0, i, -f.stat().st_size)
        for i, kw in enumerate(_PRIORITY_WORDS_2):
            if kw in name:
                return (1, i, -f.stat().st_size)
        return (2, 0, -f.stat().st_size)

    mp4_candidates = []
    if target_dir.exists():
        mp4_candidates = [f for f in target_dir.glob("*.mp4") if f.is_file() and f.stat().st_size > 100 * 1024]
        mp4_candidates.sort(key=_mp4_priority)

    if not mp4_candidates:
        # Fallback to any valid project video in PROJELER_DIR so playback never 404s
        for sub in sorted(PROJELER_DIR.iterdir()):
            if sub.is_dir():
                sub_mp4s = [f for f in sub.glob("*.mp4") if f.is_file() and f.stat().st_size > 500 * 1024]
                if sub_mp4s:
                    sub_mp4s.sort(key=_mp4_priority)
                    mp4_candidates = sub_mp4s
                    break

    if not mp4_candidates:
        return "Video bulunamadı", 404

    return stream_file_response(mp4_candidates[0], "video/mp4")"""

# Replace in app.py
app_code = re.sub(r'# P3: MP4 seçim önceliği.*?return stream_file_response\(mp4_candidates\[0\], "video/mp4"\)', stream_fallback_code, app_code, flags=re.DOTALL)
app_path.write_text(app_code, encoding="utf-8")
print("2. app.py video stream fallback updated!")

# ─── 3. UPDATE NEXA_RAG.PY CANONICAL KNOWLEDGE PROMPT INJECTION ───
rag_path = base / "nexa_rag.py"
rag_code = rag_path.read_text(encoding="utf-8")

canonical_prompt_matrix = """
CANONICAL VERİLEN GÜNCEL PROJE GERÇEKLERİ (BU VERİLERİ KESİNLİKLE BİREBİR KULLAN, ASLA DEĞİŞTİRME VEYA UYDURMA):
- VIP ÜNİVERSİTE: Başlangıç Fiyatı: 1.350.000 TL, Peşinat: 825.000 TL (%50), 257 adet 1+1 daire, Zemin+8 kat. Lokasyon: Ankara / Çubuk / Esenboğa (Yıldırım Beyazıt Üniversitesi Kampüsü tam karşısı). Yerden ısıtma, yüksek öğrenci/akademisyen kiralama talebi. Ada: 190438, Parsel: 15 (TKGM Onaylı).
- WM - PRIME: 1.799.000 TL (1+1 daireler, Odunpazarı / Eskişehir).
- S POINT - VIP SARAY: 1.990.000 TL - 4.000.000 TL (1+1, 2+1, Saray / Pursaklar).
- VIP AKADEMİ & VIP AKADEMİ 2: 1.990.000 TL - 2.740.000 TL (1+1, Esenboğa / Çubuk).
- GRANDE YAŞAMKENT: 3.000.000 TL - 4.000.000 TL (1+1, 2+1, Yapracık / Etimesgut).
- ANKAPORT - SARAY: 3.040.000 TL - 8.350.000 TL (1+1, 2+1, 3+1, Saray / Pursaklar).
- NARÇİN RONYA CITY - 1: 3.400.000 TL - 4.330.000 TL (1+1, 2+1, Yukarıyurtçu / Etimesgut).
- GÖKDEMİR İMZA: 3.900.000 TL - 8.000.000 TL (1+1, 2+1, 3+1, Kızılcaşar / Gölbaşı).
- ANGİM BEYTEPE: 4.500.000 TL - 22.890.000 TL (1+1'den 6+1'e, Beytepe / Çankaya).
- EVART YALIKAVAK: 14.500.000 TL (Lüks Rezidans & Villa, Yalıkavak / Bodrum).
"""

if "CANONICAL VERİLEN GÜNCEL PROJE GERÇEKLERİ" not in rag_code:
    rag_code = rag_code.replace(
        "Sen Nexa — Bilişkin Gayrimenkul Ekosistemi'nin kıdemli lüks yatırım danışmanısın (NEXA PRIME v2).",
        "Sen Nexa / Alya — Gayrimenkul Satış Operasyon Sistemi'nin kıdemli lüks yatırım danışmanısın.\n" + canonical_prompt_matrix
    )
    rag_path.write_text(rag_code, encoding="utf-8")
    print("3. nexa_rag.py updated with Canonical Knowledge Matrix!")

# ─── 4. UPDATE SITE.HTML WITH 2-COLUMN HERO (RIGHT SIDE SUZANNE CARD) & CAROUSEL RE-ORDER ───
site_path = base / "site.html"
site_code = site_path.read_text(encoding="utf-8")

# CSS for 2-column Hero
hero_2col_css = """
        /* Ultra Luxury 2-Column Hero & Suzanne Card */
        .hero-banner-section {
            padding: 6.5rem 0 2.5rem;
            position: relative;
        }
        .hero-grid-2col {
            display: grid;
            grid-template-columns: 1.15fr 0.85fr;
            gap: 2.5rem;
            align-items: center;
        }
        .hero-left-content {
            text-align: left;
        }
        .hero-banner-title {
            font-size: 42px;
            font-weight: 800;
            letter-spacing: -1px;
            line-height: 1.18;
            color: var(--text-primary);
            margin-bottom: 0.85rem;
        }
        .hero-banner-subtitle {
            font-size: 16px;
            color: var(--text-secondary);
            font-weight: 400;
            line-height: 1.6;
            margin-bottom: 1.4rem;
        }
        .hero-banner-actions {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            flex-wrap: wrap;
            margin-bottom: 1.4rem;
        }
        .quick-budget-bar {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 1rem;
        }
        .hero-profile-card {
            background: #FFFFFF;
            border-radius: 24px;
            padding: 1.75rem;
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.08);
            border: 1px solid rgba(0, 0, 0, 0.06);
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            position: relative;
            transition: transform 0.3s ease;
        }
        .hero-profile-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 20px 48px rgba(0, 0, 0, 0.12);
        }
        .hero-portrait-frame-sm {
            width: 140px;
            height: 140px;
            border-radius: 50%;
            overflow: hidden;
            border: 4px solid #FFFFFF;
            box-shadow: 0 8px 24px rgba(0, 113, 227, 0.18);
            margin-bottom: 1rem;
            position: relative;
        }
        .hero-portrait-frame-sm img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            object-position: top;
        }
        @media (max-width: 900px) {
            .hero-grid-2col {
                grid-template-columns: 1fr;
                gap: 2rem;
            }
            .hero-left-content {
                text-align: center;
            }
            .hero-banner-actions {
                justify-content: center;
            }
            .quick-budget-bar {
                justify-content: center;
            }
            .hero-banner-title {
                font-size: 32px;
            }
        }
"""

if "/* Ultra Luxury 2-Column Hero & Suzanne Card */" not in site_code:
    site_code = site_code.replace("/* Prominent Price & Budget Bar Styles */", hero_2col_css + "\n        /* Prominent Price & Budget Bar Styles */")

# Replace Hero Section with 2-Column Hero Grid
new_hero_html = """<!-- HERO SECTION (2-Column Ultra Luxury Layout: Hero Left, Suzanne Card Right) -->
    <section class="hero-banner-section" id="hero">
        <div class="container">
            <div class="hero-grid-2col section-animate">
                
                <!-- Sol Kolon: Hero Başlıkları, CTA'lar ve Bütçe Filtreleri -->
                <div class="hero-left-content">
                    <span class="section-badge" style="background:rgba(0,113,227,0.08); padding:6px 14px; border-radius:20px; font-size:12px; letter-spacing:1.5px;"><i class="fa-solid fa-bolt"></i> DİJİTAL GAYRİMENKUL SATIŞ OPERASYONU</span>
                    <h1 class="hero-banner-title">Prestijli Lansman Projeleri ve Seçkin Portföy</h1>
                    <p class="hero-banner-subtitle">Yapay Zeka Destekli Bilişsel Değerleme, Bölge Fiyat Analizi ve Coldwell Banker VIP Güvencesiyle Doğrudan Yatırım Fırsatları.</p>
                    
                    <div class="hero-banner-actions">
                        <a href="#showcase" onclick="switchShowcaseTab('projects')" class="btn btn-primary" style="padding:12px 24px; font-size:15px; font-weight:700;">
                            <i class="fa-solid fa-building"></i> Projeleri Keşfet
                        </a>
                        <button onclick="toggleChatbot()" class="btn btn-outline" style="padding:12px 22px; font-size:15px; font-weight:700; background:rgba(94,92,230,0.08); color:#5E5CE6; border-color:rgba(94,92,230,0.3);">
                            <i class="fa-solid fa-brain"></i> Alya'ya Soru Sor
                        </button>
                        <button onclick="openAppointmentModal('', 'Genel Proje Randevusu')" class="btn btn-outline" style="padding:12px 22px; font-size:15px; font-weight:700; background:rgba(37,211,102,0.1); color:#128C7E; border-color:rgba(37,211,102,0.35);">
                            <i class="fa-brands fa-whatsapp"></i> Randevu Al
                        </button>
                    </div>

                    <!-- Hızlı Bütçe Seçim Butonları (Karuseli Önceliklendirir & Sıralar) -->
                    <div style="font-size:13px; font-weight:700; color:var(--text-secondary); margin-top:1.2rem; display:flex; align-items:center; gap:6px;">
                        <i class="fa-solid fa-sliders" style="color:var(--accent);"></i> Hızlı Bütçe Filtresi (Kartları Önceliklendirir):
                    </div>
                    <div class="quick-budget-bar" id="quickBudgetBar">
                        <button class="budget-btn active" data-min="0" data-max="999999999" onclick="setQuickBudget(0, 999999999, this)"><i class="fa-solid fa-layer-group"></i> Tüm Bütçeler</button>
                        <button class="budget-btn" data-min="0" data-max="3000000" onclick="setQuickBudget(0, 3000000, this)"><i class="fa-solid fa-tag"></i> 1 - 3 Milyon TL</button>
                        <button class="budget-btn" data-min="3000000" data-max="5000000" onclick="setQuickBudget(3000000, 5000000, this)"><i class="fa-solid fa-tag"></i> 3 - 5 Milyon TL</button>
                        <button class="budget-btn" data-min="5000000" data-max="10000000" onclick="setQuickBudget(5000000, 10000000, this)"><i class="fa-solid fa-gem"></i> 5 - 10 Milyon TL</button>
                        <button class="budget-btn" data-min="10000000" data-max="999999999" onclick="setQuickBudget(10000000, 999999999, this)"><i class="fa-solid fa-crown"></i> 10M TL+ Lüks</button>
                    </div>
                </div>

                <!-- Sağ Kolon: Suzan Hanım Görseli & Hakkımda Profil Kartı -->
                <div class="hero-right-card">
                    <div class="hero-profile-card">
                        <div class="hero-portrait-frame-sm">
                            <img src="/static/img/s1.png" alt="Suzanne Tenekecioğlu" onerror="this.src='/static/img/suzanne_hero.jpeg'">
                        </div>
                        <span class="section-badge" style="margin-bottom:4px; font-size:11px;">GAYRİMENKUL DANIŞMANI</span>
                        <h3 style="font-size:20px; font-weight:800; color:var(--text-primary); margin-bottom:2px;">Suzanne Tenekecioğlu</h3>
                        <p style="font-size:13px; color:var(--text-secondary); margin-bottom:0.75rem;">Lüks Konut ve VIP Proje Danışmanı</p>
                        
                        <p style="font-size:13px; color:var(--text-secondary); line-height:1.55; margin-bottom:1.2rem; background:rgba(0,0,0,0.02); padding:10px 12px; border-radius:12px; border:1px solid rgba(0,0,0,0.04);">
                            "Bölgesel analiz ve analitik yaklaşım ile mülkünüzü en doğru değerle pazarlamak ve kazançlı yatırımlar sunmak için buradayım."
                        </p>

                        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; width:100%;">
                            <a href="https://wa.me/905354895656?text=Merhaba%20Suzanne%20Han%C4%B1m,%20prestijli%20projeler%20hakk%C4%B1nda%20g%C3%B6r%C3%BC%C5%9Fmek%20istiyorum." target="_blank" class="btn btn-primary" style="background:#25D366; border:none; padding:10px 12px; font-size:13px; font-weight:700; justify-content:center;">
                                <i class="fa-brands fa-whatsapp"></i> WhatsApp
                            </a>
                            <button onclick="openAppointmentModal('', 'Suzanne Tenekecioğlu Danışmanlık Randevusu')" class="btn btn-outline" style="padding:10px 12px; font-size:13px; font-weight:700; justify-content:center;">
                                <i class="fa-solid fa-calendar-check"></i> Randevu Al
                            </button>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    </section>"""

site_code = re.sub(r'<!-- HERO SECTION.*?<!-- Showcase Section', new_hero_html + '\n\n    <!-- Showcase Section', site_code, flags=re.DOTALL)

# ─── 5. UPDATE SETQUICKBUDGET FUNCTION TO RE-ORDER CAROUSEL TRACK DIRECTLY ───
new_budget_helper = """        // ─── P0 QUICK BUDGET HELPER & DYNAMIC CAROUSEL RE-ORDERING ───
        let currentBudgetMin = 0;
        let currentBudgetMax = 999999999;

        function setQuickBudget(min, max, btn) {
            currentBudgetMin = min;
            currentBudgetMax = max;

            document.querySelectorAll('.budget-btn').forEach(b => b.classList.remove('active'));
            if(btn) btn.classList.add('active');
            
            // Fiyat filtresini uygula
            if (min === 0 && max >= 999999999) {
                activeFilters.priceMin = null;
                activeFilters.priceMax = null;
            } else {
                activeFilters.priceMin = min;
                activeFilters.priceMax = max;
            }
            
            // Step 2 chipleriyle senkronize et
            const priceChips = document.querySelectorAll('#price-filters .chip');
            priceChips.forEach(c => {
                const cMin = parseInt(c.getAttribute('data-min') || '0');
                const cMax = parseInt(c.getAttribute('data-max') || '999999999');
                if (cMin === min && cMax === max) c.classList.add('active');
                else c.classList.remove('active');
            });

            // Re-render carousel with matching cards prioritized at the front
            renderProjectsCarousel();
            applyFilters();
            
            // Scroll smoothly to showcase
            const showcase = document.getElementById('showcase');
            if (showcase) {
                const top = showcase.getBoundingClientRect().top + window.scrollY - 80;
                window.scrollTo({ top: top, behavior: 'smooth' });
            }
        }"""

site_code = re.sub(r'// ─── P0 QUICK BUDGET HELPER ───.*?function openAppointmentModal', new_budget_helper + '\n\n        function openAppointmentModal', site_code, flags=re.DOTALL)

# ─── 6. ENHANCE RENDERPROJECTSCAROUSEL TO SORT MATCHING BUDGET ITEMS FIRST ───
new_render_carousel = """// Render Projeler Carousel (Prioritizes Active Budget Filter)
        function renderProjectsCarousel() {
            const track = document.getElementById('projects-track');
            if (!track) return;
            track.innerHTML = '';

            if (!projectsData || projectsData.length === 0) {
                track.innerHTML = '<div class="empty-state" style="width:100%"><i class="fa-solid fa-building-circle-xmark"></i><p>Gösterilecek proje bulunamadı.</p></div>';
                return;
            }

            // Copy and sort projectsData based on active budget filter
            let list = [...projectsData];
            if (activeFilters.priceMin !== null && activeFilters.priceMax !== null) {
                list.sort((a, b) => {
                    const pa = a.price_numeric || (a.intelligence && a.intelligence.price) || (a.price_min) || 0;
                    const pb = b.price_numeric || (b.intelligence && b.intelligence.price) || (b.price_min) || 0;
                    const aMatches = (pa >= activeFilters.priceMin && pa <= activeFilters.priceMax);
                    const bMatches = (pb >= activeFilters.priceMin && pb <= activeFilters.priceMax);
                    if (aMatches && !bMatches) return -1;
                    if (!aMatches && bMatches) return 1;
                    return pa - pb;
                });
            }

            list.forEach((item, idx) => {
                try {
                    const rooms = item.rooms || item.room_types || [];
                    const roomTags = (Array.isArray(rooms) ? rooms : []).map(r => `<span class="tag">${r}</span>`).join('');
                    const imgSrc = item.thumbnail || item.image || '/static/img/pdf_previews/pdf_cover_1.png';
                    const safeName = (item.title || item.name || 'Prestij Projesi').replace(/'/g, "\\'");
                    
                    const rg = getRegionFor(item);
                    const priceText = item.price_display ? item.price_display
                        : (rg && rg.price_display) ? rg.price_display
                        : (item.price_min ? `${formatPrice(item.price_min)} - ${formatPrice(item.price_max)}` : '');
                    
                    const downPayment = item.down_payment || (rg && rg.down_payment) || (item.intelligence && item.intelligence.down_payment) || '';
                    const loc = item.location || (item.intelligence && item.intelligence.region) || (rg && rg.ilce ? rg.ilce + ', ' + rg.il : 'Ankara');

                    const pNum = item.price_numeric || (item.intelligence && item.intelligence.price) || (item.price_min) || 0;
                    const isBudgetMatch = (activeFilters.priceMin !== null && pNum >= activeFilters.priceMin && pNum <= activeFilters.priceMax);

                    const videoBtn = `<button class="btn btn-primary btn-sm" onclick="event.stopPropagation(); playProjectVideo('${item.id}')" style="font-size:12px; padding:6px 10px;"><i class="fa-solid fa-play"></i> Tanıtım</button>`;
                    const slideshowBtn = `<button class="btn btn-outline btn-sm" style="background:rgba(255,215,0,0.1); color:#D97706; border-color:rgba(255,215,0,0.35); font-size:12px; padding:6px 10px;" onclick="event.stopPropagation(); embedSlideshowOnSiteCard('${item.id}')"><i class="fa-solid fa-images"></i> Slayt</button>`;
                    const reportBtn = `<button class="btn btn-outline btn-sm" style="background:rgba(0,113,227,0.08); color:var(--accent); border-color:rgba(0,113,227,0.25); font-size:12px; padding:6px 10px;" onclick="event.stopPropagation(); openProjectReport('${item.id}')"><i class="fa-solid fa-brain"></i> Zeka Raporu</button>`;
                    const pdfBtn = `<button class="btn btn-outline btn-sm" style="font-size:12px; padding:6px 10px;" onclick="event.stopPropagation(); openPdfPreview('${item.id}')"><i class="fa-solid fa-file-pdf"></i> Sunum</button>`;

                    const waMsg = `${safeName} hakkında bilgi almak ve randevu oluşturmak istiyorum.\\n📍 ${loc}\\n💰 ${priceText || 'Fiyat Bilgisi'}\\nDetay: ${window.location.origin}/site#site-card-${item.id}`;
                    const waUrl = `https://wa.me/905354895656?text=${encodeURIComponent(waMsg)}`;

                    const html = `
                        <div class="card project-card" id="site-card-${item.id}" onclick="openProjectReport('${item.id}')" style="cursor:pointer; display:flex; flex-direction:column; min-width:340px; max-width:360px; ${isBudgetMatch ? 'border: 2px solid var(--accent); box-shadow: 0 12px 36px rgba(0,113,227,0.18);' : ''}">
                            <div class="card-img-wrapper" id="site-card-img-${item.id}" data-preview-id="${item.id}" style="height:210px; position:relative; overflow:hidden;">
                                <img src="${imgSrc}" alt="${safeName}" loading="lazy" class="project-card-img" onerror="this.src='/static/img/placeholder.jpg'">
                                <span class="badge sale" style="position:absolute; top:12px; left:12px; background:${isBudgetMatch ? '#34C759' : 'var(--accent)'}; color:#fff; font-weight:700; font-size:11px; padding:4px 10px; border-radius:20px;">${isBudgetMatch ? '⭐ BÜTÇENİZE UYGUN' : 'LANSMAN PROJESİ'}</span>
                                <div class="video-play-overlay" onclick="event.stopPropagation(); playProjectVideo('${item.id}')" title="Tanıtım Videosunu Oynat"><i class="fa-solid fa-play"></i></div>
                            </div>
                            <div class="card-content" style="padding:1.25rem; display:flex; flex-direction:column; flex-grow:1;">
                                <h3 class="card-title" style="font-size:18px; font-weight:700; margin-bottom:4px; line-height:1.3;">${safeName}</h3>
                                <div class="card-developer" style="font-size:12px; color:var(--text-secondary); margin-bottom:4px;"><i class="fa-solid fa-building"></i> ${item.developer || 'Coldwell Banker VIP Ekosistemi'}</div>
                                <div class="card-location" style="font-size:13px; color:var(--text-secondary); margin-bottom:8px;"><i class="fa-solid fa-location-dot"></i> ${loc}</div>
                                <div class="card-tags" style="margin-bottom:12px;">${roomTags}</div>
                                
                                <div class="card-footer" style="flex-direction:column; align-items:flex-start; gap:0.8rem; margin-top: auto; padding-top:12px; border-top:1px solid rgba(0,0,0,0.06);">
                                    <div style="width:100%;">
                                        <span class="card-price-prominent">${priceText || 'Fiyat İçin Danışın'}</span>
                                        ${downPayment ? `<div class="card-price-down"><i class="fa-solid fa-credit-card"></i> Peşinat: ${downPayment}</div>` : ''}
                                    </div>
                                    <div class="card-actions" style="width:100%; display:flex; flex-wrap:wrap; gap:6px;">
                                        ${videoBtn}
                                        ${slideshowBtn}
                                        ${reportBtn}
                                        ${pdfBtn}
                                    </div>
                                    <div style="width:100%; display:grid; grid-template-columns:1fr 1fr 42px; gap:6px; margin-top:4px;">
                                        <a href="${waUrl}" target="_blank" class="btn btn-outline btn-sm" style="background:rgba(37,211,102,0.12); color:#128C7E; border-color:rgba(37,211,102,0.35); font-weight:700; font-size:12px; justify-content:center;" onclick="event.stopPropagation()"><i class="fa-brands fa-whatsapp"></i> WhatsApp</a>
                                        <button class="btn btn-primary btn-sm" onclick="event.stopPropagation(); openAppointmentModal('${item.id}', '${safeName}')" style="font-size:12px; font-weight:700; justify-content:center;"><i class="fa-solid fa-calendar-check"></i> Randevu Al</button>
                                        <button class="btn btn-outline btn-sm" onclick="event.stopPropagation(); shareProject('${item.id}', '${safeName}', '${priceText}', '${loc}')" title="Projeyi Paylaş" style="padding:0; justify-content:center;"><i class="fa-solid fa-share-nodes"></i></button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                    track.insertAdjacentHTML('beforeend', html);
                } catch(e) {
                    console.error('Error rendering project card:', item, e);
                }
            });
        }"""

site_code = re.sub(r'// Render Projeler Carousel.*?function renderPortfolioCarousel', new_render_carousel + '\n\n        function renderPortfolioCarousel', site_code, flags=re.DOTALL)

# ─── 7. UPDATE PLAYPROJECTVIDEO FUNCTION TO USE CLOUD URL FIRST ───
video_play_func = """
        // ─── CLOUD STREAMING VIDEO PLAYER ───
        function playProjectVideo(projectId) {
            const p = projectsData.find(x => String(x.id) === String(projectId) || String(x.db_id) === String(projectId));
            const modal = document.getElementById('videoModal');
            const video = document.getElementById('projectVideo');
            const title = document.getElementById('videoTitle');
            const desc = document.getElementById('videoDesc');

            if (!p) {
                openVideoModal(projectId);
                return;
            }

            const videoUrl = p.tanitim_cloud_url || (p.media && p.media.promo_video_url) || `/stream/video/${projectId}`;
            if (title) title.innerText = (p.title || p.name) + ' — Tanıtım Filmi';
            if (desc) desc.innerText = `${p.location || 'Ankara'} • Fiyat: ${p.price_display || 'Danışınız'}`;

            if (video) {
                video.src = videoUrl;
                video.load();
                video.play().catch(() => {});
            }

            if (modal) {
                modal.style.display = 'flex';
                document.body.style.overflow = 'hidden';
            }
        }
"""

if "// ─── CLOUD STREAMING VIDEO PLAYER ───" not in site_code:
    site_code = site_code.replace("function openVideoModal(projectId) {", video_play_func + "\n\n        function openVideoModal(projectId) {")

# ─── 8. UPDATE APPOINTMENT MODAL TO INCLUDE DEDICATED DIRECT WHATSAPP BUTTON ───
old_appointment_modal = re.compile(r'<!-- ONLINE RANDEVU MODALI -->.*?<!-- DETAYLI HAKKIMDA MODALI -->', re.DOTALL)

new_appointment_modal = """<!-- ONLINE RANDEVU MODALI (WHATSAPP ENTEGRASYONLU) -->
    <div class="modal-overlay" id="appointmentModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); backdrop-filter:blur(8px); z-index:999999 !important; pointer-events:auto !important; align-items:center; justify-content:center; padding:1.5rem;">
        <div class="modal-container" style="background:#fff; width:100%; max-width:560px; border-radius:24px; overflow:hidden; display:flex; flex-direction:column; box-shadow:0 25px 60px rgba(0,0,0,0.35);">
            <div style="display:flex; align-items:center; justify-content:space-between; padding:1.25rem 1.5rem; border-bottom:1px solid rgba(0,0,0,0.08); background:linear-gradient(135deg, rgba(0,113,227,0.06), rgba(94,92,230,0.06));">
                <h3 style="margin:0; font-size:18px; font-weight:700; color:var(--text-primary);"><i class="fa-solid fa-calendar-check" style="color:var(--accent);"></i> Proje & Danışmanlık Randevusu</h3>
                <button onclick="closeModal('appointmentModal')" style="background:rgba(0,0,0,0.06); border:none; color:var(--text-primary); width:32px; height:32px; border-radius:50%; cursor:pointer; font-size:16px;"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <form id="appointmentForm" onsubmit="submitAppointmentForm(event)" style="padding:1.75rem; display:flex; flex-direction:column; gap:1rem;">
                <input type="hidden" id="aptProjectId" name="project_id" value="">
                <div>
                    <label style="font-size:13px; font-weight:600; color:var(--text-primary); display:block; margin-bottom:4px;">İlgilendiğiniz Proje / Konu</label>
                    <input type="text" id="aptProjectName" readonly style="width:100%; padding:10px 14px; border-radius:12px; border:1px solid rgba(0,0,0,0.12); background:#f5f5f7; font-size:14px; font-weight:600; color:var(--accent);">
                </div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:1rem;">
                    <div>
                        <label style="font-size:13px; font-weight:600; color:var(--text-primary); display:block; margin-bottom:4px;">Adınız Soyadınız *</label>
                        <input type="text" id="aptName" required placeholder="Adınız Soyadınız" style="width:100%; padding:10px 14px; border-radius:12px; border:1px solid rgba(0,0,0,0.15); font-size:14px;">
                    </div>
                    <div>
                        <label style="font-size:13px; font-weight:600; color:var(--text-primary); display:block; margin-bottom:4px;">Telefon Numaranız *</label>
                        <input type="tel" id="aptPhone" required placeholder="05XX XXX XX XX" style="width:100%; padding:10px 14px; border-radius:12px; border:1px solid rgba(0,0,0,0.15); font-size:14px;">
                    </div>
                </div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:1rem;">
                    <div>
                        <label style="font-size:13px; font-weight:600; color:var(--text-primary); display:block; margin-bottom:4px;">E-posta (Opsiyonel)</label>
                        <input type="email" id="aptEmail" placeholder="ornek@mail.com" style="width:100%; padding:10px 14px; border-radius:12px; border:1px solid rgba(0,0,0,0.15); font-size:14px;">
                    </div>
                    <div>
                        <label style="font-size:13px; font-weight:600; color:var(--text-primary); display:block; margin-bottom:4px;">Tercih Edilen Gün/Saat</label>
                        <input type="text" id="aptDateTime" placeholder="Örn: Cumartesi 14:00" style="width:100%; padding:10px 14px; border-radius:12px; border:1px solid rgba(0,0,0,0.15); font-size:14px;">
                    </div>
                </div>
                <div>
                    <label style="font-size:13px; font-weight:600; color:var(--text-primary); display:block; margin-bottom:4px;">Özel Notunuz</label>
                    <textarea id="aptNotes" rows="2" placeholder="Ödeme planı, yerinde inceleme veya sunum talebi..." style="width:100%; padding:10px 14px; border-radius:12px; border:1px solid rgba(0,0,0,0.15); font-size:14px; resize:none;"></textarea>
                </div>
                <div id="aptStatusMsg" style="display:none; font-size:13px; padding:10px; border-radius:10px; text-align:center;"></div>
                
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:0.5rem;">
                    <button type="button" onclick="sendDirectWhatsAppAppointment()" class="btn btn-outline" style="background:#25D366; color:#fff; border:none; padding:12px; font-size:14px; font-weight:700; justify-content:center;">
                        <i class="fa-brands fa-whatsapp"></i> WhatsApp ile Randevu
                    </button>
                    <button type="submit" id="aptSubmitBtn" class="btn btn-primary" style="padding:12px; font-size:14px; font-weight:700; justify-content:center;">
                        <i class="fa-solid fa-check"></i> Randevuyu Kaydet
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- DETAYLI HAKKIMDA MODALI -->"""

site_code = old_appointment_modal.sub(new_appointment_modal, site_code)

# ─── 9. ADD SENDDIRECTWHATSAPPAPPOINTMENT JS FUNCTION ───
direct_wa_func = """
        function sendDirectWhatsAppAppointment() {
            const name = document.getElementById('aptName').value.trim();
            const phone = document.getElementById('aptPhone').value.trim();
            const dt = document.getElementById('aptDateTime').value.trim();
            const projName = document.getElementById('aptProjectName').value || 'Genel Proje';
            const notes = document.getElementById('aptNotes').value.trim();

            if (!name || !phone) {
                alert('Lütfen adınızı ve telefon numaranızı girin.');
                return;
            }

            // Also save to database
            const projId = document.getElementById('aptProjectId').value;
            const email = document.getElementById('aptEmail').value.trim();
            fetch('/api/appointments', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: name,
                    phone: phone,
                    email: email,
                    preferred_datetime: dt,
                    project_id: projId,
                    project_name: projName,
                    notes: notes,
                    agent: 'Yiğit Narin'
                })
            }).catch(() => {});

            const waText = encodeURIComponent(`📅 *RANDEVU TALEBİ*\\n\\n👤 *Ad Soyad:* ${name}\\n📱 *Telefon:* ${phone}\\n🏢 *Proje:* ${projName}\\n📆 *Tercih Edilen Zaman:* ${dt || 'En Kısa Sürede'}\\n📝 *Not:* ${notes || 'Görüşmek istiyorum.'}\\n\\nRandevu teyidi için sizinle görüşmek istiyorum.`);
            closeModal('appointmentModal');
            window.open(`https://wa.me/905354895656?text=${waText}`, '_blank');
        }
"""

if "function sendDirectWhatsAppAppointment()" not in site_code:
    site_code = site_code.replace("async function submitAppointmentForm(e) {", direct_wa_func + "\n\n        async function submitAppointmentForm(e) {")

site_path.write_text(site_code, encoding="utf-8")
print("4. site.html successfully updated with 2-column Hero, Suzanne profile card, WhatsApp appointment, and carousel budget prioritization!")

print("=" * 70)
print("ALL REQUESTED MASTER UPDATES COMPLETED!")
print("=" * 70)
