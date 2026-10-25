
import { useState } from "react";
import asadSummaries from "./summary.json";
import CloudinaryTools from "./CloudinaryTools.jsx";
import "./App.css";

const translations = {
  en: {
    tagline: "Know before you go",
    description: "Check reported ration stock before visiting a shop.",
    search: "Search by shop ID, commodity or district...",
    clearSearch: "Clear search",
    directory: "RATION DIRECTORY",
    nearby: "Ration shops",
    shop: "shops",
    available: "Reported stock available",
    noStock: "NO REPORTED STOCK",
    warning: "Physical availability is not verified.",
    details: "View all stock details",
    noResults: "No matching shops found.",
    detailHeading: "SHOP DETAILS",
    close: "Close",
    confirm: "Please confirm with the shop before visiting.",
    footer: "Ration Seva · Transparency for every beneficiary",
    fresh: "Recently reported",
    stale: "Report may be outdated",
    freshnessUnknown: "Report date unavailable",
    freshnessNote:
      "Freshness is based on the report date, not physical stock verification.",
    source: "Source",
    district: "District",
    afso: "AFSO",
    dataTime: "Data time",
    low: "LOW STOCK",
    flags: "Data warnings",
    noFlags: "No warnings in this summary.",
    notLive: "Historical public report · Not live",
    stockSummary: "Reported stock preview",
    allCommodities: "All reported commodities",
    sourceNotice:
      "Reported quantities are not confirmation of physical stock at the shop.",
    dataError: "The shop dataset could not be read. Check src/summary.json.",
    reportDate: "Report date",
    toolsEyebrow: "MORE SERVICES",
    toolsTitle: "Tools & services",
  },
  kn: {
    tagline: "ಹೋಗುವ ಮೊದಲು ತಿಳಿಯಿರಿ",
    description: "ಅಂಗಡಿಗೆ ಹೋಗುವ ಮೊದಲು ವರದಿಯಾದ ಪಡಿತರ ದಾಸ್ತಾನು ಪರಿಶೀಲಿಸಿ.",
    search: "ಅಂಗಡಿ ID, ವಸ್ತು ಅಥವಾ ಜಿಲ್ಲೆ ಮೂಲಕ ಹುಡುಕಿ...",
    clearSearch: "ಹುಡುಕಾಟ ತೆರವುಗೊಳಿಸಿ",
    directory: "ಪಡಿತರ ಅಂಗಡಿಗಳ ಪಟ್ಟಿ",
    nearby: "ಪಡಿತರ ಅಂಗಡಿಗಳು",
    shop: "ಅಂಗಡಿಗಳು",
    available: "ವರದಿಯಲ್ಲಿ ದಾಸ್ತಾನು ಲಭ್ಯವಿದೆ",
    noStock: "ದಾಸ್ತಾನು ವರದಿಯಾಗಿಲ್ಲ",
    warning: "ನೈಜ ದಾಸ್ತಾನು ಪರಿಶೀಲಿಸಲಾಗಿಲ್ಲ.",
    details: "ಎಲ್ಲಾ ದಾಸ್ತಾನು ವಿವರಗಳು",
    noResults: "ಹೊಂದಾಣಿಕೆಯ ಅಂಗಡಿಗಳು ಕಂಡುಬಂದಿಲ್ಲ.",
    detailHeading: "ಅಂಗಡಿ ವಿವರಗಳು",
    close: "ಮುಚ್ಚಿ",
    confirm: "ಭೇಟಿ ನೀಡುವ ಮೊದಲು ಅಂಗಡಿಯಲ್ಲಿ ದೃಢಪಡಿಸಿ.",
    footer: "ರೇಷನ್ ಸೇವಾ · ಪ್ರತಿಯೊಬ್ಬ ಫಲಾನುಭವಿಗೂ ಪಾರದರ್ಶಕತೆ",
    fresh: "ಇತ್ತೀಚಿನ ವರದಿ",
    stale: "ವರದಿ ಹಳೆಯದಾಗಿರಬಹುದು",
    freshnessUnknown: "ವರದಿ ದಿನಾಂಕ ಲಭ್ಯವಿಲ್ಲ",
    freshnessNote:
      "ಇದು ವರದಿ ದಿನಾಂಕವನ್ನು ಆಧರಿಸಿದೆ; ನೈಜ ದಾಸ್ತಾನು ಪರಿಶೀಲನೆಯಲ್ಲ.",
    source: "ಮೂಲ",
    district: "ಜಿಲ್ಲೆ",
    afso: "AFSO",
    dataTime: "ಡೇಟಾ ಸಮಯ",
    low: "ಕಡಿಮೆ ದಾಸ್ತಾನು",
    flags: "ಡೇಟಾ ಎಚ್ಚರಿಕೆಗಳು",
    noFlags: "ಈ ಸಾರಾಂಶದಲ್ಲಿ ಎಚ್ಚರಿಕೆಗಳಿಲ್ಲ.",
    notLive: "ಹಿಂದಿನ ಸಾರ್ವಜನಿಕ ವರದಿ · ನೈಜ ಸಮಯದ ಡೇಟಾ ಅಲ್ಲ",
    stockSummary: "ವರದಿಯಾದ ದಾಸ್ತಾನು ಪೂರ್ವವೀಕ್ಷಣೆ",
    allCommodities: "ಎಲ್ಲಾ ವರದಿಯಾದ ವಸ್ತುಗಳು",
    sourceNotice: "ವರದಿಯಾದ ಪ್ರಮಾಣವು ನೈಜ ದಾಸ್ತಾನು ದೃಢೀಕರಣವಲ್ಲ.",
    dataError: "ಡೇಟಾಸೆಟ್ ಓದಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. src/summary.json ಪರಿಶೀಲಿಸಿ.",
    reportDate: "ವರದಿ ದಿನಾಂಕ",
    toolsEyebrow: "ಹೆಚ್ಚುವರಿ ಸೇವೆಗಳು",
    toolsTitle: "ಪರಿಕರಗಳು ಮತ್ತು ಸೇವೆಗಳು",
  },
  hi: {
    tagline: "जाने से पहले जानें",
    description: "दुकान जाने से पहले रिपोर्ट किया गया राशन स्टॉक देखें।",
    search: "दुकान ID, वस्तु या जिले से खोजें...",
    clearSearch: "खोज साफ़ करें",
    directory: "राशन दुकान सूची",
    nearby: "राशन की दुकानें",
    shop: "दुकानें",
    available: "रिपोर्ट में स्टॉक उपलब्ध",
    noStock: "स्टॉक रिपोर्ट नहीं किया गया",
    warning: "वास्तविक स्टॉक सत्यापित नहीं है।",
    details: "स्टॉक का पूरा विवरण",
    noResults: "कोई मेल खाती दुकान नहीं मिली।",
    detailHeading: "दुकान का विवरण",
    close: "बंद करें",
    confirm: "जाने से पहले दुकान से पुष्टि करें।",
    footer: "राशन सेवा · हर लाभार्थी के लिए पारदर्शिता",
    fresh: "हाल की रिपोर्ट",
    stale: "रिपोर्ट पुरानी हो सकती है",
    freshnessUnknown: "रिपोर्ट की तारीख उपलब्ध नहीं है",
    freshnessNote:
      "यह रिपोर्ट की तारीख पर आधारित है, वास्तविक स्टॉक सत्यापन पर नहीं।",
    source: "स्रोत",
    district: "जिला",
    afso: "AFSO",
    dataTime: "डेटा का समय",
    low: "कम स्टॉक",
    flags: "डेटा चेतावनियाँ",
    noFlags: "इस सारांश में कोई चेतावनी नहीं है।",
    notLive: "पुरानी सार्वजनिक रिपोर्ट · लाइव नहीं",
    stockSummary: "रिपोर्ट किए गए स्टॉक की झलक",
    allCommodities: "सभी रिपोर्ट की गई वस्तुएँ",
    sourceNotice:
      "रिपोर्ट की गई मात्रा दुकान के वास्तविक स्टॉक की पुष्टि नहीं है।",
    dataError: "डेटासेट नहीं पढ़ा जा सका। src/summary.json जाँचें।",
    reportDate: "रिपोर्ट की तारीख",
    toolsEyebrow: "अतिरिक्त सेवाएँ",
    toolsTitle: "टूल और सेवाएँ",
  },
};

