const $ = id => document.getElementById(id);
let stream, recorder, timer, segmentTimer, startedAt = 0, chunks = [], liveText = '', requestQueue = Promise.resolve(), liveMode = false;
const setStatus = text => { $('status').textContent = text; };
const elapsed = () => Math.min(60, (Date.now() - startedAt) / 1000);

async function transcribe(blob, append = false) {
  const form = new FormData();
  const ext = blob.type.includes('wav') ? 'wav' : blob.type.includes('ogg') ? 'ogg' : 'webm';
  form.append('file', blob, `recording.${ext}`);
  form.append('language', $('language').value);
  const began = performance.now();
  setStatus(append ? '实时识别中…' : '正在使用本地模型识别…');
  const response = await fetch('/api/transcribe', { method: 'POST', body: form });
  const result = await response.json();
  if (!response.ok) throw Error(result.detail || '识别失败');
  if (append) {
    liveText += (liveText && result.text ? ' ' : '') + result.text;
    $('result').value = liveText;
  } else $('result').value = result.text;
  $('duration').textContent = `${result.duration_seconds} 秒`;
  $('elapsed').textContent = `${((performance.now() - began) / 1000).toFixed(1)} 秒`;
  setStatus(result.text ? '识别完成' : '没有检测到可识别语音');
}
function safeTranscribe(blob, append) {
  requestQueue = requestQueue.then(() => transcribe(blob, append)).catch(e => setStatus(`识别失败：${e.message}`));
  return requestQueue;
}
function startSegment() {
  if (!stream || !liveMode) return;
  chunks = [];
  recorder = new MediaRecorder(stream);
  recorder.ondataavailable = e => { if (e.data.size) chunks.push(e.data); };
  recorder.onstop = () => {
    const blob = new Blob(chunks, { type: recorder.mimeType || 'audio/webm' });
    if (blob.size) safeTranscribe(blob, true);
    if (liveMode && elapsed() < 60) segmentTimer = setTimeout(startSegment, 100);
  };
  recorder.start();
  segmentTimer = setTimeout(() => { if (recorder?.state === 'recording') recorder.stop(); }, 4000);
}
$('start').onclick = async () => {
  try {
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) throw Error('当前浏览器不支持麦克风录音');
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    chunks = []; liveText = ''; requestQueue = Promise.resolve(); $('result').value = '';
    startedAt = Date.now(); liveMode = $('live').checked;
    $('start').disabled = true; $('stop').disabled = false;
    setStatus(liveMode ? '正在录音并实时识别… 最长 60 秒' : '正在录音… 最长 60 秒');
    timer = setInterval(() => {
      const sec = Math.floor(elapsed());
      $('clock').textContent = `${String(Math.floor(sec / 60)).padStart(2, '0')}:${String(sec % 60).padStart(2, '0')}`;
      if (sec >= 60) $('stop').click();
    }, 250);
    if (liveMode) startSegment();
    else {
      recorder = new MediaRecorder(stream);
      recorder.ondataavailable = e => { if (e.data.size) chunks.push(e.data); };
      recorder.start();
    }
  } catch (e) {
    setStatus(e.name === 'NotAllowedError' ? '麦克风权限被拒绝，请在浏览器设置中允许访问。' : `无法启动麦克风：${e.message}`);
    stream?.getTracks().forEach(track => track.stop()); stream = null;
    $('start').disabled = false; $('stop').disabled = true;
  }
};
$('stop').onclick = async () => {
  if (!recorder) return;
  clearInterval(timer); clearTimeout(segmentTimer);
  const wasLive = liveMode;
  const activeRecorder = recorder;
  if (!wasLive) {
    await new Promise(resolve => {
      activeRecorder.onstop = () => { resolve(); };
      if (activeRecorder.state !== 'inactive') activeRecorder.stop(); else resolve();
    });
  } else {
    liveMode = false;
    if (activeRecorder.state !== 'inactive') await new Promise(resolve => {
      const previous = activeRecorder.onstop;
      activeRecorder.onstop = event => { previous?.(event); resolve(); };
      activeRecorder.stop();
    });
  }
  stream?.getTracks().forEach(track => track.stop()); stream = null;
  $('start').disabled = false; $('stop').disabled = true;
  const sec = Math.floor(elapsed()); $('clock').textContent = `${String(Math.floor(sec / 60)).padStart(2, '0')}:${String(sec % 60).padStart(2, '0')}`;
  if (!wasLive) {
    const blob = new Blob(chunks, { type: activeRecorder.mimeType || 'audio/webm' });
    if (blob.size) await safeTranscribe(blob, false); else setStatus('录音为空，请重试。');
  } else {
    await requestQueue;
    setStatus($('result').value ? '实时识别完成' : '录音已停止；没有检测到可识别语音');
  }
  recorder = null;
};
$('file').onchange = e => { const file = e.target.files[0]; if (file) safeTranscribe(file, false); e.target.value = ''; };
$('copy').onclick = async () => {
  try { await navigator.clipboard.writeText($('result').value); setStatus('识别文字已复制'); }
  catch { setStatus('复制失败：请检查浏览器剪贴板权限'); }
};
