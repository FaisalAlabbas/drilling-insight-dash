import { useQuery } from "@tanstack/react-query";
import { ConfigResponse } from "./types";

const API_BASE_URL = import.meta.env.VITE_AI_BASE_URL || "http://localhost:8000";

export const getConfig = async (): Promise<ConfigResponse> => {
  const response = await fetch(`${API_BASE_URL}/config`);
  if (!response.ok) {
    throw new Error("Failed to fetch config");
  }
  return response.json();
};

export const useConfig = () => {
  return useQuery({
    queryKey: ["config"],
    queryFn: getConfig,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 3,
  });
};
