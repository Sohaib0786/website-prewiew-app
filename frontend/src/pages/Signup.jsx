import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import AuthLayout from "../components/AuthLayout.jsx";
import { useAuth } from "../AuthContext.jsx";

export default function Signup() {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (password.length < 8) return setError("Password must be at least 8 characters.");
    if (password !== confirm) return setError("Passwords don't match.");
    setBusy(true);
    try {
      await signup(name.trim(), email.trim(), password);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthLayout
      title="Create your account"
      subtitle="It takes a few seconds. No email verification needed."
      footer={<>Already have an account? <Link to="/login">Log in</Link></>}
    >
      <form onSubmit={onSubmit} className="form" noValidate>
        <label>
          Name
          <input value={name} onChange={(e) => setName(e.target.value)}
                 autoComplete="name" required placeholder="Your name" />
        </label>
        <label>
          Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                 autoComplete="email" required placeholder="you@example.com" />
        </label>
        <label>
          Password
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                 autoComplete="new-password" required placeholder="At least 8 characters" />
        </label>
        <label>
          Confirm password
          <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)}
                 autoComplete="new-password" required placeholder="Repeat your password" />
        </label>
        {error && <div className="alert" role="alert">{error}</div>}
        <button className="btn primary" disabled={busy || !name || !email || !password || !confirm}>
          {busy ? "Creating account…" : "Sign up"}
        </button>
      </form>
    </AuthLayout>
  );
}
