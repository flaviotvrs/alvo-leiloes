import { useQuery } from "@tanstack/react-query";
import { NavLink } from "react-router-dom";

import { apiGet, buildQuery } from "../api/client";
import type { ImoveisListResponse } from "../api/types";

const linkBase = "font-serif text-[13.5px] px-[14px] py-[7px] rounded-sm transition-colors";

function useTotalNaBase() {
  return useQuery({
    queryKey: ["imoveis", "total-base"],
    queryFn: () => apiGet<ImoveisListResponse>(`/imoveis${buildQuery({ limit: 1 })}`),
    staleTime: 60_000,
  });
}

export function NavBar() {
  const { data } = useTotalNaBase();

  return (
    <div className="sticky top-0 z-20 flex h-[60px] items-center justify-between gap-8 bg-ink px-7 text-onDark">
      <div className="flex items-center gap-7">
        <div className="flex items-baseline gap-2">
          <span className="font-mono text-[20px] font-semibold tracking-[0.2em]">ALVO</span>
          <span className="font-mono text-[11px] uppercase tracking-[0.22em] text-onDark4">Leilões</span>
        </div>
        <nav className="flex gap-0.5">
          <NavLink
            to="/triagem"
            className={({ isActive }) =>
              `${linkBase} ${isActive ? "bg-ink2 text-onDark" : "text-onDark4 hover:bg-ink2/50"}`
            }
          >
            Triagem
          </NavLink>
          <NavLink
            to="/funil"
            className={({ isActive }) =>
              `${linkBase} ${isActive ? "bg-ink2 text-onDark" : "text-onDark4 hover:bg-ink2/50"}`
            }
          >
            Funil de aprovação
          </NavLink>
        </nav>
      </div>
      <div className="flex items-center gap-[18px]">
        <div className="font-mono text-[11px] tracking-[0.04em] text-onDark4">
          {data ? `${data.total} IMÓVEIS COM ANÁLISE NA BASE` : ""}
        </div>
        <div className="flex items-center gap-[9px]">
          <div className="grid h-[27px] w-[27px] place-items-center rounded-full bg-green font-mono text-[11px] font-semibold text-white">
            FL
          </div>
          <span className="text-[13px] text-onDark2">Flavio</span>
        </div>
      </div>
    </div>
  );
}
