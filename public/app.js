/* Locally hosted Leaflet and data; only the background tiles use a third-party service. */
'use strict';
const $ = id => document.getElementById(id);
const state = {features: [], manifest: null, selected: null, overlay: null};
const map = L.map('map', {zoomControl: false, preferCanvas: true}).setView([29.978, -90.075], 12);
L.control.zoom({position: 'topright'}).addTo(map);
const basemap = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  className: 'basemap-tiles',
  maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);
map.attributionControl.addAttribution('<a href="https://bikestreets.com/la/new-orleans/">Bike Streets</a>');
let tileWarning = false;
function message(text) { $('map-message').textContent = text; $('map-message').hidden = false; }
basemap.on('tileerror', () => {
  if (!tileWarning) { tileWarning = true; message('Background tiles could not load. Local bicycle routes are still available.'); }
});
const routes = L.geoJSON(null, {style: styleRoute, onEachFeature: (f, layer) => layer.bindPopup(() => popup(f))}).addTo(map);
const boundary = L.geoJSON(null, {interactive: false, style: {color: '#194d3f', weight: 2, fillOpacity: 0.025, dashArray: '4 5'}}).addTo(map);
const bestHighlight = L.geoJSON(null,{style:{color:'#b13478',weight:7,opacity:1}}).addTo(map);
const cityRoutes = L.geoJSON(null,{style:styleRoute,onEachFeature:(f,l)=>l.bindPopup(()=>popup(f))}).addTo(map);
let cityFeatures=[];
async function loadCity() {
  try {
    const [data,source]=await Promise.all([readJson('data/city-bikeways.geojson'),readJson('data/city-bikeways-source.json')]);
    cityFeatures=data.features;
    $('designated-label').textContent='OSM-marked routes + city bikeways';
    render();
  } catch { $('designated-label').textContent='OSM-marked routes · city data unavailable'; }
}
let pickSets={network:[],traffic:[]}, picksLoading=true, selectedPick=null;
async function loadPicks() {
  const results=await Promise.allSettled([readJson('data/best-routes.geojson'),readJson('data/best-routes-traffic.geojson')]);
  ['network','traffic'].forEach((network,i)=>{
    if(results[i].status==='fulfilled') pickSets[network]=results[i].value.features.map(f=>({...f,properties:{...f.properties,network,key:`${network}:${f.properties.rank}`}}));
  });
  picksLoading=false;renderPicks();
}
function clearPick() {
  selectedPick=null;map.closePopup();bestHighlight.clearLayers();$('clear-pick').hidden=true;
}
function renderPicks() {
  if(picksLoading)return;
  const enabled=[...($('network').checked?pickSets.network:[]),...($('designated').checked?pickSets.traffic:[])].sort((a,b)=>b.properties.canopy_pct-a.properties.canopy_pct);
  if(selectedPick&&!enabled.some(f=>f.properties.key===selectedPick))clearPick();
  $('best-routes').replaceChildren();
  $('picks-description').textContent='Connected 1 km (0.62 mi) picks from enabled networks, ranked by average nearby canopy. 2017 tree cover.';
  if(!enabled.length)$('best-routes').textContent=(!$('network').checked&&!$('designated').checked)?'Tick a route layer to see its best-covered stretches.':'Route picks are unavailable for the enabled layer.';
  $('traffic-picks-download').hidden=!$('designated').checked;
  for (const [i,feature] of enabled.entries()) {
    const p=feature.properties,button=document.createElement('button');
    button.className='route-pick';button.dataset.network=p.network;button.setAttribute('aria-pressed',String(selectedPick===p.key));
    const category=p.network==='traffic'?'More traffic':'Low-stress';
    const rank=document.createElement('span');rank.className='rank';rank.textContent=String(i+1).padStart(2,'0');
    const name=document.createElement('span');name.className='pick-name';name.textContent=p.neighborhood;
    const detail=document.createElement('small');detail.textContent=`${category} · 1 km / 0.62 mi`;name.append(detail);
    const score=document.createElement('strong');score.textContent=`${Math.round(p.canopy_pct)}%`;
    button.append(rank,name,score);
    button.addEventListener('click',()=>{
      selectedPick=p.key;
      document.querySelectorAll('.route-pick').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));
      bestHighlight.clearLayers().addData(feature);bestHighlight.bringToFront();
      map.stop();map.fitBounds(bestHighlight.getBounds(),{padding:[45,45],maxZoom:16,animate:false});
      const content=document.createElement('div');
      content.textContent=`${p.name} · ${category}: ${p.canopy_pct}% nearby canopy over 1 km. NOAA 2017 imagery. Exploratory corridor; check direction and crossings.`;
      bestHighlight.getLayers()[0].bindPopup(content).openPopup();
      $('clear-pick').hidden=false;
      if (innerWidth<=650) document.querySelector('.map-shell').scrollIntoView({behavior:'smooth'});
    });
    $('best-routes').append(button);
  }
}
$('clear-pick').addEventListener('click',()=>{clearPick();renderPicks();});
function kind(p) {
  if (p.source_layer === 'city') return 'city';
  if (p.source_layer === 'construction' || p.is_under_construction) return 'construction';
  return p.source_layer === 'network' ? 'network' : 'designated';
}
function color(p) {
  if (kind(p) === 'construction') return '#de702c';
  const n = p.canopy_pct;
  return n === null || n === undefined ? '#416f9b' : n < 20 ? '#91a5ae' : n < 40 ? '#77b89a' : n < 60 ? '#24865b' : '#005b3c';
}
function styleRoute(f) {
  const p=f.properties, measured=p.canopy_pct!=null, low=measured&&p.canopy_pct<20;
  const weight=kind(p)==='construction'?4:low?2.75:measured&&p.canopy_pct>=60?5:measured&&p.canopy_pct>=40?4.5:3.5;
  return {color: color(p), weight, opacity: low ? .85 : .95,
    dashArray: kind(f.properties) === 'construction' ? '7 6' : ['designated','city'].includes(kind(f.properties)) ? '3 3' : null};
}
function popup(f) {
  const p = f.properties, box = document.createElement('div');
  const label = document.createElement('div'); label.className = 'popup-label';
  label.textContent = {network: 'Low-stress network', designated: 'More traffic', construction: 'Construction disruption',city:'City of New Orleans bikeway'}[kind(p)];
  const score = document.createElement('strong'); score.className = 'popup-score';
  score.textContent = p.canopy_pct == null ? 'Not measured' : `${Math.round(p.canopy_pct)}% canopy`;
  const detail = document.createElement('div');
  detail.textContent = p.source_layer==='city' ? `${p.name} · ${p.facility} · ${Math.round(p.length_m)} m` : `${Math.round(p.length_m)} m segment · ${kind(p)==='designated'?'OSM-marked bikeway (via Bike Streets tiles)':'Bike Streets'}`;
  const note = document.createElement('div'); note.className = 'popup-note';
  note.textContent = p.canopy_pct == null ? 'No reliable canopy measurement is available for this segment.' : 'Nearby canopy within 10 m · NOAA 2017 imagery. Not a measurement of current or time-of-day shade.';
  if (kind(p) === 'construction') note.textContent += ' Marked under construction in the network snapshot.';
  box.append(label, score, detail, note); return box;
}
function render() {
  const threshold = Number($('threshold').value);
  const visible = state.features.filter(f => {
    const k = kind(f.properties);
    // Keep construction warnings visible regardless of the canopy threshold.
    return $(k).checked && (k === 'construction' || threshold === 0 ||
      (f.properties.canopy_pct != null && f.properties.canopy_pct >= threshold));
  });
  routes.clearLayers().addData({type: 'FeatureCollection', features: visible});
  cityRoutes.clearLayers();
  const visibleCity=$('designated').checked?cityFeatures.filter(f=>threshold===0||(f.properties.canopy_pct!=null&&f.properties.canopy_pct>=threshold)):[];
  cityRoutes.addData({type:'FeatureCollection',features:visibleCity});
  bestHighlight.bringToFront();
  const network = visible.filter(f => kind(f.properties) === 'network');
  updateStats(network,'route-miles','canopy-average');
  updateStats([...visible.filter(f=>kind(f.properties)==='designated'),...visibleCity],'traffic-miles','traffic-canopy');
  renderPicks();
  $('threshold-label').textContent = threshold ? `${threshold}% or more` : 'All routes';
  if (state.overlay) {
    if ($('canopy').checked) state.overlay.addTo(map); else state.overlay.remove();
  }
}
function updateStats(features,milesId,canopyId) {
  const length=features.reduce((sum,f)=>sum+f.properties.length_m,0);
  const measured=features.filter(f=>f.properties.canopy_pct!=null);
  const measuredLength=measured.reduce((sum,f)=>sum+f.properties.length_m,0);
  $(milesId).textContent=(length/1609.344).toFixed(1);
  $(canopyId).textContent=measuredLength?`${Math.round(measured.reduce((sum,f)=>sum+f.properties.length_m*f.properties.canopy_pct,0)/measuredLength)}%`:'—';
}
async function readJson(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`${path} returned ${response.status}`);
  return response.json();
}
async function initialize() {
  try {
    const [manifest, data] = await Promise.all([readJson('data/manifest.json'), readJson('data/routes.geojson')]);
    state.manifest = manifest; state.features = data.features;
    const ready = manifest.status === 'ready' && manifest.canopy.downloaded;
    const status = ready ? `Canopy: NOAA ${manifest.canopy.year} imagery · Historical coverage, not live shade.` : 'Bike Streets routes are loaded. Tree canopy has not been imported yet; blue routes are not shade ratings.';
    $('data-status').textContent = status; $('about-status').textContent = status;
    $('network-date').textContent = `Snapshot retrieved ${manifest.network.retrieved_utc.slice(0,10)}.`;
    $('threshold').disabled = !ready;
    if (ready) {
      $('filter-help').textContent = 'Filter both networks by canopy within 10 m. Construction warnings stay visible. Statistics follow the layers and canopy filter shown.';
      $('canopy-label').textContent = 'NOAA · 2017 imagery · generalized display';
      if (manifest.canopy.overlay) {
        const o = manifest.canopy.overlay;
        state.overlay = L.imageOverlay(o.url, o.bounds, {opacity: .9, interactive: false, zIndex: 200});
        state.overlay.on('error', () => message('The canopy image could not load. Route canopy measurements remain available.'));
        $('canopy').disabled = false;
      }
      map.attributionControl.addAttribution('Canopy: NOAA OCM');
    }
    render();
    const params = new URLSearchParams(location.hash.slice(1));
    const lat = Number(params.get('lat')), lng = Number(params.get('lng')), zoom = Number(params.get('z'));
    if (params.has('lat') && params.has('lng') && params.has('z') && Number.isFinite(lat) && Number.isFinite(lng) && Number.isFinite(zoom) && Math.abs(lat) <= 85 && Math.abs(lng) <= 180 && zoom >= 2 && zoom <= 19) map.setView([lat,lng],zoom);
  } catch (error) {
    $('data-status').textContent = 'The route data could not load. Please reload the page or check the data files.';
    $('data-status').classList.add('error'); console.error(error);
  }
  try {
    const neighborhoods = await readJson('data/neighborhoods.geojson');
    neighborhoods.features.sort((a,b) => a.properties.name.localeCompare(b.properties.name)).forEach((feature, i) => {
      const option = document.createElement('option'); option.value = i; option.textContent = feature.properties.name;
      $('neighborhood').append(option);
    });
    $('neighborhood').addEventListener('change', () => {
      boundary.clearLayers();
      if ($('neighborhood').value === '') { reset(); return; }
      const feature = neighborhoods.features[Number($('neighborhood').value)];
      boundary.addData(feature); map.stop(); map.fitBounds(boundary.getBounds(), {padding: [40,40], maxZoom: 15, animate: false});
    });
  } catch { $('neighborhood').disabled = true; }
}
function reset() { map.stop(); map.setView([29.978, -90.075],12,{animate:false}); boundary.clearLayers(); $('neighborhood').value = ''; }
['network','designated','construction','canopy','threshold'].forEach(id => $(id).addEventListener('input',render));
$('reset-button').addEventListener('click',reset);
$('locate-button').addEventListener('click', () => map.locate({setView: true, maxZoom: 15, timeout: 10000}));
let locationDot;
map.on('locationfound', e => { if (locationDot) locationDot.remove(); locationDot = L.circleMarker(e.latlng, {radius: 7, color: '#fff', weight: 3, fillColor: '#285ec2', fillOpacity: 1}).addTo(map).bindPopup('Your location'); });
map.on('locationerror', () => message('Your location is unavailable. Choose a neighborhood or pan the map instead.'));
$('about-button').addEventListener('click', () => $('about-dialog').showModal());
$('close-about').addEventListener('click', () => $('about-dialog').close());
$('about-dialog').addEventListener('click', e => { if (e.target === $('about-dialog')) { const b = e.target.getBoundingClientRect(); if (e.clientX < b.left || e.clientX > b.right || e.clientY < b.top || e.clientY > b.bottom) e.target.close(); } });
$('share-button').addEventListener('click', async () => {
  const center = map.getCenter();
  const url = new URL(location.href); url.hash = new URLSearchParams({lat:center.lat.toFixed(5),lng:center.lng.toFixed(5),z:map.getZoom()}).toString();
  try { await navigator.clipboard.writeText(url.href); $('share-button').textContent = 'Link copied'; setTimeout(() => {$('share-button').textContent = 'Share map';},2000); }
  catch { history.replaceState(null,'',url.href); message('The address bar now contains this map view. Copy its URL to share.'); }
});
initialize();
loadPicks();
loadCity();
