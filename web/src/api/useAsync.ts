import { useEffect, useState } from "react";

export type State<T> = { data: T | null; error: string | null; loading: boolean };

export function useAsync<T>(fn: () => Promise<T>, deps: unknown[] = []): State<T> {
  const [s, setS] = useState<State<T>>({ data: null, error: null, loading: true });
  useEffect(() => {
    let live = true;
    setS({ data: null, error: null, loading: true });
    fn().then(
      (data) => live && setS({ data, error: null, loading: false }),
      (e: Error) => live && setS({ data: null, error: e.message, loading: false }),
    );
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  return s;
}
