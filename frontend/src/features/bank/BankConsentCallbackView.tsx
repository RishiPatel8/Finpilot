import React, { useEffect, useState } from 'react';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Loader2,
  ShieldCheck,
  Building2,
  ArrowRight,
  ExternalLink,
} from 'lucide-react';
import { apiRequest } from '../../services/api';
import { BankAccount } from '../../types';

interface CallbackResult {
  consent_id: string;
  consent_handle: string;
  provider: string;
  status: string;
  message: string;
  accounts_linked: number;
  accounts: BankAccount[];
}

interface BankConsentCallbackViewProps {
  onComplete: (targetTab?: 'bank' | 'overview') => void;
}

export const BankConsentCallbackView: React.FC<BankConsentCallbackViewProps> = ({ onComplete }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CallbackResult | null>(null);

  // Extract query parameters from Finvu / Account Aggregator redirect
  const searchParams = new URLSearchParams(window.location.search);
  const consentHandle =
    searchParams.get('consentHandle') ||
    searchParams.get('consent_handle') ||
    searchParams.get('handle') ||
    '';
  const paramStatus = searchParams.get('status') || '';
  const paramErrorCode = searchParams.get('errorCode') || searchParams.get('error') || '';

  useEffect(() => {
    const processCallback = async () => {
      if (!consentHandle) {
        setError(
          'Missing consent handle in the redirect URL. Please return to Bank Accounts and initiate a new Account Aggregator session.'
        );
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        // Security requirement: We pass the callback parameters to the backend,
        // which authoritatively queries the Account Aggregator adapter directly
        // rather than blindly trusting the frontend query parameters.
        const res = await apiRequest<CallbackResult>('/bank/consent/callback', {
          method: 'POST',
          body: JSON.stringify({
            consent_handle: consentHandle,
            status: paramStatus,
            error: paramErrorCode || undefined,
          }),
        });

        setResult(res);
      } catch (err: any) {
        setError(
          err?.message ||
            'Failed to verify Account Aggregator consent with Finvu/Bank servers. Please try again.'
        );
      } finally {
        setLoading(false);
      }
    };

    processCallback();
  }, [consentHandle, paramStatus, paramErrorCode]);

  return (
    <div className="max-w-2xl mx-auto py-12 px-4 sm:px-6">
      <div className="bg-white border border-[#E2E8F0] rounded-2xl shadow-sm overflow-hidden">
        {/* Header Banner */}
        <div className="bg-gradient-to-r from-[#F8FAFC] to-[#EEF2F6] p-6 border-b border-[#E2E8F0] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-[#172033]">
                Account Aggregator Consent Flow
              </h2>
              <p className="text-xs text-[#64748B]">
                RBI-Regulated NBFC-AA Consent Verification
              </p>
            </div>
          </div>
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
            Finvu / ReBIT 2.0
          </span>
        </div>

        {/* Content Area */}
        <div className="p-6 sm:p-8 space-y-6">
          {loading && (
            <div className="text-center py-10 space-y-4">
              <Loader2 className="w-10 h-10 text-blue-600 animate-spin mx-auto" />
              <h3 className="text-base font-semibold text-[#172033]">
                Verifying Authoritative Consent Status...
              </h3>
              <p className="text-sm text-[#64748B] max-w-md mx-auto">
                Validating consent cryptographic handle <code className="bg-slate-100 px-1.5 py-0.5 rounded text-xs text-slate-800">{consentHandle || '...'}</code> directly with Account Aggregator servers.
              </p>
            </div>
          )}

          {!loading && error && (
            <div className="space-y-6">
              <div className="p-4 rounded-xl bg-red-50 border border-red-200 flex items-start gap-3">
                <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-sm font-semibold text-red-900">
                    Consent Verification Failed
                  </h4>
                  <p className="text-xs text-red-700 mt-1 leading-relaxed">
                    {error}
                  </p>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-amber-50/70 border border-amber-200 text-xs text-amber-900 space-y-1">
                <p className="font-semibold flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 text-amber-600" />
                  Security Notice
                </p>
                <p>
                  FinPilot AI never trusts URL query parameters as proof of consent approval. All consent transitions require direct cryptographic verification against the Account Aggregator service.
                </p>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => onComplete('bank')}
                  className="px-4 py-2 text-sm font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-xl transition"
                >
                  Back to Bank Accounts
                </button>
              </div>
            </div>
          )}

          {!loading && result && (
            <div className="space-y-6">
              {result.status === 'ACTIVE' ? (
                <>
                  <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="text-sm font-semibold text-emerald-900">
                        Consent Approved & Accounts Connected!
                      </h4>
                      <p className="text-xs text-emerald-700 mt-1 leading-relaxed">
                        {result.message}
                      </p>
                    </div>
                  </div>

                  {/* Discovered Accounts */}
                  {result.accounts && result.accounts.length > 0 && (
                    <div className="space-y-3">
                      <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                        Synchronized Bank Accounts ({result.accounts.length})
                      </h4>
                      <div className="space-y-2">
                        {result.accounts.map((acc) => (
                          <div
                            key={acc.id}
                            className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50 flex items-center justify-between"
                          >
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center text-blue-700">
                                <Building2 className="w-4 h-4" />
                              </div>
                              <div>
                                <p className="text-sm font-medium text-slate-900">
                                  {acc.institution_name}
                                </p>
                                <p className="text-xs text-slate-500">
                                  {acc.account_type.toUpperCase()} • {acc.account_number_masked}
                                </p>
                              </div>
                            </div>
                            <div className="text-right">
                              <p className="text-sm font-semibold text-slate-900">
                                ₹{acc.current_balance.toLocaleString('en-IN')}
                              </p>
                              <span className="text-[10px] text-emerald-600 font-medium">
                                Verified Synced
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
                    <button
                      type="button"
                      onClick={() => onComplete('overview')}
                      className="px-4 py-2 text-sm font-medium text-slate-700 hover:text-slate-900 transition"
                    >
                      View Dashboard
                    </button>
                    <button
                      type="button"
                      onClick={() => onComplete('bank')}
                      className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-xl transition shadow-sm"
                    >
                      Manage Bank Accounts
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="text-sm font-semibold text-amber-900">
                        Consent Declined or Cancelled
                      </h4>
                      <p className="text-xs text-amber-700 mt-1 leading-relaxed">
                        {result.message}
                      </p>
                    </div>
                  </div>

                  <p className="text-xs text-slate-500">
                    No financial data or account statements were accessed or stored. You can initiate a new consent request at any time when you wish to link your accounts.
                  </p>

                  <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
                    <button
                      type="button"
                      onClick={() => onComplete('bank')}
                      className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-slate-900 hover:bg-slate-800 rounded-xl transition shadow-sm"
                    >
                      Return to Bank Accounts
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                </>
              )}
            </div>
          )}
        </div>

        {/* Footer Technical Metadata */}
        <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 text-[11px] text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>
            Redirect Route: <code className="text-slate-700">/bank/consent/callback</code>
          </span>
          <span className="flex items-center gap-1 text-slate-600">
            <ExternalLink className="w-3 h-3" />
            Finvu Production AA Host: web.finvu.in
          </span>
        </div>
      </div>
    </div>
  );
};
