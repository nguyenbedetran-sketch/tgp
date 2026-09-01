const TGP_CATEGORY_LABELS = {
  nha_pho: 'Nhà phố',
  biet_thu: 'Biệt thự',
  van_phong: 'Văn phòng',
  noi_that: 'Nội thất',
  thuong_mai: 'Công trình thương mại',
  khac: 'Khác',
};

function tgpFormatVnd(value) {
  if (value === null || value === undefined || isNaN(value)) return '';
  return Math.round(value).toLocaleString('vi-VN') + ' VNĐ';
}

function tgpEscapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str ?? '';
  return div.innerHTML;
}

function tgpFormatDate(isoLike) {
  if (!isoLike) return '';
  const d = new Date(isoLike.replace(' ', 'T'));
  if (isNaN(d.getTime())) return isoLike;
  return d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });
}
