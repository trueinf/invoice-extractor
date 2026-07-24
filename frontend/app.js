const DEFAULT_API_BASE_URL = "";
const DEFAULT_API_BASE_URL_PLACEHOLDER = "https://api.yourdomain.com";
const STORAGE_KEY = "invoiceExtractorApiBaseUrl";

const apiBaseUrlInput = document.getElementById("apiBaseUrl");
const saveApiBaseUrlButton = document.getElementById("saveApiBaseUrl");
const resetApiBaseUrlButton = document.getElementById("resetApiBaseUrl");
const fileInput = document.getElementById("fileInput");
const modeSelect = document.getElementById("modeSelect");
const extractButton = document.getElementById("extractButton");
const statusText = document.getElementById("statusText");
const output = document.getElementById("output");

function getApiBaseUrl() {
  return localStorage.getItem(STORAGE_KEY) || DEFAULT_API_BASE_URL;
}

function setStatus(message) {
  statusText.textContent = message;
}

function setOutput(value) {
  output.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
}

function getUploadEndpoint(baseUrl, mode) {
  const normalized = baseUrl.replace(/\/$/, "");
  return mode === "sync" ? `${normalized}/v1/extractions/sync` : `${normalized}/v1/extractions`;
}

async function pollJob(statusUrl, resultUrl) {
  const response = await fetch(statusUrl);
  if (!response.ok) {
    throw new Error(`Polling failed: ${response.status}`);
  }
  const job = await response.json();
  setStatus(`Job status: ${job.status}`);
  setOutput(job);

  if (job.status === "queued" || job.status === "processing") {
    await new Promise((resolve) => setTimeout(resolve, 1500));
    return pollJob(statusUrl, resultUrl);
  }

  if (job.status === "completed" && resultUrl) {
    const resultResponse = await fetch(resultUrl);
    if (!resultResponse.ok) {
      throw new Error(`Result fetch failed: ${resultResponse.status}`);
    }
    const result = await resultResponse.json();
    setOutput(result);
    setStatus("Completed");
    return result;
  }

  if (job.status === "failed") {
    setStatus("Failed");
  }

  return job;
}

async function extractInvoice() {
  const file = fileInput.files[0];
  if (!file) {
    setStatus("Choose a file first.");
    return;
  }

  const apiBaseUrl = apiBaseUrlInput.value.trim();
  if (!apiBaseUrl) {
    setStatus("Set the API base URL first.");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  const mode = modeSelect.value;
  const endpoint = getUploadEndpoint(apiBaseUrl, mode);

  extractButton.disabled = true;
  setStatus("Uploading...");
  setOutput("Processing...");

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || `Request failed with status ${response.status}`);
    }

    setOutput(data);

    if (mode === "async" && data.status_url) {
      setStatus(`Job created: ${data.job_id}`);
      await pollJob(data.status_url, data.result_url);
    } else {
      setStatus("Completed");
    }
  } catch (error) {
    setStatus("Error");
    setOutput({ error: error.message });
  } finally {
    extractButton.disabled = false;
  }
}

apiBaseUrlInput.placeholder = DEFAULT_API_BASE_URL_PLACEHOLDER;
apiBaseUrlInput.value = getApiBaseUrl();
if (!apiBaseUrlInput.value) {
  setStatus("Enter your backend API URL");
}

saveApiBaseUrlButton.addEventListener("click", () => {
  localStorage.setItem(STORAGE_KEY, apiBaseUrlInput.value.trim());
  setStatus("Saved API base URL");
});

resetApiBaseUrlButton.addEventListener("click", () => {
  localStorage.removeItem(STORAGE_KEY);
  apiBaseUrlInput.value = DEFAULT_API_BASE_URL;
  apiBaseUrlInput.placeholder = DEFAULT_API_BASE_URL_PLACEHOLDER;
  setStatus("Reset API base URL");
});

extractButton.addEventListener("click", extractInvoice);
