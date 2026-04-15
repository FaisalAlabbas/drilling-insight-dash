import { useQuery } from "@tanstack/react-query";
import type { ConfigResponse } from "./api-types";
import { fetchConfig } from "./api-service";

export const getConfig = async (): Promise<ConfigResponse> => {
  const config = await fetchConfig();
  if (!config) {
    throw new Error("Failed to fetch config");
  }
  return config;
};

export const useConfig = () => {
  return useQuery({
    queryKey: ["config"],
    queryFn: getConfig,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 3,
  });
};