const reports = Array.isArray(asadSummaries)
  ? asadSummaries
  : Array.isArray(asadSummaries?.reports)
    ? asadSummaries.reports
    : [];

function isPackaging(item) {
  const name = String(item?.commodity || "").trim().toUpperCase();

  return (
    name.includes("PACKAGING") ||
    /\b\d+\s*KG\s*BAG\b/.test(name) ||
    /\bGUNNY\b/.test(name)
  );
}

function getFreshness(reportDate, t) {
  if (!reportDate) {
    return {
      label: t.freshnessUnknown,
      className: "freshness-unknown",
    };
  }

  const parts = String(reportDate).split("-").map(Number);

  if (parts.length !== 3 || parts.some(Number.isNaN)) {
    return {
      label: t.freshnessUnknown,
      className: "freshness-unknown",
    };
  }

  const [year, month, day] = parts;
  const report = new Date(year, month - 1, day);
  const today = new Date();

  if (
    report.getFullYear() !== year ||
    report.getMonth() !== month - 1 ||
    report.getDate() !== day
  ) {
    return {
      label: t.freshnessUnknown,
      className: "freshness-unknown",
    };
  }

  report.setHours(0, 0, 0, 0);
  today.setHours(0, 0, 0, 0);

  const ageInDays = Math.floor(
    (today.getTime() - report.getTime()) / 86400000
  );

  if (ageInDays >= 0 && ageInDays <= 1) {
    return { label: t.fresh, className: "freshness-fresh" };
  }

  return { label: t.stale, className: "freshness-stale" };
}

