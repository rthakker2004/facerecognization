const video = document.getElementById('video');
const captureBtn = document.getElementById('capture');
const status = document.getElementById('status');
navigator.mediaDevices.getUserMedia({ video: true }).then(stream => { video.srcObject = stream; }).catch(err => { status.innerText = 'Unable to access camera: ' + err; });
captureBtn.addEventListener('click', async ()=>{
  const candidate = document.getElementById('candidate').value || 'unknown';
  const canvas = document.createElement('canvas');
  canvas.width = video.videoWidth || 320;
  canvas.height = video.videoHeight || 240;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  canvas.toBlob(async (blob)=>{
    const fd = new FormData();
    fd.append('image', blob, 'capture.jpg');
    fd.append('candidate', candidate);
    status.innerText = 'Sending...';
    const res = await fetch('/vote', { method: 'POST', body: fd });
    const j = await res.json();
    status.innerText = JSON.stringify(j);
  }, 'image/jpeg', 0.9);
});
