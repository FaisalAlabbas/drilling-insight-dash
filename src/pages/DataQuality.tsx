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
import { AlertTriangle, CheckCircle, XCircle } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { fetchDataQuality } from "@/lib/api-service";
import type { DataQualityMetrics } from "@/lib/api-types";

const getDataQuality = async (): Promise<DataQualityMetrics> => {
  const result = await fetchDataQuality();
  if (!result) {
    throw new Error("Failed to fetch data quality metrics");
  }
  return result;
};

export default function DataQuality() {
  const {
    data: quality,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["data-quality"],
    queryFn: getDataQuality,
    refetchInterval: 30000,
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

  if (!quality) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-destructive">No data quality metrics available</div>
      </div>
    );
  }

  const getQualityIcon = (rate: number) => {
    if (rate >= 0.95) return <CheckCircle className="h-4 w-4 text-green-600" />;
    if (rate >= 0.85) return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
    return <XCircle className="h-4 w-4 text-red-600" />;
  };

  const totalMissingRate =
    Object.values(quality.missing_rate_by_column).reduce((sum, rate) => sum + rate, 0) /
    Math.max(1, Object.keys(quality.missing_rate_by_column).length);
  const totalOutliers = Object.values(quality.outlier_counts).reduce(
    (sum, count) => sum + count,
    0
  );
  const dataCompleteness =
    ((quality.total_rows - totalOutliers) / Math.max(1, quality.total_rows)) * 100;

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
            {getQualityIcon(dataCompleteness / 100)}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dataCompleteness.toFixed(1)}%</div>
            <Progress value={dataCompleteness} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-1">
              {quality.total_rows} total records
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Missing Data Rate</CardTitle>
            {getQualityIcon(1 - totalMissingRate)}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(totalMissingRate * 100).toFixed(2)}%
            </div>
            <Progress value={totalMissingRate * 100} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-1">
              Across {Object.keys(quality.missing_rate_by_column).length} columns
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Data Gaps</CardTitle>
            {quality.gaps_detected > 5 ? (
              <AlertTriangle className="h-4 w-4 text-yellow-600" />
            ) : (
              <CheckCircle className="h-4 w-4 text-green-600" />
            )}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{quality.gaps_detected}</div>
            <p className="text-xs text-muted-foreground mt-2">
              {quality.gaps_detected > 0
                ? "Gaps in timestamp sequence"
                : "No gaps detected"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Outliers</CardTitle>
            {totalOutliers > 10 ? (
              <AlertTriangle className="h-4 w-4 text-yellow-600" />
            ) : (
              <CheckCircle className="h-4 w-4 text-green-600" />
            )}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalOutliers}</div>
            <p className="text-xs text-muted-foreground mt-2">
              {totalOutliers > 0 ? "Anomalies detected" : "No anomalies"}
            </p>
          </CardContent>
        </Card>
      </div>

      {Object.keys(quality.missing_rate_by_column).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Missing Data by Column</CardTitle>
            <CardDescription>
              Percentage of missing values for each telemetry field
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(quality.missing_rate_by_column).map(([column, rate]) => (
                <div key={column}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium">{column}</span>
                    <span className="text-sm text-muted-foreground">
                      {(rate * 100).toFixed(2)}%
                    </span>
                  </div>
                  <Progress value={rate * 100} />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Outlier Statistics</CardTitle>
          <CardDescription>Statistical anomalies detected in sensor data</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            {Object.entries(quality.outlier_counts).map(([metric, count]) => (
              <div key={metric} className="border rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium capitalize">{metric}</span>
                  <Badge variant={count > 0 ? "destructive" : "default"}>
                    {count} outlier{count !== 1 ? "s" : ""}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                  {count > 0
                    ? `${count} reading${count !== 1 ? "s" : ""} exceed range`
                    : "All readings normal"}
                </p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
