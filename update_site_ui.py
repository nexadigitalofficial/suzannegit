import sys
import re
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

site_path = Path(r"C:\Users\USER\Desktop\3\site.html")
content = site_path.read_text(encoding="utf-8")

# 1. Update Title and Meta
content = content.replace(
    "<title>Suzanne Tenekecioğlu | Premium Gayrimenkul & Lüks Proje Danışmanı</title>",
    "<title>Coldwell Banker VIP | Prestijli Lansman Projeleri & Dijital Satış Operasyonu</title>"
)

# 2. Add New CSS Styles for Budget Bar, Prominent Prices, Appointment Modal, Share Toast
new_css = """
        /* Prominent Price & Budget Bar Styles */
        .quick-budget-bar {
            display: flex;
            align-items: center;
            justify-content: center;
            flex-wrap: wrap;
            gap: 12px;
            margin: 1.5rem auto 2rem;
            max-width: 960px;
        }
        .budget-btn {
            background: #FFFFFF;
            border: 1.5px solid rgba(0, 113, 227, 0.18);
            color: var(--text-primary);
            padding: 10px 20px;
            border-radius: 30px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.25s ease;
            box-shadow: 0 3px 12px rgba(0, 0, 0, 0.04);
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        .budget-btn:hover {
            border-color: var(--accent);
            color: var(--accent);
            transform: translateY(-2px);
            box-shadow: 0 6px 18px rgba(0, 113, 227, 0.15);
        }
        .budget-btn.active {
            background: var(--accent);
            color: #FFFFFF;
            border-color: var(--accent);
            box-shadow: 0 6px 20px rgba(0, 113, 227, 0.3);
        }
        .project-card-img {
            aspect-ratio: 16 / 9;
            width: 100%;
            height: 210px;
            object-fit: cover;
            object-position: center;
            transition: transform 0.4s ease;
        }
        .card-price-prominent {
            font-size: 22px;
            font-weight: 800;
            color: var(--accent);
            letter-spacing: -0.5px;
            display: block;
            margin-bottom: 4px;
        }
        .card-price-down {
            font-size: 12px;
            color: var(--text-secondary);
            font-weight: 600;
            margin-bottom: 8px;
        }
        .hero-banner-section {
            padding: 7.5rem 0 2rem;
            text-align: center;
            position: relative;
        }
        .hero-banner-inner {
            max-width: 860px;
            margin: 0 auto;
        }
        .hero-banner-title {
            font-size: 46px;
            font-weight: 700;
            letter-spacing: -1.2px;
            line-height: 1.2;
            color: var(--text-primary);
            margin-bottom: 1rem;
        }
        .hero-banner-subtitle {
            font-size: 18px;
            color: var(--text-secondary);
            font-weight: 400;
            line-height: 1.6;
            margin-bottom: 1.8rem;
        }
        .hero-banner-actions {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1rem;
            flex-wrap: wrap;
            margin-bottom: 1.5rem;
        }
        .about-compact-card {
            background: #FFFFFF;
            border-radius: var(--radius);
            padding: 3rem;
            box-shadow: var(--card-shadow);
            border: 1px solid var(--border);
            margin: 4rem auto 2rem;
        }
        @media (max-width: 768px) {
            .hero-banner-title { font-size: 30px; letter-spacing: -0.5px; }
            .hero-banner-subtitle { font-size: 15px; }
            .hero-banner-section { padding: 5.5rem 0 1.5rem; }
            .about-compact-card { padding: 1.5rem; }
            .quick-budget-bar { gap: 8px; }
            .budget-btn { font-size: 12px; padding: 8px 14px; }
        }
"""

if "/* Prominent Price & Budget Bar Styles */" not in content:
    content = content.replace("</style>", new_css + "\n    </style>")

# 3. Restructure HTML Sections: Hero Banner + Budget Bar -> Showcase -> Filter/Search -> About (Compact) -> Contact
old_hero_pattern = re.compile(r'<!-- Hero & Hakkımda Area \(Top Section\) -->.*?<!-- Showcase Section', re.DOTALL)

