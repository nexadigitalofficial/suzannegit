import sys
import re
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

site_path = Path(r"C:\Users\USER\Desktop\3\site.html")
content = site_path.read_text(encoding="utf-8")

# Enhance renderProjectsCarousel Card Template
old_carousel_pattern = re.compile(r'// Render Projeler Carousel\s*function renderProjectsCarousel\(\) \{.*?function renderPortfolioCarousel', re.DOTALL)

new_carousel_code = """// Render Projeler Carousel
        function renderProjectsCarousel() {
            const track = document.getElementById('projects-track');
            if (!track) return;
            track.innerHTML = '';

            if (!projectsData || projectsData.length === 0) {
                track.innerHTML = '<div class="empty-state" style="width:100%"><i class="fa-solid fa-building-circle-xmark"></i><p>Gösterilecek proje bulunamadı.</p></div>';
                return;
            }

            projectsData.forEach(item => {
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

                    const videoBtn = item.has_video ? `<button class="btn btn-primary btn-sm" onclick="event.stopPropagation(); embedDriveVideoOnSiteCard('${item.id}')" style="font-size:12px; padding:6px 10px;"><i class="fa-solid fa-play"></i> Tanıtım</button>` : '';
                    const slideshowBtn = `<button class="btn btn-outline btn-sm" style="background:rgba(255,215,0,0.1); color:#D97706; border-color:rgba(255,215,0,0.35); font-size:12px; padding:6px 10px;" onclick="event.stopPropagation(); embedSlideshowOnSiteCard('${item.id}')"><i class="fa-solid fa-images"></i> Slayt</button>`;
                    const reportBtn = `<button class="btn btn-outline btn-sm" style="background:rgba(0,113,227,0.08); color:var(--accent); border-color:rgba(0,113,227,0.25); font-size:12px; padding:6px 10px;" onclick="event.stopPropagation(); openProjectReport('${item.id}')"><i class="fa-solid fa-brain"></i> Zeka Raporu</button>`;
                    const pdfBtn = `<button class="btn btn-outline btn-sm" style="font-size:12px; padding:6px 10px;" onclick="event.stopPropagation(); openPdfPreview('${item.id}')"><i class="fa-solid fa-file-pdf"></i> Sunum</button>`;

                    // Canonical WhatsApp template
                    const waMsg = `${safeName} hakkında bilgi almak istiyorum.\\n📍 ${loc}\\n💰 ${priceText || 'Fiyat Bilgisi'}\\nDetay: ${window.location.origin}/site#site-card-${item.id}`;
                    const waUrl = `https://wa.me/905354895656?text=${encodeURIComponent(waMsg)}`;

                    const html = `
                        <div class="card project-card" id="site-card-${item.id}" onclick="openProjectReport('${item.id}')" style="cursor:pointer; display:flex; flex-direction:column; min-width:340px; max-width:360px;">
                            <div class="card-img-wrapper" id="site-card-img-${item.id}" data-preview-id="${item.id}" style="height:210px; position:relative; overflow:hidden;">
                                <img src="${imgSrc}" alt="${safeName}" loading="lazy" class="project-card-img" onerror="this.src='/static/img/placeholder.jpg'">
                                <span class="badge sale" style="position:absolute; top:12px; left:12px; background:var(--accent); color:#fff; font-weight:700; font-size:11px; padding:4px 10px; border-radius:20px;">LANSMAN PROJESİ</span>
                                ${item.has_video ? `<div class="video-play-overlay" onclick="event.stopPropagation(); embedDriveVideoOnSiteCard('${item.id}')" title="Bulut Tanıtım Videosu Oynat"><i class="fa-solid fa-play"></i></div>` : ''}
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
        }

        function renderPortfolioCarousel"""

content = old_carousel_pattern.sub(new_carousel_code, content)

# Enhance applyFilters Grid Project Card Template
old_grid_card_pattern = re.compile(r'if\(itemObj\.type === \'project\'\) \{.*?grid\.insertAdjacentHTML\(\'beforeend\', cardHtml\);\s*\} else \{', re.DOTALL)

