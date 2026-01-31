import { useState, type FormEvent, useMemo } from 'react';
import { useAuth } from '../contexts';

interface RegisterPageProps {
  onSwitchToLogin: () => void;
}

interface PasswordStrength {
  score: number;
  checks: {
    length: boolean;
    uppercase: boolean;
    lowercase: boolean;
    digit: boolean;
    special: boolean;
  };
}

function checkPasswordStrength(password: string): PasswordStrength {
  const checks = {
    length: password.length >= 12,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    digit: /\d/.test(password),
    special: /[!@#$%^&*(),.?":{}|<>]/.test(password),
  };

  const score = Object.values(checks).filter(Boolean).length;
  return { score, checks };
}

export function RegisterPage({ onSwitchToLogin }: RegisterPageProps) {
  const { register } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const passwordStrength = useMemo(() => checkPasswordStrength(password), [password]);
  const passwordsMatch = password === confirmPassword;
  const isPasswordValid = passwordStrength.score === 5;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    if (!passwordsMatch) {
      setError('Passwords do not match');
      return;
    }

    if (!isPasswordValid) {
      setError('Password does not meet requirements');
      return;
    }

    setIsLoading(true);

    try {
      await register({ email, password });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  const strengthLabel = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong'][passwordStrength.score - 1] || '';
  const strengthClass = ['very-weak', 'weak', 'fair', 'good', 'strong'][passwordStrength.score - 1] || '';

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h2>Create Account</h2>
        <p className="auth-subtitle">Secure your secrets today</p>

        <form onSubmit={handleSubmit} className="auth-form">
          {error && <div className="error-message">{error}</div>}

          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              autoComplete="email"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              required
              autoComplete="new-password"
            />
            {password && (
              <div className="password-strength">
                <div className={`strength-bar ${strengthClass}`}>
                  <div style={{ width: `${(passwordStrength.score / 5) * 100}%` }} />
                </div>
                <span className={`strength-label ${strengthClass}`}>{strengthLabel}</span>
              </div>
            )}
          </div>

          <div className="password-requirements">
            <p className={passwordStrength.checks.length ? 'met' : ''}>
              ✓ At least 12 characters
            </p>
            <p className={passwordStrength.checks.uppercase ? 'met' : ''}>
              ✓ One uppercase letter
            </p>
            <p className={passwordStrength.checks.lowercase ? 'met' : ''}>
              ✓ One lowercase letter
            </p>
            <p className={passwordStrength.checks.digit ? 'met' : ''}>
              ✓ One digit
            </p>
            <p className={passwordStrength.checks.special ? 'met' : ''}>
              ✓ One special character
            </p>
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="••••••••••••"
              required
              autoComplete="new-password"
              className={confirmPassword && !passwordsMatch ? 'error' : ''}
            />
            {confirmPassword && !passwordsMatch && (
              <span className="field-error">Passwords do not match</span>
            )}
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={isLoading || !isPasswordValid || !passwordsMatch}
          >
            {isLoading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        <p className="auth-switch">
          Already have an account?{' '}
          <button type="button" onClick={onSwitchToLogin} className="link-button">
            Sign in
          </button>
        </p>
      </div>
    </div>
  );
}
