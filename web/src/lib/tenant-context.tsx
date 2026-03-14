'use client';

import { createContext, useContext, useState, type ReactNode } from 'react';

type TenantCtx = {
  tenantId: string;
  setTenantId: (id: string) => void;
};

const TenantContext = createContext<TenantCtx>({
  tenantId: '',
  setTenantId: () => {},
});

const DEFAULT = process.env.NEXT_PUBLIC_DEFAULT_TENANT_ID || '';

export function TenantProvider({ children }: { children: ReactNode }) {
  const [tenantId, setTenantId] = useState(DEFAULT);
  return (
    <TenantContext.Provider value={{ tenantId, setTenantId }}>
      {children}
    </TenantContext.Provider>
  );
}

export function useTenant() {
  return useContext(TenantContext);
}
