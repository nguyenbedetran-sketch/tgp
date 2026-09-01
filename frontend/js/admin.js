/**
 * Admin dashboard: login, section navigation, CRUD for every resource,
 * dashboard stats, CSV export. Talks only to the real backend API
 * (app/routes/*.py) - nothing here is mocked.
 */

// ---------------------------------------------------------------------
// Auth / view switching
// ---------------------------------------------------------------------
async function checkAuthAndBoot() {
  if (!TGP_API.isLoggedIn()) { showLoginView(); return; }
  try {
    const res = await TGP_API.get('/api/auth/me');
    document.getElementById('current-user-name').textContent = res.data.user.username || res.data.user.full_name || '';
    showAdminView();
    initSectionNav();
    loadSection('dashboard');
  } catch (e) {
    TGP_API.setToken(null);
    showLoginView();
  }
}

function showLoginView() {
  document.getElementById('login-view').style.display = 'flex';
  document.getElementById('admin-view').style.display = 'none';
}

function showAdminView() {
  document.getElementById('login-view').style.display = 'none';
  document.getElementById('admin-view').style.display = 'flex';
}

document.getElementById('login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const payload = Object.fromEntries(fd.entries());
  const errBox = document.getElementById('login-error');
  const btn = document.getElementById('login-submit');
  errBox.textContent = '';
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Đang đăng nhập...';
  try {
    const res = await TGP_API.post('/api/auth/login', payload, { auth: false });
    TGP_API.setToken(res.data.token);
    checkAuthAndBoot();
  } catch (err) {
    errBox.textContent = err.error || 'Đăng nhập thất bại';
  } finally {
    btn.disabled = false;
    btn.textContent = 'Đăng nhập';
  }
});

document.getElementById('logout-btn').addEventListener('click', async () => {
  try { await TGP_API.post('/api/auth/logout', {}); } catch (e) {}
  TGP_API.setToken(null);
  showLoginView();
});

// ---------------------------------------------------------------------
// Section navigation
// ---------------------------------------------------------------------
const SECTION_TITLES = {
  dashboard: 'Tổng quan', hero: 'Slide trang chủ', strengths: 'Điểm mạnh',
  projects: 'Dự án', services: 'Dịch vụ', blog: 'Bài viết',
  contacts: 'Yêu cầu tư vấn', team: 'Đội ngũ', testimonials: 'Đánh giá khách hàng',
  settings: 'Thông tin công ty',
};

function initSectionNav() {
  document.querySelectorAll('[data-section]').forEach(el => {
    el.addEventListener('click', (e) => {
      e.preventDefault();
      loadSection(el.getAttribute('data-section'));
    });
  });
}

function loadSection(name) {
  document.querySelectorAll('.admin-nav-item[data-section]').forEach(el => {
    el.classList.toggle('active', el.getAttribute('data-section') === name);
  });
  document.querySelectorAll('[data-panel]').forEach(el => {
    el.style.display = el.getAttribute('data-panel') === name ? 'block' : 'none';
  });
  document.getElementById('section-title').textContent = SECTION_TITLES[name] || '';

  const loaders = {
    dashboard: loadDashboard, hero: loadHeroSlidesAdmin, strengths: loadStrengthsAdmin,
    projects: loadProjectsAdmin, services: loadServicesAdmin,
    blog: loadBlogAdmin, contacts: loadContactsAdmin, team: loadTeamAdmin,
    testimonials: loadTestimonialsAdmin, settings: loadSettingsAdmin,
  };
  loaders[name] && loaders[name]();
}