new_hero_showcase = """<!-- HERO SECTION (P0 High-Conversion Direct Showcase) -->
    <section class="hero-banner-section" id="hero">
        <div class="container">
            <div class="hero-banner-inner section-animate">
                <span class="section-badge" style="background:rgba(0,113,227,0.08); padding:6px 16px; border-radius:20px;"><i class="fa-solid fa-bolt"></i> DİJİTAL GAYRİMENKUL SATIŞ OPERASYONU</span>
                <h1 class="hero-banner-title">Prestijli Lansman Projeleri ve Seçkin Portföy</h1>
                <p class="hero-banner-subtitle">Yapay Zeka Destekli Bilişsel Değerleme, Bölge Fiyat Analizi ve Coldwell Banker VIP Güvencesiyle Doğrudan Yatırım Fırsatları.</p>
                
                <div class="hero-banner-actions">
                    <a href="#showcase" onclick="switchShowcaseTab('projects')" class="btn btn-primary" style="padding:14px 28px; font-size:16px; font-weight:700;">
                        <i class="fa-solid fa-building"></i> Projeleri Keşfet
                    </a>
                    <button onclick="toggleChatbot()" class="btn btn-outline" style="padding:14px 28px; font-size:16px; font-weight:700; background:rgba(94,92,230,0.08); color:#5E5CE6; border-color:rgba(94,92,230,0.3);">
                        <i class="fa-solid fa-brain"></i> Alya'ya Soru Sor
                    </button>
                    <a href="https://wa.me/905354895656?text=Merhaba,%20prestijli%20gayrimenkul%20projeleri%20hakk%C4%B1nda%20bilgi%20almak%20istiyorum." target="_blank" class="btn btn-outline" style="padding:14px 28px; font-size:16px; font-weight:700; background:rgba(37,211,102,0.1); color:#128C7E; border-color:rgba(37,211,102,0.3);">
                        <i class="fa-brands fa-whatsapp"></i> Danışman Hattı
                    </a>
                </div>

                <!-- Hızlı Bütçe Seçim Barı (Direct Quick Filters) -->
                <div class="quick-budget-bar" id="quickBudgetBar">
                    <button class="budget-btn active" data-min="0" data-max="999999999" onclick="setQuickBudget(0, 999999999, this)"><i class="fa-solid fa-layer-group"></i> Tüm Bütçeler</button>
                    <button class="budget-btn" data-min="0" data-max="3000000" onclick="setQuickBudget(0, 3000000, this)"><i class="fa-solid fa-tag"></i> 1 - 3 Milyon TL</button>
                    <button class="budget-btn" data-min="3000000" data-max="5000000" onclick="setQuickBudget(3000000, 5000000, this)"><i class="fa-solid fa-tag"></i> 3 - 5 Milyon TL</button>
                    <button class="budget-btn" data-min="5000000" data-max="10000000" onclick="setQuickBudget(5000000, 10000000, this)"><i class="fa-solid fa-gem"></i> 5 - 10 Milyon TL</button>
                    <button class="budget-btn" data-min="10000000" data-max="999999999" onclick="setQuickBudget(10000000, 999999999, this)"><i class="fa-solid fa-crown"></i> 10M TL+ Lüks</button>
                </div>
            </div>
        </div>
    </section>

    <!-- Showcase Section"""

content = old_hero_pattern.sub(new_hero_showcase, content)

