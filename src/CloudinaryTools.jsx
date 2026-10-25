
import { useState } from "react";

const API_BASE = (
  import.meta.env.VITE_API_URL || "https://ration-seva.onrender.com"
).replace(/\/+$/, "");

export default function CloudinaryTools() {
  const [tool, setTool] = useState("proof");
  const [fpsId, setFpsId] = useState("");
  const [event, setEvent] = useState("stock_arrival");
  const [image, setImage] = useState(null);
  const [expectedKg, setExpectedKg] = useState("70");
  const [commodity, setCommodity] = useState("Rice");
  const [tolerance, setTolerance] = useState("0.1");
  const [language, setLanguage] = useState("en");
  const [timings, setTimings] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  function changeTool(nextTool) {
    setTool(nextTool);
    setError("");
    setResult(null);
    setImage(null);
  }

  async function submit(eventObject) {
    eventObject.preventDefault();
    setError("");
    setResult(null);

    if (!fpsId.trim()) {
      setError("Enter the ration shop FPS ID.");
      return;
    }

    if (tool !== "notice" && !image) {
      setError("Choose an image first.");
      return;
    }

    const form = new FormData();
    form.append("fps_id", fpsId.trim());

    if (tool === "proof") {
      form.append("image", image);
      form.append("event", event);
    } else if (tool === "scale") {
      const weight = Number(expectedKg);
      const allowedDifference = Number(tolerance);

      if (!Number.isFinite(weight) || weight <= 0) {
        setError("Expected weight must be greater than zero.");
        return;
      }

      if (
        !Number.isFinite(allowedDifference) ||
        allowedDifference < 0
      ) {
        setError("Tolerance cannot be negative.");
        return;
      }

      form.append("image", image);
      form.append("expected_kg", String(weight));
      form.append("commodity", commodity);
      form.append("tolerance_kg", String(allowedDifference));
    } else {
      form.append("language", language);

      if (timings.trim()) {
        form.append("timings", timings.trim());
      }
    }

    setLoading(true);

    try {
      const endpoint = tool === "scale" ? "scale-check" : tool;

      const response = await fetch(`${API_BASE}/${endpoint}`, {
        method: "POST",
        body: form,
      });

      const body = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          body.detail || `Request failed (${response.status})`
        );
      }

      setResult(body);
    } catch (err) {
      console.error("RationSeva API request failed:", err);

      setError(
        err.message === "Failed to fetch"
          ? "Could not connect to the backend. Check the browser console for the network or CORS error."
          : err.message || "Request failed. Check the backend connection."
      );
    } finally {
      setLoading(false);
    }
  }

  function renderResult(value, path = "result") {
    if (value == null) return <span>—</span>;

    if (typeof value === "object") {
      if (Array.isArray(value)) {
        return (
          <ul>
            {value.map((child, index) => (
              <li key={`${path}.${index}`}>
                {renderResult(child, `${path}.${index}`)}
              </li>
            ))}
          </ul>
        );
      }

      return (
        <div className="api-result-nested">
          {Object.entries(value).map(([key, child]) => (
            <div key={`${path}.${key}`} className="api-result-row">
              <strong>{key.replaceAll("_", " ")}: </strong>
              {renderResult(child, `${path}.${key}`)}
            </div>
          ))}
        </div>
      );
    }

    if (
      typeof value === "string" &&
      /^https?:\/\/\S+$/i.test(value)
    ) {
      const isImage =
        /\.(png|jpe?g|webp|gif)(\?.*)?$/i.test(value);

      return (
        <span>
          <a href={value} target="_blank" rel="noreferrer">
            {isImage ? "Open image" : value}
          </a>
          {isImage && (
            <img
              src={value}
              alt="Backend-generated result"
              style={{
                display: "block",
                maxWidth: "100%",
                maxHeight: 320,
                marginTop: 8,
              }}
            />
          )}
        </span>
      );
    }

    return <span>{String(value)}</span>;
  }

  const scaleVerdict =
    tool === "scale" && result
      ? String(result.verdict || "").toUpperCase()
      : "";

  return (
    <section
      className="cloudinary-tools"
      aria-labelledby="tools-heading"
    >
      <p className="eyebrow">PHOTO TOOLS</p>

      <h2 id="tools-heading">RationSeva support tools</h2>

      <p>
        Upload evidence or generate a stock notice. Results depend
        on the submitted image and backend processing; they do not
        independently verify physical stock.
      </p>

      <div
        className="api-tool-tabs"
        role="group"
        aria-label="Choose a tool"
      >
        <button
          type="button"
          aria-pressed={tool === "proof"}
          onClick={() => changeTool("proof")}
        >
          Photo proof
        </button>

        <button
          type="button"
          aria-pressed={tool === "scale"}
          onClick={() => changeTool("scale")}
        >
          Weighing check
        </button>

        <button
          type="button"
          aria-pressed={tool === "notice"}
          onClick={() => changeTool("notice")}
        >
          Stock notice
        </button>
      </div>

      <form onSubmit={submit} className="api-tool-form">
        <label>
          FPS shop ID
          <input
            value={fpsId}
            onChange={(e) => setFpsId(e.target.value)}
            placeholder="e.g. 0313044"
            required
          />
        </label>

        {tool === "proof" && (
          <>
            <label>
              Photo event
              <select
                value={event}
                onChange={(e) => setEvent(e.target.value)}
              >
                <option value="stock_arrival">Stock arrival</option>
                <option value="doorstep_delivery">
                  Doorstep delivery
                </option>
                <option value="weighing">Weighing</option>
                <option value="complaint">Complaint evidence</option>
              </select>
            </label>

            <label>
              Evidence photo
              <input
                type="file"
                accept="image/*"
                capture="environment"
                onChange={(e) =>
                  setImage(e.target.files?.[0] || null)
                }
                required
              />
            </label>
          </>
        )}

        {tool === "scale" && (
          <>
            <label>
              Commodity
              <input
                value={commodity}
                onChange={(e) => setCommodity(e.target.value)}
                required
              />
            </label>

            <label>
              Expected weight (kg)
              <input
                type="number"
                min="0.01"
                step="any"
                value={expectedKg}
                onChange={(e) => setExpectedKg(e.target.value)}
                required
              />
            </label>

            <label>
              Allowed difference (kg)
              <input
                type="number"
                min="0"
                step="any"
                value={tolerance}
                onChange={(e) => setTolerance(e.target.value)}
                required
              />
            </label>

            <label>
              Scale photo
              <input
                type="file"
                accept="image/*"
                capture="environment"
                onChange={(e) =>
                  setImage(e.target.files?.[0] || null)
                }
                required
              />
            </label>
          </>
        )}

        {tool === "notice" && (
          <>
            <label>
              Notice language
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
              >
                <option value="en">English</option>
                <option value="hi">Hindi</option>
                <option value="te">Telugu</option>
              </select>
            </label>

            <label>
              Shop timings (optional)
              <input
                maxLength={40}
                value={timings}
                onChange={(e) => setTimings(e.target.value)}
                placeholder="e.g. 9 AM – 5 PM"
              />
            </label>
          </>
        )}

        <button type="submit" disabled={loading}>
          {loading
            ? "Processing…"
            : tool === "notice"
              ? "Generate notice"
              : "Upload and process"}
        </button>
      </form>

      {error && (
        <p role="alert" className="warning">
          {error}
        </p>
      )}

      {result && (
        <div className="api-result" aria-live="polite">
          {tool === "scale" && scaleVerdict === "SHORT_WEIGHT" ? (
            <>
              <h3>Review weighing result</h3>
              <p>
                The backend reported a possible weight shortage.
                Review the reading and evidence carefully before
                deciding what to do next.
              </p>

              {result.message && <p>{result.message}</p>}

              <p>
                <strong>Expected weight:</strong>{" "}
                {result.expected_kg ?? expectedKg} kg
              </p>

              <p>
                <strong>Detected reading:</strong>{" "}
                {result.reading_kg ?? "Unavailable"} kg
              </p>

              {result.stamped_url && (
                <p>
                  <a
                    href={result.stamped_url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    View evidence image
                  </a>
                </p>
              )}

              <p>
                No complaint has been filed by this result. The
                current backend response does not confirm complaint
                submission.
              </p>
            </>
          ) : (
            <>
              <h3>
                {tool === "scale" ? "Weighing result" : "Backend response"}
              </h3>
              {tool === "scale" && result.message && (
                <p>{result.message}</p>
              )}
            </>
          )}

          {renderResult(result)}

          <details>
            <summary>View raw response</summary>
            <pre
              style={{
                whiteSpace: "pre-wrap",
                overflowWrap: "anywhere",
              }}
            >
              {JSON.stringify(result, null, 2)}
            </pre>
          </details>
        </div>
      )}
    </section>
  );
}