// ---------------------------------------------------------------------
// Dashboard
// ---------------------------------------------------------------------
async function loadDashboard() {
  try {
    const res = await TGP_API.get('/api/admin/dashboard');
    const d = res.data;
    const cards = [
      ['Tổng số dự án', d.total_projects, `${d.published_projects} đã xuất bản`],
      ['Tổng yêu cầu tư vấn', d.total_contacts, `${d.new_contacts} yêu cầu mới`],
      ['Yêu cầu tháng này', d.contacts_this_month, ''],
      ['Bài viết', d.total_blog_posts, ''],
      ['Lượt sử dụng công cụ ước tính', d.total_estimates, ''],
      ['Lượt truy cập', d.total_page_views, `${d.page_views_this_month} trong tháng này`],
    ];
    document.getElementById('dashboard-stats').innerHTML = cards.map(([label, value, sub]) => `
      <div class="stat-card"><div class="label">${label}</div><div class="value">${value}</div>${sub ? `<div class="sub">${sub}</div>` : ''}</div>`).join('');

    document.getElementById('recent-contacts-body').innerHTML = (d.recent_contacts || []).map(c => `
      <tr><td>${tgpEscapeHtml(c.full_name)}</td><td>${phoneLink(c.phone)}</td>
      <td>${tgpEscapeHtml(TGP_CATEGORY_LABELS[c.construction_type] || c.construction_type || '—')}</td>
      <td><span class="badge badge-${c.status}">${statusLabel(c.status)}</span></td>
      <td>${tgpFormatDate(c.created_at)}</td></tr>`).join('') ||
      '<tr><td colspan="5" class="table-empty">Chưa có yêu cầu tư vấn nào</td></tr>';
    initSectionNav();
  } catch (e) {
    tgpToast('Không thể tải dữ liệu tổng quan', 'error');
  }
}

function phoneLink(phone) {
  if (!phone) return '—';
  return `<a href="tel:${tgpEscapeHtml(phone.replace(/\s+/g, ''))}">${tgpEscapeHtml(phone)}</a>`;
}

function statusLabel(s) {
  return { new: 'Mới', contacted: 'Đã liên hệ', closed: 'Đã đóng' }[s] || s;
}

// ---------------------------------------------------------------------
// Generic modal helpers
// ---------------------------------------------------------------------
function openModal(title, fieldsHtml, onSubmit) {
  document.getElementById('modal-title').textContent = title;
  const form = document.getElementById('modal-form');
  form.innerHTML = fieldsHtml + '<div class="form-field full" style="margin-top:16px"><button type="submit" class="btn btn-primary btn-block">Lưu</button></div>';
  bindImageFields(form);
  form.onsubmit = async (e) => {
    e.preventDefault();
    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    try {
      await onSubmit(new FormData(form));
      closeModal();
    } catch (err) {
      tgpToast(err.error || 'Có lỗi xảy ra', 'error');
    } finally {
      submitBtn.disabled = false;
    }
  };
  document.getElementById('modal-overlay').classList.add('open');
}

function closeModal() {
  document.getElementById('modal-overlay').classList.remove('open');
}
document.getElementById('modal-overlay').addEventListener('click', (e) => {
  if (e.target.id === 'modal-overlay') closeModal();
});

function field(label, name, value = '', type = 'text', extra = '') {
  return `<div class="form-field"><label>${label}</label><input type="${type}" name="${name}" value="${tgpEscapeHtml(value)}" ${extra}></div>`;
}
function fieldFull(label, name, value = '', tag = 'input', extra = '') {
  if (tag === 'textarea') return `<div class="form-field full"><label>${label}</label><textarea name="${name}" rows="4" ${extra}>${tgpEscapeHtml(value)}</textarea></div>`;
  return `<div class="form-field full"><label>${label}</label><input name="${name}" value="${tgpEscapeHtml(value)}" ${extra}></div>`;
}
function selectField(label, name, options, selected = '', full = false) {
  const opts = options.map(([val, text]) => `<option value="${val}" ${val === selected ? 'selected' : ''}>${text}</option>`).join('');
  return `<div class="form-field ${full ? 'full' : ''}"><label>${label}</label><select name="${name}">${opts}</select></div>`;
}