# 4. Add Compact About Section & Why Us after Filter Section and before Contact
about_compact_html = """
    <!-- Hakkımda & Neden Biz Section (Moved Below Showcase) -->
    <section class="about-section container section-animate" id="about">
        <div class="about-compact-card">
            <div style="display:grid; grid-template-columns: minmax(280px, 340px) 1fr; gap:3rem; align-items:center;">
                <div style="text-align:center;">
                    <div class="hero-portrait-frame" style="max-width:280px; margin:0 auto 1.5rem; border-radius:24px; overflow:hidden; box-shadow:0 12px 36px rgba(0,0,0,0.12);">
                        <img src="/static/img/s1.png" alt="Suzanne Tenekecioğlu" style="width:100%; height:auto; display:block;" onerror="this.src='/static/img/suzanne_hero.jpeg'">
                    </div>
                    <span class="section-badge">GAYRİMENKUL DANIŞMANI</span>
                    <h3 style="font-size:24px; font-weight:700; margin-bottom:4px;">Suzanne Tenekecioğlu</h3>
                    <p style="font-size:14px; color:var(--text-secondary); margin-bottom:1.2rem;">Lüks Konut ve VIP Proje Danışmanı</p>
                    <button onclick="openAboutModal()" class="btn btn-outline" style="width:100%; justify-content:center; font-size:14px; font-weight:600;">
                        <i class="fa-solid fa-user"></i> Detaylı Özgeçmiş &amp; Vizyon
                    </button>
                </div>
                <div>
                    <span class="section-badge">GÜVEN VE DENEYİM</span>
                    <h2 class="section-title" style="font-size:32px; font-weight:700; margin-bottom:1rem;">Doğru Yatırım, Güvenilir Gelecek</h2>
                    <p class="about-paragraph" style="font-size:16px; line-height:1.7; color:var(--text-secondary); margin-bottom:1rem;">
                        Gayrimenkul sektörünün dinamik yapısını, hukuki süreçlerin güvenilirliğini ve müşteri memnuniyetini merkeze alan bir anlayışla yola çıktım. Yılların getirdiği mesleki birikim, analitik bakış açısı ve saha tecrübemle yanınızdayım.
                    </p>
                    <p class="about-paragraph" style="font-size:16px; line-height:1.7; color:var(--text-secondary); margin-bottom:1.8rem;">
                        Piyasa analizlerinden hedef kitle belirlemeye, doğru pazarlama stratejilerinden müzakere süreçlerine kadar her detayı titizlikle yöneterek, zamanınızı ve sermayenizi en verimli şekilde değerlendirmenizi sağlıyorum.
                    </p>
                    
                    <div class="why-me-grid" style="display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:1rem;">
                        <div style="background:rgba(0,0,0,0.02); padding:1rem; border-radius:14px; border:1px solid rgba(0,0,0,0.05); display:flex; gap:10px; align-items:flex-start;">
                            <i class="fa-solid fa-shield-halved" style="color:var(--accent); font-size:20px; margin-top:2px;"></i>
                            <div><strong style="font-size:14px; display:block;">Güven &amp; Şeffaflık</strong><span style="font-size:12px; color:var(--text-secondary);">Açık iletişim ve tam güven esası</span></div>
                        </div>
                        <div style="background:rgba(0,0,0,0.02); padding:1rem; border-radius:14px; border:1px solid rgba(0,0,0,0.05); display:flex; gap:10px; align-items:flex-start;">
                            <i class="fa-solid fa-chart-line" style="color:var(--accent); font-size:20px; margin-top:2px;"></i>
                            <div><strong style="font-size:14px; display:block;">Piyasa Hakimiyeti</strong><span style="font-size:12px; color:var(--text-secondary);">Bölgesel analiz ve doğru fiyat</span></div>
                        </div>
                        <div style="background:rgba(0,0,0,0.02); padding:1rem; border-radius:14px; border:1px solid rgba(0,0,0,0.05); display:flex; gap:10px; align-items:flex-start;">
                            <i class="fa-solid fa-user-check" style="color:var(--accent); font-size:20px; margin-top:2px;"></i>
                            <div><strong style="font-size:14px; display:block;">Kişiye Özel Çözüm</strong><span style="font-size:12px; color:var(--text-secondary);">Bütçeye ve hedefe tam uyum</span></div>
                        </div>
                        <div style="background:rgba(0,0,0,0.02); padding:1rem; border-radius:14px; border:1px solid rgba(0,0,0,0.05); display:flex; gap:10px; align-items:flex-start;">
                            <i class="fa-solid fa-bullseye" style="color:var(--accent); font-size:20px; margin-top:2px;"></i>
                            <div><strong style="font-size:14px; display:block;">Sonuç Odaklılık</strong><span style="font-size:12px; color:var(--text-secondary);">Hızlı ve etkin pazarlama ağı</span></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>
"""

