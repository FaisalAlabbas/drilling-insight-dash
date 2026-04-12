import { useQuery } from "@tanstack/react-query";
import type { ConfigResponse } from "./api-types";
import { ConfigResponseSchema } from "./zod-schemas";

const API_BASE_URL = import.meta.env.VITE_AI_BASE_URL || "http://localhost:8001";

export const getConfig = async (): Promise<ConfigResponse> => {
  const response = await fetch(`${API_BASE_URL}/config`);
  if (!response.ok) {
    throw new Error("Failed to fetch config");
  }
  const json = await response.json();
  return ConfigResponseSchema.parse(json);
};

export const useConfig = () => {
  return useQuery({
    queryKey: ["config"],
    queryFn: getConfig,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 3,
  });
};