// Image field: preview + "Chon anh" upload button instead of a raw URL box.
// The uploaded file is sent straight to POST /api/admin/upload; the URL that
// comes back is what actually gets submitted, via the hidden input `name`.
function imageField(label, name, value = '') {
  return `
    <div class="form-field full">
      <label>${label}</label>
      <div class="image-field" data-image-field>
        <div class="image-field-preview">${value ? `<img src="${tgpEscapeHtml(value)}" alt="">` : '<span>Chưa có ảnh</span>'}</div>
        <label class="btn btn-outline-dark btn-sm image-field-upload">
          <span>${value ? 'Đổi ảnh' : 'Chọn ảnh'}</span>
          <input type="file" accept="image/*" hidden>
        </label>
        <input type="hidden" name="${name}" value="${tgpEscapeHtml(value)}">
      </div>
    </div>`;
}

function bindImageFields(container) {
  container.querySelectorAll('[data-image-field]').forEach(wrap => {
    const fileInput = wrap.querySelector('input[type="file"]');
    const hiddenInput = wrap.querySelector('input[type="hidden"]');
    const preview = wrap.querySelector('.image-field-preview');
    const label = wrap.querySelector('.image-field-upload span');
    fileInput.addEventListener('change', async () => {
      const file = fileInput.files[0];
      if (!file) return;
      const originalLabel = label.textContent;
      label.textContent = 'Đang tải lên...';
      try {
        const fd = new FormData();
        fd.append('file', file);
        const res = await TGP_API.post('/api/admin/upload', fd);
        hiddenInput.value = res.data.url;
        preview.innerHTML = `<img src="${res.data.url}" alt="">`;
        label.textContent = 'Đổi ảnh';
      } catch (err) {
        tgpToast(err.error || 'Tải ảnh lên thất bại', 'error');
        label.textContent = originalLabel;
      } finally {
        fileInput.value = '';
      }
    });
  });
}

// ---------------------------------------------------------------------
// Hero slides (trang chủ)
// ---------------------------------------------------------------------
async function loadHeroSlidesAdmin() {
  try {
    const res = await TGP_API.get('/api/hero-slides');
    const rows = res.data || [];
    document.getElementById('hero-slides-body').innerHTML = rows.map(s => `
      <tr>
        <td>${s.image_url ? `<img src="${tgpEscapeHtml(s.image_url)}" alt="" style="width:64px;height:44px;object-fit:cover;border-radius:6px">` : '—'}</td>
        <td>${tgpEscapeHtml(s.title_line1)}${s.title_line2 ? ' ' + tgpEscapeHtml(s.title_line2) : ''}</td>
        <td>${s.sort_order}</td>
        <td class="table-actions">
          <button class="icon-btn" onclick='openHeroSlideModal(${JSON.stringify(s).replace(/'/g, "&apos;")})'>Sửa</button>
          <button class="icon-btn danger" onclick="deleteHeroSlide(${s.id})">Xóa</button>
        </td>
      </tr>`).join('') || '<tr><td colspan="4" class="table-empty">Chưa có slide nào. Nhấn "+ Thêm slide" để tạo mới.</td></tr>';
  } catch (e) { tgpToast('Không thể tải danh sách slide', 'error'); }
}

function openHeroSlideModal(s) {
  s = s || {};
  const html = `
    ${imageField('Ảnh nền slide', 'image_url', s.image_url)}
    ${field('Dòng nhỏ phía trên (eyebrow)', 'eyebrow', s.eyebrow)}
    ${field('Tiêu đề dòng 1', 'title_line1', s.title_line1)}
    ${field('Tiêu đề dòng 2 (màu nhấn - để trống nếu không cần)', 'title_line2', s.title_line2)}
    ${fieldFull('Mô tả ngắn', 'subtitle', s.subtitle, 'textarea')}
    ${field('Nút 1 - chữ trên nút', 'button1_text', s.button1_text)}
    ${field('Nút 1 - liên kết đến', 'button1_link', s.button1_link)}
    ${field('Nút 2 - chữ trên nút', 'button2_text', s.button2_text)}
    ${field('Nút 2 - liên kết đến', 'button2_link', s.button2_link)}
    ${field('Thứ tự hiển thị (số nhỏ hơn hiện trước)', 'sort_order', s.sort_order ?? 0, 'number')}
  `;
  openModal(s.id ? 'Chỉnh sửa slide' : 'Thêm slide mới', html, async (fd) => {
    const payload = Object.fromEntries(fd.entries());
    if (s.id) await TGP_API.put(`/api/hero-slides/${s.id}`, payload);
    else await TGP_API.post('/api/hero-slides', payload);
    tgpToast('Đã lưu slide thành công');
    loadHeroSlidesAdmin();
  });
}

