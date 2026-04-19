import { useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { CheckCircle2, AlertTriangle, AlertCircle, Info } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { fetchModelMetrics } from "@/lib/api-service";
import { predictDecision } from "@/lib/aiApi";
import type { PredictResponse } from "@/lib/api-types";

const PIE_COLORS = ["#10b981", "#f59e0b", "#ef4444", "#3b82f6", "#8b5cf6", "#ec4899", "#14b8a6", "#f97316"];

function MetricUnavailable({ label }: { label?: string }) {
  return (
    <div className="flex items-center gap-1.5 text-muted-foreground text-xs">
      <Info className="h-3 w-3 shrink-0" />
      <span>{label || "Not available from current training run"}</span>
    </div>
  );
}

export function AIEvaluation() {
  const [testResult, setTestResult] = useState<PredictResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [testError, setTestError] = useState<string | null>(null);

  const {
    data: modelMetrics,
    isLoading: metricsLoading,
    error: metricsError,
  } = useQuery({
    queryKey: ["model-metrics"],
    queryFn: async () => {
      const result = await fetchModelMetrics();
      if (!result) throw new Error("Failed to fetch model metrics");
      return result;
    },
    retry: 3,
    retryDelay: 2000,
    refetchInterval: 15000,
  });

  // --- Derived data: per-class metrics table ---
  const classMetrics = modelMetrics?.per_class_metrics
    ? Object.entries(modelMetrics.per_class_metrics).map(([className, m]) => ({
        class: className,
        precision: m.precision,
        recall: m.recall,
        f1: m.f1,
        support: m.support,
      }))
    : [];

  // --- Derived data: feature importance chart ---
  const featureData = modelMetrics?.feature_importances ?? null;

  // --- Derived data: class distribution pie ---
  const classDistribution = modelMetrics?.class_distribution
    ? Object.entries(modelMetrics.class_distribution).map(([name, value], i) => ({
        name,
        value,
        fill: PIE_COLORS[i % PIE_COLORS.length],
      }))
    : null;

  // --- Derived data: feature names badges ---
  const featureNames = modelMetrics?.feature_names ?? null;

  // --- Derived data: split ratio ---
  const splitRatio = modelMetrics?.dataset_info?.split_ratio;
  const splitLabel = splitRatio != null
    ? `${Math.round(splitRatio * 100)}/${Math.round((1 - splitRatio) * 100)}`
    : null;

  // --- Derived data: confusion matrix ---
  const confusionMatrix = modelMetrics?.confusion_matrix ?? null;

  // --- Derived data: overfitting check ---
  const overfitCheck = modelMetrics?.overfit_check ?? null;

  const runTest = async () => {
    setLoading(true);
    setTestError(null);
    try {
      const data = await predictDecision({
        WOB_klbf: 35,
        RPM_demo: 110,
        ROP_ft_hr: 75,
        PHIF: 0.22,
        VSH: 0.32,
        SW: 0.42,
        KLOGH: 0.52,
        Torque_kftlb: 3500,
        Vibration_g: 0.35,
        DLS_deg_per_100ft: 1.8,
        Inclination_deg: 50,
        Azimuth_deg: 105,
        Formation_Class: "Limestone",
      });
      setTestResult(data);
    } catch (error) {
      const msg = error instanceof Error ? error.message : "Unknown error";
      setTestError(`Failed to connect to backend: ${msg}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">AI Model Evaluation</h1>
          <p className="text-muted-foreground">
            Performance metrics and testing for the drilling recommendation model
          </p>
          {modelMetrics && (
            <Badge variant="outline" className="ml-2">
              Model Version: {modelMetrics.model_version || "Unknown"}
            </Badge>
          )}
        </div>

        {/* Model Status Alert */}
        {metricsError && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Unable to load model metrics. Ensure the backend is running and the model
              has been trained. Run <code>cd ai_service && python train.py</code> to
              train the model.
            </AlertDescription>
          </Alert>
        )}

        {metricsLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-muted-foreground">Loading model metrics...</div>
          </div>
        ) : !modelMetrics || modelMetrics.available === false ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center h-64">
              <AlertTriangle className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">Model Not Available</h3>
              <p className="text-muted-foreground text-center mb-4">
                The ML model has not been trained yet. The system is currently using
                rule-based recommendations.
              </p>
              <code className="bg-muted px-3 py-1 rounded text-sm">
                cd ai_service && python train.py
              </code>
            </CardContent>
          </Card>
        ) : (
          <div>
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    Accuracy
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {modelMetrics.accuracy != null
                      ? (modelMetrics.accuracy * 100).toFixed(1) + "%"
                      : "N/A"}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Test set ({modelMetrics.dataset_info?.test_samples ?? "?"} samples)
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    Macro F1
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {modelMetrics.macro_f1 != null
                      ? modelMetrics.macro_f1.toFixed(3)
                      : "N/A"}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">Unweighted average across classes</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    Weighted F1
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {modelMetrics.weighted_f1 != null
                      ? modelMetrics.weighted_f1.toFixed(3)
                      : "N/A"}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">Support-weighted average</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    Training Data
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {modelMetrics.dataset_info?.total_samples ?? "N/A"}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Total samples (train: {modelMetrics.dataset_info?.train_samples ?? "?"})
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    Output Classes
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {modelMetrics.per_class_metrics
                      ? Object.keys(modelMetrics.per_class_metrics).length
                      : "N/A"}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">Steering commands</p>
                </CardContent>
              </Card>
            </div>

            {/* Tabs for different views */}
            <Tabs defaultValue="performance" className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="performance">Performance</TabsTrigger>
                <TabsTrigger value="features">Features</TabsTrigger>
                <TabsTrigger value="classes">Classes</TabsTrigger>
                <TabsTrigger value="test">Test Model</TabsTrigger>
              </TabsList>

              {/* Performance Tab */}
              <TabsContent value="performance" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Model Overview</CardTitle>
                    <CardDescription>
                      Core performance metrics and configuration
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                      <div>
                        <p className="text-sm text-muted-foreground">Accuracy</p>
                        <p className="text-lg font-semibold">
                          {modelMetrics.accuracy != null
                            ? (modelMetrics.accuracy * 100).toFixed(1) + "%"
                            : "N/A"}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Macro Precision</p>
                        <p className="text-lg font-semibold">
                          {modelMetrics.precision != null
                            ? modelMetrics.precision.toFixed(3)
                            : "N/A"}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Macro Recall</p>
                        <p className="text-lg font-semibold">
                          {modelMetrics.recall != null
                            ? modelMetrics.recall.toFixed(3)
                            : "N/A"}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Weighted F1</p>
                        <p className="text-lg font-semibold">
                          {modelMetrics.weighted_f1 != null
                            ? modelMetrics.weighted_f1.toFixed(3)
                            : "N/A"}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Test Split</p>
                        <p className="text-lg font-semibold">
                          {splitLabel ?? "N/A"}
                        </p>
                      </div>
                    </div>

                    {/* Overfitting Check */}
                    {overfitCheck ? (
                      <div className="mt-6">
                        <h3 className="font-semibold mb-3">Overfitting Check (Train vs. Test)</h3>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                          <div>
                            <p className="text-sm text-muted-foreground">Train Accuracy</p>
                            <p className="text-lg font-semibold">
                              {(overfitCheck.train_accuracy * 100).toFixed(1)}%
                            </p>
                          </div>
                          <div>
                            <p className="text-sm text-muted-foreground">Test Accuracy</p>
                            <p className="text-lg font-semibold">
                              {(overfitCheck.test_accuracy * 100).toFixed(1)}%
                            </p>
                          </div>
                          <div>
                            <p className="text-sm text-muted-foreground">Accuracy Gap</p>
                            <p className={`text-lg font-semibold ${overfitCheck.accuracy_gap > 0.10 ? "text-red-500" : overfitCheck.accuracy_gap > 0.05 ? "text-yellow-500" : "text-green-500"}`}>
                              {overfitCheck.accuracy_gap > 0 ? "+" : ""}{(overfitCheck.accuracy_gap * 100).toFixed(1)}%
                            </p>
                          </div>
                          <div>
                            <p className="text-sm text-muted-foreground">Train Macro F1</p>
                            <p className="text-lg font-semibold">
                              {overfitCheck.train_macro_f1.toFixed(3)}
                            </p>
                          </div>
                          <div>
                            <p className="text-sm text-muted-foreground">Test Macro F1</p>
                            <p className="text-lg font-semibold">
                              {overfitCheck.test_macro_f1.toFixed(3)}
                            </p>
                          </div>
                          <div>
                            <p className="text-sm text-muted-foreground">F1 Gap</p>
                            <p className={`text-lg font-semibold ${overfitCheck.f1_gap > 0.10 ? "text-red-500" : overfitCheck.f1_gap > 0.05 ? "text-yellow-500" : "text-green-500"}`}>
                              {overfitCheck.f1_gap > 0 ? "+" : ""}{(overfitCheck.f1_gap * 100).toFixed(1)}%
                            </p>
                          </div>
                        </div>
                        {overfitCheck.f1_gap > 0.10 && (
                          <Alert className="mt-3">
                            <AlertTriangle className="h-4 w-4" />
                            <AlertDescription>
                              F1 gap exceeds 10% — the model may be overfitting to the training data.
                              Consider adding regularization or collecting more samples.
                            </AlertDescription>
                          </Alert>
                        )}
                      </div>
                    ) : (
                      <div className="mt-6">
                        <h3 className="font-semibold mb-3">Overfitting Check</h3>
                        <MetricUnavailable label="Retrain the model to generate overfitting diagnostics" />
                      </div>
                    )}

                    <div className="mt-6">
                      <h3 className="font-semibold mb-3">Class Distribution (Full Dataset)</h3>
                      {classDistribution ? (
                        <ResponsiveContainer width="100%" height={300}>
                          <PieChart>
                            <Pie
                              data={classDistribution}
                              cx="50%"
                              cy="50%"
                              labelLine={false}
                              label={({ name, value }) => `${name}: ${value}`}
                              outerRadius={100}
                              fill="#8884d8"
                              dataKey="value"
                            >
                              {classDistribution.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.fill} />
                              ))}
                            </Pie>
                            <Tooltip />
                          </PieChart>
                        </ResponsiveContainer>
                      ) : (
                        <MetricUnavailable label="Class distribution not available from training output" />
                      )}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Features Tab */}
              <TabsContent value="features" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Feature Importance</CardTitle>
                    <CardDescription>
                      Most influential drilling parameters in model decisions
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {featureData && featureData.length > 0 ? (
                      <ResponsiveContainer width="100%" height={400}>
                        <BarChart data={featureData.slice(0, 10)}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="name" angle={-45} textAnchor="end" height={120} />
                          <YAxis />
                          <Tooltip
                            formatter={(value: number) => [value.toFixed(4), "Importance"]}
                          />
                          <Bar dataKey="importance" fill="#3b82f6" />
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="flex flex-col items-center justify-center h-64">
                        <Info className="h-8 w-8 text-muted-foreground mb-3" />
                        <p className="text-muted-foreground text-sm text-center">
                          Feature importance data not available from current training run.
                          <br />
                          Retrain the model to generate this data.
                        </p>
                      </div>
                    )}

                    <div className="mt-6 space-y-2">
                      <h3 className="font-semibold">Input Features Used</h3>
                      {featureNames && featureNames.length > 0 ? (
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                          {featureNames.map((feature) => (
                            <Badge key={feature} variant="secondary">
                              {feature}
                            </Badge>
                          ))}
                        </div>
                      ) : (
                        <MetricUnavailable label="Feature list not available from training output" />
                      )}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Classes Tab */}
              <TabsContent value="classes" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Per-Class Performance</CardTitle>
                    <CardDescription>
                      Detailed metrics for each steering command class on the test set
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {classMetrics.length === 0 ? (
                      <MetricUnavailable label="Per-class metrics not available from current training run" />
                    ) : (
                      <>
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b">
                                <th className="text-left py-2 px-2">Class</th>
                                <th className="text-center py-2 px-2">Precision</th>
                                <th className="text-center py-2 px-2">Recall</th>
                                <th className="text-center py-2 px-2">F1-Score</th>
                                <th className="text-center py-2 px-2">Support</th>
                              </tr>
                            </thead>
                            <tbody>
                              {classMetrics.map((metric, idx) => (
                                <tr key={idx} className={idx % 2 === 0 ? "bg-muted/50" : ""}>
                                  <td className="py-2 px-2 font-medium">{metric.class}</td>
                                  <td className="text-center py-2 px-2">
                                    {metric.precision.toFixed(2)}
                                  </td>
                                  <td className="text-center py-2 px-2">
                                    {metric.recall.toFixed(2)}
                                  </td>
                                  <td className="text-center py-2 px-2">
                                    {metric.f1.toFixed(2)}
                                  </td>
                                  <td className="text-center py-2 px-2">{metric.support}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>

                        {classMetrics.some((m) => m.support <= 2) && (
                          <Alert className="mt-4">
                            <AlertTriangle className="h-4 w-4" />
                            <AlertDescription>
                              Some classes have very few test samples (support &le; 2).
                              Per-class metrics for these classes are unreliable.
                            </AlertDescription>
                          </Alert>
                        )}
                      </>
                    )}
                  </CardContent>
                </Card>

                {/* Confusion Matrix */}
                <Card>
                  <CardHeader>
                    <CardTitle>Confusion Matrix</CardTitle>
                    <CardDescription>
                      Predicted vs. actual class counts on the test set
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {confusionMatrix ? (
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b">
                              <th className="text-left py-2 px-2">Actual \ Predicted</th>
                              {confusionMatrix.labels.map((label) => (
                                <th key={label} className="text-center py-2 px-2 min-w-[70px]">
                                  {label}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {confusionMatrix.matrix.map((row, i) => {
                              const rowTotal = row.reduce((a, b) => a + b, 0);
                              return (
                                <tr key={i} className={i % 2 === 0 ? "bg-muted/50" : ""}>
                                  <td className="py-2 px-2 font-medium">
                                    {confusionMatrix.labels[i]}
                                  </td>
                                  {row.map((cell, j) => {
                                    const isCorrect = i === j;
                                    const intensity = rowTotal > 0 ? cell / rowTotal : 0;
                                    return (
                                      <td
                                        key={j}
                                        className={`text-center py-2 px-2 font-mono ${
                                          isCorrect
                                            ? "font-bold text-green-700 dark:text-green-400"
                                            : cell > 0
                                              ? "text-red-600 dark:text-red-400"
                                              : "text-muted-foreground"
                                        }`}
                                        style={
                                          isCorrect && intensity > 0
                                            ? { backgroundColor: `rgba(16, 185, 129, ${intensity * 0.2})` }
                                            : cell > 0
                                              ? { backgroundColor: `rgba(239, 68, 68, ${intensity * 0.15})` }
                                              : undefined
                                        }
                                      >
                                        {cell}
                                      </td>
                                    );
                                  })}
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <MetricUnavailable label="Confusion matrix not available — retrain the model to generate this data" />
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Test Tab */}
              <TabsContent value="test" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Test Model Prediction</CardTitle>
                    <CardDescription>
                      Send a prediction request to the live backend API
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <p className="text-sm text-muted-foreground">
                      This test sends a sample telemetry packet to the backend and
                      displays the live prediction.
                    </p>

                    <Button onClick={runTest} disabled={loading} className="w-full">
                      {loading ? "Testing..." : "Run Test Prediction"}
                    </Button>

                    {testError && (
                      <Alert variant="destructive">
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>{testError}</AlertDescription>
                      </Alert>
                    )}

                    {testResult && (
                      <div className="space-y-4 mt-4">
                        <Alert
                          className={
                            testResult.gate_status === "ACCEPTED"
                              ? "border-green-500"
                              : "border-red-500"
                          }
                        >
                          <CheckCircle2 className="h-4 w-4" />
                          <AlertDescription>
                            Backend connection successful! Model is returning real
                            predictions.
                          </AlertDescription>
                        </Alert>

                        <div className="bg-muted p-4 rounded-lg space-y-3">
                          <div className="flex justify-between">
                            <span className="text-sm font-medium">Recommendation</span>
                            <Badge variant="outline">{testResult.recommendation}</Badge>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm font-medium">Confidence</span>
                            <span className="font-mono">
                              {(testResult.confidence * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm font-medium">Gate Status</span>
                            <Badge
                              variant={
                                testResult.gate_status === "ACCEPTED"
                                  ? "default"
                                  : "destructive"
                              }
                            >
                              {testResult.gate_status}
                            </Badge>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm font-medium">Message</span>
                            <span className="text-sm">{testResult.alert_message}</span>
                          </div>

                          <div className="mt-4 border-t pt-3">
                            <p className="text-xs font-semibold text-muted-foreground mb-2">
                              Raw Response
                            </p>
                            <pre className="bg-background p-2 rounded text-xs overflow-auto max-h-40">
                              {JSON.stringify(testResult, null, 2)}
                            </pre>
                          </div>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>

            {/* Summary Stats */}
            <Card>
              <CardHeader>
                <CardTitle>Model Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <p>
                    <span className="font-medium">Algorithm:</span>{" "}
                    {modelMetrics.algorithm || "Unknown"}{" "}
                    {modelMetrics.n_estimators ? `(${modelMetrics.n_estimators} estimators)` : ""}
                  </p>
                  <p>
                    <span className="font-medium">Version:</span>{" "}
                    {modelMetrics.model_version || "Unknown"}
                  </p>
                  <p>
                    <span className="font-medium">Training Split:</span>{" "}
                    {splitLabel
                      ? `${splitLabel} (${modelMetrics.dataset_info?.train_samples} train / ${modelMetrics.dataset_info?.test_samples} test)`
                      : "N/A"}
                  </p>
                  <p>
                    <span className="font-medium">Input Features:</span>{" "}
                    {modelMetrics.dataset_info?.features != null
                      ? `${modelMetrics.dataset_info.features} total`
                      : "N/A"}
                  </p>
                  <p>
                    <span className="font-medium">Output Classes:</span>{" "}
                    {modelMetrics.per_class_metrics
                      ? Object.keys(modelMetrics.per_class_metrics).join(", ")
                      : "N/A"}
                  </p>
                  {modelMetrics.timestamp && (
                    <p>
                      <span className="font-medium">Trained:</span>{" "}
                      {new Date(modelMetrics.timestamp).toLocaleString()}
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}

export default AIEvaluation;
