import { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Upload, ShieldCheck, AlertTriangle, Loader, Trash2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface PredictionResult {
  prediction: "FRAUD" | "SAFE";
  confidence: number;
  risk_score: number;
  risk_level: string;
  timestamp: string;
}

interface CSVRow {
  [key: string]: string | number;
}

interface AnalysisResult {
  prediction: "FRAUD" | "SAFE";
  confidence: number;
  risk_score: number;
  risk_level: string;
  row_data?: CSVRow;
}

// Get API URL from environment variable or use same domain
const getApiUrl = () => {
  // On Vercel, use relative path to Vercel API functions
  if (typeof window !== 'undefined' && !window.location.hostname.includes('localhost')) {
    return window.location.origin;
  }
  
  // For local development
  return 'http://localhost:5000';
};

const Index = () => {
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const apiUrl = getApiUrl();
  
  // CSV data state
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [csvData, setCsvData] = useState<CSVRow[]>([]);
  const [csvColumns, setCsvColumns] = useState<string[]>([]);
  
  // Prediction input
  const [transactionId, setTransactionId] = useState("");
  const [customerId, setCustomerId] = useState("");
  
  // Results
  const [prediction, setPrediction] = useState<PredictionResult | null>(null);
  const [selectedRow, setSelectedRow] = useState<CSVRow | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  // Check if backend is available
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await fetch(`${apiUrl}/api/health`, {
          method: 'GET',
          mode: 'cors',
        });
        if (response.ok) {
          setBackendStatus('online');
        } else {
          setBackendStatus('offline');
        }
      } catch (error) {
        console.warn('Backend health check failed:', error);
        setBackendStatus('offline');
      }
    };
    
    checkBackend();
  }, [apiUrl]);

  // Parse CSV file
  const parseCSV = (file: File): Promise<CSVRow[]> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const csv = e.target?.result as string;
          const lines = csv.trim().split('\n');
          const headers = lines[0].split(',').map(h => h.trim());
          
          const data = lines.slice(1).map((line) => {
            const values = line.split(',').map(v => v.trim());
            const row: CSVRow = {};
            headers.forEach((header, i) => {
              row[header] = values[i];
            });
            return row;
          });
          
          setCsvColumns(headers);
          resolve(data);
        } catch (error) {
          reject(error);
        }
      };
      reader.onerror = () => reject(new Error("Failed to read file"));
      reader.readAsText(file);
    });
  };

  // Handle CSV file upload
  const handleCSVFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (!file.name.endsWith('.csv')) {
        toast({
          title: "Invalid file type",
          description: "Please upload a CSV file.",
          variant: "destructive",
        });
        return;
      }
      
      setCsvFile(file);
      try {
        const data = await parseCSV(file);
        setCsvData(data);
        setPrediction(null);
        setSelectedRow(null);
        
        toast({
          title: "CSV Loaded",
          description: `Loaded ${data.length} rows. Found columns: ${csvColumns.join(", ")}`,
        });
      } catch (error) {
        toast({
          title: "Error parsing CSV",
          description: error instanceof Error ? error.message : "Failed to parse CSV file",
          variant: "destructive",
        });
      }
    }
  };

  // Find row by ID and make prediction
  const handlePrediction = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!csvData.length) {
      toast({
        title: "No data",
        description: "Please upload a CSV file first",
        variant: "destructive",
      });
      return;
    }

    if (!transactionId && !customerId) {
      toast({
        title: "Missing ID",
        description: "Please enter either Transaction ID or Customer ID",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    
    try {
      // Find the row in CSV
      let foundRow = null;
      
      if (transactionId) {
        foundRow = csvData.find(row => 
          String(row['Transaction_ID'] || row['transaction_id'] || '').toLowerCase() === transactionId.toLowerCase()
        );
      }
      
      if (!foundRow && customerId) {
        foundRow = csvData.find(row => 
          String(row['Customer_ID'] || row['customer_id'] || '').toLowerCase() === customerId.toLowerCase()
        );
      }

      if (!foundRow) {
        toast({
          title: "Not found",
          description: "No transaction found with the given ID",
          variant: "destructive",
        });
        setIsLoading(false);
        return;
      }

      setSelectedRow(foundRow);

      // Prepare data for prediction
      const predictionData = {
        transaction_amount: parseFloat(String(foundRow['Transaction_Amount'] || foundRow['amount'] || 0)),
        payment_method: String(foundRow['Payment_Method'] || foundRow['payment_method'] || 'other').toLowerCase(),
        product_category: String(foundRow['Product_Category'] || foundRow['product_category'] || 'other').toLowerCase(),
        quantity: parseInt(String(foundRow['Quantity'] || foundRow['quantity'] || 1)),
        customer_age: parseInt(String(foundRow['Customer_Age'] || foundRow['customer_age'] || 35)),
        device_used: String(foundRow['Device_Used'] || foundRow['device_used'] || 'desktop').toLowerCase(),
        account_age_days: parseInt(String(foundRow['Account_Age_Days'] || foundRow['account_age_days'] || 35)),
        transaction_hour: parseInt(String(foundRow['Transaction_Hour'] || foundRow['transaction_hour'] || 12)),
      };

      const response = await fetch(`${apiUrl}/api/predict`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(predictionData),
        mode: 'cors',
      });

      if (!response.ok) {
        try {
          const errorData = await response.json();
          throw new Error(errorData.error || `API error: ${response.status}`);
        } catch (jsonError) {
          // If response is not JSON, it's probably HTML error page
          const errorText = await response.text();
          console.error('API Error Response:', errorText);
          throw new Error(`API error: ${response.status} ${response.statusText}. The backend may not be running or configured correctly.`);
        }
      }

      let data;
      try {
        data = await response.json();
      } catch (jsonError) {
        console.error('Failed to parse response:', jsonError);
        throw new Error('Invalid response from API. Backend may not be running or is returning HTML instead of JSON.');
      }
      
      setPrediction({
        prediction: data.prediction === "FRAUD" ? "FRAUD" : "SAFE",
        confidence: data.confidence,  // Keep as decimal (0.75 = 75%)
        risk_score: data.risk_score,
        risk_level: data.risk_level,
        timestamp: data.timestamp,
      });

      toast({
        title: "Analysis complete",
        description: `Transaction analyzed: ${data.prediction}`,
        variant: data.prediction === "FRAUD" ? "destructive" : "default",
      });
    } catch (error) {
      console.error("Error:", error);
      toast({
        title: "Analysis failed",
        description: error instanceof Error ? error.message : "Unable to process the request",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Clear all data
  const handleClear = () => {
    setCsvFile(null);
    setCsvData([]);
    setCsvColumns([]);
    setPrediction(null);
    setSelectedRow(null);
    setTransactionId("");
    setCustomerId("");
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="min-h-screen bg-background py-8 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-foreground mb-2">Fraud Guard</h1>
          <p className="text-muted-foreground">Upload CSV file, select transaction by ID, and get instant fraud detection results</p>
          
          {/* Backend Status Warning */}
          {backendStatus === 'offline' && (
            <div className="mt-4 p-3 bg-yellow-100 border border-yellow-400 text-yellow-800 rounded">
              <strong>⚠️ Warning:</strong> Backend API is not available. Make sure your Railway backend is running and VITE_API_URL environment variable is set correctly.
            </div>
          )}
          {backendStatus === 'online' && (
            <div className="mt-4 p-3 bg-green-100 border border-green-400 text-green-800 rounded">
              <strong>✓ Backend Connected</strong>
            </div>
          )}
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          {/* LEFT PANEL - CSV Upload & ID Input */}
          <div className="space-y-6">
            {/* CSV Upload */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="h-5 w-5 text-primary" />
                  Upload CSV File
                </CardTitle>
                <CardDescription>Upload your transaction CSV file</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-center w-full">
                    <label
                      htmlFor="csv-file"
                      className="flex flex-col items-center justify-center w-full h-40 border-2 border-border border-dashed rounded-lg cursor-pointer bg-muted/50 hover:bg-muted transition-colors"
                    >
                      <div className="flex flex-col items-center justify-center pt-5 pb-6">
                        <Upload className="w-10 h-10 mb-2 text-muted-foreground" />
                        <p className="text-sm font-medium text-muted-foreground">
                          {csvFile ? csvFile.name : "Click to upload CSV"}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {csvData.length > 0 ? `${csvData.length} rows loaded` : "CSV format only"}
                        </p>
                      </div>
                      <input
                        id="csv-file"
                        type="file"
                        className="hidden"
                        accept=".csv"
                        onChange={handleCSVFileChange}
                        ref={fileInputRef}
                      />
                    </label>
                  </div>

                  {csvColumns.length > 0 && (
                    <div className="bg-muted p-3 rounded text-sm space-y-2">
                      <p className="font-medium text-xs">CSV Columns Found:</p>
                      <div className="flex flex-wrap gap-1">
                        {csvColumns.map((col, idx) => (
                          <span key={idx} className="bg-background px-2 py-1 rounded text-xs">
                            {col}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* ID Input */}
            {csvData.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Search Transaction</CardTitle>
                  <CardDescription>Enter Transaction ID or Customer ID</CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handlePrediction} className="space-y-4">
                    <div>
                      <Label htmlFor="transaction-id">Transaction ID</Label>
                      <Input
                        id="transaction-id"
                        type="text"
                        placeholder="Enter Transaction ID..."
                        value={transactionId}
                        onChange={(e) => setTransactionId(e.target.value)}
                      />
                    </div>

                    <div>
                      <Label htmlFor="customer-id">Customer ID</Label>
                      <Input
                        id="customer-id"
                        type="text"
                        placeholder="Enter Customer ID..."
                        value={customerId}
                        onChange={(e) => setCustomerId(e.target.value)}
                      />
                    </div>

                    <div className="flex gap-2">
                      <Button type="submit" className="flex-1" disabled={isLoading}>
                        {isLoading ? (
                          <>
                            <Loader className="mr-2 h-4 w-4 animate-spin" />
                            Analyzing...
                          </>
                        ) : (
                          "Analyze"
                        )}
                      </Button>
                      <Button type="button" variant="outline" onClick={handleClear}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </form>
                </CardContent>
              </Card>
            )}
          </div>

          {/* RIGHT PANEL - Results */}
          <div>
            {!prediction ? (
              <Card className="h-full">
                <CardHeader>
                  <CardTitle>Detection Results</CardTitle>
                  <CardDescription>Results will appear here</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-col items-center justify-center h-64 text-center">
                    <ShieldCheck className="h-16 w-16 text-muted-foreground mb-4" />
                    <p className="text-muted-foreground">
                      Upload a CSV and enter an ID to analyze a transaction
                    </p>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardHeader>
                  <CardTitle>Detection Results</CardTitle>
                  <CardDescription>{new Date(prediction.timestamp).toLocaleString()}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Main Result */}
                  <div
                    className={`p-6 rounded-lg border-2 ${
                      prediction.prediction === "FRAUD"
                        ? "bg-destructive/10 border-destructive"
                        : "bg-green-100/20 border-green-500"
                    }`}
                  >
                    <div className="flex items-center gap-3 mb-2">
                      {prediction.prediction === "FRAUD" ? (
                        <AlertTriangle className="h-8 w-8 text-destructive" />
                      ) : (
                        <ShieldCheck className="h-8 w-8 text-green-600" />
                      )}
                      <div>
                        <h3 className="text-2xl font-bold">
                          {prediction.prediction === "FRAUD" ? "⚠️ FRAUD" : "✓ SAFE"}
                        </h3>
                        <p className="text-sm text-muted-foreground">
                          Confidence: {(prediction.confidence * 100).toFixed(2)}%
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Stats */}
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="bg-muted p-3 rounded">
                      <p className="text-muted-foreground text-xs">Risk Score</p>
                      <p className="font-bold text-lg">{(prediction.risk_score * 100).toFixed(2)}%</p>
                    </div>
                    <div className="bg-muted p-3 rounded">
                      <p className="text-muted-foreground text-xs">Risk Level</p>
                      <p className="font-bold capitalize">{prediction.risk_level}</p>
                    </div>
                  </div>

                  {/* Transaction Data */}
                  {selectedRow && (
                    <div className="bg-muted p-4 rounded-lg border space-y-2">
                      <h4 className="font-semibold text-sm mb-3">Transaction Data</h4>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        {Object.entries(selectedRow).map(([key, value], idx) => (
                          <div key={idx} className="truncate">
                            <p className="text-muted-foreground text-xs truncate">{key}:</p>
                            <p className="font-mono text-xs truncate" title={String(value)}>
                              {String(value).slice(0, 20)}{String(value).length > 20 ? '...' : ''}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Warning */}
                  {prediction.prediction === "FRAUD" && (
                    <div className="bg-destructive/10 border border-destructive rounded-lg p-4">
                      <p className="text-sm font-medium text-destructive">⚠️ Alert</p>
                      <p className="text-sm text-muted-foreground mt-1">
                        This transaction shows fraud indicators. Review manually.
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