async function deleteHeroSlide(id) {
  if (!confirm('Xóa slide này?')) return;
  try { await TGP_API.del(`/api/hero-slides/${id}`); tgpToast('Đã xóa slide'); loadHeroSlidesAdmin(); }
  catch (e) { tgpToast(e.error || 'Không thể xóa', 'error'); }
}

// ---------------------------------------------------------------------
// Strengths ("Vi sao chon chung toi" - trang chủ)
// ---------------------------------------------------------------------
async function loadStrengthsAdmin() {
  try {
    const res = await TGP_API.get('/api/strengths');
    const rows = res.data || [];
    document.getElementById('strengths-body').innerHTML = rows.map(s => `
      <tr>
        <td>${s.image_url ? `<img src="${tgpEscapeHtml(s.image_url)}" alt="" style="width:56px;height:42px;object-fit:cover;border-radius:6px">` : '—'}</td>
        <td>${tgpEscapeHtml(s.title)}</td>
        <td>${tgpEscapeHtml((s.description || '').slice(0, 60))}</td>
        <td>${s.sort_order}</td>
        <td class="table-actions">
          <button class="icon-btn" onclick='openStrengthModal(${JSON.stringify(s).replace(/'/g, "&apos;")})'>Sửa</button>
          <button class="icon-btn danger" onclick="deleteStrength(${s.id})">Xóa</button>
        </td>
      </tr>`).join('') || '<tr><td colspan="5" class="table-empty">Chưa có điểm mạnh nào</td></tr>';
  } catch (e) { tgpToast('Không thể tải danh sách', 'error'); }
}

function openStrengthModal(s) {
  s = s || {};
  const html = `
    ${imageField('Ảnh minh hoạ', 'image_url', s.image_url)}
    ${field('Tiêu đề', 'title', s.title)}
    ${fieldFull('Mô tả', 'description', s.description, 'textarea')}
    ${field('Thứ tự hiển thị (số nhỏ hơn hiện trước)', 'sort_order', s.sort_order ?? 0, 'number')}
  `;
  openModal(s.id ? 'Chỉnh sửa điểm mạnh' : 'Thêm điểm mạnh mới', html, async (fd) => {
    const payload = Object.fromEntries(fd.entries());
    if (s.id) await TGP_API.put(`/api/strengths/${s.id}`, payload);
    else await TGP_API.post('/api/strengths', payload);
    tgpToast('Đã lưu thành công');
    loadStrengthsAdmin();
  });
}

async function deleteStrength(id) {
  if (!confirm('Xóa điểm mạnh này?')) return;
  try { await TGP_API.del(`/api/strengths/${id}`); tgpToast('Đã xóa'); loadStrengthsAdmin(); }
  catch (e) { tgpToast(e.error || 'Không thể xóa', 'error'); }
}

// ---------------------------------------------------------------------
// Projects
// ---------------------------------------------------------------------
async function loadProjectsAdmin() {
  try {
    const res = await TGP_API.get('/api/projects?status=all');
    const rows = res.data || [];
    document.getElementById('projects-body').innerHTML = rows.map(p => `
      <tr>
        <td>${tgpEscapeHtml(p.title)}</td>
        <td>${tgpEscapeHtml(TGP_CATEGORY_LABELS[p.category] || p.category)}</td>
        <td>${tgpEscapeHtml(p.location || '—')}</td>
        <td><span class="badge badge-${p.status}">${p.status === 'published' ? 'Đã đăng' : 'Nháp'}</span></td>
        <td class="table-actions">
          <button class="icon-btn" onclick='openProjectModal(${JSON.stringify(p).replace(/'/g, "&apos;")})'>Sửa</button>
          <button class="icon-btn danger" onclick="deleteProject(${p.id})">Xóa</button>
        </td>
      </tr>`).join('') || '<tr><td colspan="5" class="table-empty">Chưa có dự án nào. Nhấn "+ Thêm dự án" để tạo mới.</td></tr>';
  } catch (e) { tgpToast('Không thể tải danh sách dự án', 'error'); }
}

