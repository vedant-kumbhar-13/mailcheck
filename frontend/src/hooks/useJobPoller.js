import { useEffect, useRef, useState } from "react";
import { getJobStatus } from "../api/bulk";
/**
 * Polls GET /api/jobs/{id} every 2 seconds until status is ready or failed.
 * Stops automatically when terminal state is reached.
 */
export function useJobPoller(jobId, jobKey) {
    const [meta, setMeta] = useState(null);
    const [error, setError] = useState(null);
    const timerRef = useRef(null);
    useEffect(() => {
        if (!jobId || !jobKey)
            return;
        const poll = async () => {
            try {
                const m = await getJobStatus(jobId, jobKey);
                setMeta(m);
                if (m.status === "ready" || m.status === "failed") {
                    if (timerRef.current)
                        clearInterval(timerRef.current);
                }
            }
            catch (e) {
                setError(e instanceof Error ? e.message : "Poll failed");
                if (timerRef.current)
                    clearInterval(timerRef.current);
            }
        };
        poll(); // immediate first check
        timerRef.current = setInterval(poll, 2000);
        return () => {
            if (timerRef.current)
                clearInterval(timerRef.current);
        };
    }, [jobId, jobKey]);
    return { meta, error };
}
