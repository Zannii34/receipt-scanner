// Upload + review logic (works for both camera and file upload)

// Mode switching
document.querySelectorAll(".mode-tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".mode-tab").forEach(t => t.classList.remove("active"));
    tab.classList.add("active");
    const mode = tab.dataset.mode;
    document.getElementById("cameraMode").classList.toggle("hidden", mode !== "camera");
    document.getElementById("uploadMode").classList.toggle("hidden", mode !== "upload");
    if (mode !== "camera" && typeof stopCamera === "function") stopCamera();
  });
});

// File upload handlers
const uploadZone = document.getElementById("uploadZone");
const fileInput = document.getElementById("fileInput");
const browseBtn = document.getElementById("browseBtn");

if (uploadZone) {
  uploadZone.addEventListener("click", () => fileInput.click());
  browseBtn.addEventListener("click", (e) => { e.stopPropagation(); fileInput.click(); });
  fileInput.addEventListener("change", (e) => {
    if (e.target.files[0]) uploadImage(e.target.files[0], e.target.files[0].name);
  });

  uploadZone.addEventListener("dragover", (e) => { e.preventDefault(); uploadZone.classList.add("dragover"); });
  uploadZone.addEventListener("dragleave", () => uploadZone.classList.remove("dragover"));
  uploadZone.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadZone.classList.remove("dragover");
    if (e.dataTransfer.files[0]) uploadImage(e.dataTransfer.files[0], e.dataTransfer.files[0].name);
  });
}

// Main upload + extraction function
async function uploadImage(blobOrFile, filename) {
  const status = document.getElementById("status");
  const reviewSection = document.getElementById("reviewSection");
  const previewImg = document.getElementById("previewImg");

  status.textContent = "🔍 Extracting information...";
  status.classList.remove("hidden");
  status.style.color = "";
  reviewSection.classList.add("hidden");

  previewImg.src = URL.createObjectURL(blobOrFile);

  const form = new FormData();
  form.append("file", blobOrFile, filename);

  try {
    const res = await fetch("/upload", { method: "POST", body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Upload failed");

    document.getElementById("filename").value = data.filename;
    document.getElementById("rawText").value = data.raw_text || "";
    document.getElementById("merchant").value = data.merchant || "";
    document.getElementById("date").value = data.date || "";
    document.getElementById("category").value = data.category || "other";
    document.getElementById("vatIncluded").checked = !!data.vat_included;
    document.getElementById("subtotal").value = data.subtotal != null ? data.subtotal.toFixed(2) : "";
    document.getElementById("vatAmount").value = data.vat_amount != null ? data.vat_amount.toFixed(2) : "";
    document.getElementById("total").value = data.total != null ? data.total.toFixed(2) : "";
    document.getElementById("vatRate").value = String(data.vat_rate || 0.15);

    status.classList.add("hidden");
    reviewSection.classList.remove("hidden");
    reviewSection.scrollIntoView({ behavior: "smooth" });
  } catch (e) {
    status.textContent = "Error: " + e.message;
    status.style.color = "#c33";
  }
}

// Auto-compute VAT when total changes (if VAT included)
function recalcVatFromTotal() {
  if (!document.getElementById("vatIncluded").checked) return;
  const total = parseFloat(document.getElementById("total").value);
  const rate = parseFloat(document.getElementById("vatRate").value);
  if (isNaN(total) || isNaN(rate) || rate <= 0) return;
  const vat = total * rate / (1 + rate);
  const sub = total - vat;
  document.getElementById("vatAmount").value = vat.toFixed(2);
  document.getElementById("subtotal").value = sub.toFixed(2);
}

const totalInput = document.getElementById("total");
if (totalInput) {
  totalInput.addEventListener("blur", recalcVatFromTotal);
  document.getElementById("vatRate").addEventListener("change", recalcVatFromTotal);
  document.getElementById("vatIncluded").addEventListener("change", () => {
    if (document.getElementById("vatIncluded").checked) recalcVatFromTotal();
  });
}

// Save form
const reviewForm = document.getElementById("reviewForm");
if (reviewForm) {
  reviewForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const payload = {
      filename: document.getElementById("filename").value,
      raw_text: document.getElementById("rawText").value,
      merchant: document.getElementById("merchant").value.trim(),
      date: document.getElementById("date").value || null,
      category: document.getElementById("category").value,
      vat_included: document.getElementById("vatIncluded").checked,
      subtotal: parseFloat(document.getElementById("subtotal").value) || null,
      vat_amount: parseFloat(document.getElementById("vatAmount").value) || null,
      total: parseFloat(document.getElementById("total").value) || null,
      vat_rate: parseFloat(document.getElementById("vatRate").value),
      notes: document.getElementById("notes").value.trim(),
      list_id: parseInt(document.getElementById("listSelect").value) || null,
    };

    try {
      const res = await fetch("/receipts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error("Save failed");
      window.location.reload();
    } catch (err) {
      alert("Could not save: " + err.message);
    }
  });
}

// Cancel button
const cancelBtn = document.getElementById("cancelBtn");
if (cancelBtn) {
  cancelBtn.addEventListener("click", () => {
    document.getElementById("reviewSection").classList.add("hidden");
    if (typeof stopCamera === "function") stopCamera();
  });
}

// Retake button
const retakeBtn = document.getElementById("retakeBtn");
if (retakeBtn) {
  retakeBtn.addEventListener("click", () => {
    document.getElementById("reviewSection").classList.add("hidden");
    if (typeof startCamera === "function") startCamera();
  });
}

// Delete receipt buttons
document.querySelectorAll("[data-delete]").forEach(btn => {
  btn.addEventListener("click", async () => {
    if (!confirm("Delete this receipt?")) return;
    const id = btn.dataset.delete;
    await fetch("/receipt/" + id, { method: "DELETE" });
    window.location.reload();
  });
});