if "<!-- Hakkımda & Neden Biz Section (Moved Below Showcase) -->" not in content:
    content = content.replace("<!-- Contact Section -->", about_compact_html + "\n\n    <!-- Contact Section -->")

# 5. Add Appointment Modal and About Full Modal
modals_html = """
    <!-- ONLINE RANDEVU MODALI -->
    <div class="modal-overlay" id="appointmentModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); backdrop-filter:blur(8px); z-index:999999 !important; pointer-events:auto !important; align-items:center; justify-content:center; padding:1.5rem;">
        <div class="modal-container" style="background:#fff; width:100%; max-width:560px; border-radius:24px; overflow:hidden; display:flex; flex-direction:column; box-shadow:0 25px 60px rgba(0,0,0,0.35);">
            <div style="display:flex; align-items:center; justify-content:space-between; padding:1.25rem 1.5rem; border-bottom:1px solid rgba(0,0,0,0.08); background:linear-gradient(135deg, rgba(0,113,227,0.06), rgba(94,92,230,0.06));">
                <h3 style="margin:0; font-size:18px; font-weight:700; color:var(--text-primary);"><i class="fa-solid fa-calendar-check" style="color:var(--accent);"></i> Proje Randevu Talebi</h3>
                <button onclick="closeModal('appointmentModal')" style="background:rgba(0,0,0,0.06); border:none; color:var(--text-primary); width:32px; height:32px; border-radius:50%; cursor:pointer; font-size:16px;"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <form id="appointmentForm" onsubmit="submitAppointmentForm(event)" style="padding:1.75rem; display:flex; flex-direction:column; gap:1rem;">
                <input type="hidden" id="aptProjectId" name="project_id" value="">
                <div>
                    <label style="font-size:13px; font-weight:600; color:var(--text-primary); display:block; margin-bottom:4px;">İlgilendiğiniz Proje</label>
                    <input type="text" id="aptProjectName" readonly style="width:100%; padding:10px 14px; border-radius:12px; border:1px solid rgba(0,0,0,0.12); background:#f5f5f7; font-size:14px; font-weight:600; color:var(--accent);">
                </div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:1rem;">
                    <div>
                        <label style="font-size:13px; font-weight:600; color:var(--text-primary); display:block; margin-bottom:4px;">Adınız Soyadınız *</label>
                        <input type="text" id="aptName" required placeholder="Ahmet Yılmaz" style="width:100%; padding:10px 14px; border-radius:12px; border:1px solid rgba(0,0,0,0.15); font-size:14px;">
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
                    <label style="font-size:13px; font-weight:600; color:var(--text-primary); display:block; margin-bottom:4px;">Özel Not / Sorunuz</label>
                    <textarea id="aptNotes" rows="2" placeholder="Ödeme planı veya yerinde sunum talebi..." style="width:100%; padding:10px 14px; border-radius:12px; border:1px solid rgba(0,0,0,0.15); font-size:14px; resize:none;"></textarea>
                </div>
                <div id="aptStatusMsg" style="display:none; font-size:13px; padding:10px; border-radius:10px; text-align:center;"></div>
                <button type="submit" id="aptSubmitBtn" class="btn btn-primary" style="width:100%; padding:12px; font-size:15px; font-weight:700; justify-content:center; margin-top:0.5rem;">
                    <i class="fa-solid fa-check"></i> Randevu Talebini Gönder
                </button>
            </form>
        </div>
    </div>

    <!-- DETAYLI HAKKIMDA MODALI -->
    <div class="modal-overlay" id="aboutModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); backdrop-filter:blur(8px); z-index:999999 !important; pointer-events:auto !important; align-items:center; justify-content:center; padding:1.5rem;">
        <div class="modal-container" style="background:#fff; width:100%; max-width:800px; max-height:85vh; border-radius:24px; overflow:hidden; display:flex; flex-direction:column; box-shadow:0 25px 60px rgba(0,0,0,0.35);">
            <div style="display:flex; align-items:center; justify-content:space-between; padding:1.25rem 1.5rem; border-bottom:1px solid rgba(0,0,0,0.08); background:#f8f9fa;">
                <h3 style="margin:0; font-size:18px; font-weight:700; color:var(--text-primary);">Suzanne Tenekecioğlu — Özgeçmiş &amp; Vizyon</h3>
                <button onclick="closeModal('aboutModal')" style="background:rgba(0,0,0,0.06); border:none; color:var(--text-primary); width:32px; height:32px; border-radius:50%; cursor:pointer; font-size:16px;"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div style="padding:2rem; overflow-y:auto; font-size:15px; line-height:1.8; color:var(--text-primary);">
                <p style="margin-bottom:1rem;"><strong>Coldwell Banker VIP Ekosistemi</strong> bünyesinde lüks konut, markalı lansman projeleri ve ticari gayrimenkul alanında yatırımcılara profesyonel danışmanlık hizmeti sunmaktayım.</p>
                <p style="margin-bottom:1rem;">Gayrimenkul sektörünün dinamik yapısını, hukuki süreçlerin güvenilirliğini ve müşteri memnuniyetini merkeze alan bir anlayışla hareket ediyorum. Yılların getirdiği mesleki birikim, analitik bakış açısı ve saha tecrübemle; mülkünüzü en doğru değerle pazarlamak veya hayalinizdeki yatırımı gerçeğe dönüştürmek için yanınızdayım.</p>
                <p style="margin-bottom:1.5rem;">Piyasa analizlerinden hedef kitle belirlemeye, doğru pazarlama stratejilerinden müzakere süreçlerine kadar her detayı titizlikle yöneterek zamanınızı ve sermayenizi en verimli şekilde değerlendirmenizi sağlıyorum.</p>
                <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:12px; margin-top:1rem;">
                    <img src="/static/img/s2.jpeg" alt="Suzanne Tenekecioğlu" style="width:100%; height:140px; object-fit:cover; border-radius:12px; cursor:pointer;" onclick="openImageModal(this.src)" onerror="this.src='/static/img/suzanne.jpg'">
                    <img src="/static/img/s3.jpeg" alt="Suzanne Tenekecioğlu" style="width:100%; height:140px; object-fit:cover; border-radius:12px; cursor:pointer;" onclick="openImageModal(this.src)" onerror="this.src='/static/img/suzanne.jpg'">
                    <img src="/static/img/s4.jpeg" alt="Suzanne Tenekecioğlu" style="width:100%; height:140px; object-fit:cover; border-radius:12px; cursor:pointer;" onclick="openImageModal(this.src)" onerror="this.src='/static/img/suzanne.jpg'">
                </div>
            </div>
        </div>
    </div>
"""

