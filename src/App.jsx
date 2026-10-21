
import { useEffect, useState } from "react";
import { supabase } from "./supabaseClient";
import "./App.css";

const translations = {
  en: {
    tagline: "Know before you go",
    description: "Check reported ration stock before visiting a shop.",
    search: "Search by shop name, ID or location...",
    directory: "RATION DIRECTORY",
    nearby: "Ration shops",
    shop: "shops",
    reported: "Government-reported stock",
    updated: "Last updated",
    available: "Reported stock available",
    warning: "Physical availability is not verified.",
    details: "View shop details",
    sample: "DEMO DATA — NOT LIVE GOVERNMENT DATA",
    rice: "Rice",
    wheat: "Wheat",
    kg: "kg",
    noResults: "No matching shops found.",
    detailHeading: "SHOP DETAILS",
    close: "Close",
    confirm: "Please confirm with the shop before visiting.",
    footer: "Ration Seva · Transparency for every beneficiary",
    location: "Sample location",
    fresh: "Recently updated (demo)",
    stale: "Update may be outdated",
    freshnessUnknown: "Update date unavailable",
    freshnessNote:
      "Freshness is based on the report date, not physical stock verification.",
  },
  kn: {
    tagline: "ಹೋಗುವ ಮೊದಲು ತಿಳಿಯಿರಿ",
    description: "ಅಂಗಡಿಗೆ ಹೋಗುವ ಮೊದಲು ವರದಿಯಾದ ಪಡಿತರ ದಾಸ್ತಾನು ಪರಿಶೀಲಿಸಿ.",
    search: "ಅಂಗಡಿ ಹೆಸರು, ID ಅಥವಾ ಸ್ಥಳದ ಮೂಲಕ ಹುಡುಕಿ...",
    directory: "ಪಡಿತರ ಅಂಗಡಿಗಳ ಪಟ್ಟಿ",
    nearby: "ಪಡಿತರ ಅಂಗಡಿಗಳು",
    shop: "ಅಂಗಡಿಗಳು",
    reported: "ಸರ್ಕಾರ ವರದಿ ಮಾಡಿದ ದಾಸ್ತಾನು",
    updated: "ಕೊನೆಯ ನವೀಕರಣ",
    available: "ವರದಿಯ ಪ್ರಕಾರ ದಾಸ್ತಾನು ಲಭ್ಯವಿದೆ",
    warning: "ಭೌತಿಕ ಲಭ್ಯತೆಯನ್ನು ಪರಿಶೀಲಿಸಲಾಗಿಲ್ಲ.",
    details: "ಅಂಗಡಿ ವಿವರಗಳು",
    sample: "ಡೆಮೋ ಡೇಟಾ — ನೈಜ ಸರ್ಕಾರಿ ಡೇಟಾ ಅಲ್ಲ",
    rice: "ಅಕ್ಕಿ",
    wheat: "ಗೋಧಿ",
    kg: "ಕೆಜಿ",
    noResults: "ಹೊಂದಾಣಿಕೆಯ ಅಂಗಡಿಗಳು ಕಂಡುಬಂದಿಲ್ಲ.",
    detailHeading: "ಅಂಗಡಿ ವಿವರಗಳು",
    close: "ಮುಚ್ಚಿ",
    confirm: "ಹೋಗುವ ಮೊದಲು ಅಂಗಡಿಯೊಂದಿಗೆ ಖಚಿತಪಡಿಸಿಕೊಳ್ಳಿ.",
    footer: "ರೇಷನ್ ಸೇವಾ · ಪ್ರತಿಯೊಬ್ಬ ಫಲಾನುಭವಿಗೂ ಪಾರದರ್ಶಕತೆ",
    location: "ಮಾದರಿ ಸ್ಥಳ",
    fresh: "ಇತ್ತೀಚೆಗೆ ನವೀಕರಿಸಲಾಗಿದೆ (ಡೆಮೋ)",
    stale: "ನವೀಕರಣ ಹಳೆಯದಾಗಿರಬಹುದು",
    freshnessUnknown: "ನವೀಕರಣದ ದಿನಾಂಕ ಲಭ್ಯವಿಲ್ಲ",
    freshnessNote:
      "ಇದು ವರದಿಯ ದಿನಾಂಕವನ್ನು ಆಧರಿಸಿದೆ; ನೈಜ ದಾಸ್ತಾನು ಪರಿಶೀಲನೆಯಲ್ಲ.",
  },
  hi: {
    tagline: "जाने से पहले जानें",
    description: "दुकान जाने से पहले रिपोर्ट किया गया राशन स्टॉक देखें।",
    search: "दुकान के नाम, ID या स्थान से खोजें...",
    directory: "राशन दुकान सूची",
    nearby: "राशन की दुकानें",
    shop: "दुकानें",
    reported: "सरकार द्वारा रिपोर्ट किया गया स्टॉक",
    updated: "अंतिम अपडेट",
    available: "रिपोर्ट के अनुसार स्टॉक उपलब्ध है",
    warning: "वास्तविक उपलब्धता सत्यापित नहीं है।",
    details: "दुकान का विवरण देखें",
    sample: "डेमो डेटा — लाइव सरकारी डेटा नहीं",
    rice: "चावल",
    wheat: "गेहूँ",
    kg: "किग्रा",
    noResults: "कोई मेल खाती दुकान नहीं मिली।",
    detailHeading: "दुकान का विवरण",
    close: "बंद करें",
    confirm: "जाने से पहले दुकान से पुष्टि करें।",
    footer: "राशन सेवा · हर लाभार्थी के लिए पारदर्शिता",
    location: "नमूना स्थान",
    fresh: "हाल ही में अपडेट किया गया (डेमो)",
    stale: "अपडेट पुराना हो सकता है",
    freshnessUnknown: "अपडेट की तारीख उपलब्ध नहीं है",
    freshnessNote:
      "यह रिपोर्ट की तारीख पर आधारित है, वास्तविक स्टॉक सत्यापन पर नहीं।",
  },
};