function openProjectModal(p) {
  p = p || {};
  const html = `
    ${fieldFull('Tên dự án', 'title', p.title)}
    ${selectField('Loại công trình', 'category', Object.entries(TGP_CATEGORY_LABELS), p.category)}
    ${field('Địa điểm', 'location', p.location)}
    ${field('Diện tích (m²)', 'area_m2', p.area_m2 ?? '', 'number')}
    ${field('Năm thực hiện', 'year', p.year ?? '', 'number')}
    ${field('Chi phí hiển thị', 'cost_display', p.cost_display)}
    ${selectField('Trạng thái', 'status', [['draft', 'Nháp'], ['published', 'Đã đăng']], p.status || 'draft')}
    ${imageField('Ảnh bìa', 'cover_image', p.cover_image)}
    ${fieldFull('Tóm tắt', 'summary', p.summary, 'textarea')}
    ${fieldFull('Ý tưởng thiết kế', 'concept', p.concept, 'textarea')}
    ${fieldFull('Ghi chú thiết kế / tiến độ', 'design_notes', p.design_notes, 'textarea')}
  `;
  openModal(p.id ? 'Chỉnh sửa dự án' : 'Thêm dự án mới', html, async (fd) => {
    const payload = Object.fromEntries(fd.entries());
    if (p.id) await TGP_API.put(`/api/projects/${p.id}`, payload);
    else await TGP_API.post('/api/projects', payload);
    tgpToast('Đã lưu dự án thành công');
    loadProjectsAdmin();
  });
}

async function deleteProject(id) {
  if (!confirm('Xóa dự án này?')) return;
  try { await TGP_API.del(`/api/projects/${id}`); tgpToast('Đã xóa dự án'); loadProjectsAdmin(); }
  catch (e) { tgpToast(e.error || 'Không thể xóa', 'error'); }
}

// ---------------------------------------------------------------------
// Services
// ---------------------------------------------------------------------
async function loadServicesAdmin() {
  try {
    const res = await TGP_API.get('/api/services');
    const rows = res.data || [];
    document.getElementById('services-body').innerHTML = rows.map(s => `
      <tr><td>${tgpEscapeHtml(s.code)}</td><td>${tgpEscapeHtml(s.title)}</td><td>${tgpEscapeHtml((s.short_description || '').slice(0, 60))}</td>
      <td class="table-actions">
        <button class="icon-btn" onclick='openServiceModal(${JSON.stringify(s).replace(/'/g, "&apos;")})'>Sửa</button>
        <button class="icon-btn danger" onclick="deleteService(${s.id})">Xóa</button>
      </td></tr>`).join('') || '<tr><td colspan="4" class="table-empty">Chưa có dịch vụ nào</td></tr>';
  } catch (e) { tgpToast('Không thể tải danh sách dịch vụ', 'error'); }
}

function openServiceModal(s) {
  s = s || {};
  const html = `
    ${fieldFull('Tên dịch vụ', 'title', s.title)}
    ${field('Số thứ tự hiển thị (VD: 01)', 'icon', s.icon)}
    ${fieldFull('Mô tả ngắn', 'short_description', s.short_description, 'textarea')}
    ${fieldFull('Mô tả chi tiết', 'description', s.description, 'textarea')}
  `;
  openModal(s.id ? 'Chỉnh sửa dịch vụ' : 'Thêm dịch vụ mới', html, async (fd) => {
    const payload = Object.fromEntries(fd.entries());
    if (s.id) await TGP_API.put(`/api/services/${s.id}`, payload);
    else await TGP_API.post('/api/services', payload);
    tgpToast('Đã lưu dịch vụ thành công');
    loadServicesAdmin();
  });
}