if "<!-- ONLINE RANDEVU MODALI -->" not in content:
    content = content.replace("<!-- VIDEO MODAL -->", modals_html + "\n\n    <!-- VIDEO MODAL -->")

# 6. Update AI Assistant Title & Floating Button
content = content.replace(
    '<span class="toggle-tip">Nexa AI Asistan\'a Sor</span>',
    '<span class="toggle-tip">Alya — Dijital Asistan\'a Sor</span>'
)
content = content.replace(
    '<h4>Nexa AI</h4>',
    '<h4>Alya</h4>'
)

# 7. Add Quick Budget, Appointment, Share and Agent Attribution JavaScript Helpers
js_helpers = """
        // ─── P0 QUICK BUDGET HELPER ───
        function setQuickBudget(min, max, btn) {
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

            applyFilters();
            
            // Scroll to projects if clicked
            const showcase = document.getElementById('showcase');
            if (showcase) {
                const top = showcase.getBoundingClientRect().top + window.scrollY - 80;
                window.scrollTo({ top: top, behavior: 'smooth' });
            }
        }

        // ─── ONLINE RANDEVU MODAL VE SUBMISSION ───
        function openAppointmentModal(projectId, projectName) {
            const modal = document.getElementById('appointmentModal');
            const idInput = document.getElementById('aptProjectId');
            const nameInput = document.getElementById('aptProjectName');
            const msgEl = document.getElementById('aptStatusMsg');
            if (idInput) idInput.value = projectId || '';
            if (nameInput) nameInput.value = projectName || 'Genel Portföy & VIP Proje';
            if (msgEl) msgEl.style.display = 'none';
            if (modal) {
                modal.style.display = 'flex';
                document.body.style.overflow = 'hidden';
            }
        }

        function openAboutModal() {
            const modal = document.getElementById('aboutModal');
            if (modal) {
                modal.style.display = 'flex';
                document.body.style.overflow = 'hidden';
            }
        }

        async function submitAppointmentForm(e) {
            e.preventDefault();
            const btn = document.getElementById('aptSubmitBtn');
            const msgEl = document.getElementById('aptStatusMsg');
            const name = document.getElementById('aptName').value.trim();
            const phone = document.getElementById('aptPhone').value.trim();
            const email = document.getElementById('aptEmail').value.trim();
            const dt = document.getElementById('aptDateTime').value.trim();
            const projId = document.getElementById('aptProjectId').value;
            const projName = document.getElementById('aptProjectName').value;
            const notes = document.getElementById('aptNotes').value.trim();

            if (!name || !phone) {
                alert('Lütfen adınızı ve telefon numaranızı girin.');
                return;
            }

            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Gönderiliyor...';

            // Check URL agent parameter
            const urlParams = new URLSearchParams(window.location.search);
            const agentParam = urlParams.get('agent') || 'Yiğit Narin';

            try {
                const res = await fetch('/api/appointments', {
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
                        agent: agentParam
                    })
                });
                const data = await res.json();
                if (data.success) {
                    msgEl.style.display = 'block';
                    msgEl.style.background = 'rgba(52, 199, 89, 0.15)';
                    msgEl.style.color = '#248A3D';
                    msgEl.innerHTML = '<strong>✓ Talebiniz Alındı!</strong> Danışmanımız en kısa sürede sizinle iletişime geçecektir.';
                    
                    const waText = encodeURIComponent(`Merhaba, ${projName} projesi için randevu talebi oluşturdum.\\nAdım: ${name}\\nTelefonum: ${phone}\\nTercih: ${dt}`);
                    setTimeout(() => {
                        closeModal('appointmentModal');
                        btn.disabled = false;
                        btn.innerHTML = '<i class="fa-solid fa-check"></i> Randevu Talebini Gönder';
                        window.open(`https://wa.me/905354895656?text=${waText}`, '_blank');
                    }, 1800);
                } else {
                    msgEl.style.display = 'block';
                    msgEl.style.background = 'rgba(255, 59, 48, 0.15)';
                    msgEl.style.color = '#D70015';
                    msgEl.innerText = data.message || 'Kayıt sırasında bir hata oluştu.';
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fa-solid fa-check"></i> Randevu Talebini Gönder';
                }
            } catch (err) {
                msgEl.style.display = 'block';
                msgEl.style.background = 'rgba(255, 59, 48, 0.15)';
                msgEl.style.color = '#D70015';
                msgEl.innerText = 'Bağlantı hatası oluştu.';
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-check"></i> Randevu Talebini Gönder';
            }
        }

        // ─── PROJE PAYLAŞMA HELPER ───
        function shareProject(id, name, price, loc) {
            const url = `${window.location.origin}/site#site-card-${id}`;
            const text = `${name}\\n📍 ${loc}\\n💰 ${price}\\nDetaylar: ${url}`;
            if (navigator.share) {
                navigator.share({ title: name, text: text, url: url }).catch(() => {});
            } else {
                navigator.clipboard.writeText(text).then(() => {
                    alert('Proje bağlantısı panoya kopyalandı!');
                }).catch(() => {
                    prompt('Proje linkini kopyalayabilirsiniz:', url);
                });
            }
        }
"""

if "// ─── P0 QUICK BUDGET HELPER ───" not in content:
    content = content.replace("async function fetchProjects() {", js_helpers + "\n\n        async function fetchProjects() {")

# Write updated content
site_path.write_text(content, encoding="utf-8")
print("site.html successfully transformed into high-conversion digital sales operational system!")
