// Camera capture for receipt scanning
let stream = null;
let currentFacingMode = "environment";

const video = document.getElementById("video");
const startCamBtn = document.getElementById("startCamBtn");
const switchCamBtn = document.getElementById("switchCamBtn");
const captureBtn = document.getElementById("captureBtn");
const stopCamBtn = document.getElementById("stopCamBtn");

async function startCamera() {
  try {
    if (stream) {
      stream.getTracks().forEach(t => t.stop());
    }
    stream = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: { ideal: currentFacingMode },
        width: { ideal: 1920 },
        height: { ideal: 1080 }
      },
      audio: false
    });
    video.srcObject = stream;
    await video.play();

    startCamBtn.classList.add("hidden");
    captureBtn.classList.remove("hidden");
    stopCamBtn.classList.remove("hidden");
    switchCamBtn.classList.remove("hidden");
  } catch (err) {
    alert("Could not access camera: " + err.message + "\n\nMake sure you're on HTTPS or localhost, and grant camera permission.");
  }
}

function stopCamera() {
  if (stream) {
    stream.getTracks().forEach(t => t.stop());
    stream = null;
    video.srcObject = null;
  }
  startCamBtn.classList.remove("hidden");
  captureBtn.classList.add("hidden");
  stopCamBtn.classList.add("hidden");
  switchCamBtn.classList.add("hidden");
}

function switchCamera() {
  currentFacingMode = currentFacingMode === "environment" ? "user" : "environment";
  if (stream) startCamera();
}

async function capturePhoto() {
  if (!stream || !video.videoWidth) {
    alert("Camera not ready yet");
    return;
  }

  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0);

  canvas.toBlob(async (blob) => {
    if (!blob) return;
    stopCamera();
    await uploadImage(blob, "receipt.jpg");
  }, "image/jpeg", 0.9);
}

startCamBtn.addEventListener("click", startCamera);
stopCamBtn.addEventListener("click", stopCamera);
switchCamBtn.addEventListener("click", switchCamera);
captureBtn.addEventListener("click", capturePhoto);

// Clean up camera on page unload
window.addEventListener("beforeunload", () => {
  if (stream) stream.getTracks().forEach(t => t.stop());
});