function formatReportDate(date) {
  if (!date) return "—";

  const parsed = new Date(`${date}T00:00:00`);

  if (Number.isNaN(parsed.getTime())) return date;

  return parsed.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function getCommodityStatus(item) {
  const closing = Number(item?.closing ?? 0);
  const existingStatus = String(item?.status || "").toUpperCase();

  if (closing <= 0) return "OUT_OF_STOCK";
  if (existingStatus === "LOW") return "LOW";

  if (
    String(item?.commodity || "").trim().toLowerCase() === "frice" &&
    closing <= 10
  ) {
    return "LOW";
  }

  return "AVAILABLE";
}

function getSafeFlags(report) {
  return (Array.isArray(report?.flags) ? report.flags : []).map((flag) => {
    const flagType = String(flag?.flag || "").toUpperCase();

    if (flagType === "LOW_STOCK") {
      const item = (report.commodities || []).find(
        (commodity) =>
          String(commodity.commodity).toLowerCase() ===
          String(flag.commodity).toLowerCase()
      );

      const closing = Number(item?.closing);

      return {
        ...flag,
        message: Number.isFinite(closing)
          ? `Reported closing balance: ${closing.toLocaleString("en-IN")} ${
              item?.unit || ""
            }. This is a prototype low-stock warning, not an official threshold.`
          : "A low-stock warning appears in the source summary. Verify the reported quantity before relying on it.",
      };
    }

    if (flagType === "FRACTIONAL_PACKETS") {
      return {
        ...flag,
        message:
          "The reported quantity is not a whole number. Verify the source unit and quantity before interpreting it as a packet count.",
      };
    }

    return flag;
  });
}

function CommodityCard({ item, t }) {
  const closing = Number(item?.closing ?? 0);
  const status = getCommodityStatus(item);

  const statusLabel =
    status === "LOW"
      ? t.low
      : status === "OUT_OF_STOCK"
        ? t.noStock
        : t.available;

  return (
    <div className="commodity">
      <span>{item?.commodity || "Unknown commodity"}</span>

      <strong>
        {Number.isFinite(closing)
          ? closing.toLocaleString("en-IN")
          : "—"}{" "}
        {item?.unit || ""}
      </strong>

      <span
        className={`status ${
          status === "LOW" || status === "OUT_OF_STOCK" ? "stock-low" : ""
        }`}
      >
        {statusLabel}
      </span>
    </div>
  );
}

function StockFreshness({ reportDate, t }) {
  const freshness = getFreshness(reportDate, t);

  return (
    <div className={`freshness ${freshness.className}`}>
      <span className="freshness-dot" />
      <span>{freshness.label}</span>
    </div>
  );
}

function ShopDetails({ report, onClose, t }) {
  const commodities = Array.isArray(report?.commodities)
    ? report.commodities.filter((item) => !isPackaging(item))
    : [];

  const flags = getSafeFlags(report);

  return (
    <section className="details-panel" aria-live="polite">
      <div className="details-heading">
        <div>
          <p className="eyebrow">{t.detailHeading}</p>
          <h2>FPS {report.fps_id}</h2>
          <p className="shop-meta">
            {report.district || "—"} · {t.afso}: {report.afso || "—"}
          </p>
        </div>

        <button
          type="button"
          className="close-button"
          onClick={onClose}
        >
          ✕ {t.close}
        </button>
      </div>

      <p className="demo-notice">ⓘ {t.notLive}</p>
      <p className="stock-label">{t.allCommodities}</p>

      <div className="commodities details-commodities">
        {commodities.map((item, index) => (
          <CommodityCard
            key={`${item.commodity}-${index}`}
            item={item}
            t={t}
          />
        ))}
      </div>

      <h3>{t.flags}</h3>

      {flags.length > 0 ? (
        flags.map((flag, index) => (
          <p
            className="warning"
            key={`${flag.flag}-${flag.commodity}-${index}`}
          >
            <strong>{flag.commodity}: </strong>
            {flag.message}
          </p>
        ))
      ) : (
        <p className="muted-copy">{t.noFlags}</p>
      )}

      <p className="updated">
        {t.reportDate}: {formatReportDate(report.report_date)}
      </p>

      <p className="updated">
        {t.dataTime}: {report.data_time || "—"}
      </p>

      <p className="updated">
        {t.source}: {report.source || "Public stock report"}
      </p>

      <StockFreshness reportDate={report.report_date} t={t} />

      <p className="freshness-note">{t.freshnessNote}</p>

      <p className="warning">
        ⓘ {t.warning} {t.confirm}
      </p>
    </section>
  );
}

export default function App() {
  const [language, setLanguage] = useState("en");
  const [query, setQuery] = useState("");
  const [selectedShop, setSelectedShop] = useState(null);

  const t = translations[language];

  const filteredReports = reports.filter((report) => {
    const commodities = Array.isArray(report?.commodities)
      ? report.commodities
      : [];

    const searchable = [
      report?.fps_id,
      report?.district,
      report?.afso,
      ...commodities
        .filter((item) => !isPackaging(item))
        .map((item) => item.commodity),
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();

    return searchable.includes(query.trim().toLowerCase());
  });

  return (
    <main className="app">
      <header className="topbar">
        <a className="brand" href="#" aria-label="Ration Seva home">
          <span className="brand-icon">🌾</span>
          <span>Ration Seva</span>
        </a>

        <fieldset className="language-picker">
          <legend>Language / ಭಾಷೆ / भाषा</legend>

          {[
            ["en", "English"],
            ["kn", "ಕನ್ನಡ"],
            ["hi", "हिंदी"],
          ].map(([code, label]) => (
            <label key={code}>
              <input
                type="radio"
                name="language"
                value={code}
                checked={language === code}
                onChange={() => setLanguage(code)}
              />
              {label}
            </label>
          ))}
        </fieldset>
      </header>

      <section className="hero">
        <p className="eyebrow">PUBLIC DISTRIBUTION · PDS</p>
        <h1>{t.tagline}</h1>
        <p className="hero-copy">{t.description}</p>

        <div className="search-wrap">
          <span className="search-icon" aria-hidden="true">
            ⌕
          </span>

          <input
            className="search"
            type="search"
            placeholder={t.search}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            aria-label={t.search}
          />

          {query.trim() !== "" && (
            <button
              type="button"
              className="clear-search"
              onClick={() => setQuery("")}
            >
              {t.clearSearch}
            </button>
          )}
        </div>
      </section>

      {/* Tools now appear before the shop directory. */}
      <section className="tools-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">{t.toolsEyebrow}</p>
            <h2>{t.toolsTitle}</h2>
          </div>
        </div>

        <CloudinaryTools />
      </section>

      <section className="shop-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">{t.directory}</p>
            <h2>{t.nearby}</h2>
          </div>

          <span className="shop-count">
            {filteredReports.length} {t.shop}
          </span>
        </div>

        <p className="demo-notice">ⓘ {t.notLive}</p>

        {reports.length === 0 ? (
          <p className="warning">{t.dataError}</p>
        ) : filteredReports.length === 0 ? (
          <p className="empty">{t.noResults}</p>
        ) : (
          <div className="shop-grid">
            {filteredReports.map((report, reportIndex) => {
              const commodities = Array.isArray(report?.commodities)
                ? report.commodities
                : [];

              const nonzeroCommodities = commodities.filter(
                (item) =>
                  !isPackaging(item) && Number(item.closing) > 0
              );

              const previewCommodities = nonzeroCommodities.slice(0, 4);
              const remainingCount = Math.max(
                0,
                nonzeroCommodities.length - previewCommodities.length
              );

              return (
                <article
                  className="shop-card"
                  key={`${report.fps_id}-${report.report_date || reportIndex}`}
                >
                  <div className="shop-card-top">
                    <span className="shop-icon" aria-hidden="true">
                      🏪
                    </span>
                    <span className="shop-id-label">
                      FPS {report.fps_id || "Unknown"}
                    </span>
                  </div>

                  <h3>{report.district || "Ration shop"}</h3>

                  <p className="shop-meta">
                    {t.district}: {report.district || "—"} · {t.afso}:{" "}
                    {report.afso || "—"}
                  </p>

                  <p className="stock-label">{t.stockSummary}</p>

                  {previewCommodities.length > 0 ? (
                    <div className="commodities">
                      {previewCommodities.map((item, index) => (
                        <CommodityCard
                          key={`${item.commodity}-${index}`}
                          item={item}
                          t={t}
                        />
                      ))}
                    </div>
                  ) : (
                    <p className="empty-stock">{t.noStock}</p>
                  )}

                  {remainingCount > 0 && (
                    <p className="more-stock">
                      +{remainingCount} more commodities in shop details
                    </p>
                  )}

                  <p className="updated">
                    {t.reportDate}: {formatReportDate(report.report_date)}
                  </p>

                  <StockFreshness
                    reportDate={report.report_date}
                    t={t}
                  />

                  <p className="warning">ⓘ {t.sourceNotice}</p>

                  <button
                    type="button"
                    className="details-button"
                    onClick={() => setSelectedShop(report)}
                  >
                    {t.details} <span aria-hidden="true">→</span>
                  </button>
                </article>
              );
            })}
          </div>
        )}
      </section>

      {selectedShop && (
        <ShopDetails
          report={selectedShop}
          onClose={() => setSelectedShop(null)}
          t={t}
        />
      )}

      <footer>{t.footer}</footer>
    </main>
  );
}
