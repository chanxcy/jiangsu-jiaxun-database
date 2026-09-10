'use strict';
(() => {
  const SVG_NS = 'http://www.w3.org/2000/svg', GROUP_DISTANCE = 26;
  const byId = id => document.getElementById(id);
  const el = (tag, value, cls) => { const node = document.createElement(tag); if (cls) node.className = cls; if (value !== undefined) node.textContent = value; return node; };
  const svgEl = tag => document.createElementNS(SVG_NS, tag);
  const recordHref = id => `record.html?id=${encodeURIComponent(id)}`;
  const state = { places: [], coordinates: [], details: {}, filtered: [], pinned: null, projection: null };

  function excerpt(detail) {
    const source = [...(detail.text_units || [])].sort((a, b) => Number(a.sequence_no) - Number(b.sequence_no)).map(unit => unit.original_text || '').join('').replace(/\s+/g, '');
    if (!source) return detail.original_text_status === '待复核' ? '原文待复核' : '原文待补';
    return source.length > 90 ? `${source.slice(0, 90)}……` : source;
  }
  function uniqueRelations(placeId, recordId) { return [...new Set((state.details[recordId]?.places || []).filter(item => item.place_id === placeId).map(item => item.relation_type).filter(Boolean))]; }
  function appendRecordCard(root, place, item) {
    const detail = state.details[item.record_id]; if (!detail) return;
    const article = el('article', undefined, 'map-record'); article.dataset.placeId = place.place_id; article.dataset.recordId = item.record_id;
    const title = el('a', detail.standard_title, 'map-record-title'); title.href = recordHref(item.record_id);
    article.append(title, el('p', `${detail.primary_person_name || '主要人物待查'} · ${detail.era || '时代待考'} · 家训核验 ${detail.verification_level}级`));
    const relations = el('ul', undefined, 'plain-list'); uniqueRelations(place.place_id, item.record_id).forEach(value => relations.append(el('li', `关联类型：${value}`))); article.append(relations, el('blockquote', excerpt(detail), 'map-excerpt')); root.append(article);
  }
  function detailCard(placeIds, pinned = false) {
    const root = el('div', undefined, 'map-detail-card');
    if (pinned) root.append(el('p', '已固定当前点位；点击地图空白处返回地点列表。', 'pin-note'));
    placeIds.forEach((placeId, index) => {
      const place = state.places.find(item => item.place_id === placeId), coord = state.coordinates.find(item => item.place_id === placeId); if (!place || !coord) return;
      const section = el('section', undefined, 'map-place-detail'); if (index) section.classList.add('separated');
      section.append(el('h3', place.modern_name || '现代地名待核'), el('p', `历史地名：${place.historical_name || '—'}`), el('p', `定位状态：${coord.status === 'located' ? '已定位' : '位置待核'}`), el('p', `定位精度：${coord.display_precision || coord.precision}`), el('p', `地理核验：${coord.geographic_verification}级`));
      const records = [...new Map((place.records || []).map(item => [`${place.place_id}:${item.record_id}`, item])).values()]; records.forEach(record => appendRecordCard(section, place, record));
      if (coord.source_url) { const source = el('a', '查看主要核验依据', 'evidence-link'); source.href = coord.source_url; source.target = '_blank'; source.rel = 'noopener'; section.append(source); } root.append(section);
    }); return root;
  }
  function renderDefaultList() {
    const root = byId('place-detail'); root.replaceChildren(el('p', '将鼠标移到点位，或使用键盘聚焦点位，即可在此查看家训详情。点击点位可固定内容。', 'sidebar-prompt'));
    state.filtered.forEach(coord => { const place = state.places.find(item => item.place_id === coord.place_id); if (!place) return; const article = el('article', undefined, `place-summary ${coord.status}`); article.append(el('h3', place.modern_name || place.historical_name), el('p', `${place.historical_name || '历史地名待核'} · ${coord.display_precision || coord.precision}`), el('p', coord.status === 'located' ? `已定位 · 地理核验 ${coord.geographic_verification}级` : '位置待核 · 不生成地图点', 'place-status')); const links = el('div', undefined, 'tags'); [...new Map((place.records || []).map(item => [item.record_id, item])).values()].forEach(record => { const a = el('a', record.standard_title); a.href = recordHref(record.record_id); links.append(a); }); article.append(links); root.append(article); });
    if (!state.filtered.length) root.append(el('p', '没有符合当前筛选的地点。', 'empty'));
  }
  function updateSidePanel(placeIds, pinned = false) { byId('place-detail').replaceChildren(detailCard(placeIds, pinned)); }
  function clearPinned() { state.pinned = null; renderDefaultList(); }
  function coordinatesOf(geometry) { const polygons = geometry.type === 'Polygon' ? [geometry.coordinates] : geometry.coordinates; return polygons.flatMap(polygon => polygon.flatMap(ring => ring)); }
  function makeProjection(boundary) { const points = boundary.features.flatMap(feature => coordinatesOf(feature.geometry)), lons = points.map(point => point[0]), lats = points.map(point => point[1]), bounds = { minLon: Math.min(...lons), maxLon: Math.max(...lons), minLat: Math.min(...lats), maxLat: Math.max(...lats) }, width = 720, height = 760, pad = 36, scale = Math.min((width - pad * 2) / (bounds.maxLon - bounds.minLon), (height - pad * 2) / (bounds.maxLat - bounds.minLat)), xOffset = (width - (bounds.maxLon - bounds.minLon) * scale) / 2, yOffset = (height - (bounds.maxLat - bounds.minLat) * scale) / 2; return ([lon, lat]) => [xOffset + (lon - bounds.minLon) * scale, height - yOffset - (lat - bounds.minLat) * scale]; }
  function pathData(geometry, project) { const polygons = geometry.type === 'Polygon' ? [geometry.coordinates] : geometry.coordinates; return polygons.map(polygon => polygon.map(ring => ring.map((point, i) => { const [x, y] = project(point); return `${i ? 'L' : 'M'}${x.toFixed(2)},${y.toFixed(2)}`; }).join(' ') + ' Z').join(' ')).join(' '); }
  function ringArea(ring) { return Math.abs(ring.reduce((sum, point, i) => { const next = ring[(i + 1) % ring.length]; return sum + point[0] * next[1] - next[0] * point[1]; }, 0) / 2); }
  function visualCenter(geometry) { const polygons = geometry.type === 'Polygon' ? [geometry.coordinates] : geometry.coordinates, outer = polygons.map(polygon => polygon[0]).sort((a, b) => ringArea(b) - ringArea(a))[0], projected = outer.map(state.projection), xs = projected.map(point => point[0]), ys = projected.map(point => point[1]); return [(Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2]; }
  function renderBoundary(boundary) {
    state.projection = makeProjection(boundary); const layer = byId('boundary-layer'), labels = byId('city-label-layer'); layer.replaceChildren(); labels.replaceChildren();
    boundary.features.forEach(feature => { const region = feature.properties.region, city = feature.properties.city_name, path = svgEl('path'); path.setAttribute('d', pathData(feature.geometry, state.projection)); path.setAttribute('class', `city-boundary region-${region === '苏南' ? 'south' : region === '苏中' ? 'central' : 'north'}`); path.dataset.city = city; layer.append(path); const [x, y] = visualCenter(feature.geometry), label = svgEl('text'); label.textContent = city; label.setAttribute('x', x.toFixed(1)); label.setAttribute('y', y.toFixed(1)); label.setAttribute('class', 'city-label'); label.dataset.city = city; labels.append(label); }); byId('map-status').hidden = true;
  }
  function projectedGroups(items) { const candidates = items.filter(item => item.status === 'located').map(item => ({ ...item, point: state.projection([item.longitude, item.latitude]) })), groups = []; candidates.forEach(item => { const group = groups.find(existing => existing.some(member => Math.hypot(member.point[0] - item.point[0], member.point[1] - item.point[1]) <= GROUP_DISTANCE)); if (group) group.push(item); else groups.push([item]); }); return groups; }
  function renderMarkers() {
    const layer = byId('marker-layer'); layer.replaceChildren(); if (!state.projection) return;
    projectedGroups(state.filtered).forEach(items => { const placeIds = [...new Set(items.map(item => item.place_id))], x = items.reduce((sum, item) => sum + item.point[0], 0) / items.length, y = items.reduce((sum, item) => sum + item.point[1], 0) / items.length, group = svgEl('g'); group.setAttribute('class', 'map-marker'); group.setAttribute('tabindex', '0'); group.setAttribute('role', 'button'); group.setAttribute('transform', `translate(${x} ${y})`); group.dataset.placeIds = placeIds.join(','); const names = placeIds.map(id => state.places.find(place => place.place_id === id)?.historical_name).filter(Boolean).join('、'); group.setAttribute('aria-label', `查看${names}的家训信息${placeIds.length > 1 ? `，共${placeIds.length}个相近地点` : ''}`); const halo = svgEl('circle'); halo.setAttribute('r', '16'); halo.setAttribute('class', 'marker-halo'); const dot = svgEl('circle'); dot.setAttribute('r', '7'); dot.setAttribute('class', 'marker-dot'); group.append(halo, dot); if (placeIds.length > 1) { const count = svgEl('text'); count.textContent = String(placeIds.length); count.setAttribute('class', 'marker-count'); count.setAttribute('x', '12'); count.setAttribute('y', '-10'); group.append(count); } group.addEventListener('mouseenter', () => { if (!state.pinned) updateSidePanel(placeIds); }); group.addEventListener('focus', () => { if (!state.pinned) updateSidePanel(placeIds); }); group.addEventListener('click', event => { event.stopPropagation(); state.pinned = placeIds; updateSidePanel(placeIds, true); }); group.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); state.pinned = placeIds; updateSidePanel(placeIds, true); } if (event.key === 'Escape') clearPinned(); }); layer.append(group); });
  }
  function placeMatches(coord, filters) { const place = state.places.find(item => item.place_id === coord.place_id), records = (place?.records || []).map(item => state.details[item.record_id]).filter(Boolean); return (!filters.city || place.prefecture_city === filters.city) && (!filters.precision || coord.precision === filters.precision) && (!filters.era || records.some(record => record.era === filters.era)) && (!filters.level || records.some(record => record.verification_level === filters.level)); }
  function applyFilters() { const filters = Object.fromEntries(new FormData(byId('map-filters')).entries()); state.filtered = state.coordinates.filter(coord => placeMatches(coord, filters)); state.pinned = null; renderMarkers(); renderDefaultList(); }
  function options(select, values) { [...new Set(values.filter(Boolean))].sort((a, b) => a.localeCompare(b, 'zh-CN')).forEach(value => { const option = el('option', value); option.value = value; select.append(option); }); }
  async function loadJson(name) { const response = await fetch(`data/${name}`); if (!response.ok) throw new Error(name); return response.json(); }
  async function init() {
    try { const [places, coordinates, details, boundary] = await Promise.all(['places.json', 'place_coordinates.json', 'record_details.json', 'jiangsu_boundary.geojson'].map(loadJson)); state.places = places; state.coordinates = coordinates.places; state.details = details; renderBoundary(boundary); options(byId('map-filters').elements.city, places.map(item => item.prefecture_city)); options(byId('map-filters').elements.era, Object.values(details).map(item => item.era)); options(byId('map-filters').elements.level, Object.values(details).map(item => item.verification_level)); options(byId('map-filters').elements.precision, state.coordinates.map(item => item.precision)); byId('map-filters').addEventListener('change', applyFilters); byId('map-clear').addEventListener('click', () => { byId('map-filters').reset(); applyFilters(); }); byId('jiaxun-map').addEventListener('click', event => { if (!event.target.closest('.map-marker')) clearPinned(); }); state.filtered = state.coordinates; renderMarkers(); renderDefaultList(); }
    catch (error) { console.error(error); byId('jiaxun-map').hidden = true; const status = byId('map-status'); status.hidden = false; status.textContent = '地图未能加载。正在尝试显示可访问地点列表。'; try { const [places, coordinates, details] = await Promise.all(['places.json', 'place_coordinates.json', 'record_details.json'].map(loadJson)); state.places = places; state.coordinates = coordinates.places; state.details = details; state.filtered = state.coordinates; renderDefaultList(); } catch (_) { byId('place-detail').replaceChildren(el('p', '地点数据也未能载入。', 'notice')); } }
  }
  window.addEventListener('DOMContentLoaded', init);
})();
