import type { GuardrailFlag, RAGResponse, User, UserRole } from './types';

export function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.map((x) => String(x));
}

/** Backend sends flag codes as strings; UI expects { type, message, severity }. */
export function normalizeGuardrailFlags(raw: unknown): GuardrailFlag[] {
  if (!Array.isArray(raw) || raw.length === 0) return [];
  return raw.map((item) => {
    if (typeof item === 'string') {
      return {
        type: item,
        message: item.replace(/_/g, ' '),
        severity: 'warning' as const,
      };
    }
    const o = item as Record<string, unknown>;
    return {
      type: String(o.type ?? 'guardrail'),
      message: String(o.message ?? o.type ?? ''),
      severity: o.severity === 'error' ? ('error' as const) : ('warning' as const),
    };
  });
}

export function normalizeRAGResponse(data: unknown): RAGResponse {
  const d = (data && typeof data === 'object' ? data : {}) as Record<string, unknown>;
  const rbacReason = d.rbac_denial_reason ?? d.rbac_reason;
  return {
    answer: String(d.answer ?? ''),
    sources: Array.isArray(d.sources) ? (d.sources as RAGResponse['sources']) : [],
    route: String(d.route ?? ''),
    user_role: (d.user_role as UserRole) || 'employee',
    accessible_collections: asStringArray(d.accessible_collections),
    guardrail_flags: normalizeGuardrailFlags(d.guardrail_flags),
    guardrail_warnings: asStringArray(d.guardrail_warnings),
    rbac_denied: Boolean(d.rbac_denied),
    rbac_denial_reason: rbacReason != null ? String(rbacReason) : undefined,
  };
}

export function normalizeUser(data: unknown): User {
  const d = (data && typeof data === 'object' ? data : {}) as Record<string, unknown>;
  return {
    username: String(d.username ?? ''),
    name: String(d.name ?? ''),
    role: (d.role as UserRole) || 'employee',
    department: String(d.department ?? ''),
    accessible_collections: asStringArray(d.accessible_collections),
  };
}