async function deleteService(id) {
  if (!confirm('Xóa dịch vụ này?')) return;
  try { await TGP_API.del(`/api/services/${id}`); tgpToast('Đã xóa dịch vụ'); loadServicesAdmin(); }
  catch (e) { tgpToast(e.error || 'Không thể xóa', 'error'); }
}

// ---------------------------------------------------------------------
// Blog
// ---------------------------------------------------------------------
async function loadBlogAdmin() {
  try {
    const res = await TGP_API.get('/api/blog?status=all');
    const rows = res.data || [];
    document.getElementById('blog-body').innerHTML = rows.map(p => `
      <tr><td>${tgpEscapeHtml(p.title)}</td><td>${tgpEscapeHtml(p.category || '—')}</td>
      <td><span class="badge badge-${p.status}">${p.status === 'published' ? 'Đã đăng' : 'Nháp'}</span></td>
      <td>${tgpFormatDate(p.published_at || p.created_at)}</td>
      <td class="table-actions">
        <button class="icon-btn" onclick="editBlogPost(${p.id})">Sửa</button>
        <button class="icon-btn danger" onclick="deleteBlogPost(${p.id})">Xóa</button>
      </td></tr>`).join('') || '<tr><td colspan="5" class="table-empty">Chưa có bài viết nào</td></tr>';
  } catch (e) { tgpToast('Không thể tải danh sách bài viết', 'error'); }
}

async function editBlogPost(id) {
  const res = await TGP_API.get(`/api/blog/${id}`);
  openBlogModal(res.data);
}

function openBlogModal(p) {
  p = p || {};
  const html = `
    ${fieldFull('Tiêu đề', 'title', p.title)}
    ${field('Chuyên mục', 'category', p.category)}
    ${field('Tác giả', 'author', p.author)}
    ${selectField('Trạng thái', 'status', [['draft', 'Nháp'], ['published', 'Đã đăng']], p.status || 'draft')}
    ${imageField('Ảnh thumbnail', 'thumbnail_url', p.thumbnail_url)}
    ${fieldFull('Tóm tắt', 'excerpt', p.excerpt, 'textarea')}
    ${fieldFull('Nội dung', 'content', p.content, 'textarea', 'rows="8" required')}
  `;
  openModal(p.id ? 'Chỉnh sửa bài viết' : 'Viết bài mới', html, async (fd) => {
    const payload = Object.fromEntries(fd.entries());
    if (p.id) await TGP_API.put(`/api/blog/${p.id}`, payload);
    else await TGP_API.post('/api/blog', payload);
    tgpToast('Đã lưu bài viết thành công');
    loadBlogAdmin();
  });
}

async function deleteBlogPost(id) {
  if (!confirm('Xóa bài viết này?')) return;
  try { await TGP_API.del(`/api/blog/${id}`); tgpToast('Đã xóa bài viết'); loadBlogAdmin(); }
  catch (e) { tgpToast(e.error || 'Không thể xóa', 'error'); }
}

// ---------------------------------------------------------------------
// Contacts
// ---------------------------------------------------------------------
async function loadContactsAdmin() {
  const statusFilter = document.getElementById('contact-status-filter').value;
  try {
    const res = await TGP_API.get(`/api/admin/contacts${statusFilter !== 'all' ? '?status=' + statusFilter : ''}`);
    const rows = res.data || [];
    document.getElementById('contacts-body').innerHTML = rows.map(c => `
      <tr>
        <td>${tgpEscapeHtml(c.full_name)}</td><td>${phoneLink(c.phone)}</td><td>${tgpEscapeHtml(c.email || '—')}</td>
        <td>${tgpEscapeHtml(TGP_CATEGORY_LABELS[c.construction_type] || c.construction_type || '—')}</td>
        <td>
          <select onchange="updateContactStatus(${c.id}, this.value)" style="padding:6px 10px;border-radius:6px;border:1px solid var(--border-soft)">
            <option value="new" ${c.status === 'new' ? 'selected' : ''}>Mới</option>
            <option value="contacted" ${c.status === 'contacted' ? 'selected' : ''}>Đã liên hệ</option>
            <option value="closed" ${c.status === 'closed' ? 'selected' : ''}>Đã đóng</option>
          </select>
        </td>
        <td>${tgpFormatDate(c.created_at)}</td>
        <td class="table-actions"><button class="icon-btn danger" onclick="deleteContact(${c.id})">Xóa</button></td>
      </tr>`).join('') || '<tr><td colspan="7" class="table-empty">Chưa có yêu cầu tư vấn nào</td></tr>';
  } catch (e) { tgpToast('Không thể tải danh sách yêu cầu tư vấn', 'error'); }
}
document.getElementById('contact-status-filter').addEventListener('change', loadContactsAdmin);