const shops = [
  {
    id: "DEMO-001",
    name: "Demo Ration Shop 001",
    area: "Sample location",
    rice: 250,
    wheat: 80,
    updated: "20 Oct 2026",
  },
  {
    id: "DEMO-002",
    name: "Demo Ration Shop 002",
    area: "Sample location",
    rice: 120,
    wheat: 45,
    updated: "19 Oct 2026",
  },
];

function getFreshness(updated, t) {
  if (!updated) {
    return {
      label: t.freshnessUnknown,
      className: "freshness-unknown",
    };
  }

  const date = new Date(`${updated} 00:00:00`);

  if (Number.isNaN(date.getTime())) {
    return {
      label: t.freshnessUnknown,
      className: "freshness-unknown",
    };
  }

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const ageInDays = Math.floor(
    (today.getTime() - date.getTime()) / (1000 * 60 * 60 * 24)
  );

  if (ageInDays >= 0 && ageInDays <= 1) {
    return {
      label: t.fresh,
      className: "freshness-fresh",
    };
  }

  return {
    label: t.stale,
    className: "freshness-stale",
  };
}

function StockFreshness({ shop, t }) {
  const freshness = getFreshness(shop.updated, t);

  return (
    <div className={`freshness ${freshness.className}`}>
      <span className="freshness-dot" />
      <span>{freshness.label}</span>
    </div>
  );
}

