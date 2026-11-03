import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import AuthLayout from "../components/AuthLayout.jsx";
import { useAuth } from "../AuthContext.jsx";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(email.trim(), password);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthLayout
      title="Log in"
      subtitle="Welcome back. Your saved pages are waiting."
      footer={<>New here? <Link to="/signup">Create an account</Link></>}
    >
      <form onSubmit={onSubmit} className="form" noValidate>
        <label>
          Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                 autoComplete="email" required placeholder="you@example.com" />
        </label>
        <label>
          Password
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                 autoComplete="current-password" required placeholder="Your password" />
        </label>
        {error && <div className="alert" role="alert">{error}</div>}
        <button className="btn primary" disabled={busy || !email || !password}>
          {busy ? "Logging in…" : "Log in"}
        </button>
      </form>
    </AuthLayout>
  );
}
