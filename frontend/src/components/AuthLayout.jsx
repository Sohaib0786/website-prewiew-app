export default function AuthLayout({ title, subtitle, children, footer }) {
  return (
    <div className="auth">
      <aside className="auth-side">
        <div className="brand">Site Shelf</div>
        <div className="frame frame-hero" aria-hidden="true">
          <div className="frame-bar">
            <span /><span /><span />
            <div className="frame-url">example.com/your-saved-page</div>
          </div>
          <div className="frame-body">
            <div className="ghost g1" />
            <div className="ghost g2" />
            <div className="ghost g3" />
            <div className="ghost g4" />
          </div>
        </div>
        <p className="auth-pitch">
          Paste a link. Get a picture of the page. Come back to it whenever you need.
        </p>
      </aside>

      <main className="auth-main">
        <div className="auth-card">
          <h1>{title}</h1>
          <p className="muted">{subtitle}</p>
          {children}
          <div className="auth-footer">{footer}</div>
        </div>
      </main>
    </div>
  );
}
