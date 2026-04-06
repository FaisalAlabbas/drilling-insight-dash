import { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CheckCircle2, AlertTriangle, TrendingUp } from 'lucide-react';

export function AIEvaluation() {
  const [testResult, setTestResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  // Model Performance Metrics
  const modelMetrics = {
    accuracy: 0.774,
    f1_score: 0.74,
    precision: 0.71,
    recall: 0.77,
    model_type: "Random Forest Classifier",
    training_samples: 120,
    test_samples: 31,
    classes: 5,
    top_features: [
      { name: 'PHIF (Porosity)', importance: 0.1556 },
      { name: 'DLS (Dogleg Severity)', importance: 0.1493 },
      { name: 'VSH (Shale Volume)', importance: 0.1255 },
      { name: 'Azimuth', importance: 0.1006 },
      { name: 'Vibration', importance: 0.0863 },
    ]
  };

  // Per-class performance
  const classMetrics = [
    { class: 'Build', precision: 0.60, recall: 1.00, f1: 0.75, support: 3 },
    { class: 'Drop', precision: 0.75, recall: 0.75, f1: 0.75, support: 4 },
    { class: 'Hold', precision: 0.82, recall: 0.86, f1: 0.84, support: 21 },
    { class: 'Turn Left', precision: 0.00, recall: 0.00, f1: 0.00, support: 2 },
    { class: 'Turn Right', precision: 0.00, recall: 0.00, f1: 0.00, support: 1 },
  ];

  // Feature importance data for chart
  const featureData = modelMetrics.top_features.map(f => ({
    name: f.name,
    importance: (f.importance * 100).toFixed(2)
  }));

  // Class distribution
  const classDistribution = [
    { name: 'Build', value: 75, fill: '#10b981' },
    { name: 'Hold', value: 43, fill: '#f59e0b' },
    { name: 'Drop', value: 17, fill: '#ef4444' },
    { name: 'Turn Right', value: 8, fill: '#3b82f6' },
    { name: 'Turn Left', value: 8, fill: '#8b5cf6' },
  ];

  const runTest = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
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
          Formation_Class: "Limestone"
        })
      });
      const data = await response.json();
      setTestResult(data);
    } catch (error) {
      console.error('Test failed:', error);
      alert('Failed to connect to backend. Make sure the API server is running on port 8000.');
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
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Accuracy</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{(modelMetrics.accuracy * 100).toFixed(1)}%</div>
              <p className="text-xs text-muted-foreground mt-1">Test set performance</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">F1-Score</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{modelMetrics.f1_score.toFixed(2)}</div>
              <p className="text-xs text-muted-foreground mt-1">Weighted average</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Training Data</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{modelMetrics.training_samples + modelMetrics.test_samples}</div>
              <p className="text-xs text-muted-foreground mt-1">Total samples</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Output Classes</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{modelMetrics.classes}</div>
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
                <CardDescription>Core performance metrics and configuration</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Precision</p>
                    <p className="text-lg font-semibold">{modelMetrics.precision.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Recall</p>
                    <p className="text-lg font-semibold">{modelMetrics.recall.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Model Type</p>
                    <p className="text-sm font-semibold">Random Forest</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Test Split</p>
                    <p className="text-sm font-semibold">80/20</p>
                  </div>
                </div>

                <div className="mt-6">
                  <h3 className="font-semibold mb-3">Class Distribution</h3>
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
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Features Tab */}
          <TabsContent value="features" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Top 10 Feature Importance</CardTitle>
                <CardDescription>Most influential drilling parameters in model decisions</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart data={featureData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="importance" fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>

                <div className="mt-6 space-y-2">
                  <h3 className="font-semibold">Input Features Used</h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                    {[
                      'WOB_klbf', 'RPM_demo', 'ROP_ft_hr', 'PHIF', 'VSH', 'SW',
                      'KLOGH', 'Torque_kftlb', 'Vibration_g', 'DLS_deg_per_100ft',
                      'Inclination_deg', 'Azimuth_deg', 'Formation_Class'
                    ].map(feature => (
                      <Badge key={feature} variant="secondary">{feature}</Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Classes Tab */}
          <TabsContent value="classes" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Per-Class Performance</CardTitle>
                <CardDescription>Detailed metrics for each steering command class</CardDescription>
              </CardHeader>
              <CardContent>
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
                        <tr key={idx} className={idx % 2 === 0 ? 'bg-muted/50' : ''}>
                          <td className="py-2 px-2 font-medium">{metric.class}</td>
                          <td className="text-center py-2 px-2">{metric.precision.toFixed(2)}</td>
                          <td className="text-center py-2 px-2">{metric.recall.toFixed(2)}</td>
                          <td className="text-center py-2 px-2">{metric.f1.toFixed(2)}</td>
                          <td className="text-center py-2 px-2">{metric.support}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <Alert className="mt-4">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    Classes "Turn Left" and "Turn Right" have limited test samples and show low performance. Use caution when model predicts these classes.
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Test Tab */}
          <TabsContent value="test" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Test Model Prediction</CardTitle>
                <CardDescription>Send a prediction request to the live backend API</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  This test sends a sample telemetry packet to the backend and displays the live prediction.
                </p>

                <Button onClick={runTest} disabled={loading} className="w-full">
                  {loading ? 'Testing...' : 'Run Test Prediction'}
                </Button>

                {testResult && (
                  <div className="space-y-4 mt-4">
                    <Alert className={testResult.gate_status === 'ACCEPTED' ? 'border-green-500' : 'border-red-500'}>
                      <CheckCircle2 className="h-4 w-4" />
                      <AlertDescription>
                        Backend connection successful! Model is returning real predictions.
                      </AlertDescription>
                    </Alert>

                    <div className="bg-muted p-4 rounded-lg space-y-3">
                      <div className="flex justify-between">
                        <span className="text-sm font-medium">Recommendation</span>
                        <Badge variant="outline">{testResult.recommendation}</Badge>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm font-medium">Confidence</span>
                        <span className="font-mono">{(testResult.confidence * 100).toFixed(1)}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm font-medium">Gate Status</span>
                        <Badge variant={testResult.gate_status === 'ACCEPTED' ? 'default' : 'destructive'}>
                          {testResult.gate_status}
                        </Badge>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm font-medium">Message</span>
                        <span className="text-sm">{testResult.alert_message}</span>
                      </div>

                      <div className="mt-4 border-t pt-3">
                        <p className="text-xs font-semibold text-muted-foreground mb-2">Raw Response</p>
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
                <span className="font-medium">Algorithm:</span> {modelMetrics.model_type} with 500 estimators
              </p>
              <p>
                <span className="font-medium">Training Strategy:</span> Temporal/spatial ordering (first 80% by depth)
              </p>
              <p>
                <span className="font-medium">Input Features:</span> 12 numerical + 1 categorical (13 total)
              </p>
              <p>
                <span className="font-medium">Output:</span> 5 steering command classes
              </p>
              <p>
                <span className="font-medium">Status:</span> Production-ready ✓
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default AIEvaluation;
