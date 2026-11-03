import { useEffect, useState } from "react";
import { api } from "../api.js";
import { useAuth } from "../AuthContext.jsx";
import PreviewCard from "../components/PreviewCard.jsx";

const TEST_URL =
  "https://www.justdial.com/Hyderabad/Dr-Sarita-Rao-Tx-Hospitals-Near-Masjid-Uppal-Bus-Stand-Bharath-Nagar-Colony-Uppal/040PXX40-XX40-231215200040-Y2E1_BZDET";

export default function Dashboard() {
  const { user, logout } = useAuth();
  const [url, setUrl] = useState("");
  const [sites, setSites] = useState([]);
  const [latest, setLatest] = useState(null);
  const [listLoading, setListLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .listSites()
      .then(setSites)
      .catch((e) => setError(e.message))
      .finally(() => setListLoading(false));
  }, []);

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!url.trim() || busy) return;
    setError("");
    setLatest(null);
    setBusy(true);
    try {
      const site = await api.addSite(url.trim());
      setLatest(site);
      setSites((prev) => [site, ...prev]);
      setUrl("");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const onDelete = async (site) => {
    if (!window.confirm(`Delete the saved preview for ${site.url}?`)) return;
    try {
      await api.deleteSite(site.id);
      setSites((prev) => prev.filter((s) => s.id !== site.id));
      setLatest((prev) => (prev && prev.id === site.id ? null : prev));
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand dark">Site Shelf</div>
        <div className="topbar-right">
          <span className="muted">{user.name}</span>
          <button className="btn ghost" onClick={logout}>Log out</button>
        </div>
      </header>

      <main className="container">
        <section className="hero">
          <h1>Save a page with a picture of it</h1>
          <form className="urlbar" onSubmit={onSubmit}>
            <input
              type="text"
              inputMode="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Paste a website address, e.g. https://example.com"
              aria-label="Website URL"
              disabled={busy}
              autoFocus
            />
            <button className="btn primary" disabled={busy || !url.trim()}>
              {busy ? "Capturing…" : "Preview & save"}
            </button>
          </form>
          <div className="hero-hint">
            <button type="button" className="btn link" onClick={() => setUrl(TEST_URL)} disabled={busy}>
              Fill in the test URL
            </button>
          </div>

          {error && <div className="alert" role="alert">{error}</div>}

          {busy && (
            <div className="working" role="status">
              <div className="spinner" />
              <div>
                <strong>Capturing the page…</strong>
                <div className="muted small">Some sites take up to 30 seconds to load.</div>
              </div>
            </div>
          )}

          {latest && !busy && (
            <div className="latest">
              <div className="latest-label">Saved just now</div>
              <PreviewCard site={latest} large />
            </div>
          )}
        </section>

        <section className="library">
          <div className="section-head">
            <h2>Saved pages</h2>
            <span className="muted">{sites.length} saved</span>
          </div>

          {listLoading ? (
            <div className="muted">Loading your saved pages…</div>
          ) : sites.length === 0 ? (
            <div className="empty">
              <strong>Nothing saved yet.</strong>
              <span>Paste a website address above and it will show up here with a preview.</span>
            </div>
          ) : (
            <div className="grid">
              {sites.map((s) => (
                <PreviewCard key={s.id} site={s} onDelete={onDelete} />
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