async function updateContactStatus(id, status) {
  try { await TGP_API.put(`/api/admin/contacts/${id}`, { status }); tgpToast('Đã cập nhật trạng thái'); }
  catch (e) { tgpToast(e.error || 'Không thể cập nhật', 'error'); }
}

async function deleteContact(id) {
  if (!confirm('Xóa yêu cầu tư vấn này?')) return;
  try { await TGP_API.del(`/api/admin/contacts/${id}`); tgpToast('Đã xóa'); loadContactsAdmin(); }
  catch (e) { tgpToast(e.error || 'Không thể xóa', 'error'); }
}

// ---------------------------------------------------------------------
// Team
// ---------------------------------------------------------------------
async function loadTeamAdmin() {
  try {
    const res = await TGP_API.get('/api/team');
    const rows = res.data || [];
    document.getElementById('team-body').innerHTML = rows.map(m => `
      <tr><td>${tgpEscapeHtml(m.full_name)}</td><td>${tgpEscapeHtml(m.position)}</td><td>${tgpEscapeHtml(m.specialty || '—')}</td>
      <td class="table-actions">
        <button class="icon-btn" onclick='openTeamModal(${JSON.stringify(m).replace(/'/g, "&apos;")})'>Sửa</button>
        <button class="icon-btn danger" onclick="deleteTeamMember(${m.id})">Xóa</button>
      </td></tr>`).join('') || '<tr><td colspan="4" class="table-empty">Chưa có thành viên nào</td></tr>';
  } catch (e) { tgpToast('Không thể tải đội ngũ', 'error'); }
}

function openTeamModal(m) {
  m = m || {};
  const html = `
    ${field('Họ tên', 'full_name', m.full_name)}
    ${field('Chức vụ', 'position', m.position)}
    ${fieldFull('Chuyên môn', 'specialty', m.specialty)}
    ${imageField('Ảnh đại diện', 'photo_url', m.photo_url)}
  `;
  openModal(m.id ? 'Chỉnh sửa thành viên' : 'Thêm thành viên', html, async (fd) => {
    const payload = Object.fromEntries(fd.entries());
    if (m.id) await TGP_API.put(`/api/team/${m.id}`, payload);
    else await TGP_API.post('/api/team', payload);
    tgpToast('Đã lưu thông tin thành viên');
    loadTeamAdmin();
  });
}

async function deleteTeamMember(id) {
  if (!confirm('Xóa thành viên này?')) return;
  try { await TGP_API.del(`/api/team/${id}`); tgpToast('Đã xóa'); loadTeamAdmin(); }
  catch (e) { tgpToast(e.error || 'Không thể xóa', 'error'); }
}

// ---------------------------------------------------------------------
// Testimonials
// ---------------------------------------------------------------------
async function loadTestimonialsAdmin() {
  try {
    const res = await TGP_API.get('/api/testimonials');
    const rows = res.data || [];
    document.getElementById('testimonials-body').innerHTML = rows.map(t => `
      <tr><td>${tgpEscapeHtml(t.customer_name)}</td><td>${tgpEscapeHtml(t.project_name || '—')}</td>
      <td>${'★'.repeat(t.rating)}${'☆'.repeat(5 - t.rating)}</td>
      <td>${tgpEscapeHtml((t.content || '').slice(0, 50))}...</td>
      <td class="table-actions">
        <button class="icon-btn" onclick='openTestimonialModal(${JSON.stringify(t).replace(/'/g, "&apos;")})'>Sửa</button>
        <button class="icon-btn danger" onclick="deleteTestimonial(${t.id})">Xóa</button>
      </td></tr>`).join('') || '<tr><td colspan="5" class="table-empty">Chưa có đánh giá nào</td></tr>';
  } catch (e) { tgpToast('Không thể tải đánh giá', 'error'); }
}