export default function App() {
  const [language, setLanguage] = useState("en");
  const [query, setQuery] = useState("");
  const [selectedShop, setSelectedShop] = useState(null);

  // Connection test only. The demo shops remain unchanged.
  useEffect(() => {
    let cancelled = false;

    async function testSupabase() {
      const { data, error } = await supabase
        .from("stock_reports")
        .select("id")
        .limit(5);

      if (cancelled) return;

      if (error) {
        console.error("Supabase test failed:", error.message);
        return;
      }

      console.log("Supabase connection successful!");
      console.log("Stock reports:", data);
    }

    testSupabase().catch((error) => {
      if (!cancelled) {
        console.error("Supabase unexpected error:", error);
      }
    });

    return () => {
      cancelled = true;
    };
  }, []);

  const t = translations[language];

  const filteredShops = shops.filter((shop) =>
    `${shop.name} ${shop.id} ${shop.area}`
      .toLowerCase()
      .includes(query.toLowerCase().trim())
  );

  return (
    <main className="app">
      <header className="topbar">
        <a className="brand" href="#">
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
        <p className="eyebrow">PUBLIC DISTRIBUTION • PDS</p>
        <h1>{t.tagline}</h1>
        <p className="hero-copy">{t.description}</p>

        <input
          className="search"
          type="search"
          placeholder={t.search}
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          aria-label={t.search}
        />
      </section>

      <section className="shop-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">{t.directory}</p>
            <h2>{t.nearby}</h2>
          </div>

          <span className="shop-count">
            {filteredShops.length} {t.shop}
          </span>
        </div>

        <p className="demo-notice">ⓘ {t.sample}</p>

        <div className="shop-grid">
          {filteredShops.map((shop) => (
            <article className="shop-card" key={shop.id}>
              <div className="shop-card-top">
                <span className="shop-icon">🏪</span>
                <span className="status">{t.available}</span>
              </div>

              <h3>{shop.name}</h3>

              <p className="shop-meta">
                {shop.id} · {t.location}
              </p>

              <p className="stock-label">{t.reported}</p>

              <div className="commodities">
                <div className="commodity">
                  <span>🌾 {t.rice}</span>
                  <strong>
                    {shop.rice} {t.kg}
                  </strong>
                </div>

                <div className="commodity">
                  <span>🌾 {t.wheat}</span>
                  <strong>
                    {shop.wheat} {t.kg}
                  </strong>
                </div>
              </div>

              <p className="updated">
                {t.updated}: {shop.updated}
              </p>

              <StockFreshness shop={shop} t={t} />

              <p className="warning">ⓘ {t.warning}</p>

              <button
                className="details-button"
                onClick={() => setSelectedShop(shop)}
              >
                {t.details} →
              </button>
            </article>
          ))}

          {filteredShops.length === 0 && (
            <p className="empty">{t.noResults}</p>
          )}
        </div>
      </section>

      {selectedShop && (
        <section className="details-panel" aria-live="polite">
          <div className="details-heading">
            <div>
              <p className="eyebrow">{t.detailHeading}</p>
              <h2>{selectedShop.name}</h2>

              <p className="shop-meta">
                {selectedShop.id} · {t.location}
              </p>
            </div>

            <button
              className="close-button"
              onClick={() => setSelectedShop(null)}
            >
              ✕ {t.close}
            </button>
          </div>

          <p className="stock-label">{t.reported}</p>

          <div className="commodities">
            <div className="commodity">
              <span>🌾 {t.rice}</span>
              <strong>
                {selectedShop.rice} {t.kg}
              </strong>
            </div>

            <div className="commodity">
              <span>🌾 {t.wheat}</span>
              <strong>
                {selectedShop.wheat} {t.kg}
              </strong>
            </div>
          </div>

          <p className="updated">
            {t.updated}: {selectedShop.updated}
          </p>

          <StockFreshness shop={selectedShop} t={t} />

          <p className="freshness-note">{t.freshnessNote}</p>

          <p className="warning">
            ⓘ {t.warning} {t.confirm}
          </p>

          <p className="demo-notice">ⓘ {t.sample}</p>
        </section>
      )}

      <footer>{t.footer}</footer>
    </main>
  );
}