new_grid_card_code = """if(itemObj.type === 'project') {
                    const rooms = item.rooms || item.room_types || [];
                    const roomTags = (Array.isArray(rooms) ? rooms : []).map(r => `<span class="tag" style="background:rgba(0,113,227,0.08); color:var(--accent); padding:4px 10px; border-radius:12px; font-size:12px; font-weight:600;">${r}</span>`).join(' ');
                    const imgSrc = item.thumbnail || item.image || '/static/img/pdf_previews/pdf_cover_2.png';
                    const safeName = escapeHtml(item.title || item.name || 'Prestij Projesi');
                    const hasPrice = !!(item.price_display || item.price_min);
                    const priceText = item.price_display ? item.price_display : (item.price_min ? `${formatPrice(item.price_min)} - ${formatPrice(item.price_max)}` : '');
                    const downPayment = item.down_payment || (item.intelligence && item.intelligence.down_payment) || '';
                    const loc = item.location || (item.regionIlce ? item.regionIlce + (item.regionIl ? ', ' + item.regionIl : '') : (item.city || 'Ankara'));

                    const waMsg = `${safeName} hakkında bilgi almak istiyorum.\\n📍 ${loc}\\n💰 ${priceText || 'Fiyat Bilgisi'}\\nDetay: ${window.location.origin}/site#site-card-${item.id}`;
                    const waUrl = `https://wa.me/905354895656?text=${encodeURIComponent(waMsg)}`;

                    const videoBtn = item.has_video ? `<button class="btn btn-primary btn-sm" onclick="event.stopPropagation(); embedDriveVideoOnSiteCard('${item.id}')" style="font-size:12px; padding:6px 10px;"><i class="fa-solid fa-play"></i> Tanıtım</button>` : '';
                    const slideshowBtn = `<button class="btn btn-outline btn-sm" onclick="event.stopPropagation(); embedSlideshowOnSiteCard('${item.id}')" style="font-size:12px; padding:6px 10px; background:rgba(255,215,0,0.1); color:#D97706; border-color:rgba(255,215,0,0.3);"><i class="fa-solid fa-images"></i> Slayt</button>`;
                    const reportBtn = `<button class="btn btn-outline btn-sm" onclick="event.stopPropagation(); openProjectReport('${item.id}')" style="font-size:12px; padding:6px 10px; background:rgba(0,113,227,0.08); color:var(--accent);"><i class="fa-solid fa-brain"></i> Zeka Raporu</button>`;
                    const pdfBtn = `<button class="btn btn-outline btn-sm" onclick="event.stopPropagation(); openPdfPreview('${item.id}')" style="font-size:12px; padding:6px 10px;"><i class="fa-solid fa-file-pdf"></i> Sunum</button>`;

                    const cardHtml = `
                        <div class="card project-card" onclick="openProjectReport('${item.id}')" style="display:flex; flex-direction:column; background:#fff; border-radius:24px; overflow:hidden; border:1px solid rgba(0,0,0,0.06); box-shadow:0 4px 20px rgba(0,0,0,0.05); transition:all 0.3s ease;">
                            <div class="card-img-wrapper" style="position:relative; height:210px; overflow:hidden;" data-preview-id="${item.id}">
                                <img src="${imgSrc}" alt="${safeName}" loading="lazy" style="width:100%; height:100%; object-fit:cover;" onerror="this.src='/static/img/placeholder.jpg'">
                                <span class="badge sale" style="position:absolute; top:12px; left:12px; background:var(--accent); color:#fff; font-size:11px; font-weight:700; padding:4px 10px; border-radius:20px; letter-spacing:0.5px;">PROJE</span>
                                <span style="position:absolute; top:12px; right:12px; background:rgba(0,0,0,0.75); backdrop-filter:blur(8px); color:#FFD700; font-size:11px; font-weight:700; padding:4px 10px; border-radius:20px;"><i class="fa-solid fa-star"></i> AI Skoru: ${aiScore}</span>
                                ${item.has_video ? `<div class="video-play-overlay" onclick="event.stopPropagation(); openVideoModal('${item.id}')" title="Tanıtım Videosu" style="bottom:10px; right:10px; width:40px; height:40px;"><i class="fa-solid fa-play"></i></div>` : ''}
                            </div>
                            <div class="card-content" style="padding:1.25rem; display:flex; flex-direction:column; flex-grow:1;">
                                <h3 class="card-title" style="font-size:18px; font-weight:700; margin-bottom:4px; line-height:1.3;">${safeName}</h3>
                                <div style="font-size:12px; color:var(--text-secondary); margin-bottom:4px;"><i class="fa-solid fa-building"></i> ${item.developer || 'Coldwell Banker VIP'}</div>
                                <div style="font-size:13px; color:var(--text-secondary); margin-bottom:8px;"><i class="fa-solid fa-location-dot"></i> ${loc}</div>
                                ${item.ada_no ? `<div style="font-size:11px; color:var(--accent); font-weight:600; margin-bottom:8px;"><i class="fa-solid fa-stamp"></i> Ada ${item.ada_no} / Parsel ${item.parsel_no || ''} (TKGM Onaylı)</div>` : ''}
                                <div style="margin-bottom:12px;">${roomTags}</div>
                                <div style="margin-top:auto; padding-top:12px; border-top:1px solid rgba(0,0,0,0.06);">
                                    <span class="card-price-prominent">${priceText || 'Fiyat İçin Danışın'}</span>
                                    ${downPayment ? `<div class="card-price-down"><i class="fa-solid fa-credit-card"></i> Peşinat: ${downPayment}</div>` : ''}
                                    <div style="display:flex; flex-wrap:wrap; gap:6px; margin-bottom:10px;">
                                        ${videoBtn}
                                        ${slideshowBtn}
                                        ${reportBtn}
                                        ${pdfBtn}
                                    </div>
                                    <div style="width:100%; display:grid; grid-template-columns:1fr 1fr 42px; gap:6px;">
                                        <a href="${waUrl}" target="_blank" onclick="event.stopPropagation()" style="display:flex; align-items:center; justify-content:center; gap:6px; padding:8px 10px; border-radius:12px; background:rgba(37,211,102,0.12); color:#128C7E; font-size:12px; font-weight:700; text-decoration:none; border:1px solid rgba(37,211,102,0.35);"><i class="fa-brands fa-whatsapp"></i> WhatsApp</a>
                                        <button class="btn btn-primary btn-sm" onclick="event.stopPropagation(); openAppointmentModal('${item.id}', '${safeName}')" style="font-size:12px; font-weight:700; justify-content:center;"><i class="fa-solid fa-calendar-check"></i> Randevu</button>
                                        <button class="btn btn-outline btn-sm" onclick="event.stopPropagation(); shareProject('${item.id}', '${safeName}', '${priceText}', '${loc}')" title="Projeyi Paylaş" style="padding:0; justify-content:center;"><i class="fa-solid fa-share-nodes"></i></button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                    grid.insertAdjacentHTML('beforeend', cardHtml);
                } else {"""

content = old_grid_card_pattern.sub(new_grid_card_code, content)

site_path.write_text(content, encoding="utf-8")
print("Project card templates enhanced with prominent prices, appointment modal, and share actions!")