function openTestimonialModal(t) {
  t = t || {};
  const html = `
    ${field('Tên khách hàng', 'customer_name', t.customer_name)}
    ${field('Tên dự án', 'project_name', t.project_name)}
    ${selectField('Đánh giá (sao)', 'rating', [['5','5 sao'],['4','4 sao'],['3','3 sao'],['2','2 sao'],['1','1 sao']], String(t.rating || 5))}
    ${imageField('Ảnh đại diện', 'avatar_url', t.avatar_url)}
    ${fieldFull('Nội dung đánh giá', 'content', t.content, 'textarea')}
  `;
  openModal(t.id ? 'Chỉnh sửa đánh giá' : 'Thêm đánh giá', html, async (fd) => {
    const payload = Object.fromEntries(fd.entries());
    if (t.id) await TGP_API.put(`/api/testimonials/${t.id}`, payload);
    else await TGP_API.post('/api/testimonials', payload);
    tgpToast('Đã lưu đánh giá');
    loadTestimonialsAdmin();
  });
}

async function deleteTestimonial(id) {
  if (!confirm('Xóa đánh giá này?')) return;
  try { await TGP_API.del(`/api/testimonials/${id}`); tgpToast('Đã xóa'); loadTestimonialsAdmin(); }
  catch (e) { tgpToast(e.error || 'Không thể xóa', 'error'); }
}

// ---------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------
async function loadSettingsAdmin() {
  try {
    const res = await TGP_API.get('/api/settings', { auth: false });
    const settings = res.data || {};
    const form = document.getElementById('settings-form');
    Object.entries(settings).forEach(([key, value]) => {
      const input = form.querySelector(`[name="${key}"]`);
      if (input) input.value = value;
    });
  } catch (e) { tgpToast('Không thể tải thông tin công ty', 'error'); }
}

document.getElementById('settings-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const payload = Object.fromEntries(fd.entries());
  try {
    await TGP_API.put('/api/admin/settings', payload);
    tgpToast('Đã lưu thông tin công ty thành công');
  } catch (err) {
    tgpToast(err.error || 'Không thể lưu thông tin', 'error');
  }
});

// ---------------------------------------------------------------------
// Export (delegates rendering to the Java report service)
// ---------------------------------------------------------------------
async function exportData(dataset, format) {
  try {
    const token = TGP_API.getToken();
    const response = await fetch(`/api/admin/export/${dataset}?format=${format}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error('Export failed');
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${dataset}.${format}`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
    tgpToast('Đã xuất dữ liệu thành công');
  } catch (e) {
    tgpToast('Không thể xuất dữ liệu', 'error');
  }
}

// ---------------------------------------------------------------------
// Toasts (lightweight local copy so admin.html doesn't need main.js)
// ---------------------------------------------------------------------
function tgpToast(message, type = 'success', title) {
  let stack = document.querySelector('.toast-stack');
  if (!stack) {
    stack = document.createElement('div');
    stack.className = 'toast-stack';
    document.body.appendChild(stack);
  }
  const el = document.createElement('div');
  el.className = `toast ${type === 'error' ? 'error' : ''}`;
  el.innerHTML = `${title ? `<strong>${title}</strong>` : ''}${message}`;
  stack.appendChild(el);
  setTimeout(() => {
    el.style.transition = 'opacity .3s ease, transform .3s ease';
    el.style.opacity = '0';
    el.style.transform = 'translateX(30px)';
    setTimeout(() => el.remove(), 320);
  }, 4200);
}

document.addEventListener('DOMContentLoaded', checkAuthAndBoot);
