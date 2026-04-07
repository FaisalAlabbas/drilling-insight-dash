import React from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { AlertTriangle, CheckCircle, XCircle, TrendingDown } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

interface DataQualityMetrics {
  total_records: number;
  missing_data_rate: number;
  gap_count: number;
  outlier_count: number;
  data_completeness: number;
  last_updated: string;
}

const API_BASE_URL = import.meta.env.VITE_AI_BASE_URL || "http://localhost:8000";

const getDataQuality = async (): Promise<DataQualityMetrics> => {
  const response = await fetch(`${API_BASE_URL}/telemetry/quality`);
  if (!response.ok) {
    throw new Error("Failed to fetch data quality metrics");
  }
  return response.json();
};

export default function DataQuality() {
  const {
    data: quality,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["data-quality"],
    queryFn: getDataQuality,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading data quality metrics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-destructive">Failed to load data quality metrics</div>
      </div>
    );
  }

  const getQualityColor = (rate: number) => {
    if (rate >= 0.95) return "text-green-600";
    if (rate >= 0.85) return "text-yellow-600";
    return "text-red-600";
  };

  const getQualityIcon = (rate: number) => {
    if (rate >= 0.95) return <CheckCircle className="h-4 w-4 text-green-600" />;
    if (rate >= 0.85) return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
    return <XCircle className="h-4 w-4 text-red-600" />;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Data Quality Dashboard</h1>
        <p className="text-muted-foreground">
          Monitor data completeness, gaps, and outliers in real-time telemetry
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Data Completeness</CardTitle>
            {getQualityIcon(quality?.data_completeness || 0)}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {((quality?.data_completeness || 0) * 100).toFixed(1)}%
            </div>
            <Progress value={(quality?.data_completeness || 0) * 100} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-1">
              {quality?.total_records || 0} total records
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Missing Data Rate</CardTitle>
            <TrendingDown
              className={`h-4 w-4 ${getQualityColor(1 - (quality?.missing_data_rate || 0))}`}
            />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {((quality?.missing_data_rate || 0) * 100).toFixed(1)}%
            </div>
            <Progress
              value={(1 - (quality?.missing_data_rate || 0)) * 100}
              className="mt-2"
            />
            <p className="text-xs text-muted-foreground mt-1">Data availability</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Data Gaps</CardTitle>
            <Badge variant={quality?.gap_count === 0 ? "default" : "destructive"}>
              {quality?.gap_count || 0}
            </Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{quality?.gap_count || 0}</div>
            <p className="text-xs text-muted-foreground">Missing time periods</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Outliers Detected</CardTitle>
            <Badge variant={quality?.outlier_count === 0 ? "default" : "secondary"}>
              {quality?.outlier_count || 0}
            </Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{quality?.outlier_count || 0}</div>
            <p className="text-xs text-muted-foreground">Anomalous readings</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Quality Details</CardTitle>
          <CardDescription>
            Last updated:{" "}
            {quality?.last_updated
              ? new Date(quality.last_updated).toLocaleString()
              : "Never"}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Record Count</span>
                <span className="font-medium">{quality?.total_records || 0}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Data Completeness</span>
                <span
                  className={`font-medium ${getQualityColor(quality?.data_completeness || 0)}`}
                >
                  {((quality?.data_completeness || 0) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Missing Data Rate</span>
                <span
                  className={`font-medium ${getQualityColor(1 - (quality?.missing_data_rate || 0))}`}
                >
                  {((quality?.missing_data_rate || 0) * 100).toFixed(1)}%
                </span>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Data Gaps</span>
                <span className="font-medium">{quality?.gap_count || 0}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Outlier Count</span>
                <span className="font-medium">{quality?.outlier_count || 0}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Status</span>
                <Badge
                  variant={
                    (quality?.data_completeness || 0) >= 0.95 ? "default" : "destructive"
                  }
                >
                  {(quality?.data_completeness || 0) >= 0.95
                    ? "Healthy"
                    : "Needs Attention"}
                </Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
