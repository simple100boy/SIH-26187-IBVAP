/**
 * IBVAP Interactive Virtual Fence & Polygon Zone Canvas Editor
 */

let drawMode = 'virtual_tripwire'; // 'virtual_tripwire' or 'restricted_zone'
let activePoints = [];
let canvas = null;
let ctx = null;
let currentCameraId = 'cam-bop-01';

function initCanvasEditor() {
  canvas = document.getElementById('editor-canvas');
  if (!canvas) return;
  
  ctx = canvas.getContext('2d');
  resizeCanvas();
  window.addEventListener('resize', resizeCanvas);

  canvas.addEventListener('click', handleCanvasClick);
  canvas.addEventListener('mousemove', handleCanvasMouseMove);
}

function resizeCanvas() {
  if (!canvas || !canvas.parentElement) return;
  canvas.width = canvas.parentElement.clientWidth;
  canvas.height = canvas.parentElement.clientHeight;
  redrawCanvas();
}

function switchEditorCamera() {
  const sel = document.getElementById('editor-cam-select');
  if (!sel) return;
  currentCameraId = sel.value;
  document.getElementById('editor-bg-feed').src = `/api/cameras/feed/${currentCameraId}`;
  activePoints = [];
  redrawCanvas();
}

function setDrawMode(mode) {
  drawMode = mode;
  activePoints = [];
  
  document.getElementById('btn-mode-tripwire').classList.toggle('active', mode === 'virtual_tripwire');
  document.getElementById('btn-mode-zone').classList.toggle('active', mode === 'restricted_zone');
  
  redrawCanvas();
}

function handleCanvasClick(e) {
  const rect = canvas.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;

  activePoints.push({ x, y });

  if (drawMode === 'virtual_tripwire' && activePoints.length >= 2) {
    // Tripwire requires 2 points
    activePoints = activePoints.slice(0, 2);
  }
  redrawCanvas();
}

function handleCanvasMouseMove(e) {
  if (activePoints.length === 0) return;
  const rect = canvas.getBoundingClientRect();
  const mouseX = e.clientX - rect.left;
  const mouseY = e.clientY - rect.top;

  redrawCanvas(mouseX, mouseY);
}

function redrawCanvas(hoverX = null, hoverY = null) {
  if (!ctx) return;
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if (activePoints.length === 0) return;

  ctx.lineWidth = 3;
  
  if (drawMode === 'virtual_tripwire') {
    ctx.strokeStyle = '#00f2fe';
    ctx.fillStyle = '#ff0055';

    // Draw line
    ctx.beginPath();
    ctx.moveTo(activePoints[0].x, activePoints[0].y);
    const endX = activePoints.length > 1 ? activePoints[1].x : (hoverX !== null ? hoverX : activePoints[0].x);
    const endY = activePoints.length > 1 ? activePoints[1].y : (hoverY !== null ? hoverY : activePoints[0].y);
    
    ctx.lineTo(endX, endY);
    ctx.stroke();

    // Draw point markers
    activePoints.forEach(pt => {
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, 6, 0, Math.PI * 2);
      ctx.fill();
    });

  } else if (drawMode === 'restricted_zone') {
    ctx.strokeStyle = '#ff0055';
    ctx.fillStyle = 'rgba(255, 0, 85, 0.25)';

    ctx.beginPath();
    ctx.moveTo(activePoints[0].x, activePoints[0].y);
    for (let i = 1; i < activePoints.length; i++) {
      ctx.lineTo(activePoints[i].x, activePoints[i].y);
    }
    if (hoverX !== null && hoverY !== null) {
      ctx.lineTo(hoverX, hoverY);
    }
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    // Draw vertex dots
    ctx.fillStyle = '#00f2fe';
    activePoints.forEach(pt => {
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, 5, 0, Math.PI * 2);
      ctx.fill();
    });
  }
}

function clearCurrentCanvas() {
  activePoints = [];
  redrawCanvas();
}

async function saveCurrentZone() {
  if (activePoints.length < 2) {
    alert("Please draw points on the canvas before saving.");
    return;
  }

  // Normalize points between 0.0 and 1.0
  const normCoords = activePoints.map(pt => [
    parseFloat((pt.x / canvas.width).toFixed(4)),
    parseFloat((pt.y / canvas.height).toFixed(4))
  ]);

  const zoneId = `z-${currentCameraId}-${Date.now()}`;
  const zoneName = drawMode === 'virtual_tripwire' ? 'Virtual Tripwire Vector' : 'Restricted Perimeter Zone';

  const payload = {
    id: zoneId,
    camera_id: currentCameraId,
    zone_name: zoneName,
    zone_type: drawMode,
    coordinates: normCoords,
    severity: 'CRITICAL',
    enabled: true
  };

  try {
    const res = await fetch('/api/zones', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      alert(`Successfully saved ${drawMode} configuration for ${currentCameraId}!`);
      activePoints = [];
      redrawCanvas();
    } else {
      alert("Failed to save zone. Please check server logs.");
    }
  } catch (err) {
    console.error(err);
    alert("Network error saving zone.");
  }
}
