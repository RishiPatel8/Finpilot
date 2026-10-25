import React, { useState } from 'react';
import { X, Lock, Mail, User as UserIcon, Briefcase, Link as LinkIcon, ShieldCheck, Zap } from 'lucide-react';
import { apiRequest, setAuthToken } from '../services/api';
import { signInWithGoogle, isFirebaseConfigured } from '../services/firebase';
import { User, UserRole } from '../types';
import { Button } from './ui';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (user: User) => void;
  initialMode?: 'login' | 'register';
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  initialMode = 'login',
}) => {
  const [isLogin, setIsLogin] = useState(initialMode !== 'register');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState<UserRole>('salaried');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Sync mode when initialMode changes or modal opens
  React.useEffect(() => {
    setIsLogin(initialMode !== 'register');
    setError(null);
  }, [initialMode, isOpen]);

  // Explicit Account Linking State
  const [linkingPendingToken, setLinkingPendingToken] = useState<string | null>(null);
  const [linkPassword, setLinkPassword] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      if (isLogin) {
        const res = await apiRequest<{ access_token: string; user: User }>('/auth/login', {
          method: 'POST',
          body: JSON.stringify({ email, password }),
        });
        setAuthToken(res.access_token);
        onSuccess(res.user);
        onClose();
      } else {
        const res = await apiRequest<{ access_token: string; user: User }>('/auth/register', {
          method: 'POST',
          body: JSON.stringify({
            email,
            password,
            full_name: fullName,
            role,
          }),
        });
        setAuthToken(res.access_token);
        onSuccess(res.user);
        onClose();
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setError(null);
    setIsLoading(true);
    try {
      const idToken = await signInWithGoogle();
      const res = await apiRequest<{ access_token: string; user: User }>('/auth/firebase-login', {
        method: 'POST',
        body: JSON.stringify({
          id_token: idToken,
          role,
        }),
      });
      setAuthToken(res.access_token);
      onSuccess(res.user);
      onClose();
    } catch (err: any) {
      if (err.status === 409) {
        // Account linking required
        setError(err.message || 'An existing account matches this email. Enter your password below to link your Google account.');
        try {
          const idToken = await signInWithGoogle();
          setLinkingPendingToken(idToken);
        } catch {}
      } else {
        setError(err.message || 'Google Sign-In failed. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickDemoLogin = async () => {
    setError(null);
    setIsLoading(true);
    try {
      const mockEmail = 'aditya@example.com';
      const idToken = `mock-firebase:demo_uid_aditya:${mockEmail}:Aditya Verma`;
      const res = await apiRequest<{ access_token: string; user: User }>('/auth/firebase-login', {
        method: 'POST',
        body: JSON.stringify({
          id_token: idToken,
          role: 'salaried',
        }),
      });
      setAuthToken(res.access_token);
      onSuccess(res.user);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Demo login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirmLink = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!linkingPendingToken || !linkPassword) return;
    setIsLoading(true);
    setError(null);

    try {
      const res = await apiRequest<{ access_token: string; user: User }>('/auth/firebase-login', {
        method: 'POST',
        body: JSON.stringify({
          id_token: linkingPendingToken,
          link_password: linkPassword,
        }),
      });
      setAuthToken(res.access_token);
      onSuccess(res.user);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to link account. Please verify your password.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/75 backdrop-blur-md transition-opacity"
        onClick={onClose}
      />

      {/* Modal Dialog */}
      <div className="relative w-full max-w-md bg-[#0D111A] border border-[rgba(212,175,55,0.25)] rounded-2xl shadow-[0_25px_50px_-12px_rgba(0,0,0,0.9),0_0_30px_rgba(212,175,55,0.12)] p-6 sm:p-7 z-10 animate-in fade-in zoom-in-95 duration-200 text-[#F3F4F6]">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-1.5 rounded-xl text-[#9CA3AF] hover:text-[#F3F4F6] hover:bg-white/5 transition-colors border border-transparent hover:border-[#D4AF37]/20"
          aria-label="Close modal"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Modal Header */}
        <div className="mb-6">
          <h2 className="text-xl font-extrabold text-[#F3F4F6] tracking-tight">
            {linkingPendingToken
              ? 'Link Your Google Account'
              : isLogin
              ? 'Sign In to FinPilot AI'
              : 'Create Your FinPilot Account'}
          </h2>
          <p className="text-xs text-[#9CA3AF] mt-1">
            {linkingPendingToken
              ? 'Confirm ownership to securely link Google Sign-In to your existing profile.'
              : isLogin
              ? 'Access your private financial profiles, tax simulations, and connected AI CFO.'
              : 'Start your grounded financial intelligence journey with verified Indian tax logic.'}
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-4 p-3 rounded-xl bg-[#F43F5E]/15 border border-[#F43F5E]/30 text-xs text-[#F43F5E] leading-relaxed">
            {error}
          </div>
        )}

        {/* Account Linking Special Flow */}
        {linkingPendingToken ? (
          <form onSubmit={handleConfirmLink} className="space-y-4">
            <div className="p-3.5 rounded-xl bg-[#131824] border border-[#D4AF37]/25 flex items-start gap-2.5 text-xs text-[#F3F4F6]">
              <LinkIcon className="w-4 h-4 text-[#F5DE88] shrink-0 mt-0.5" />
              <span>
                Enter your existing password for <strong>{email}</strong> to authenticate and link Google.
              </span>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#D1D5DB] mb-1.5">
                Existing Account Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 w-4 h-4 text-[#9CA3AF]" />
                <input
                  type="password"
                  required
                  value={linkPassword}
                  onChange={(e) => setLinkPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full bg-[#131824] border border-[#222A3F] rounded-xl pl-9 pr-3 py-2 text-xs text-[#F3F4F6] placeholder-[#9CA3AF]/40 focus:outline-none focus:border-[#D4AF37] focus:ring-2 focus:ring-[#D4AF37]/20 transition-all"
                />
              </div>
            </div>

            <div className="flex gap-2 pt-2">
              <Button
                type="button"
                variant="secondary"
                size="md"
                className="flex-1"
                onClick={() => setLinkingPendingToken(null)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="md"
                className="flex-1"
                loading={isLoading}
              >
                Confirm & Link
              </Button>
            </div>
          </form>
        ) : (
          <div className="space-y-4">
            {/* Google Sign In Button */}
            <button
              type="button"
              onClick={handleGoogleSignIn}
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-3 py-2.5 px-4 bg-[#131824] hover:bg-[#1A2131] border border-[rgba(212,175,55,0.25)] hover:border-[#D4AF37]/50 text-xs font-semibold text-[#F3F4F6] rounded-xl transition-all shadow-sm focus:outline-none focus:ring-2 focus:ring-[#D4AF37]/30"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                />
              </svg>
              <span>Continue with Google</span>
            </button>

            {/* Quick Demo Access Button */}
            <button
              type="button"
              onClick={handleQuickDemoLogin}
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-2 py-2 px-4 bg-gradient-to-r from-[#D4AF37]/15 to-[#B89327]/10 hover:from-[#D4AF37]/25 hover:to-[#B89327]/20 border border-[#D4AF37]/35 text-xs font-semibold text-[#F5DE88] rounded-xl transition-all shadow-sm"
            >
              <Zap className="w-3.5 h-3.5 text-[#F5DE88]" />
              <span>Quick Demo Sign In (1-Click)</span>
            </button>

            {/* Divider */}
            <div className="relative flex items-center justify-center my-3">
              <div className="border-t border-white/10 w-full" />
              <span className="bg-[#0D111A] px-2.5 text-[10px] font-semibold text-[#9CA3AF] uppercase tracking-wider">
                Or with Email
              </span>
            </div>

            {/* Email/Password Form */}
            <form onSubmit={handleSubmit} className="space-y-3.5">
              {!isLogin && (
                <>
                  <div>
                    <label className="block text-xs font-semibold text-[#D1D5DB] mb-1">
                      Full Name
                    </label>
                    <div className="relative">
                      <UserIcon className="absolute left-3 top-2.5 w-4 h-4 text-[#9CA3AF]" />
                      <input
                        type="text"
                        required
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        placeholder="Aditya Verma"
                        className="w-full bg-[#131824] border border-[#222A3F] rounded-xl pl-9 pr-3 py-2 text-xs text-[#F3F4F6] placeholder-[#9CA3AF]/40 focus:outline-none focus:border-[#D4AF37] focus:ring-2 focus:ring-[#D4AF37]/20 transition-all"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-[#D1D5DB] mb-1">
                      Taxpayer Profile
                    </label>
                    <div className="relative">
                      <Briefcase className="absolute left-3 top-2.5 w-4 h-4 text-[#9CA3AF]" />
                      <select
                        value={role}
                        onChange={(e) => setRole(e.target.value as UserRole)}
                        className="w-full bg-[#131824] border border-[#222A3F] rounded-xl pl-9 pr-3 py-2 text-xs text-[#F3F4F6] focus:outline-none focus:border-[#D4AF37] focus:ring-2 focus:ring-[#D4AF37]/20 transition-all"
                      >
                        <option value="salaried">Salaried Employee</option>
                        <option value="freelancer">Freelancer / Professional (44ADA)</option>
                        <option value="business_owner">Business Owner (44AD)</option>
                        <option value="student">Student / Early Career</option>
                      </select>
                    </div>
                  </div>
                </>
              )}

              <div>
                <label className="block text-xs font-semibold text-[#D1D5DB] mb-1">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-2.5 w-4 h-4 text-[#9CA3AF]" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="aditya@example.com"
                    className="w-full bg-[#131824] border border-[#222A3F] rounded-xl pl-9 pr-3 py-2 text-xs text-[#F3F4F6] placeholder-[#9CA3AF]/40 focus:outline-none focus:border-[#D4AF37] focus:ring-2 focus:ring-[#D4AF37]/20 transition-all"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#D1D5DB] mb-1">
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-2.5 w-4 h-4 text-[#9CA3AF]" />
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full bg-[#131824] border border-[#222A3F] rounded-xl pl-9 pr-3 py-2 text-xs text-[#F3F4F6] placeholder-[#9CA3AF]/40 focus:outline-none focus:border-[#D4AF37] focus:ring-2 focus:ring-[#D4AF37]/20 transition-all"
                  />
                </div>
              </div>

              <Button
                type="submit"
                variant="primary"
                size="md"
                className="w-full mt-2"
                loading={isLoading}
              >
                {isLogin ? 'Sign In' : 'Create Account'}
              </Button>
            </form>

            {/* Toggle Login / Register */}
            <div className="text-center pt-2">
              <button
                type="button"
                onClick={() => {
                  setIsLogin(!isLogin);
                  setError(null);
                }}
                className="text-xs font-semibold text-[#F5DE88] hover:underline"
              >
                {isLogin
                  ? "Don't have an account yet? Register here"
                  : 'Already have an account? Sign in'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
